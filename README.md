<div align="center">
  <img src="./logo.png" alt="PubCrawler Pro Logo" width="150"/>
  <h1>PubCrawler Pro</h1>
  <p>
    <strong>您的下一代 AI 学术趋势分析助手 🚀</strong>
  </p>
  <p>
    自动化爬取、分析并洞察顶级学术会议与 arXiv 的最新研究动态。
  </p>
  <p>
    <img src="https://img.shields.io/badge/Python-3.9+-blue.svg" alt="Python Version">
    <img src="https://img.shields.io/badge/Toolchain-Command--Line%20%26%20Gradio%20UI-brightgreen" alt="Toolchain">
    <img src="https://img.shields.io/badge/AI%20Analysis-Matplotlib%20%26%20WordCloud-blueviolet" alt="AI Analysis">
    <img src="https://img.shields.io/badge/Search%20Ready-SQLite%20FTS5%20%26%20ChromaDB-orange" alt="Search Ready">
    <img src="https://img.shields.io/badge/AI%20Chat-ZhipuAI-red" alt="AI Chat">
    <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License">
  </p>
</div>

---

## 🧐 项目简介 (Introduction)

您是否曾为追踪顶级学术会议（如 NeurIPS, ICLR, CVPR）和 arXiv 的最新动态而感到力不从心？是否想一键获取特定领域在过去数年间的所有相关论文，并自动生成一份精美的趋势分析报告？

**PubCrawler Pro** 正是为此而生。它不仅仅是一个论文爬虫，更是一个集**自动化数据采集**、**智能过滤**、**趋势分析**、**本地知识库构建**和**AI 交互**于一体的强大研究工作流引擎。我们的目标是——将您从繁琐的文献筛选中解放出来，专注于最前沿、最有价值的研究。✨

## 🌟 核心功能 (Current Features)

PubCrawler Pro 已成功完成第一阶段的开发，并集成了实验性的 Gradio Web 界面，提供强大的本地搜索和 AI 交互能力。

*   **⚙️ YAML 驱动的指挥中心**: 在 `configs/tasks.yaml` 中通过简单文本配置，即可指挥系统执行复杂的抓取与分析任务，无需修改任何代码。

*   **🌐 全方位多源爬取**:
    *   **API 直连**: 已内置对 **arXiv** (官方API)、**OpenReview** (ICLR/NeurIPS) 和 **IEEE Xplore** (TPAMI) 的稳定支持。
        *   **ICLR**: 支持获取 2019-2026 年（通过配置启用）的论文。
        *   **NeurIPS**: 支持获取 2019-2026 年（通过配置启用）的论文。
        *   **TPAMI**: 支持获取最新期刊文章。
    *   **HTML 解析**: 高效解析 **CVF** (CVPR/ICCV)、**PMLR** (ICML) 和 **ACL Anthology** (ACL/EMNLP/NAACL) 等静态网站。
        *   **ICML**: 支持获取 2022-2026 年（通过配置启用）的论文。
        *   **ACL/EMNLP/NAACL**: 支持配置抓取指定年份的论文。
        *   **CVPR/ICCV**: 支持配置抓取指定年份的论文。
    *   **Selenium 驱动**: 对 **AAAI** 和 **KDD** 等需要动态渲染的网站提供支持。
    *   **并发加速**: 针对 ACL/CVF 等需要逐页访问的网站，采用多线程并发抓取，极大提升效率。
    *   **输出格式**: 爬取结果自动保存为结构化的 `.csv` 数据文件。

*   **📊 自动化分析与报告**:
    *   **趋势词云**: 为每个任务自动生成词云图 (`.png`)，让研究热点一目了然。
    *   **深度分析图表**: 自动生成**主题热度**、**主题质量 (平均分)**、**接收类型分布**和**跨年份趋势**等可视化图表 (`.png`)。
    *   **多格式产出**: 自动为每个任务生成精美的 **Markdown 报告** (`.md`) 和 **CSV 数据** (`.csv`)。

*   **🔍 本地智能搜索引擎**:
    *   **全文检索 (FTS5)**: 提供脚本将所有爬取到的论文数据构建为本地的 **SQLite 全文搜索引擎 (FTS5)**，支持关键词和字段 (`author:`, `title:`, `abstract:`) 高级搜索语法。
    *   **语义检索 (ChromaDB)**:
        *   **向量生成**: 集成 `Sentence Transformers` 模型，为每篇论文的标题和摘要生成语义向量，并存储在本地 `ChromaDB` 向量数据库中。支持增量更新。
        *   **语义搜索**: 支持基于向量余弦相似度的语义搜索，能够理解查询的含义，找到更相关的论文。

