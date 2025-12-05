"""
Image Generation Service
Generates blog images using Gemini 3 Pro Image via OpenRouter.
Uploads to Google Drive and makes publicly viewable.

v2: Uses OpenRouter with google/gemini-3-pro-image-preview (best quality)
"""

import os
import re
import json
import time
import base64
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict

import httpx
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaInMemoryUpload

logger = logging.getLogger(__name__)


@dataclass
class CompanyImageData:
    """Company context for image generation."""
    name: str
    industry: str
    language: str
    custom_prompt_instructions: Optional[str] = None


@dataclass
class ImageGenerationRequest:
    """Request for image generation."""
    headline: str
    keyword: str
    company_data: CompanyImageData
    project_folder_id: Optional[str] = None


@dataclass
class ImageGenerationResponse:
    """Response from image generation."""
    success: bool
    image_url: str = ""
    alt_text: str = ""
    drive_file_id: str = ""
    generation_time_seconds: float = 0.0
    error: Optional[str] = None
    prompt_used: Optional[str] = None


class ImageGenerator:
    """
    Handles blog image generation using:
    - Gemini 3 Pro Image via OpenRouter (best quality image generation)
    - Google Drive for storage
    """

    # OpenRouter config
    OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
    IMAGE_MODEL = "google/gemini-3-pro-image-preview"  # Best Google image model
    
    # Drive folder structure: Project → Content Output → Graphics (Final)
    CONTENT_OUTPUT_FOLDER = "04 - Content Output"
    GRAPHICS_FOLDER = "Graphics (Final)"

    # Domain-wide delegation subject (user to impersonate for Drive quota)
    # Set via GOOGLE_DELEGATION_SUBJECT environment variable
    DELEGATION_SUBJECT = os.getenv("GOOGLE_DELEGATION_SUBJECT", "")

    def __init__(self):
        self.openrouter_key = os.getenv("OPENROUTER_API_KEY")
        if not self.openrouter_key:
            raise ValueError("OPENROUTER_API_KEY not configured")
        
        # Initialize Google Drive service
        self.drive_service = self._init_drive_service()
    
    def _init_drive_service(self):
        """Initialize Google Drive API service with domain-wide delegation."""
        # Try multiple env var names for flexibility (different secrets use different names)
        sa_json = (
            os.getenv("GOOGLE_SERVICE_ACCOUNT") or  # Modal google-service-account secret
            os.getenv("SERVICE_ACCOUNT_JSON") or     # gmail-proxy style
            os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON") or
            os.getenv("GOOGLE_CREDENTIALS")
        )
        if not sa_json:
            logger.warning("No service account JSON found in environment")
            return None
        
        try:
            sa_info = json.loads(sa_json)
            logger.info(f"Initializing Drive service as: {sa_info.get('client_email', 'unknown')}")
            
            # Create base credentials
            credentials = service_account.Credentials.from_service_account_info(
                sa_info,
                scopes=["https://www.googleapis.com/auth/drive"]
            )
            
            # Apply domain-wide delegation if configured
            # This allows the SA to use the user's Drive quota
            if self.DELEGATION_SUBJECT:
                credentials = credentials.with_subject(self.DELEGATION_SUBJECT)
                logger.info(f"Using domain-wide delegation as: {self.DELEGATION_SUBJECT}")
            else:
                logger.info("Using service account credentials (no delegation)")
            
            return build("drive", "v3", credentials=credentials)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse service account JSON: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to initialize Drive service: {e}")
            return None

    async def generate(self, request: ImageGenerationRequest) -> ImageGenerationResponse:
        """
        Generate image for a blog article.
        
        Steps:
        1. Build image prompt from article context
        2. Generate image with Gemini 3 Pro Image via OpenRouter
        3. Upload to Google Drive
        4. Make publicly viewable
        5. Return URL and metadata
        """
        start_time = time.time()
        
        try:
            logger.info(f"Starting image generation for: {request.headline[:50]}...")
            
            # Step 1: Build image prompt
            prompt = self._build_image_prompt(request)
            alt_text = self._generate_alt_text(request)
            
            logger.info(f"Generated prompt ({len(prompt)} chars)")
            
            # Step 2: Generate image with Gemini 3 Pro Image via OpenRouter
            image_bytes = await self._generate_image(prompt)
            
            logger.info(f"Generated image ({len(image_bytes)} bytes)")
            
            # Step 3: Get target folder and upload
            # Note: Service accounts can't upload to root - must have a folder ID
            if not request.project_folder_id:
                raise ValueError("project_folder_id required - service accounts cannot upload to Drive root")
            
            if not self.drive_service:
                raise ValueError("Drive service not initialized - check GOOGLE_SERVICE_ACCOUNT env var")
            
            target_folder_id = await self._get_graphics_folder(request.project_folder_id)
            if not target_folder_id:
                # If we can't find/create the Graphics folder, upload directly to project folder
                target_folder_id = request.project_folder_id
                logger.warning(f"Could not find Graphics folder, uploading to project folder: {target_folder_id}")
            
            file_name = f"{self._slugify(request.keyword)}_{int(time.time())}.png"
            drive_file_id = await self._upload_to_drive(image_bytes, file_name, target_folder_id)
            
            # Step 4: Make publicly viewable
            if drive_file_id:
                await self._make_public(drive_file_id)
            
            image_url = f"https://drive.google.com/uc?export=view&id={drive_file_id}" if drive_file_id else ""
            generation_time = time.time() - start_time
            
            logger.info(f"Image uploaded to Drive: {drive_file_id} ({generation_time:.1f}s)")
            
            return ImageGenerationResponse(
                success=True,
                image_url=image_url,
                alt_text=alt_text,
                drive_file_id=drive_file_id,
                generation_time_seconds=generation_time,
                prompt_used=prompt,
            )
            
        except Exception as e:
            logger.error(f"Image generation failed: {e}")
            return ImageGenerationResponse(
                success=False,
                generation_time_seconds=time.time() - start_time,
                error=str(e),
            )

    def _build_image_prompt(self, request: ImageGenerationRequest) -> str:
        """
        Build a concise image prompt optimized for natural, editorial-style results.
        
        Key principles:
        - Specific but not over-specified (Gemini works better with cleaner prompts)
        - Real photography terminology triggers realistic output
        - Describe what you WANT, not what to avoid (negative prompts unreliable)
        - Consistent aspect ratio for blog layouts
        """
        
        # Build the core visual description based on the topic
        topic_desc = self._get_topic_visual(request.keyword, request.company_data.industry)
        
        # Get style based on industry
        style = self._get_industry_style(request.company_data.industry)
        
        prompt_parts = [
            # Core request - clear and specific
            f"Editorial photograph for a business magazine article about {request.keyword}.",
            f"",
            f"Scene: {topic_desc}",
            f"",
            # Photography style - concise technical specs
            f"Photography style:",
            f"- Shot on Canon 5D Mark IV with 35mm lens at f/2.8, ISO 400",
            f"- {style['color_tone']}",
            f"- Natural window light, soft shadows, not harsh or uniform",
            f"- Rule of thirds composition, subject not centered",
            f"- Shallow depth of field with natural background blur",
            f"- Subtle film grain, authentic textures",
            f"",
            # Key realism triggers
            f"Important: Candid documentary moment, not posed. Real office environment with natural wear and personal items visible. No text or logos in image.",
            f"",
            # Aspect ratio - critical for blog consistency
            f"Aspect ratio: 16:9 wide landscape format",
            f"",
            f"Style reference: Editorial photography from The New York Times or Bloomberg Businessweek",
        ]
        
        # Add custom instructions if provided
        if request.company_data.custom_prompt_instructions:
            prompt_parts.extend([
                f"",
                f"Additional requirements: {request.company_data.custom_prompt_instructions}",
            ])
        
        return "\n".join(prompt_parts)
    
    def _get_industry_style(self, industry: str) -> dict:
        """Get color/style preferences based on industry."""
        industry_lower = industry.lower() if industry else ""
        
        styles = {
            "technology": {"color_tone": "Cool neutral tones, modern clean aesthetic"},
            "finance": {"color_tone": "Warm amber tones, sophisticated classic feel"},
            "healthcare": {"color_tone": "Soft warm tones, calming and professional"},
            "manufacturing": {"color_tone": "Industrial neutral tones, high contrast"},
            "retail": {"color_tone": "Bright natural tones, inviting atmosphere"},
            "creative": {"color_tone": "Vibrant but natural colors, artistic energy"},
            "legal": {"color_tone": "Muted professional tones, traditional gravitas"},
            "education": {"color_tone": "Warm inviting tones, approachable feel"},
        }
        
        # Match industry to style
        for key, style in styles.items():
            if key in industry_lower:
                return style
        
        # Default professional style
        return {"color_tone": "Kodak Portra 400 color science - muted warm tones, natural skin"}
    
    def _get_topic_visual(self, keyword: str, industry: str) -> str:
        """
        Generate a specific, grounded visual description based on topic.
        Focuses on real-world scenarios rather than abstract concepts.
        """
        keyword_lower = keyword.lower()
        industry_lower = industry.lower() if industry else ""
        
        # Map common topics to specific, photographable scenes
        # AI & Technology
        if any(term in keyword_lower for term in ['ai', 'artificial intelligence', 'machine learning', 'automation']):
            return "A small team of developers in a modern office, gathered around a laptop. Coffee cups and notebooks scattered naturally. One person gesturing while explaining to colleagues. Lived-in workspace with personal items."
        
        # Customer Experience
        elif any(term in keyword_lower for term in ['customer service', 'support', 'helpdesk', 'customer experience', 'cx']):
            return "Customer service representative at their desk, headset on, genuinely engaged in conversation. Personal items visible - family photo, plant, coffee mug. Natural daylight from nearby window."
        
        # Sustainability & Environment
        elif any(term in keyword_lower for term in ['sustainability', 'green', 'eco', 'environment', 'carbon', 'renewable']):
            return "Workers in a warehouse handling boxes with recycling symbols, electric forklift in background. Industrial space with natural light from skylights. Real workers in practical clothing."
        
        # Marketing & Sales
        elif any(term in keyword_lower for term in ['marketing', 'advertising', 'brand', 'sales', 'growth', 'leads']):
            return "Creative team brainstorming in a conference room, whiteboard with sketches visible. Laptops open, some people standing, relaxed but focused. Afternoon light through blinds."
        
        # Finance & Investment
        elif any(term in keyword_lower for term in ['finance', 'investment', 'banking', 'accounting', 'budget', 'roi']):
            return "Financial analyst at desk with multiple monitors showing charts. Reading glasses, pen in hand, concentrated expression. Traditional office with wood accents and city view."
        
        # Healthcare & Medical
        elif any(term in keyword_lower for term in ['healthcare', 'medical', 'health', 'patient', 'clinical', 'hospital']):
            return "Healthcare professional consulting with a patient in a modern clinic. Warm, reassuring atmosphere. Medical equipment visible but approachable. Natural light, calm colors."
        
        # Software & Tech
        elif any(term in keyword_lower for term in ['software', 'saas', 'digital', 'tech', 'app', 'platform', 'cloud']):
            return "Software engineers pair programming at standing desk, one pointing at screen. Modern tech office with exposed brick, plants. Casual dress, authentic working moment."
        
        # Startup & Business
        elif any(term in keyword_lower for term in ['startup', 'entrepreneur', 'business', 'strategy', 'management']):
            return "Small team meeting in a coworking space, founder presenting to 3-4 people. Laptops, notebooks, whiteboards with post-its. Energy of a real working session."
        
        # E-commerce & Retail
        elif any(term in keyword_lower for term in ['ecommerce', 'retail', 'shopping', 'store', 'fulfillment', 'inventory']):
            return "Warehouse worker scanning packages with handheld device, shelves of products in background. Real fulfillment center with natural movement and activity."
        
        # Education & Training
        elif any(term in keyword_lower for term in ['education', 'learning', 'training', 'onboarding', 'course', 'workshop']):
            return "Adult professional learning session, instructor at whiteboard with small group engaged. Corporate training room with natural light, real learning moment."
        
        # HR & People
        elif any(term in keyword_lower for term in ['hr', 'hiring', 'recruitment', 'employee', 'talent', 'workforce', 'team']):
            return "HR professional in a one-on-one meeting with a candidate or employee. Comfortable office setting, warm atmosphere. Coffee cups on table, genuine conversation."
        
        # Legal & Compliance
        elif any(term in keyword_lower for term in ['legal', 'compliance', 'regulation', 'contract', 'law', 'policy']):
            return "Professional reviewing documents in a traditional office with bookshelves. Pen in hand, serious but not stern expression. Warm wood tones, afternoon light."
        
        # Cybersecurity
        elif any(term in keyword_lower for term in ['security', 'cyber', 'data protection', 'privacy', 'breach']):
            return "IT security professional at workstation with multiple monitors showing dashboards. Focused concentration, modern security operations center. Blue ambient lighting."
        
        # Manufacturing & Operations
        elif any(term in keyword_lower for term in ['manufacturing', 'production', 'factory', 'operations', 'supply chain', 'logistics']):
            return "Factory floor with workers operating machinery or reviewing quality. Industrial setting with natural light from high windows. Safety equipment visible, real work in progress."
        
        # Construction & Real Estate
        elif any(term in keyword_lower for term in ['construction', 'building', 'real estate', 'property', 'architecture']):
            return "Construction site or office with blueprints spread on table. Project managers reviewing plans, hard hats visible. Mix of indoor/outdoor industrial environment."
        
        # Food & Hospitality
        elif any(term in keyword_lower for term in ['food', 'restaurant', 'hospitality', 'hotel', 'catering', 'culinary']):
            return "Commercial kitchen or restaurant setting with staff at work. Professional but warm atmosphere. Natural steam, activity, authentic service moment."
        
        # Data & Analytics
        elif any(term in keyword_lower for term in ['data', 'analytics', 'insights', 'metrics', 'reporting', 'dashboard']):
            return "Analyst at desk reviewing data visualizations on screen, notebook with handwritten notes nearby. Modern office, focused but not sterile. Coffee cup, personal items."
        
        # Communication & Collaboration
        elif any(term in keyword_lower for term in ['communication', 'collaboration', 'meeting', 'remote', 'hybrid', 'video']):
            return "Team in hybrid meeting - some in conference room, others on video screen. Laptops, notebooks, engaged discussion. Modern office with natural light."
        
        else:
            # Smart generic fallback - use industry context
            if industry_lower:
                return f"Professional in {industry} industry setting, engaged in work related to {keyword}. Authentic office or workspace environment with natural lighting. Real working moment with personal items visible, not posed."
            else:
                return f"Professional team in modern office environment discussing {keyword}. Natural meeting room setting with laptops and notebooks. Candid working moment with natural light."

    def _generate_alt_text(self, request: ImageGenerationRequest) -> str:
        """Generate alt text for the image."""
        # Create concise alt text based on headline
        alt_text = f"Blog image: {request.headline}"
        
        # Truncate to 125 chars max for accessibility
        if len(alt_text) > 125:
            alt_text = alt_text[:122] + "..."
        
        return alt_text

    async def _generate_image(self, prompt: str, max_retries: int = 3) -> bytes:
        """
        Generate image using Gemini 3 Pro Image via OpenRouter.
        Includes retry logic with exponential backoff.
        """
        
        headers = {
            "Authorization": f"Bearer {self.openrouter_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/SCAILE-it/openblog",
            "X-Title": "OpenBlog",
        }
        
        payload = {
            "model": self.IMAGE_MODEL,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "modalities": ["image", "text"],
            "stream": False,
        }
        
        last_error = None
        
        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=120.0) as client:
                    response = await client.post(self.OPENROUTER_URL, headers=headers, json=payload)
                    
                    if response.status_code == 429:
                        # Rate limited - wait and retry
                        wait_time = (2 ** attempt) * 5  # 5s, 10s, 20s
                        logger.warning(f"Rate limited, waiting {wait_time}s before retry {attempt + 1}/{max_retries}")
                        await self._async_sleep(wait_time)
                        continue
                    
                    if response.status_code >= 500:
                        # Server error - retry with backoff
                        wait_time = (2 ** attempt) * 2  # 2s, 4s, 8s
                        logger.warning(f"Server error {response.status_code}, retrying in {wait_time}s ({attempt + 1}/{max_retries})")
                        await self._async_sleep(wait_time)
                        continue
                    
                    if not response.is_success:
                        error_text = response.text
                        raise ValueError(f"OpenRouter error: {response.status_code} - {error_text[:200]}")
                
                result = response.json()
                
                # Extract image from response
                image_bytes = self._extract_image_from_response(result)
                if image_bytes:
                    return image_bytes
                
                # No image in response - might be a content policy issue, retry
                logger.warning(f"No image in response, retrying ({attempt + 1}/{max_retries})")
                await self._async_sleep(2)
                
            except httpx.TimeoutException:
                last_error = "Request timed out after 120s"
                logger.warning(f"Timeout on attempt {attempt + 1}/{max_retries}")
                await self._async_sleep(5)
            except Exception as e:
                last_error = str(e)
                if attempt < max_retries - 1:
                    logger.warning(f"Attempt {attempt + 1} failed: {e}, retrying...")
                    await self._async_sleep(2)
                else:
                    raise
        
        raise ValueError(f"Failed after {max_retries} attempts. Last error: {last_error}")
    
    async def _async_sleep(self, seconds: float):
        """Async sleep helper."""
        import asyncio
        await asyncio.sleep(seconds)
    
    def _extract_image_from_response(self, result: dict) -> Optional[bytes]:
        """Extract image bytes from OpenRouter response."""
        choices = result.get("choices", [])
        if not choices:
            return None
        
        message = choices[0].get("message", {})
        images = message.get("images", []) or message.get("image", [])
        
        if not images:
            return None
        
        # Extract base64 data from OpenRouter format
        for img in images:
            if isinstance(img, dict):
                img_url = (
                    img.get("image_url", {}).get("url", "") or
                    img.get("imageUrl", {}).get("url", "") or
                    img.get("url", "") or
                    img.get("b64_json", "")
                )
                if img_url.startswith("data:image"):
                    image_data = img_url.split(",", 1)[1] if "," in img_url else None
                    if image_data:
                        return base64.b64decode(image_data)
                elif img_url:
                    return base64.b64decode(img_url)
            elif isinstance(img, str):
                if img.startswith("data:image"):
                    image_data = img.split(",", 1)[1] if "," in img else img
                    return base64.b64decode(image_data)
                else:
                    return base64.b64decode(img)
        
        return None

    async def _get_graphics_folder(self, project_folder_id: str) -> Optional[str]:
        """Navigate to Graphics (Final) folder within project structure."""
        if not self.drive_service:
            return None
        
        try:
            # Find Content Output folder
            content_folder = self._find_folder(project_folder_id, self.CONTENT_OUTPUT_FOLDER)
            if not content_folder:
                # Create if doesn't exist
                content_folder = self._create_folder(self.CONTENT_OUTPUT_FOLDER, project_folder_id)
            
            # Find or create Graphics folder
            graphics_folder = self._find_folder(content_folder, self.GRAPHICS_FOLDER)
            if not graphics_folder:
                graphics_folder = self._create_folder(self.GRAPHICS_FOLDER, content_folder)
            
            return graphics_folder
            
        except Exception as e:
            logger.error(f"Failed to get graphics folder: {e}")
            return None

    def _find_folder(self, parent_id: str, name: str) -> Optional[str]:
        """Find a folder by name within a parent folder."""
        if not self.drive_service:
            return None
            
        query = f"name='{name}' and '{parent_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
        results = self.drive_service.files().list(
            q=query,
            spaces="drive",
            fields="files(id, name)",
        ).execute()
        
        files = results.get("files", [])
        return files[0]["id"] if files else None

    def _create_folder(self, name: str, parent_id: str) -> str:
        """Create a folder in Drive."""
        if not self.drive_service:
            raise ValueError("Drive service not initialized")
            
        file_metadata = {
            "name": name,
            "mimeType": "application/vnd.google-apps.folder",
            "parents": [parent_id],
        }
        
        folder = self.drive_service.files().create(
            body=file_metadata,
            fields="id"
        ).execute()
        
        return folder.get("id")

    async def _upload_to_drive(
        self, 
        image_bytes: bytes, 
        file_name: str, 
        folder_id: Optional[str] = None
    ) -> str:
        """Upload image to Google Drive."""
        if not self.drive_service:
            raise ValueError("Drive service not initialized - cannot upload")
        
        file_metadata = {"name": file_name}
        if folder_id:
            file_metadata["parents"] = [folder_id]
        
        media = MediaInMemoryUpload(image_bytes, mimetype="image/png")
        
        file = self.drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields="id"
        ).execute()
        
        return file.get("id", "")

    async def _make_public(self, file_id: str) -> None:
        """Make a Drive file publicly viewable."""
        if not self.drive_service:
            return
        
        try:
            self.drive_service.permissions().create(
                fileId=file_id,
                body={"type": "anyone", "role": "reader"},
            ).execute()
        except Exception as e:
            logger.warning(f"Failed to make file public: {e}")

    def _slugify(self, text: str) -> str:
        """Convert text to URL-safe slug."""
        slug = text.lower()
        slug = re.sub(r'[^a-z0-9\s-]', '', slug)
        slug = re.sub(r'[\s_]+', '-', slug)
        slug = re.sub(r'-+', '-', slug)
        return slug.strip('-')[:50]


# Singleton instance
_generator: Optional[ImageGenerator] = None


def get_generator() -> ImageGenerator:
    """Get or create image generator instance."""
    global _generator
    if _generator is None:
        _generator = ImageGenerator()
    return _generator
