# FILE: src/scrapers/icml_scraper.py

from bs4 import BeautifulSoup
from urllib.parse import urljoin
from tqdm import tqdm
from typing import List, Dict, Optional, Any
from bs4.element import Tag

from .base_scraper import BaseScraper
from src.utils.network_utils import robust_get  # <-- 导入新的工具函数


class IcmlScraper(BaseScraper):
    """专门用于 ICML (PMLR) 网站的爬虫。"""

    def scrape(self) -> List[Dict[str, Any]]:
        index_url = self.task_info["url"]
        limit = self.task_info.get("limit")
        papers = []

        self.logger.info(f"    -> 正在抓取 ICML 索引页: {index_url}")

        response = robust_get(index_url, timeout=45)  # <-- 使用 robust_get 并增加超时
        if not response:
            return []

        try:
            soup = BeautifulSoup(response.content, 'lxml')
            paper_containers = soup.select('div.paper')
            self.logger.info(f"    -> 找到了 {len(paper_containers)} 篇论文。")

            if limit:
                paper_containers = paper_containers[:limit]
                self.logger.info(f"    -> 应用限制：处理前 {limit} 篇论文。")

            pbar_desc = f"    -> 正在解析 {self.task_info.get('conference')} 页面"
            for paper_div in tqdm(paper_containers, desc=pbar_desc, leave=True):
                paper_data = self._parse_paper_div(paper_div, index_url)
                if paper_data:
                    papers.append(paper_data)

            return papers

        except Exception as e:
            self.logger.error(f"    [✖ ERROR] 解析 ICML 页面时发生未知错误: {e}", exc_info=True)
            return []

    def _parse_paper_div(self, paper_div: Tag, base_url: str) -> Optional[Dict[str, Any]]:
        """从单个 <div class="paper"> 中解析出所有信息。"""
        try:
            title_tag = paper_div.select_one('p.title')
            title = title_tag.get_text(strip=True) if title_tag else "N/A"

            authors_tag = paper_div.select_one('p.details span.authors')
            authors = authors_tag.get_text(strip=True).replace(';', ', ') if authors_tag else "N/A"

            links_p = paper_div.select_one('p.links')
            if not links_p:
                return None

            source_url_tag = links_p.select_one('a:-soup-contains("abs")')
            source_url = urljoin(base_url, source_url_tag['href']) if source_url_tag else 'N/A'

            pdf_url_tag = links_p.select_one('a:-soup-contains("Download PDF")')
            pdf_url = urljoin(base_url, pdf_url_tag['href']) if pdf_url_tag else 'N/A'

            paper_id = source_url.split('/')[-1].replace('.html', '') if source_url != 'N/A' else title
            abstract = "N/A (摘要需访问详情页)"

            return {'id': paper_id, 'title': title, 'authors': authors, 'abstract': abstract, 'pdf_url': pdf_url,
                    'source_url': source_url}
        except Exception as e:
            self.logger.debug(f"    -> 从 ICML 容器解析失败: {e}")
            return None