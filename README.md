<div align="center">
  <img src="https://raw.githubusercontent.com/SingularGuyLeBorn/PubCrawler/main/logo.png" alt="PubCrawler Pro Logo" width="150"/>
  <h1>PubCrawler Pro</h1>
  <p>
    <strong>您的下一代 AI 学术趋势分析助手 🚀</strong>
  </p>
  <p>
    自动化爬取、分析并洞察顶级学术会议与 arXiv 的最新研究动态。
  </p>
  <p>
    <img src="https://img.shields.io/badge/Python-3.9+-blue.svg" alt="Python Version">
    <img src="https://img.shields.io/badge/UI-Streamlit-ff69b4" alt="UI Framework">
    <img src="https://img.shields.io/badge/Visualization-Plotly%20%26%20Matplotlib-blueviolet" alt="Visualization">
    <img src="https://img.shields.io/badge/Search-SQLite%20FTS5%20%7C%20ChromaDB-orange" alt="Search Engine">
    <img src="https://img.shields.io/badge/AI%20Chat-ZhipuAI-red" alt="AI Chat">
    <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License">
  </p>
</div>

---

## 🧐 项目简介 (Introduction)

您是否曾为追踪顶级学术会议（如 NeurIPS, ICLR, CVPR）和 arXiv 的最新动态而感到力不从心？是否想一键获取特定领域在过去数年间的所有相关论文，并立即生成一份精美的、可交互的趋势分析报告？

**PubCrawler Pro** 正是为此而生。它不仅仅是一个论文爬虫，更是一个集**自动化数据采集**、**智能过滤**、**动态趋势分析**、**本地知识库构建**和**AI 交互**于一体的强大研究工作流引擎。我们的目标是——将您从繁琐的文献筛选中解放出来，专注于最前沿、最有价值的研究。✨

## 🌟 核心功能 (Current Features)

PubCrawler Pro 已完成核心功能的重构，并用一个功能强大的 **Streamlit Pro UI** 替换了原有的界面，提供无缝的本地搜索、AI 交互和动态数据可视化能力。

* **⚙️ YAML 驱动的指挥中心**: 在 `configs/tasks.yaml` 中通过简单文本配置，即可指挥系统执行复杂的抓取与分析任务，无需修改任何代码。
* **🌐 全方位多源爬取**:

  * **API 直连**: 已内置对 **arXiv** (官方API)、**OpenReview** (ICLR/NeurIPS) 和 **IEEE Xplore** (TPAMI) 的稳定支持。
  * **HTML 解析**: 高效解析 **CVF** (CVPR/ICCV)、**PMLR** (ICML) 和 **ACL Anthology** (ACL/EMNLP/NAACL) 等静态网站。
  * **Selenium 驱动**: 对 **AAAI** 和 **KDD** 等需要动态渲染的网站提供支持。
  * **并发加速**: 针对 ACL/CVF 等需要逐页访问的网站，采用多线程并发抓取，极大提升效率。
  * **输出格式**: 爬取结果自动保存为结构化的 `.csv` 数据文件。
* **📊 自动化分析与报告**:

  * **趋势词云**: 为每个任务自动生成词云图 (`.png`)，让研究热点一目了然。
  * **深度分析图表**: 自动生成**主题热度**、**主题质量 (平均分)**、**接收类型分布**和**跨年份趋势**等可视化图表 (`.png`)。
  * **多格式产出**: 自动为每个任务生成精美的 **Markdown 报告** (`.md`) 和 **CSV 数据** (`.csv`)。
* **🔍 本地智能搜索引擎**:

  * **全文检索 (FTS5)**: 提供脚本将所有爬取到的论文数据构建为本地的 **SQLite 全文搜索引擎 (FTS5)**，支持关键词和字段 (`author:`, `title:`, `abstract:`) 高级搜索语法。
  * **语义检索 (ChromaDB)**:
    * **向量生成**: 集成 `Sentence Transformers` 模型，为每篇论文的标题和摘要生成语义向量，并存储在本地 `ChromaDB` 向量数据库中。支持增量更新。
    * **语义搜索**: 支持基于向量余弦相似度的语义搜索，能够理解查询的含义，找到更相关的论文。
