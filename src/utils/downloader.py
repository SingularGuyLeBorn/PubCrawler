# FILE: src/utils/downloader.py

import requests
import re
from pathlib import Path
from tqdm import tqdm


def download_pdfs(papers: list, task_name: str, output_dir: Path):
    """
    Downloads PDF files for a list of papers into a dedicated subfolder.
    """
    if not papers:
        return

    # Create a dedicated directory for the task's PDFs
    pdf_task_dir = output_dir / task_name / "pdfs"
    pdf_task_dir.mkdir(parents=True, exist_ok=True)

    print(f"Downloading PDFs to: {pdf_task_dir.resolve()}")

    for paper in tqdm(papers, desc=f"Downloading PDFs for {task_name}"):
        pdf_url = paper.get('pdf_url')
        title = paper.get('title', 'untitled')

        if not pdf_url:
            print(f"\n[SKIP] No PDF URL for title: {title}")
            continue

        # Sanitize the title to create a valid filename
        # Remove invalid characters and limit length
        sanitized_title = re.sub(r'[\\/*?:"<>|]', "", title)
        sanitized_title = sanitized_title.replace('\n', ' ').replace('\r', '')
        filename = (sanitized_title[:150] + ".pdf")  # Limit length

        filepath = pdf_task_dir / filename

        if filepath.exists():
            # print(f"\n[SKIP] File already exists: {filename}")
            continue

        try:
            response = requests.get(pdf_url, stream=True, timeout=30, headers={'User-Agent': 'Mozilla/5.0'})
            response.raise_for_status()

            # Get total file size for progress bar
            total_size = int(response.headers.get('content-length', 0))
            block_size = 1024  # 1KB

            with open(filepath, 'wb') as f, tqdm(
                    total=total_size,
                    unit='iB',
                    unit_scale=True,
                    desc=f"  -> {filename[:30]}...",
                    leave=False  # Don't leave nested progress bar after completion
            ) as pbar:
                for data in response.iter_content(block_size):
                    f.write(data)
                    pbar.update(len(data))

        except requests.exceptions.RequestException as e:
            print(f"\n[ERROR] Failed to download {pdf_url}. Reason: {e}")
            # Clean up partially downloaded file
            if filepath.exists():
                filepath.unlink()
        except Exception as e:
            print(f"\n[ERROR] An unexpected error occurred for {pdf_url}. Reason: {e}")
            if filepath.exists():
                filepath.unlink()

# END OF FILE: src/utils/downloader.py