*   **💬 AI 交互与 Gradio UI**:
    *   **Gradio Web 界面**: 提供一个易于使用的本地 Web UI (`app.py`)，无需命令行即可进行搜索和 AI 交互。
    *   **AI 对话 (ZhipuAI)**: 深度整合 `ZhipuAI (智谱AI)` 大语言模型，用户可以在搜索结果的上下文中与 AI 进行多轮对话，提问、总结、分析论文。
    *   **实时状态反馈**: 搜索和AI交互在前端提供即时反馈。
    *   **结果保存**: 允许用户将搜索结果直接保存为 Markdown 文件。

## 🗺️ 路线图 (Roadmap)

我们有一个清晰的多阶段计划，旨在将 PubCrawler Pro 从一个强大的命令行工具集和实验性的 Gradio UI 演进为顶级的智能化学术分析平台。

*   **🧱 第一阶段: 奠定基石 - 本地AI工作流 (已完成)**
    *   `[x]` YAML 驱动的集中式任务配置
    *   `[x]` 多源爬虫框架 (API, HTML, 并发HTML, Selenium)
    *   `[x]` 支持 arXiv, OpenReview (ICLR/NeurIPS), CVF (CVPR/ICCV), PMLR (ICML), ACL Anthology (ACL/EMNLP/NAACL), AAAI, KDD, TPAMI 等。
    *   `[x]` 关键词过滤与数量限制
    *   `[x]` 自动化报告 (Markdown, CSV), 词云分析与深度分析图表生成。
    *   `[x]` 本地全文搜索引擎构建与查询 (SQLite FTS5)。
    *   `[x]` **语义向量生成**: 集成 `Sentence Transformers` 模型，为每篇论文生成语义向量并存入 `ChromaDB`。
    *   `[x]` **语义搜索**: 在本地搜索引擎中加入基于向量余弦相似度的语义搜索功能。
    *   `[x]` **AI 对话 (ZhipuAI Chat)**: 基于大语言模型，实现与搜索结果论文深度问答功能。
    *   `[x]` **交互式 Gradio Web UI**: 提供一个集成搜索和 AI 对话功能的简单本地 Web 界面。

*   **🚀 第二阶段: 增强智能与可视化 - Gradio UI 进阶 (计划中)**
    *   `[ ]` **多语言支持**: 在下载论文时，将英文标题和摘要翻译成中文并单独存储，以支持中英文混合搜索和展示。
    *   `[ ]` **前端趋势分析仪表盘**:
        *   在 Gradio UI 中动态展示后端生成的趋势分析图表（词云、主题热度、主题质量、接收类型分布、跨年份趋势）。
        *   允许用户在 UI 中调整数据源（会议、年份）和自定义领域类别/关键词，并实时更新分析图表。
        *   支持多种图表类型切换（如柱状图、折线图、堆叠图），以从不同角度洞察数据。
    *   `[ ]` **前端任务管理与导出**:
        *   在 Gradio UI 中提供直接触发爬虫任务的接口。
        *   实现一键打包所有爬取数据和分析报告（Markdown, CSV, PNG）并供浏览器下载的功能。
    *   `[ ]` **AI 功能扩展**:
        *   支持对多篇选定论文进行组合式 AI 总结和对比分析。
        *   引入 AI 辅助发现研究热点、交叉领域或潜在研究空白。

*   **🌐 第三阶段: 服务化转型与自动化 - API 与后台任务 (计划中)**
    *   `[ ]` **后端 API 化**: 使用 FastAPI 或 Flask 构建一个独立的、更具扩展性的后端 API 服务。
    *   `[ ]` **数据库集成**: 使用 SQLAlchemy + PostgreSQL/SQLite 进行数据持久化，支持更复杂的查询和数据管理。
    *   `[ ]` **异步任务核心**: 集成 Celery + Redis 处理所有耗时操作（如爬虫、向量生成），并提供任务进度实时反馈。
    *   `[ ]` **“每日简报”调度器**: 实现定时任务，自动抓取 arXiv 等最新论文，并发送包含 AI 总结的个性化邮件或通知。

*   **🎨 第四阶段: 极致交互 - 现代化 Web 界面 (计划中)**
    *   `[ ]` **现代化前端**: 使用 React/Vue 等前端框架搭建现代、简洁、响应式的 Web 界面，替换 Gradio UI。
    *   `[ ]` **可视化任务配置**: 提供直观的图形化界面来配置和管理爬虫任务，无需手动编辑 YAML 文件。
    *   `[ ]` **交互式仪表盘**: 创建高度交互的趋势分析仪表盘，支持多维度的数据筛选、下钻和自定义视图。
    *   `[ ]` **用户管理与权限**: 实现基础的用户注册、登录和权限管理功能。