* **💬 交互式 Streamlit Pro UI**:

  * **统一仪表盘**: 提供一个现代化的本地 Web UI (`streamlit_app.py`)，集成了**AI 助手 & 搜索**与**趋势分析仪表盘**两大功能模块。
  * **动态图表生成**: 在仪表盘页面，可以直接选择爬取到的**任何 CSV 文件**（无论是原始数据还是分析汇总），系统会**实时**进行分析并生成由 `Plotly` 驱动的**可交互图表**。
  * **高级搜索与筛选**: 在搜索页面，除了支持关键词和语义搜索，还可以对结果按会议、年份进行多重筛选。
  * **AI 对话 (ZhipuAI)**: 深度整合 `ZhipuAI (智谱AI)` 大语言模型，用户可以在搜索结果的上下文中与 AI 进行多轮对话，提问、总结、分析论文。
  * **结果保存**: 允许用户将筛选后的搜索结果直接保存为 Markdown 文件。

## 🗺️ 路线图 (Roadmap)

我们有一个清晰的多阶段计划，旨在将 PubCrawler Pro 从一个强大的本地工具集演进为顶级的智能化学术分析平台。

* **🧱 第一阶段: 奠定基石 - 本地AI工作流 (已完成)**

  * [X]  YAML 驱动的集中式任务配置
  * [X]  多源爬虫框架 (API, HTML, 并发HTML, Selenium)
  * [X]  支持 arXiv, OpenReview, CVF, PMLR, ACL Anthology, AAAI, KDD, TPAMI 等。
  * [X]  自动化报告 (Markdown, CSV), 词云分析与深度分析图表生成。
  * [X]  本地全文搜索引擎构建与查询 (SQLite FTS5)。
  * [X]  本地语义搜索引擎构建与查询 (ChromaDB & Sentence Transformers)。
  * [X]  AI 对话 (ZhipuAI Chat) 核心服务。
  * [X]  **交互式 Streamlit Web UI**: 提供一个集成搜索、AI 对话和动态趋势分析功能的现代化本地 Web 界面。
* **🚀 第二阶段: 增强智能与可视化 - Streamlit UI 进阶 (计划中)**

  * [ ]  **多语言支持**: 在下载论文时，将英文标题和摘要翻译成中文并单独存储，以支持中英文混合搜索和展示。
  * [ ]  **前端任务管理与导出**:
    * 在 Streamlit UI 中提供直接触发爬虫任务的接口。
    * 实现一键打包所有爬取数据和分析报告（Markdown, CSV, PNG）并供浏览器下载的功能。
  * [ ]  **AI 功能扩展**:
    * 支持对多篇选定论文进行组合式 AI 总结和对比分析。
    * 引入 AI 辅助发现研究热点、交叉领域或潜在研究空白。
  * [ ]  **更丰富的可视化**: 增加更多图表类型（如网络图、散点图），并允许用户在 UI 中自定义图表参数。
* **🌐 第三阶段: 自动化爬虫支持 - API 与后台任务 (计划中)**

  * [ ]  **异步任务核心**: 集成 Celery + Redis 处理所有耗时操作（如爬虫、向量生成），并提供任务进度实时反馈。
  * [ ]  **“每日简报”调度器**: 实现定时任务，自动抓取 arXiv 等最新论文，并发送包含 AI 总结的个性化邮件或通知。
* **🎨 第四阶段: 极致交互 - 现代化 Web 界面 (计划中)**

  * **可视化任务配置**: 提供直观的图形化界面来配置和管理爬虫任务，无需手动编辑 YAML 文件。

  * [ ]  **高度交互仪表盘**: 创建支持多维度数据筛选、下钻和自定义视图的高度交互式仪表盘。

