# FILE: src/scrapers/kdd_scraper.py

import time
from typing import List, Dict, Any

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

from .base_scraper import BaseScraper


class KddScraper(BaseScraper):
    """专门用于 KDD 网站的爬虫 (使用 Selenium)。"""

    def scrape(self) -> List[Dict[str, Any]]:
        url = self.task_info["url"]
        limit = self.task_info.get("limit")

        # KDD 特定的选择器
        paper_link_selector = 'a.item-title'

        self.logger.info(f"    -> 正在启动 Selenium 访问 (KDD): {url}")
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
            self.logger.info("    -> 页面已加载. 等待 10 秒以处理动态内容...")
            time.sleep(10)

            link_elements = driver.find_elements(By.CSS_SELECTOR, paper_link_selector)
            if not link_elements:
                self.logger.warning(f"    -> Selenium 未找到任何论文链接，使用的选择器是: '{paper_link_selector}'")
                return []

            self.logger.info(f"    -> 找到了 {len(link_elements)} 个潜在的论文链接。")
            if limit and len(link_elements) > limit:
                self.logger.info(f"    -> 应用限制：处理前 {limit} 个链接。")
                link_elements = link_elements[:limit]

            papers = []
            for i, link_elem in enumerate(link_elements):
                paper_url = link_elem.get_attribute('href')
                paper_title = link_elem.text
                if paper_url and paper_title:
                    papers.append({
                        'id': f"kdd_{self.task_info['year']}_{i}",
                        'title': paper_title.strip(),
                        'authors': 'N/A (KDD Selenium)',
                        'abstract': 'N/A (KDD Selenium)',
                        'pdf_url': None,
                        'source_url': paper_url
                    })
            return papers

        except Exception as e:
            self.logger.error(f"    [✖ ERROR] KDD Selenium 抓取失败 {url}: {e}", exc_info=True)
            return []
        finally:
            if driver:
                driver.quit()