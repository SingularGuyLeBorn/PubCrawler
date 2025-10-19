# FILE: src/scrapers/arxiv_scraper.py

import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from typing import List, Dict, Any

from src.config import get_logger

logger = get_logger(__name__)


class ArxivScraper:
    """
    Scraper for the arXiv API.
    This class is designed to integrate with the existing PubCrawler framework.
    It takes a task-specific dictionary and returns a list of paper dictionaries.
    """

    BASE_URL = 'http://export.arxiv.org/api/query?'

    def __init__(self, task_info: Dict[str, Any]):
        """
        Initializes the ArxivScraper with parameters from the task config.
        """
        self.task_info = task_info
        self.search_query = task_info.get('search_query', 'cat:cs.AI')
        self.limit = task_info.get('limit')  # API has 'max_results', let's use that if limit is provided
        self.max_results = self.limit if self.limit is not None else task_info.get('max_results', 10)
        self.sort_by = task_info.get('sort_by', 'submittedDate')
        self.sort_order = task_info.get('sort_order', 'descending')
        logger.info(f"ArxivScraper initialized for query: '{self.search_query}', max_results: {self.max_results}")

    def _build_url(self) -> str:
        """Constructs the full API request URL from task parameters."""
        encoded_query = urllib.parse.quote(self.search_query)
        query_params = (
            f'search_query={encoded_query}&'
            f'start=0&'
            f'max_results={self.max_results}&'
            f'sortBy={self.sort_by}&'
            f'sortOrder={self.sort_order}'
        )
        return self.BASE_URL + query_params

    def _parse_xml_entry(self, entry: ET.Element, ns: Dict[str, str]) -> Dict[str, Any]:
        """Parses a single <entry> XML element into a paper dictionary."""

        # Helper to safely get text from an element
        def _get_text(element_name: str, namespace: str = 'atom'):
            element = entry.find(f'{namespace}:{element_name}', ns)
            if element is not None and element.text is not None:
                return element.text.strip().replace('\n', ' ').replace('  ', ' ')
            return None

        # Extract authors
        author_elements = entry.findall('atom:author', ns)
        authors = [_get_text('name') for author in author_elements] if author_elements else []

        # Extract PDF link
        pdf_url = None
        for link in entry.findall('atom:link', ns):
            if link.attrib.get('title') == 'pdf':
                pdf_url = link.attrib.get('href')
                break

        # Build the dictionary that matches the project's data structure
        paper_dict = {
            "title": _get_text('title'),
            "authors": authors,
            "abstract": _get_text('summary'),
            "pdf_url": pdf_url,
            "published_date": _get_text('published'),
            "updated_date": _get_text('updated'),
            "arxiv_id": _get_text('id'),
            "journal_ref": _get_text('journal_ref', 'arxiv'),
            "doi": _get_text('doi', 'arxiv'),
            "comment": _get_text('comment', 'arxiv')
        }
        return paper_dict

    def scrape(self) -> List[Dict[str, Any]]:
        """Executes the scrape against the arXiv API and returns a list of paper dictionaries."""
        full_url = self._build_url()
        logger.info(f"Requesting data from arXiv: {full_url}")

        papers: List[Dict[str, Any]] = []
        try:
            with urllib.request.urlopen(full_url) as response:
                if response.status != 200:
                    logger.error(f"HTTP request to arXiv failed with status code: {response.status}")
                    return papers

                xml_data = response.read().decode('utf-8')

                ns = {
                    'atom': 'http://www.w3.org/2005/Atom',
                    'arxiv': 'http://arxiv.org/schemas/atom'
                }

                root = ET.fromstring(xml_data)
                entries = root.findall('atom:entry', ns)

                logger.info(f"Found {len(entries)} entries from arXiv.")
                for entry in entries:
                    paper = self._parse_xml_entry(entry, ns)
                    papers.append(paper)

                return papers

        except urllib.error.URLError as e:
            logger.error(f"Failed to access arXiv API: {e.reason}", exc_info=True)
        except ET.ParseError as e:
            logger.error(f"Failed to parse XML from arXiv: {e}", exc_info=True)
        except Exception as e:
            logger.error(f"An unexpected error occurred during arXiv scraping: {e}", exc_info=True)

        return papers

# END OF FILE: src/scrapers/arxiv_scraper.py