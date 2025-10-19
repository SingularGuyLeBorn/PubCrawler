# FILE: src/scrapers/html_scraper.py (最终完美版)

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from tqdm import tqdm
import time
import logging
from typing import List, Dict, Any

from src.scrapers.base_scraper import BaseScraper


class HTMLScraper(BaseScraper):
    """Scraper for conferences with static HTML pages (e.g., CVF, PMLR, ACL)."""
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}

    PARSER_CONFIGS = {
        'cvf': {
            "index_paper_links": 'dt.ptitle > a[href$=".html"]',
            "title": "#papertitle", "authors": "#authors > b > i", "abstract": "#abstract",
            "pdf_link": 'meta[name="citation_pdf_url"]'
        },
        'pmlr': {
            "index_paper_links": 'div.paper .links a:nth-of-type(1)[href$=".html"]',
            "title": "h1.title", "authors": "span.authors", "abstract": "div.abstract",
            "pdf_link_from_html_url": True
        },
        'acl': {
            # --- 最终修复点: 使用最精确的选择器, 只抓取 <strong> 标签内的标题链接 ---
            "index_paper_links": 'p.d-sm-flex strong a.align-middle',

            # 详情页的选择器是正确的，保持不变
            "title": "h2#title",
            "authors": "p.lead",
            "abstract": 'div.acl-abstract > span',
            "pdf_link": 'meta[name="citation_pdf_url"]'
        }
    }

    def __init__(self, task_info: Dict[str, Any], logger: logging.Logger):
        super().__init__(task_info, logger)

    def scrape(self) -> List[Dict[str, Any]]:
        index_url = self.task_info["url"]
        parser_type = self.task_info["parser_type"]
        limit = self.task_info.get("limit")

        if parser_type not in self.PARSER_CONFIGS:
            self.logger.error(f"    [✖ ERROR] Unknown parser type '{parser_type}' for URL: {index_url}")
            return []

        self.logger.info(f"    -> Scraping HTML index page: {index_url} using '{parser_type}' parser")
        try:
            index_response = requests.get(index_url, headers=self.HEADERS, timeout=20)
            if index_response.status_code == 404:
                self.logger.warning(f"    -> Page not found (404): {index_url}")
                return []
            index_response.raise_for_status()

            soup = BeautifulSoup(index_response.content, 'lxml')
            paper_links = soup.select(self.PARSER_CONFIGS[parser_type]["index_paper_links"])

            if not paper_links:
                self.logger.warning(
                    f"    -> Could not find any paper links on index page with selector '{self.PARSER_CONFIGS[parser_type]['index_paper_links']}'")
                return []

            self.logger.info(f"    -> Found {len(paper_links)} potential paper links.")
            if limit is not None and len(paper_links) > limit:
                self.logger.info(f"    -> Applying limit: processing first {limit} papers.")
                paper_links = paper_links[:limit]

            papers = []
            pbar_desc = f"    -> Scraping {parser_type} pages"
            for link_tag in tqdm(paper_links, desc=pbar_desc, leave=True):
                try:
                    paper_url = urljoin(index_url, link_tag['href'])
                    paper_details = self._scrape_paper_page(paper_url, parser_type)
                    if paper_details: papers.append(paper_details)
                    time.sleep(0.1)
                except Exception as e:
                    self.logger.debug(f"    -> Failed to scrape detail page {link_tag.get('href', '')}: {e}")
                    continue
            return papers
        except requests.exceptions.RequestException as e:
            self.logger.error(f"    [✖ ERROR] Failed to fetch index page {index_url}: {e}")
            return []

    def _scrape_paper_page(self, url: str, parser_type: str) -> Dict[str, Any]:
        try:
            response = requests.get(url, headers=self.HEADERS, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'lxml')
            parser_map = self.PARSER_CONFIGS[parser_type]

            title = soup.select_one(parser_map['title']).get_text(strip=True) if soup.select_one(
                parser_map['title']) else 'N/A'

            authors_tags = soup.select(parser_map['authors'])
            authors = ", ".join(
                [tag.get_text(strip=True).replace("\n", "").strip() for tag in authors_tags]) if authors_tags else 'N/A'

            abstract_tag = soup.select_one(parser_map['abstract'])
            abstract = abstract_tag.get_text(strip=True) if abstract_tag else 'N/A'

            pdf_url = None
            pdf_link_tag = soup.select_one(parser_map['pdf_link'])
            if pdf_link_tag:
                pdf_url = pdf_link_tag.get('content') or pdf_link_tag.get('href')
                if pdf_url and not pdf_url.startswith('http'):
                    pdf_url = urljoin(url, pdf_url)

            paper_id = url.strip('/').split('/')[-1]

            return {'id': paper_id, 'title': title, 'authors': authors, 'abstract': abstract, 'pdf_url': pdf_url,
                    'source_url': url}
        except Exception as e:
            self.logger.debug(f"    -> Error parsing paper page {url}: {e}")
            return None