# FILE: src/scrapers/iclr_scraper.py

import openreview
import openreview.api
import re
import numpy as np
from tqdm import tqdm
from itertools import islice
import time
from typing import List, Dict, Any

from .base_scraper import BaseScraper

class IclrScraper(BaseScraper):
    """专门用于 ICLR (OpenReview) 的爬虫。"""

    def _get_v1_notes_with_retry(self, client, venue_id, limit, max_retries=3):
        """为 openreview v1 的 get_all_notes 添加简单的重试逻辑。"""
        for attempt in range(max_retries):
            try:
                self.logger.info(f"    -> [V1 API] 正在尝试获取笔记 (第 {attempt + 1}/{max_retries} 次)...")
                notes_iterator = client.get_all_notes(content={'venueid': venue_id})
                notes_list = list(islice(notes_iterator, limit)) if limit else list(notes_iterator)
                return notes_list
            except Exception as e:
                self.logger.warning(f"    -> [V1 API] 第 {attempt + 1} 次尝试失败: {e}")
                if attempt < max_retries - 1:
                    time.sleep(5 * (attempt + 1))  # 等待时间逐渐增加
                else:
                    self.logger.error(f"    -> [V1 API] 达到最大重试次数，获取失败。")
                    raise e # 抛出最终的异常

    def scrape(self) -> List[Dict[str, Any]]:
        api_version = self.task_info.get("api_version", "v2")
        venue_id = self.task_info["venue_id"]
        limit = self.task_info.get("limit")
        fetch_reviews = self.task_info.get("fetch_reviews", False)

        self.logger.info(f"    -> 使用 OpenReview API v{api_version} for venue: {venue_id}")
        if fetch_reviews:
            self.logger.info("    -> 已启用审稿信息获取。由于API速率限制，速度会变慢。")

        try:
            notes_list = []
            if api_version == "v1":
                client = openreview.Client(baseurl='https://api.openreview.net')
                # <-- 使用带重试的函数
                notes_list = self._get_v1_notes_with_retry(client, venue_id, limit)
            else:  # API v2
                client = openreview.api.OpenReviewClient(baseurl='https://api2.openreview.net')
                # V2 API 通常更稳定，但也可以为其添加重试
                notes_list = client.get_notes(content={'venueid': venue_id}, limit=limit) if limit else list(
                    client.get_all_notes(content={'venueid': venue_id}))

            if not notes_list:
                return []

            self.logger.info(f"    -> 找到了 {len(notes_list)} 份提交进行处理。")
            papers = []
            client_v2_for_reviews = openreview.api.OpenReviewClient(
                baseurl='https://api2.openreview.net') if fetch_reviews else None

            pbar_desc = f"    -> 正在解析 ICLR 论文"
            for note in tqdm(notes_list, desc=pbar_desc, leave=True):
                paper_details = self._parse_note(note)
                if fetch_reviews and client_v2_for_reviews:
                    time.sleep(0.3)
                    review_details = self._fetch_review_details(client_v2_for_reviews, note.id)
                    paper_details.update(review_details)
                papers.append(paper_details)
            return papers

        except Exception as e:
            self.logger.error(f"    [✖ ERROR] ICLR OpenReview 抓取失败: {e}", exc_info=True)
            return []

    def _parse_note(self, note: Any) -> Dict[str, Any]:
        """解析单个 OpenReview note 对象。"""
        content = note.content
        def get_field_robust(field_name, default_value):
            field_data = content.get(field_name)
            if isinstance(field_data, dict):
                return field_data.get('value', default_value)
            return field_data if field_data is not None else default_value
        return {'id': note.id, 'title': get_field_robust('title', 'N/A'), 'authors': ', '.join(get_field_robust('authors', [])), 'abstract': get_field_robust('abstract', 'N/A'), 'pdf_url': f"https://openreview.net/pdf?id={note.id}", 'source_url': f"https://openreview.net/forum?id={note.id}"}

    def _fetch_review_details(self, client: openreview.api.OpenReviewClient, forum_id: str) -> Dict[str, Any]:
        """获取单个论文的审稿信息。"""
        ratings, decision = [], 'N/A'
        try:
            related_notes = client.get_notes(forum=forum_id)
            for note in related_notes:
                if any(re.search(r'/Decision', inv, re.IGNORECASE) for inv in note.invitations):
                    decision_value = note.content.get('decision', {}).get('value')
                    if decision_value: decision = str(decision_value)
                if any(re.search(r'/Review|/Official_Review', inv, re.IGNORECASE) for inv in note.invitations):
                    rating_val = note.content.get('rating', {}).get('value')
                    if isinstance(rating_val, str):
                        match = re.search(r'^\d+', rating_val)
                        if match: ratings.append(int(match.group(0)))
                    elif isinstance(rating_val, (int, float)):
                        ratings.append(int(rating_val))
        except Exception as e:
            self.logger.debug(f"获取审稿信息失败 forum_id={forum_id}: {e}")
        return {'decision': decision, 'avg_rating': round(np.mean(ratings), 2) if ratings else None, 'review_ratings': ratings}