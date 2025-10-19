# FILE: src/utils/downloader.py (Tqdm Removed Version)

import requests
import re
from pathlib import Path

from src.config import get_logger

logger = get_logger(__name__)

def download_single_pdf(paper: dict, pdf_dir: Path):
    """
    Downloads a single PDF file. This function is now designed to be called within a loop
    controlled by an external tqdm instance.
    """
    pdf_url = paper.get('pdf_url')
    title = paper.get('title', 'untitled')

    if not pdf_url:
        logger.warning(f"    -> Skipping download (no PDF URL): {title[:50]}...")
        return False

    sanitized_title = re.sub(r'[\\/*?:"<>|]', "", title).replace('\n', ' ').replace('\r', '')
    filename = (sanitized_title[:150] + ".pdf")
    filepath = pdf_dir / filename

    if filepath.exists():
        return True # Skip if already exists

    try:
        response = requests.get(pdf_url, stream=True, timeout=30, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()

        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"    [✖ ERROR] Failed to download {pdf_url}. Reason: {e}")
        if filepath.exists(): filepath.unlink() # Clean up failed download
        return False
    except Exception as e:
        logger.error(f"    [✖ ERROR] An unexpected error occurred for {pdf_url}. Reason: {e}")
        if filepath.exists(): filepath.unlink()
        return False