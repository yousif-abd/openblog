#!/usr/bin/env python3
"""
Run pipeline with comprehensive logging to debug process death.
"""
import asyncio
import sys
import os
import signal
import traceback
import logging
from datetime import datetime

# Setup comprehensive logging FIRST
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pipeline_debug.log', mode='w'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Log startup
logger.info("=" * 60)
logger.info("PIPELINE DEBUG RUN STARTED")
logger.info(f"Python: {sys.version}")
logger.info(f"PID: {os.getpid()}")
logger.info("=" * 60)

# Signal handlers to catch termination
def signal_handler(signum, frame):
    logger.error(f"🚨 RECEIVED SIGNAL: {signum} ({signal.Signals(signum).name})")
    logger.error(f"Stack trace:\n{''.join(traceback.format_stack(frame))}")
    sys.exit(1)

signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGHUP, signal_handler)

# Import after logging setup
sys.path.insert(0, '.')
from pathlib import Path
from dotenv import load_dotenv

load_dotenv('.env.local')
if 'GOOGLE_GEMINI_API_KEY' in os.environ and 'GEMINI_API_KEY' not in os.environ:
    os.environ['GEMINI_API_KEY'] = os.environ['GOOGLE_GEMINI_API_KEY']

logger.info("Environment loaded")
logger.info(f"GEMINI_API_KEY set: {'GEMINI_API_KEY' in os.environ}")


async def main():
    start_time = datetime.now()
    logger.info(f"Starting main() at {start_time}")
    
    try:
        logger.info("Importing service.api...")
        from service.api import write_blog, BlogGenerationRequest
        logger.info("Import successful")
        
        request = BlogGenerationRequest(
            primary_keyword='AI cybersecurity automation',
            company_url='https://scaile.tech',
            language='en',
            country='US',
        )
        logger.info(f"Request created: {request.primary_keyword}")
        
        logger.info("🚀 Calling write_blog()...")
        result = await write_blog(request)
        logger.info(f"write_blog() returned, success={result.success}")
        
        if not result.success:
            logger.error(f"❌ FAILED: {result.error}")
            return 1
        
        html = result.html_content or result.html or ''
        if not html:
            logger.error("❌ No HTML content returned")
            return 1
        
        output_file = Path('PIPELINE_OUTPUT.html')
        output_file.write_text(html, encoding='utf-8')
        
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info(f"✅ SUCCESS: {len(html):,} chars saved to {output_file}")
        logger.info(f"⏱️  Total time: {elapsed:.1f}s")
        return 0
        
    except asyncio.CancelledError:
        logger.error("🚨 ASYNCIO CANCELLED")
        raise
    except KeyboardInterrupt:
        logger.error("🚨 KEYBOARD INTERRUPT")
        raise
    except Exception as e:
        logger.error(f"🚨 EXCEPTION: {type(e).__name__}: {e}")
        logger.error(traceback.format_exc())
        return 1
    finally:
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info(f"main() exiting after {elapsed:.1f}s")


if __name__ == "__main__":
    logger.info("Entering asyncio.run()")
    try:
        exit_code = asyncio.run(main())
        logger.info(f"asyncio.run() completed with code {exit_code}")
        sys.exit(exit_code)
    except Exception as e:
        logger.error(f"🚨 TOP-LEVEL EXCEPTION: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)

