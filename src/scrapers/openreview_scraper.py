# FILE: src/scrapers/openreview_scraper.py

import openreview
import openreview.api
import re
import numpy as np
from tqdm import tqdm
from itertools import islice
import time
import logging
from typing import List, Dict, Any

from src.scrapers.base_scraper import BaseScraper


class OpenReviewScraper(BaseScraper):
    """Scraper for conferences hosted on OpenReview, supporting both v1 and v2 APIs and optional review data fetching."""

    def __init__(self, task_info: Dict[str, Any], logger: logging.Logger):
        super().__init__(task_info, logger)

    def scrape(self) -> List[Dict[str, Any]]:
        api_version = self.task_info.get("api_version", "v2")
        venue_id = self.task_info["venue_id"]
        limit = self.task_info.get("limit")
        fetch_reviews = self.task_info.get("fetch_reviews", False)

        self.logger.info(f"    -> Using OpenReview API v{api_version} for venue: {venue_id}")
        if fetch_reviews:
            self.logger.info("    -> Review fetching is ENABLED. This will be slower due to API rate limits.")

        try:
            if api_version == "v1":
                notes_list = self._scrape_v1(venue_id, limit)
            else:
                notes_list = self._scrape_v2(venue_id, limit)

            if not notes_list:
                return []

            self.logger.info(f"    -> Found {len(notes_list)} submissions to process.")

            papers = []
            client_v2 = openreview.api.OpenReviewClient(
                baseurl='https://api2.openreview.net') if fetch_reviews else None

            # --- 核心修复点: `leave=True` ---
            pbar_desc = f"    -> Parsing {self.task_info.get('conference', 'papers')}"
            for note in tqdm(notes_list, desc=pbar_desc, leave=True):
                paper_details = self._parse_note(note)
                if fetch_reviews and client_v2:
                    forum_id = note.id
                    time.sleep(0.3)  # Rate limit
                    review_details = self._fetch_review_details(client_v2, forum_id)
                    paper_details.update(review_details)
                papers.append(paper_details)
            return papers

        except Exception as e:
            self.logger.error(f"    [✖ ERROR] Failed to scrape OpenReview for {venue_id}: {e}", exc_info=True)
            return []

    def _scrape_v1(self, venue_id, limit):
        client_v1 = openreview.Client(baseurl='https://api.openreview.net')
        notes_iterator = client_v1.get_all_notes(content={'venueid': venue_id})
        if limit:
            self.logger.info(f"    -> Applying limit: processing first {limit} papers.")
            return list(islice(notes_iterator, limit))
        return list(notes_iterator)

    def _scrape_v2(self, venue_id, limit):
        client_v2 = openreview.api.OpenReviewClient(baseurl='https://api2.openreview.net')
        if limit:
            self.logger.info(f"    -> Applying limit: fetching first {limit} papers using API limit.")
            return client_v2.get_notes(content={'venueid': venue_id}, limit=limit)
        notes_iterator = client_v2.get_all_notes(content={'venueid': venue_id})
        return list(notes_iterator)

    def _parse_note(self, note):
        content = note.content

        def get_field_robust(field_name, default_value):
            field_data = content.get(field_name)
            if isinstance(field_data, dict):
                return field_data.get('value', default_value)
            return field_data if field_data is not None else default_value

        return {
            'id': note.id,
            'title': get_field_robust('title', 'N/A'),
            'authors': ', '.join(get_field_robust('authors', [])),
            'abstract': get_field_robust('abstract', 'N/A'),
            'keywords': ', '.join(get_field_robust('keywords', [])),
            'pdf_url': f"https://openreview.net/pdf?id={note.id}",
            'source_url': f"https://openreview.net/forum?id={note.id}"
        }

    def _fetch_review_details(self, client, forum_id):
        try:
            related_notes = client.get_notes(forum=forum_id)
        except Exception:
            return {'decision': 'N/A', 'avg_rating': None, 'review_ratings': []}
        ratings, decision = [], 'N/A'
        for note in related_notes:
            if any(re.search(r'/Decision', inv, re.IGNORECASE) for inv in note.invitations):
                decision_value = note.content.get('decision', {}).get('value')
                if decision_value: decision = self._clean_decision(decision_value)
        for note in related_notes:
            if any(re.search(r'/Review|/Official_Review', inv, re.IGNORECASE) for inv in note.invitations):
                rating_value = note.content.get('rating', {}).get('value')
                if isinstance(rating_value, str):
                    match = re.search(r'^\d+', rating_value)
                    if match: ratings.append(int(match.group(0)))
                elif isinstance(rating_value, (int, float)):
                    ratings.append(int(rating_value))
        return {'decision': decision, 'avg_rating': round(np.mean(ratings), 2) if ratings else None,
                'review_ratings': ratings}

    def _clean_decision(self, decision_str):
        decision_str = str(decision_str).lower()
        if 'oral' in decision_str: return 'Oral'
        if 'spotlight' in decision_str: return 'Spotlight'
        if 'poster' in decision_str: return 'Poster'
        if 'reject' in decision_str: return 'Reject'
        return 'Accept'