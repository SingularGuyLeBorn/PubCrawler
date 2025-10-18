# AI 论文爬取工具 (AI Paper Scraper)

本项目是一个配置驱动的自动化工具，用于从顶级的 AI 学术会议网站爬取论文元数据（标题、摘要、作者）和 PDF 文件。

它最大的特点是支持 **OpenReview**，可以抓取包括**审稿意见、作者回复 (Rebuttal)、和最终决策**在内的完整信息，帮助你全面了解论文的接收过程。

## 核心功能

* **配置驱动**：通过 `configs/tasks.yaml` 定义所有爬取任务，无需修改代码。
* **多源爬取**：采用策略模式，支持不同类型的网站：
    * **OpenReview API** (如 ICLR, NeurIPS)
    * **静态 HTML 网站** (如 CVF, MLR Press, ACL Anthology)
* **深度信息（OpenReview 独有）**：可配置 `get_reviews: True` 来抓取审稿分数、评论、作者回复和最终决策。
* **产出物**：
    1.  **`summary.txt`**：包含所有论文的标题、摘要、作者、决策等信息，可直接用于 LLM 分析。
    2.  **`PDFs/` 目录**：存放下载的所有 PDF 文件。
    3.  **`.zip` 压缩包**：将所有 PDF 自动打包，方便归档。
* **关键词过滤**：可在 `yaml` 中配置 `filters`，只爬取你感兴趣的论文。
* **环境管理**：使用 `uv` 进行快速的环境和依赖管理。

## 支不支持热点分析？

**不支持。**

本项目是一个**数据采集和预处理工具**。它的目标是为你准备好“弹药”（即 `summary.txt` 和 PDF）。

你需要使用其他工具（如你提到的 LLM，或 `AI-Paper-Trends` 项目）来对这些数据进行**下一步的分析**。

## 当前支持的会议

本工具的爬虫是按**网站源**分类的。

| 会议 | 源类型 | 爬虫 | 状态 |
| :--- | :--- | :--- | :--- |
| **ICLR** | OpenReview | `OpenReviewScraper` | ✅ **完全支持** (含审稿) |
| **NeurIPS** | OpenReview | `OpenReviewScraper` | ✅ **完全支持** (含审稿) |
| **CVPR** | CVF | `HTMLScraper` (`_parse_cvf`) | ✅ **完全支持** |
| **ICCV** | CVF | `HTMLScraper` (`_parse_cvf`) | ✅ **完全支持** |
| **ICML** | MLR Press | `HTMLScraper` (`_parse_mlr`) | ✅ **完全支持** |
| **ACL** | ACL Anthology | `HTMLScraper` (`_parse_acl`) | ⚠️ **TODO** (需要2次请求) |
| **EMNLP** | ACL Anthology | `HTMLScraper` (`_parse_acl`) | ⚠️ **TODO** (需要2次请求) |

**注：** `ACL` 和 `EMNLP` 的网站 (aclanthology.org) 布局比较特殊，需要在列表页抓取论文链接，然后再对每篇论文**发起第二次请求**来抓取摘要。这个解析逻辑（`_parse_acl`）需要你去实现（见下方扩展指南）。

## 🚀 快速上手

1.  **安装 uv (如果未安装)**
    ```bash
    curl -LsSf [https://astral.sh/uv/install.sh](https://astral.sh/uv/install.sh) | sh
    ```

2.  **创建并激活环境**
    ```bash
    git clone [你的仓库URL]
    cd ai-paper-scraper
    
    # 创建虚拟环境
    uv venv
    
    # 激活环境 (macOS/Linux)
    source .venv/bin/activate
    # (Windows)
    # .venv\Scripts\activate
    ```

3.  **安装依赖**
    ```bash
    # 在项目根目录创建 pyproject.toml
    uv pip install openreview-py requests beautifulsoup4 pyyaml rich tqdm
    ```

4.  **配置任务**
    * 打开 `configs/tasks.yaml`。
    * 按照你的需求修改 `tasks:` 列表。

5.  **运行爬虫**
    ```bash
    python src/main.py
    ```

6.  **查看结果**
    * 所有产出都在 `outputs/` 目录下，按 `[会议]_[年份]` 命名。

## 🛠️ 如何扩展（添加新会议）

这是本工具的核心设计。你有三种扩展方式：

### 1. (最简单) 添加已支持的 OpenReview 会议

例如，添加 `ICLR 2024`：

1.  **`configs/tasks.yaml`**：
    * 在 `tasks:` 列表里加一个新条目，`conference` 设为 'ICLR'，`year` 设为 2024。

**完成。** `OpenReviewScraper` 会自动处理。

### 2. (简单) 添加已支持的 HTML 网站会议

例如，添加 `ECCV 2024` (它和 CVPR 都在 CVF 网站上)：

1.  **`configs/tasks.yaml`**：
    * 在 `source_definitions.html_cvf` 中添加 `ECCV: "https://openaccess.thecvf.com/ECCVYYYY?day=all"`。
    * 在 `tasks:` 列表中添加 `ECCV 2024` 的任务，`source_type` 设为 `html_cvf`。
2.  **`src/main.py`**：
    * 在 `SCRAPER_STRATEGY` 字典中添加 `'ECCV': HTMLScraper`。

**完成。** `HTMLScraper` 会自动使用 `_parse_cvf` 解析器。

### 3. (最难) 添加一个全新的 HTML 网站

例如，你要添加 `AAAI` (它在 `aaai.org` 上，布局全新)：

1.  **`configs/tasks.yaml`**：
    * `source_definitions`：添加新组 `html_aaai: { AAAI: "https://www.aaai.org/YYYY/papers/" }`。
    * `tasks`：添加 `AAAI` 任务，`source_type` 设为 `html_aaai`。
2.  **`src/main.py`**：
    * `SCRAPER_STRATEGY`：添加 `'AAAI': HTMLScraper`。
3.  **`src/scrapers/html_scraper.py`**：
    * **创建新解析器**：在 `HTMLScraper` 类中，添加一个新函数 `def _parse_aaai(self, soup, base_url)`。你需要在这里编写 `BeautifulSoup` 解析逻辑。
    * **更新 `fetch_papers`**：在 `fetch_papers` 方法中，添加路由逻辑：
        ```python
        elif 'proceedings.mlr.press' in self.base_url:
            return self._parse_mlr(soup, self.base_url)
        elif 'aclanthology.org' in self.base_url:
            return self._parse_acl(soup, self.base_url)
        elif 'aaai.org' in self.base_url: # <-- 新增
            return self._parse_aaai(soup, self.base_url) # <-- 新增
        else:
            print(f"[red]没有为 {self.base_url} 提供解析器。[/red]")
            return []
        ```

**这就是扩展 ACL/EMNLP 的方法**：你需要去 `html_scraper.py` 中，实现 `_parse_acl` 函数的逻辑。