#!/usr/bin/env python3
"""
OpenBlog CLI - AI-Powered Blog Article Generation

Generate high-quality blog articles using Gemini AI directly, no API keys required.

Usage:
    openblog generate "keyword" --company "Company Name"
    openblog generate "keyword" --company "Company Name" --url https://company.com
    openblog generate "keyword" --company "Company Name" -o article.md
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.markdown import Markdown

console = Console()

# Output directory
DOWNLOADS_DIR = Path.home() / "Downloads"
CONFIG_DIR = Path.home() / ".openblog"
CONFIG_FILE = CONFIG_DIR / "config.json"


def get_config() -> dict:
    """Load configuration."""
    if not CONFIG_FILE.exists():
        return {}
    try:
        return json.loads(CONFIG_FILE.read_text())
    except Exception:
        return {}


def save_config(config: dict) -> None:
    """Save configuration."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(config, indent=2))


def get_gemini_key() -> Optional[str]:
    """Get Gemini API key from environment or config."""
    key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if key:
        return key
    config = get_config()
    return config.get("gemini_api_key")


@click.group()
@click.version_option(version="2.0.0", prog_name="openblog")
def cli():
    """OpenBlog - AI-Powered Blog Article Generation

    Generate high-quality blog articles using Gemini AI.
    No API keys required for CLI usage - just your Gemini API key.
    """
    pass


@cli.command()
@click.option("--key", prompt="Enter your Gemini API key", hide_input=True,
              help="Your Gemini API key")
def configure(key: str):
    """Configure your Gemini API key."""
    config = get_config()
    config["gemini_api_key"] = key
    save_config(config)
    console.print("[green]✓[/green] API key saved to ~/.openblog/config.json")


@cli.command()
@click.argument("keyword")
@click.option("--company", "-c", required=True, help="Company name")
@click.option("--url", "-u", help="Company website URL")
@click.option("--country", default="US", help="Target country (default: US)")
@click.option("--language", default="en", help="Content language (default: en)")
@click.option("--output", "-o", help="Output file path")
@click.option("--json-output", is_flag=True, help="Output as JSON instead of Markdown")
def generate(keyword: str, company: str, url: Optional[str], country: str,
             language: str, output: Optional[str], json_output: bool):
    """Generate a blog article for KEYWORD.

    Examples:
        openblog generate "best CRM software" --company "Acme Corp"
        openblog generate "cloud migration tips" -c "TechStart" -u https://techstart.io
        openblog generate "SEO strategies 2024" -c "Marketing Pro" -o article.md
    """
    gemini_key = get_gemini_key()
    if not gemini_key:
        console.print("[red]Error:[/red] No Gemini API key found.")
        console.print("Set GEMINI_API_KEY environment variable or run: openblog configure")
        sys.exit(1)

    # Set the API key for the pipeline
    os.environ["GEMINI_API_KEY"] = gemini_key
    os.environ["GOOGLE_API_KEY"] = gemini_key

    asyncio.run(_generate_article(keyword, company, url, country, language, output, json_output))


async def _generate_article(keyword: str, company: str, url: Optional[str],
                           country: str, language: str, output: Optional[str],
                           json_output: bool):
    """Generate article using the pipeline."""
    from pipeline.services.content_generation_service import (
        ContentGenerationService,
        GenerationRequest,
        GenerationMode
    )

    console.print(Panel(
        f"[bold]Generating article for:[/bold] {keyword}\n"
        f"[bold]Company:[/bold] {company}\n"
        f"[bold]Country:[/bold] {country} | [bold]Language:[/bold] {language}",
        title="OpenBlog Generator"
    ))

    # Build company info
    company_info = {
        "company_name": company,
        "description": f"{company} - Professional services",
    }
    if url:
        company_info["website"] = url

    # Create generation request
    request = GenerationRequest(
        primary_keyword=keyword,
        company_name=company,
        country=country,
        language=language,
        company_info=company_info,
        mode=GenerationMode.PRODUCTION
    )

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Generating article...", total=None)

        try:
            # Initialize service and generate
            service = ContentGenerationService()
            result = await service.generate_content(request)

            progress.update(task, description="[green]Article generated!")

        except Exception as e:
            progress.update(task, description=f"[red]Error: {str(e)}")
            console.print(f"\n[red]Generation failed:[/red] {str(e)}")
            sys.exit(1)

    if not result.success:
        console.print(f"\n[red]Generation failed:[/red] {result.error_message}")
        sys.exit(1)

    # Extract content
    content = result.content or {}

    # Build output
    if json_output:
        output_content = json.dumps(content, indent=2, ensure_ascii=False)
        file_ext = ".json"
    else:
        # Build markdown
        md_parts = []

        if content.get("headline"):
            md_parts.append(f"# {content['headline']}\n")

        if content.get("meta_description"):
            md_parts.append(f"> {content['meta_description']}\n")

        if content.get("body"):
            md_parts.append(content["body"])

        if content.get("citations"):
            md_parts.append("\n## Sources\n")
            for i, citation in enumerate(content.get("citations", []), 1):
                if isinstance(citation, dict):
                    title = citation.get("title", f"Source {i}")
                    cite_url = citation.get("url", "")
                    md_parts.append(f"{i}. [{title}]({cite_url})")
                else:
                    md_parts.append(f"{i}. {citation}")

        output_content = "\n".join(md_parts)
        file_ext = ".md"

    # Determine output path
    if output:
        output_path = Path(output)
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_keyword = "".join(c if c.isalnum() or c in " -_" else "_" for c in keyword)[:50]
        filename = f"openblog_{safe_keyword}_{timestamp}{file_ext}"
        output_path = DOWNLOADS_DIR / filename

    # Ensure parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write output
    output_path.write_text(output_content, encoding="utf-8")

    console.print(f"\n[green]✓[/green] Article saved to: {output_path}")

    # Show preview
    if not json_output and content.get("headline"):
        console.print("\n[bold]Preview:[/bold]")
        console.print(Panel(
            f"[bold]{content.get('headline', 'Untitled')}[/bold]\n\n"
            f"{content.get('meta_description', '')[:200]}...",
            title="Article Preview"
        ))

    # Show stats
    if result.quality_report:
        console.print(f"\n[bold]Quality Score:[/bold] {result.quality_report.overall_score}/100")

    console.print(f"[bold]Generation Time:[/bold] {result.execution_time_ms/1000:.1f}s")


@cli.command()
def info():
    """Show configuration and environment info."""
    console.print(Panel("[bold]OpenBlog Configuration[/bold]", title="Info"))

    gemini_key = get_gemini_key()
    if gemini_key:
        console.print(f"[green]✓[/green] Gemini API Key: {gemini_key[:8]}...{gemini_key[-4:]}")
    else:
        console.print("[yellow]![/yellow] No Gemini API key configured")

    console.print(f"\nConfig file: {CONFIG_FILE}")
    console.print(f"Output directory: {DOWNLOADS_DIR}")


if __name__ == "__main__":
    cli()
