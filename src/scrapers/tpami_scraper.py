# FILE: src/scrapers/tpami_scraper.py (API Version)

import requests
import json
from typing import List, Dict, Any
from tqdm import tqdm
import time

from .base_scraper import BaseScraper


class TpamiScraper(BaseScraper):
    """
    专门用于 IEEE TPAMI 期刊的爬虫 (使用后台 API)。
    这是一个更稳定、更高效的方案，取代了 Selenium。
    """
    BASE_URL = "https://ieeexplore.ieee.org"

    def _get_issue_number(self, punumber: str) -> str:
        """
        第一步: 调用 metadata API 获取最新的 'issueNumber'。
        这个 issueNumber 是获取论文列表的关键。
        """
        metadata_url = f"{self.BASE_URL}/rest/publication/home/metadata?pubid={punumber}"
        headers = {
            # 关键请求头，模拟从期刊主页发起的请求
            'Referer': f'{self.BASE_URL}/xpl/conhome/{punumber}/proceeding',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.logger.info(f"    -> 正在获取 issue number from: {metadata_url}")
        try:
            response = requests.get(metadata_url, headers=headers, timeout=20)
            response.raise_for_status()
            data = response.json()
            # issueNumber 可以是 'Early Access' 的 ID，也可以是最新一期的 ID
            issue_number = str(data['currentIssue']['issueNumber'])
            self.logger.info(f"    -> 成功获取 issue number: {issue_number}")
            return issue_number
        except Exception as e:
            self.logger.error(f"    [✖ ERROR] 获取 issue number 失败: {e}")
            return None

    def scrape(self) -> List[Dict[str, Any]]:
        punumber = self.task_info.get("punumber")
        if not punumber:
            self.logger.error("    [✖ ERROR] TPAMI task in YAML must have a 'punumber'. For TPAMI, it's '34'.")
            return []

        limit = self.task_info.get("limit")

        issue_number = self._get_issue_number(punumber)
        if not issue_number:
            return []

        papers = []
        page_number = 1
        total_records = 0
        total_pages = 1  # 先假设只有一页

        self.logger.info("    -> 开始逐页获取论文列表...")
        pbar = tqdm(total=total_records or limit or 25, desc=f"    -> Scraping TPAMI page {page_number}")

        while True:
            toc_url = f"{self.BASE_URL}/rest/search/pub/{punumber}/issue/{issue_number}/toc"
            payload = {
                "pageNumber": str(page_number),
                "punumber": str(punumber),
                "isnumber": str(issue_number)
            }
            headers = {
                'Referer': f'{self.BASE_URL}/xpl/conhome/{punumber}/proceeding?pageNumber={page_number}',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Content-Type': 'application/json;charset=UTF-8'
            }

            try:
                response = requests.post(toc_url, headers=headers, data=json.dumps(payload), timeout=20)
                response.raise_for_status()
                data = response.json()

                if page_number == 1:
                    total_records = data.get('totalRecords', 0)
                    total_pages = data.get('totalPages', 1)
                    pbar.total = limit if limit and limit < total_records else total_records
                    self.logger.info(f"    -> 共发现 {total_records} 篇论文，分布在 {total_pages} 页。")

                records = data.get('records', [])
                if not records:
                    self.logger.info("    -> 当前页没有更多论文，抓取结束。")
                    break

                for record in records:
                    papers.append({
                        'id': record.get('articleNumber', ''),
                        'title': record.get('highlightedTitle', 'N/A').replace('<br>', ' '),
                        'authors': ', '.join([author['name'] for author in record.get('authors', [])]),
                        'abstract': record.get('abstract', 'N/A'),
                        'pdf_url': f"请访问源页面查看PDF（可能需要订阅）",
                        'source_url': self.BASE_URL + record.get('documentLink', ''),
                        'conference': 'TPAMI'
                    })
                    pbar.update(1)
                    if limit and len(papers) >= limit:
                        break

                if (limit and len(papers) >= limit) or page_number >= total_pages:
                    break

                page_number += 1
                pbar.set_description(f"    -> Scraping TPAMI page {page_number}")
                time.sleep(1)  # 友好访问

            except Exception as e:
                self.logger.error(f"    [✖ ERROR] 在第 {page_number} 页抓取失败: {e}")
                break

        pbar.close()
        return papers