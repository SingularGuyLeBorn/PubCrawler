# FILE: src/scrapers/arxiv_scraper.py

import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from typing import List, Dict, Any
import logging

from .base_scraper import BaseScraper


class ArxivScraper(BaseScraper):
    """Scraper for the arXiv API."""
    BASE_URL = 'http://export.arxiv.org/api/query?'

    def __init__(self, task_info: Dict[str, Any], logger: logging.Logger):
        super().__init__(task_info, logger)
        self.search_query = self.task_info.get('search_query', 'cat:cs.AI')
        self.limit = self.task_info.get('limit')
        self.max_results = self.limit if self.limit is not None else self.task_info.get('max_results', 10)
        self.sort_by = self.task_info.get('sort_by', 'submittedDate')
        self.sort_order = self.task_info.get('sort_order', 'descending')

    def _build_url(self) -> str:
        encoded_query = urllib.parse.quote(self.search_query)
        query_params = (f'search_query={encoded_query}&start=0&max_results={self.max_results}&'
                        f'sortBy={self.sort_by}&sortOrder={self.sort_order}')
        return self.BASE_URL + query_params

    def _parse_xml_entry(self, entry: ET.Element, ns: Dict[str, str]) -> Dict[str, Any]:
        def _get_text(element_name: str, namespace: str = 'atom'):
            element = entry.find(f'{namespace}:{element_name}', ns)
            return element.text.strip().replace('\n', ' ') if element is not None and element.text else None

        author_elements = entry.findall('atom:author', ns)
        authors_list = [author.find('atom:name', ns).text for author in author_elements if
                        author.find('atom:name', ns) is not None]

        pdf_url = None
        for link in entry.findall('atom:link', ns):
            if link.attrib.get('title') == 'pdf':
                pdf_url = link.attrib.get('href')
                break

        arxiv_id_url = _get_text('id')
        arxiv_id = arxiv_id_url.split('/abs/')[-1] if arxiv_id_url else "N/A"

        return {"id": arxiv_id, "title": _get_text('title'), "authors": ", ".join(authors_list),
                "abstract": _get_text('summary'), "pdf_url": pdf_url, "source_url": arxiv_id_url}

    def scrape(self) -> List[Dict[str, Any]]:
        full_url = self._build_url()
        self.logger.info(f"    -> Requesting data from arXiv: {self.search_query}")
        papers: List[Dict[str, Any]] = []
        try:
            with urllib.request.urlopen(full_url) as response:
                if response.status != 200:
                    self.logger.error(f"    [✖ ERROR] HTTP request to arXiv failed with status code: {response.status}")
                    return papers
                xml_data = response.read().decode('utf-8')
                ns = {'atom': 'http://www.w3.org/2005/Atom', 'arxiv': 'http://arxiv.org/schemas/atom'}
                root = ET.fromstring(xml_data)
                entries = root.findall('atom:entry', ns)
                for entry in entries:
                    papers.append(self._parse_xml_entry(entry, ns))
                return papers
        except Exception as e:
            self.logger.error(f"    [✖ ERROR] An unexpected error occurred during arXiv scraping: {e}", exc_info=True)
            return papers