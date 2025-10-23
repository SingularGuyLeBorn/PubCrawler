# FILE: src/scrapers/acl_scraper.py (Concurrent Version)

from bs4 import BeautifulSoup
from urllib.parse import urljoin
from tqdm import tqdm
from typing import List, Dict, Optional, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

from .base_scraper import BaseScraper
from src.utils.network_utils import robust_get


class AclScraper(BaseScraper):
    """
    专门用于 ACL Anthology 网站的爬虫。
    此版本经过优化，使用多线程并发获取论文详情，以大幅提高速度。
    """

    def _scrape_details_page(self, url: str) -> Optional[Dict[str, Any]]:
        """
        抓取并解析单个 ACL 论文详情页。这是将被并发执行的核心工作函数。
        """
        response = robust_get(url, timeout=20)
        if not response:
            self.logger.debug(f"    -> 请求详情页失败 (已重试): {url}")
            return None

        try:
            soup = BeautifulSoup(response.content, 'lxml')

            title_tag = soup.select_one("h2#title")
            title = title_tag.get_text(strip=True) if title_tag else "N/A"

            author_tags = soup.select("p.lead a")
            authors = ", ".join([a.get_text(strip=True) for a in author_tags]) if author_tags else "N/A"

            abstract_tag = soup.select_one("div.acl-abstract > span")
            abstract = abstract_tag.get_text(strip=True) if abstract_tag else "N/A"

            pdf_url_tag = soup.select_one('meta[name="citation_pdf_url"]')
            pdf_url = pdf_url_tag['content'] if pdf_url_tag else None
            if pdf_url and not pdf_url.startswith('http'):
                pdf_url = urljoin(url, pdf_url)

            paper_id = url.strip('/').split('/')[-1]

            return {'id': paper_id, 'title': title, 'authors': authors, 'abstract': abstract, 'pdf_url': pdf_url,
                    'source_url': url}
        except Exception as e:
            self.logger.debug(f"    -> 解析 ACL 详情页失败 {url}: {e}")
            return None

    def scrape(self) -> List[Dict[str, Any]]:
        index_url = self.task_info["url"]

        # 从配置中读取并发参数，并提供安全的默认值
        max_workers = self.task_info.get("max_workers", 1)
        max_papers_limit = self.task_info.get("max_papers_limit", 0)

        # 1. 首先，获取包含所有论文链接的索引页
        self.logger.info(f"    -> 正在抓取 ACL 索引页: {index_url}")
        response = robust_get(index_url)
        if not response:
            return []

        if response.status_code == 404:
            self.logger.warning(f"    -> 页面未找到 (404): {index_url}")
            return []

        try:
            soup = BeautifulSoup(response.content, 'lxml')
            link_tags = soup.select('p.d-sm-flex strong a.align-middle')

            detail_urls = [urljoin(index_url, tag['href']) for tag in link_tags if
                           f'{self.task_info["year"]}.acl-long.0' not in tag['href']]
            self.logger.info(f"    -> 索引页解析完成，共找到 {len(detail_urls)} 篇有效论文。")

            # 2. 应用数量限制
            urls_to_crawl = detail_urls
            if max_papers_limit > 0:
                # 智能限制：取用户设置和实际数量中的较小值
                actual_limit = min(max_papers_limit, len(detail_urls))
                urls_to_crawl = detail_urls[:actual_limit]
                self.logger.info(f"    -> 已应用数量限制，将爬取前 {len(urls_to_crawl)} 篇论文。")

            if not urls_to_crawl:
                return []

            # 3. 使用 ThreadPoolExecutor 进行并发爬取
            papers = []
            pbar_desc = f"    -> 并发解析 {self.task_info.get('conference')} 详情页"

            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_url = {executor.submit(self._scrape_details_page, url): url for url in urls_to_crawl}

                # 使用 tqdm 显示进度
                for future in tqdm(as_completed(future_to_url), total=len(urls_to_crawl), desc=pbar_desc, leave=True):
                    result = future.result()
                    if result:
                        papers.append(result)

            return papers

        except Exception as e:
            self.logger.error(f"    [✖ ERROR] 解析 ACL 页面时发生未知错误: {e}", exc_info=True)
            return []