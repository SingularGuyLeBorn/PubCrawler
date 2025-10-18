# FILE: src/processor.py

import logging
import os
import requests
import zipfile
import re
from typing import Iterator, Dict, Any
from tqdm import tqdm

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class Processor:
    """
    Processes a stream of paper data to generate output files.
    - A summary.txt file for LLM analysis.
    - A compressed .zip file containing all downloaded PDFs.
    """

    def __init__(self, output_dir: str = 'output', download_pdfs: bool = False):
        self.output_dir = output_dir
        self.download_pdfs = download_pdfs
        self.summary_path = os.path.join(self.output_dir, 'summary.txt')
        self.zip_path = os.path.join(self.output_dir, 'papers.zip')

        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)

    def _sanitize_filename(self, title: str) -> str:
        """Creates a safe filename from a paper title."""
        # Remove invalid characters
        sanitized = re.sub(r'[\\/*?:"<>|]', "", title)
        # Truncate to a reasonable length
        return (sanitized[:100] + '.pdf') if len(sanitized) > 100 else (sanitized + '.pdf')

    def _format_summary_entry(self, paper_data: Dict[str, Any]) -> str:
        """Formats a single paper's data into the specified text format."""
        # Safely get all required fields
        title = paper_data.get('title', 'N/A')
        authors = ", ".join(paper_data.get('authors', []))
        conference = paper_data.get('conference', 'N/A')
        year = paper_data.get('year', 'N/A')
        source_url = paper_data.get('source_url', 'N/A')
        pdf_link = paper_data.get('pdf_link', 'N/A')
        abstract = paper_data.get('abstract', 'No abstract available.')
        reviews = paper_data.get('reviews', [])

        # Build the entry string
        entry = []
        entry.append("=" * 80)
        entry.append(f"Title: {title}")
        entry.append(f"Authors: {authors}")
        entry.append(f"Conference: {conference} {year}")
        entry.append(f"Source URL: {source_url}")
        entry.append(f"PDF Link: {pdf_link}")
        entry.append("\n--- Abstract ---")
        entry.append(abstract)

        if reviews:
            entry.append(f"\n--- Reviews ({len(reviews)}) ---")
            for i, review in enumerate(reviews, 1):
                review_title = review.get('title', 'N/A')
                review_comment = review.get('comment', 'No comment.')
                review_decision = review.get('decision', None)
                review_rating = review.get('rating', None)

                entry.append(f"\n[Review {i}]")
                entry.append(f"Title: {review_title}")
                if review_decision:
                    entry.append(f"Decision: {review_decision}")
                if review_rating:
                    entry.append(f"Rating: {review_rating}")
                entry.append(f"Comment: {review_comment}")

        entry.append("=" * 80 + "\n\n")
        return "\n".join(entry)

    def _download_pdf(self, pdf_url: str, filename: str, zip_file: zipfile.ZipFile):
        """Downloads a PDF in streaming fashion and adds it to the zip archive."""
        if not pdf_url:
            logging.warning(f"Skipping download for '{filename}' due to missing URL.")
            return

        temp_pdf_path = os.path.join(self.output_dir, filename)
        try:
            logging.info(f"Downloading: {pdf_url}")
            with requests.get(pdf_url, stream=True, timeout=30, headers=HEADERS) as r:
                r.raise_for_status()
                with open(temp_pdf_path, 'wb') as f:
                    # Download in chunks to keep memory usage low
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)

            # Add the downloaded file to the zip archive
            zip_file.write(temp_pdf_path, arcname=filename)
            logging.info(f"Added to zip: {filename}")

        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to download {pdf_url}: {e}")
        except Exception as e:
            logging.error(f"An error occurred while handling {filename}: {e}")
        finally:
            # Clean up the temporary PDF file
            if os.path.exists(temp_pdf_path):
                os.remove(temp_pdf_path)

    def process_papers(self, papers_iterator: Iterator[Dict[str, Any]], total: int):
        """
        The main processing pipeline. Iterates through papers and writes to files.
        """
        logging.info("Starting paper processing pipeline...")
        logging.info(f"Summary will be saved to: {self.summary_path}")
        if self.download_pdfs:
            logging.info(f"PDFs will be saved to: {self.zip_path}")
        else:
            logging.info("PDF download is disabled.")

        # Clear summary file at the start of a run
        with open(self.summary_path, 'w', encoding='utf-8') as f:
            f.write("--- PubCrawler Summary ---\n\n")

        try:
            with zipfile.ZipFile(self.zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Use tqdm for a nice progress bar
                pbar = tqdm(papers_iterator, total=total, desc="Processing papers")
                for paper_data in pbar:
                    # 1. Format and append to summary.txt
                    summary_entry = self._format_summary_entry(paper_data)
                    with open(self.summary_path, 'a', encoding='utf-8') as f:
                        f.write(summary_entry)

                    # 2. Download PDF if enabled
                    if self.download_pdfs:
                        filename = self._sanitize_filename(paper_data.get('title', 'untitled'))
                        self._download_pdf(paper_data.get('pdf_link'), filename, zipf)

        except Exception as e:
            logging.error(f"A critical error occurred during processing: {e}")

        logging.info("Processing pipeline complete.")

# END OF FILE: src/processor.py