## 🚀 快速开始 (Getting Started)

### 1. 环境准备

* Python 3.9+
* Git

### 2. 安装与配置

1. **克隆项目**

   ```bash
   git clone https://github.com/SingularGuyLeBorn/PubCrawler.git
   cd PubCrawler
   ```
2. **创建并激活虚拟环境**

   ```bash
   # 创建虚拟环境
   python -m venv .venv
   # 激活 (Windows)
   .\.venv\Scripts\activate
   # 激活 (macOS / Linux)
   source .venv/bin/activate
   ```
3. **安装依赖**
   我们已为您准备好 `requirements.txt` 文件。直接运行安装命令即可：

   ```bash
   # 建议使用国内镜像源以加速
   pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

   # 如果需要 GPU 支持 (推荐): 确保正确安装 PyTorch
   # 参考 https://pytorch.org/get-started/locally/
   # 例如，对于 CUDA 12.1 (Windows):
   # pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
   ```
4. **【重要】下载 NLTK 数据包**
   首次运行时，需要手动下载停用词数据。

   ```bash
   python -m nltk.downloader stopwords
   ```
5. **配置任务**
   将 `configs/tasks.yaml.example` 复制一份并重命名为 `configs/tasks.yaml`。

   ```bash
   # Windows
   copy configs\tasks.yaml.example configs\tasks.yaml
   # macOS / Linux
   cp configs/tasks.yaml.example configs/tasks.yaml
   ```

   打开 `configs/tasks.yaml` 文件，根据您的需求启用或修改任务。将您想运行的任务的 `enabled` 字段设置为 `true`。
6. **配置环境变量 (为 AI 功能准备)**
   在项目根目录创建一个 `.env` 文件，并填入您的人工智能模型 API 密钥。目前，AI Chat 功能支持 `ZhipuAI`。

   ```
   # .env
   ZHIPUAI_API_KEY="YOUR_ZHIPUAI_API_KEY_HERE"
   ```

### 3. 如何运行 (Execution Flow)

项目的工作流分为几个步骤，确保您按照正确的顺序执行以充分利用所有功能。

#### **第一步: 采集数据与分析 (命令行)**

这是核心步骤，用于抓取论文数据并生成初始分析报告。它会自动读取 `configs/tasks.yaml`，执行所有 `enabled: true` 的任务。

```bash
python src/crawlers/run_crawler.py
```

* **输入**: `configs/tasks.yaml`
* **输出**: 所有爬取的数据 (`.csv`)、报告 (`.md`)、词云图 (`.png`) 和分析图表 (`.png`) 都将保存在 `output/` 目录下，按会议和年份自动创建子文件夹。

**命令行爬虫高级用法示例**:

* **启用/禁用任务**: 编辑 `configs/tasks.yaml`，将对应任务的 `enabled` 字段设置为 `true` 或 `false`。
* **并发线程数**: 对于 `acl` 或 `cvf` 等 `source_type` 的任务，您可以在 `configs/tasks.yaml` 中设置 `max_workers` 参数来调整并发线程数，例如 `max_workers: 24`。
* **限制爬取数量**: 您可以为任何任务设置 `max_papers_limit: 100` 来限制单个任务爬取的论文数量，便于快速测试。
* **测试并发性能**: 如果您想优化 ACL 或 CVF 爬虫的 `max_workers` 参数，可以运行 `src/test/test_acl.py` 脚本进行性能测试，它会为您推荐最佳线程数：
  ```bash
  python src/test/test_acl.py
  ```

---

#### **第二步: 构建本地搜索引擎 (命令行)**

如果您想对采集到的所有论文进行快速本地搜索（包括关键词搜索和语义搜索），需要构建数据库。