## 🚀 快速开始 (Getting Started)

### 1. 环境准备

*   Python 3.9+
*   Git

### 2. 安装与配置

1.  **克隆项目**
    ```bash
    git clone https://github.com/SingularGuyLeBorn/PubCrawler.git
    cd PubCrawler
    ```

2.  **创建并激活虚拟环境**
    ```bash
    # 创建虚拟环境
    python -m venv .venv
    # 激活 (Windows)
    .\.venv\Scripts\activate
    # 激活 (macOS / Linux)
    source .venv/bin/activate
    ```

3.  **安装依赖**
    首先，在项目根目录创建 `requirements.txt` 文件，并填入以下内容：
    ```txt
    # requirements.txt
    requests
    beautifulsoup4
    lxml
    pandas
    numpy
    matplotlib
    seaborn
    wordcloud
    nltk
    pyyaml
    tqdm
    openreview-py
    selenium
    webdriver-manager
    python-dotenv
    scikit-learn
    colorama
    gradio                  # for Web UI
    chromadb                # for semantic search
    sentence-transformers   # for embedding generation
    torch                   # for sentence-transformers (GPU support recommended)
    zai                     # ZhipuAI client for AI chat
    ```
    然后运行安装命令：
    ```bash
    # 建议使用国内镜像源以加速
    pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

    # 如果需要 GPU 支持 (推荐): 确保正确安装 PyTorch
    # 参考 https://pytorch.org/get-started/locally/
    # 例如，对于 CUDA 12.1 (Windows):
    # pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
    ```

4.  **【重要】下载 NLTK 数据包**
    首次运行时，需要手动下载停用词数据。
    ```bash
    python -m nltk.downloader stopwords
    ```

5.  **配置任务**
    将 `configs/tasks.yaml.example` 复制一份并重命名为 `configs/tasks.yaml`。
    ```bash
    # Windows
    copy configs\tasks.yaml.example configs\tasks.yaml
    # macOS / Linux
    cp configs/tasks.yaml.example configs/tasks.yaml
    ```
    打开 `configs/tasks.yaml` 文件，根据您的需求启用或修改任务。将您想运行的任务的 `enabled` 字段设置为 `true`。

6.  **配置环境变量 (为 AI 功能准备)**
    在项目根目录创建一个 `.env` 文件，并填入您的人工智能模型 API 密钥。目前，AI Chat 功能支持 `ZhipuAI`。
    ```
    # .env
    ZHIPUAI_API_KEY="YOUR_ZHIPUAI_API_KEY_HERE"
    # 例如：如果未来支持Hugging Face模型，您可以在这里添加
    # HF_API_TOKEN="hf_..."
    ```

### 3. 如何运行 (Execution Flow)

项目的工作流分为几个步骤，确保您按照正确的顺序执行以充分利用所有功能。

#### **第一步: 采集数据与分析 (命令行)**

这是核心步骤，用于抓取论文数据并生成初始分析报告。它会自动读取 `configs/tasks.yaml`，执行所有 `enabled: true` 的任务。
```bash
python src/crawlers/run_crawler.py
```
*   **输入**: `configs/tasks.yaml`
*   **输出**: 所有爬取的数据 (`.csv`)、报告 (`.md`)、词云图 (`.png`) 和分析图表 (`.png`) 都将保存在 `output/` 目录下，按会议和年份自动创建子文件夹。

**命令行爬虫高级用法示例**:

*   **启用/禁用任务**: 编辑 `configs/tasks.yaml`，将对应任务的 `enabled` 字段设置为 `true` 或 `false`。
*   **并发线程数**: 对于 `acl` 或 `cvf` 等 `source_type` 的任务，您可以在 `configs/tasks.yaml` 中设置 `max_workers` 参数来调整并发线程数，例如 `max_workers: 24`。
*   **限制爬取数量**: 您可以为任何任务设置 `max_papers_limit: 100` 来限制单个任务爬取的论文数量，便于快速测试。
*   **关键词过滤**: 在任务配置中添加 `filters` 列表，例如：
    ```yaml
    - name: 'ICLR_2025_Transformer'
      conference: 'ICLR'
      year: 2025
      source_type: 'iclr'
      enabled: true
      filters:
        - "transformer"
        - "attention"
    ```
    这将只保留标题或摘要中包含 "transformer" 或 "attention" 的论文。
*   **测试并发性能**: 如果您想优化 ACL 或 CVF 爬虫的 `max_workers` 参数，可以运行 `src/test/test_acl.py` 脚本进行性能测试，它会为您推荐最佳线程数：
    ```bash
    python src/test/test_acl.py
    ```

---

#### **第二步: 构建本地搜索引擎 (命令行)**

