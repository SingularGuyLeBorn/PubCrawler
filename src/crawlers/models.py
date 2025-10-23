# FILE: src/models.py

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Paper:
    """
    一个用于存储论文信息的数据类，确保所有 scraper 返回统一的结构。
    """
    id: str
    title: str
    authors: List[str]
    summary: str
    published_date: str
    updated_date: str

    pdf_url: Optional[str] = None
    categories: List[str] = field(default_factory=list)
    primary_category: Optional[str] = None

    # 发表信息
    journal_ref: Optional[str] = None
    doi: Optional[str] = None

    # 额外备注，例如项目主页
    comment: Optional[str] = None

    # 作者及其单位的详细信息
    author_details: List[str] = field(default_factory=list)

# END OF FILE: src/models.py