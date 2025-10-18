# FILE: src/scrapers/html_scraper.py

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from tqdm import tqdm
import time

from src.scrapers.base_scraper import BaseScraper


class HTMLScraper(BaseScraper):
    """
    Scraper for conferences with static HTML pages (e.g., CVF, PMLR, ACL).
    """

    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    PARSER_CONFIGS = {
        'cvf': {
            "index_paper_links": 'dt.ptitle > a[href$=".html"]',
            "title": "#papertitle",
            "authors": "#authors > b > i",
            "abstract": "#abstract",
            "pdf_link": 'meta[name="citation_pdf_url"]'
        },
        'pmlr': {
            "index_paper_links": 'div.paper .links a:nth-of-type(1)[href$=".html"]',
            "title": "h1.title",
            "authors": "span.authors",
            "abstract": "div.abstract",
            "pdf_link": 'div.paper .links a[href$=".pdf"]'
        },
        'acl': {
            "index_paper_links": 'p.d-sm-flex > strong > a[href]',
            "title": "h2#title > a",
            "authors": "p.lead",
            "abstract": 'div.acl-abstract > span',
            "pdf_link": 'a.btn-primary[href$=".pdf"]'
        }
    }

    def scrape(self):
        index_url = self.task_info["url"]
        parser_type = self.task_info["parser_type"]
        limit = self.task_info.get("limit")  # Get limit from task info

        if parser_type not in self.PARSER_CONFIGS:
            self.logger.error(f"Unknown parser type '{parser_type}' for URL: {index_url}")
            return []

        self.logger.info(f"Scraping HTML index page: {index_url} using '{parser_type}' parser")

        try:
            index_response = requests.get(index_url, headers=self.HEADERS, timeout=20)
            index_response.raise_for_status()

            soup = BeautifulSoup(index_response.content, 'lxml')
            paper_links = soup.select(self.PARSER_CONFIGS[parser_type]["index_paper_links"])

            if not paper_links:
                self.logger.warning(
                    f"Could not find any paper links on {index_url} with selector '{self.PARSER_CONFIGS[parser_type]['index_paper_links']}'")
                return []

            self.logger.info(f"Found {len(paper_links)} potential paper links.")

            # --- LIMIT LOGIC APPLIED HERE ---
            if limit is not None and len(paper_links) > limit:
                self.logger.info(f"Applying limit: processing first {limit} papers out of {len(paper_links)}.")
                paper_links = paper_links[:limit]

            papers = []
            for link_tag in tqdm(paper_links, desc=f"Scraping {parser_type} pages"):
                try:
                    paper_url = urljoin(index_url, link_tag['href'])
                    paper_details = self._scrape_paper_page(paper_url, parser_type)
                    if paper_details:
                        papers.append(paper_details)
                    time.sleep(0.2)
                except Exception as e:
                    self.logger.error(f"Error scraping a single paper link. URL: {link_tag.get('href')}. Error: {e}")
                    continue

            return papers

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to fetch index page {index_url}: {e}")
            return []

    def _scrape_paper_page(self, url: str, parser_type: str):
        try:
            response = requests.get(url, headers=self.HEADERS, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'lxml')

            parser_map = self.PARSER_CONFIGS[parser_type]

            title = soup.select_one(parser_map['title'])
            authors = soup.select_one(parser_map['authors'])
            abstract = soup.select_one(parser_map['abstract'])
            pdf_link_tag = soup.select_one(parser_map['pdf_link'])

            pdf_url = None
            if pdf_link_tag:
                pdf_url = pdf_link_tag.get('content') or pdf_link_tag.get('href')
                if not pdf_url.startswith('http'):
                    pdf_url = urljoin(url, pdf_url)

            return {
                'title': title.get_text(strip=True) if title else 'N/A',
                'authors': authors.get_text(strip=True).replace('\n', ' ').replace('\t', ' ') if authors else 'N/A',
                'abstract': abstract.get_text(strip=True) if abstract else 'N/A',
                'pdf_url': pdf_url,
                'source_url': url
            }

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to scrape paper page {url}: {e}")
            return None

# END OF FILE: src/scrapers/html_scraper.py