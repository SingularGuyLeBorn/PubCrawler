# FILE: src/scrapers/base_scraper.py

from abc import ABC, abstractmethod
from typing import List, Dict, Any
from src.models import Paper


class BaseScraper(ABC):
    """
    所有抓取器类的抽象基类。
    定义了所有具体抓取器必须遵循的接口。
    """

    def __init__(self, task_config: Dict[str, Any]):
        """
        初始化抓取器。

        Args:
            task_config (Dict[str, Any]): 从 tasks.yaml 中读取的特定任务配置。
        """
        self.task_config = task_config
        print(f"[{self.__class__.__name__}] 初始化...")

    @abstractmethod
    def scrape(self) -> List[Paper]:
        """
        执行抓取的核心方法。

        每个子类必须实现此方法，以执行其特定的抓取逻辑，
        并返回一个包含 Paper对象的列表。

        Returns:
            List[Paper]: 抓取到的论文信息列表。
        """
        raise NotImplementedError("每个 scraper 子类必须实现 scrape 方法。")

# END OF FILE: src/scrapers/base_scraper.py