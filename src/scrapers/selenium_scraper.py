# FILE: src/scrapers/selenium_scraper.py

import time
from urllib.parse import urljoin

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

from src.scrapers.base_scraper import BaseScraper


class SeleniumScraper(BaseScraper):
    """
    Scraper for dynamic websites that require JavaScript rendering.
    This is a reconnaissance tool; full parsing is highly site-specific.
    """

    SITE_CONFIGS = {
        'IJCAI': {
            'paper_link_selector': 'div.paper_wrapper > div.details > a[href^="https://www.ijcai.org/proceedings"]',
            'title_selector': 'h1',
            'authors_selector': 'div.authors',
            'abstract_selector': 'div.abstract',
        },
        'default': {
            'paper_link_selector': 'a[href*="paper"], a[href*="article"], a[href*="abs"]',
        }
    }

    def scrape(self):
        url = self.task_info["url"]
        parser_type = self.task_info.get("parser_type", "default")
        limit = self.task_info.get("limit")
        site_config = self.SITE_CONFIGS.get(parser_type, self.SITE_CONFIGS['default'])

        self.logger.info(f"Starting Selenium for URL: {url}")

        driver = None
        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument(
                'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')

            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)

            driver.get(url)
            time.sleep(10)

            link_elements = driver.find_elements(By.CSS_SELECTOR, site_config['paper_link_selector'])

            if not link_elements:
                self.logger.warning(
                    f"Selenium found no paper links with selector '{site_config['paper_link_selector']}'")
                filename = f"_selenium_dump_{parser_type}.html"
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(driver.page_source)
                self.logger.info(f"Saved page source to {filename} for debugging.")
                return []

            self.logger.info(f"Found {len(link_elements)} potential paper links.")

            # --- LIMIT LOGIC APPLIED HERE ---
            if limit is not None and len(link_elements) > limit:
                self.logger.info(f"Applying limit: processing first {limit} papers out of {len(link_elements)}.")
                link_elements = link_elements[:limit]

            papers = []
            for link_elem in link_elements:
                paper_url = link_elem.get_attribute('href')
                paper_title = link_elem.text
                if paper_url and paper_title:
                    papers.append({
                        'title': paper_title.strip(),
                        'authors': 'N/A (Selenium Recon)',
                        'abstract': 'N/A (Selenium Recon)',
                        'pdf_url': None,
                        'source_url': paper_url
                    })

            return papers

        except Exception as e:
            self.logger.error(f"Selenium scraping failed for {url}: {e}", exc_info=True)
            return []
        finally:
            if driver:
                driver.quit()

# END OF FILE: src/scrapers/selenium_scraper.py