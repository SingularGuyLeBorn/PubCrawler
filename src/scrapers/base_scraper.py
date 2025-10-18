# FILE: src/scrapers/base_scraper.py

from abc import ABC, abstractmethod
from src.config import get_logger


class BaseScraper(ABC):
    """Abstract base class for all scrapers."""

    def __init__(self, task_info: dict):
        self.task_info = task_info
        self.logger = get_logger(self.__class__.__name__)

    @abstractmethod
    def scrape(self):
        """
        The main method to perform scraping.
        Should return a list of dictionaries, where each dictionary represents a paper.
        """
        pass

# END OF FILE: src/scrapers/base_scraper.py