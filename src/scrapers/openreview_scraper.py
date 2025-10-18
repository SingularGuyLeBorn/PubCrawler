# FILE: src/scrapers/openreview_scraper.py

import openreview
import openreview.api
from tqdm import tqdm

from src.scrapers.base_scraper import BaseScraper


class OpenReviewScraper(BaseScraper):
    """Scraper for conferences hosted on OpenReview."""

    def scrape(self):
        """
        Fetches paper data from OpenReview using the v1 or v2 API.
        """
        api_version = self.task_info.get("api_version", "v2")
        venue_id = self.task_info["venue_id"]
        limit = self.task_info.get("limit")  # Get limit from task info

        self.logger.info(f"Using OpenReview API v{api_version} for venue: {venue_id}")

        try:
            notes_list = []
            if api_version == "v1":
                client = openreview.Client(baseurl='https://api.openreview.net')
                notes_iterator = client.get_all_notes(content={'venueid': venue_id}, details='original')
                notes_list = list(notes_iterator)  # Must convert iterator to list to slice
            else:  # API v2
                client = openreview.api.OpenReviewClient(baseurl='https://api2.openreview.net')
                notes_iterator = client.get_all_notes(content={'venueid': venue_id})
                notes_list = list(notes_iterator)  # Must convert iterator to list to slice

            if not notes_list:
                self.logger.warning(f"No papers found for venue_id: {venue_id}")
                return []

            self.logger.info(f"Found {len(notes_list)} total notes.")

            # --- LIMIT LOGIC APPLIED HERE (BEFORE PARSING) ---
            if limit is not None and len(notes_list) > limit:
                self.logger.info(f"Applying limit: processing first {limit} papers out of {len(notes_list)}.")
                notes_list = notes_list[:limit]

            papers = [self._parse_note(note) for note in tqdm(notes_list, desc=f"Parsing {venue_id}")]
            papers = [p for p in papers if p]
            return papers

        except Exception as e:
            self.logger.error(f"Failed to scrape OpenReview for {venue_id}: {e}", exc_info=True)
            return []

    def _parse_note(self, note):
        """
        Parses an OpenReview Note object into a standardized paper dictionary.
        This version is robust to handle both v1 (flat) and v2 (nested dict) structures.
        """
        try:
            content = note.content if hasattr(note, 'content') else note

            def get_field_value(field_name, default_value):
                """A helper to safely extract values from either v1 or v2 format."""
                field = content.get(field_name)
                if isinstance(field, dict):
                    # Handles v2 format like {'value': '...'}
                    return field.get('value', default_value)
                elif field is not None:
                    # Handles v1 format (direct value)
                    return field
                return default_value

            title = get_field_value('title', 'N/A')
            abstract = get_field_value('abstract', 'N/A')
            authors_list = get_field_value('authors', [])
            keywords_list = get_field_value('keywords', [])

            # PDF URL logic is slightly more complex
            pdf_url = None
            pdf_field = content.get('pdf')
            if isinstance(pdf_field, dict):  # v2 format
                pdf_url = pdf_field.get('url')
            elif isinstance(pdf_field, str):  # v1 format
                pdf_url = pdf_field

            if not pdf_url:
                bibtex = get_field_value('_bibtex', '')
                if 'url={' in bibtex:
                    pdf_url = bibtex.split('url={')[-1].split('}')[0]

            if pdf_url and pdf_url.startswith('/pdf/'):
                pdf_url = f"https://openreview.net{pdf_url}"

            return {
                'title': title,
                'authors': ', '.join(authors_list),
                'abstract': abstract,
                'pdf_url': pdf_url,
                'keywords': ', '.join(keywords_list),
                'raw_data': note.to_json() if hasattr(note, 'to_json') else str(note)
            }
        except Exception as e:
            self.logger.error(f"Failed to parse a note: {e}", exc_info=True)
            self.logger.debug(f"Problematic note data: {note}")
            return None
# END OF FILE: src/scrapers/openreview_scraper.py