# FILE: src/scrapers/base_scraper.py

from abc import ABC, abstractmethod
from typing import List, Dict, Any
import logging

class BaseScraper(ABC):
    """
    所有抓取器类的抽象基类。
    定义了所有具体抓取器必须遵循的接口。
    """

    def __init__(self, task_info: Dict[str, Any], logger: logging.Logger):
        """
        初始化抓取器。

        Args:
            task_info (Dict[str, Any]): 从 tasks.yaml 中读取并构建的特定任务配置。
            logger (logging.Logger): 从主程序传递过来的共享日志记录器。
        """
        self.task_info = task_info
        self.logger = logger

    @abstractmethod
    def scrape(self) -> List[Dict[str, Any]]:
        """
        执行抓取的核心方法。

        每个子类必须实现此方法，以执行其特定的抓取逻辑，
        并返回一个包含标准字典结构的论文列表。

        Returns:
            List[Dict[str, Any]]: 抓取到的论文信息列表。
        """
        raise NotImplementedError("每个 scraper 子类必须实现 scrape 方法。")