1. **构建全文搜索索引 (FTS5)**:
   它会读取 `output/metadata` 目录下的所有 `.csv` 文件，并创建一个名为 `papers.db` 的 SQLite 数据库。

   ```bash
   python src/search/indexer.py
   ```

   * **输入**: `output/metadata/**/*.csv`
   * **输出**: `database/papers.db` 文件。
2. **生成并存储语义向量 (ChromaDB)**:
   此步骤会为 `papers.db` 中的论文生成语义向量并存储到 `database/chroma_db`。

   ```bash
   python src/search/embedder_chroma.py
   ```

   * **输入**: `database/papers.db`
   * **输出**: `database/chroma_db` 目录 (ChromaDB 向量数据库)。
   * **注意**: 首次运行时间较长，后续支持增量更新。您可以在 `src/search/embedder_chroma.py` 中通过修改 `PAPER_LIMIT` 来控制处理的论文数量进行快速测试。

---

#### **第三步: 启动交互式 Streamlit Web UI**

运行 Streamlit Web UI，开始通过图形界面进行搜索、分析和 AI 交互！

```bash
streamlit run streamlit_app.py
```
*   **浏览器访问**: 启动后，Streamlit 会在您的终端中提供一个本地 URL (通常是 `http://localhost:8501`)，并自动在浏览器中打开。
*   **趋势分析**: 在“趋势分析仪表盘”页面，选择会议、年份和具体的 CSV 文件，即可查看动态生成的交互式图表。
*   **搜索与AI**: 在“AI 助手 & 搜索”页面，进行关键词或语义搜索 (`sem:` 前缀)，对结果进行筛选，并与 AI 对话。

---

## 🗺️ 论文地图 (Paper Map)

本节旨在提供一个关于人工智能及其相关领域顶级学术会议和研究机构的宏观概览，为您的研究导航。

### 顶级会议概览


| 研究领域                       | 会议列表                                                                      |
| :----------------------------- | :---------------------------------------------------------------------------- |
| **🤖 人工智能 (AI)**           | NeurIPS, ICML, ICLR, AAAI, IJCAI, AISTATS, UAI, COLT, CoRL, AutoML, ACML, ALT |
| **💬 计算语言学 (CL)**         | ACL, EMNLP, NAACL, COLING, ARR, COLM                                          |
| **👁️ 计算机视觉 (CV)**       | CVPR, ICCV, ECCV, WACV, BMVC, 3DV                                             |
| **📈 数据挖掘 (Data Mining)**  | KDD                                                                           |
| **🕸️ 信息检索 (IR)**         | WWW, SIGIR                                                                    |
| **🦾 机器人学 (Robotics)**     | ICRA, IROS, RSS                                                               |
| **🎨 计算机图形学 (Graphics)** | SIGGRAPH, SIGGRAPH Asia, EUROGRAPHICS                                         |
| **📡 计算机网络 (Networking)** | SIGCOMM                                                                       |
| **🎬 多媒体 (Multimedia)**     | ACM-MM                                                                        |

### 顶级期刊概览 (Top Journals)


| 研究领域                   | 期刊列表                                                                            |
| :------------------------- | :---------------------------------------------------------------------------------- |
| **🤖 人工智能/机器学习** | JMLR, TPAMI, Artificial Intelligence, Machine Learning, Nature Machine Intelligence |
| **👁️ 计算机视觉**        | IJCV, TIP                                                                           |
| **💬 计算语言学**          | Computational Linguistics, TACL                                                     |
| **🦾 机器人学**            | T-RO, IJRR, Science Robotics                                                        |
| **📈 数据挖掘/工程**       | TKDD, TKDE                                                                          |
| **🌐 综合/顶级**           | Nature, Science, PNAS                                                               |

## 🙌 贡献 (Contributing)

欢迎任何形式的贡献！如果您有好的想法、发现了 Bug 或者想添加对新会议的支持，请随时提交 Pull Request 或创建 Issue。

## 📄 许可证 (License)

本项目采用 [MIT License](LICENSE) 授权。