如果您想对采集到的所有论文进行快速本地搜索（包括关键词搜索和语义搜索），需要构建数据库。

1.  **构建全文搜索索引 (FTS5)**:
    它会读取 `output/metadata` 目录下的所有 `.csv` 文件，并创建一个名为 `papers.db` 的 SQLite 数据库。
    ```bash
    python src/search/indexer.py
    ```
    *   **输入**: `output/metadata/**/*.csv`
    *   **输出**: `database/papers.db` 文件。

2.  **生成并存储语义向量 (ChromaDB)**:
    此步骤会为 `papers.db` 中的论文生成语义向量并存储到 `database/chroma_db`。
    ```bash
    python src/search/embedder_chroma.py
    ```
    *   **输入**: `database/papers.db`
    *   **输出**: `database/chroma_db` 目录 (ChromaDB 向量数据库)。
    *   **注意**: 首次运行时间较长，后续支持增量更新。您可以在 `src/search/embedder_chroma.py` 中通过修改 `PAPER_LIMIT` 来控制处理的论文数量进行快速测试。

---

#### **第三步: 启动交互式 Web UI (Gradio)**

运行 Gradio Web UI，开始通过图形界面进行搜索和 AI 交互！
```bash
python app.py
```
*   **浏览器访问**: 启动后，Gradio 会在您的终端中提供一个本地 URL (通常是 `http://127.0.0.1:7860`)。
*   **搜索语法**:
    *   **关键词搜索**: 直接输入关键词，例如 `transformer author:vaswani`。
    *   **语义搜索**: 在查询前加上 `sem:`，例如 `sem: efficiency of few-shot learning`。
*   **AI 聊天**: 搜索结果显示后，点击 "与AI对话" 按钮，即可在侧边栏与 AI 进行多轮对话，AI 会利用搜索到的论文作为上下文回答您的问题。

---

#### **（可选）通过命令行使用本地搜索引擎**

如果您偏爱命令行，也可以直接通过命令行工具查询您的知识库。
```bash
python src/search/search_ai_assistant.py
```
*   **输入**: 您的搜索查询 (例如 `author:lecun + cnn` 或 `sem: reinforcement learning benchmarks`)
*   **输出**: 交互式的命令行结果展示，并可选择将搜索结果保存为格式化的 Markdown 文件，或启动 AI CLI 对话。

## 🗺️ 论文地图 (Paper Map)

本节旨在提供一个关于人工智能及其相关领域顶级学术会议和研究机构的宏观概览，为您的研究导航。

### 顶级会议概览

| 研究领域           | 会议列表                                                                                                      |
| :----------------- | :------------------------------------------------------------------------------------------------------------ |
| **🤖 人工智能 (AI)** | NeurIPS, ICML, ICLR, AAAI, IJCAI, AISTATS, UAI, COLT, CoRL, AutoML, ACML, ALT                                   |
| **💬 计算语言学 (CL)** | ACL, EMNLP, NAACL, COLING, ARR, COLM                                                                           |
| **👁️ 计算机视觉 (CV)** | CVPR, ICCV, ECCV, WACV, BMVC, 3DV                                                                              |
| **📈 数据挖掘 (Data Mining)** | KDD                                                                                                           |
| **🕸️ 信息检索 (IR)** | WWW, SIGIR                                                                                                      |
| **🦾 机器人学 (Robotics)** | ICRA, IROS, RSS                                                                                               |
| **🎨 计算机图形学 (Graphics)** | SIGGRAPH, SIGGRAPH Asia, EUROGRAPHICS                                                                         |
| **📡 计算机网络 (Networking)** | SIGCOMM                                                                                                       |
| **🎬 多媒体 (Multimedia)** | ACM-MM                                                                                                        |

### 顶级期刊概览 (Top Journals)

| 研究领域           | 期刊列表                                                     |
| :----------------- | :----------------------------------------------------------- |
| **🤖 人工智能/机器学习** | JMLR, TPAMI, Artificial Intelligence, Machine Learning, Nature Machine Intelligence |
| **👁️ 计算机视觉** | IJCV, TIP                                                    |
| **💬 计算语言学** | Computational Linguistics, TACL                              |
| **🦾 机器人学** | T-RO, IJRR, Science Robotics                                 |
| **📈 数据挖掘/工程** | TKDD, TKDE                                                   |
| **🌐 综合/顶级** | Nature, Science, PNAS                                        |

## 🙌 贡献 (Contributing)

欢迎任何形式的贡献！如果您有好的想法、发现了 Bug 或者想添加对新会议的支持，请随时提交 Pull Request 或创建 Issue。

## 📄 许可证 (License)

本项目采用 [MIT License](LICENSE) 授权。