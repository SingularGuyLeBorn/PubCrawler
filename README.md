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
    <img src="https://img.shields.io/badge/Toolchain-Command--Line-brightgreen" alt="Toolchain">
    <img src="https://img.shields.io/badge/AI%20Analysis-Matplotlib%20%26%20WordCloud-blueviolet" alt="AI Analysis">
    <img src="https://img.shields.io/badge/Search%20Ready-SQLite%20FTS5-orange" alt="Search Ready">
    <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License">
  </p>
</div>

---

## 🧐 项目简介 (Introduction)

您是否曾为追踪顶级学术会议（如 NeurIPS, ICLR, CVPR）和 arXiv 的最新动态而感到力不从心？是否想一键获取特定领域在过去数年间的所有相关论文，并自动生成一份精美的趋势分析报告？

**PubCrawler Pro** 正是为此而生。它不仅仅是一个论文爬虫，更是一个集**自动化数据采集**、**智能过滤**、**趋势分析**和**本地知识库构建**于一体的强大研究工作流引擎。我们的目标是——将您从繁琐的文献筛选中解放出来，专注于最前沿、最有价值的研究。✨

## 🌟 核心功能 (Current Features)

*   **⚙️ YAML 驱动的指挥中心**: 在 `configs/tasks.yaml` 中通过简单文本配置，即可指挥系统执行复杂的抓取与分析任务，无需修改任何代码。

*   **🌐 全方位多源爬取**:
    *   **API 直连**: 已内置对 **arXiv** (官方API) 和 **OpenReview** (ICLR/NeurIPS) 的稳定支持。
    *   **HTML 解析**: 高效解析 **CVF** (CVPR/ICCV), **PMLR** (ICML), 和 **ACL Anthology** (ACL/EMNLP) 等静态网站。
    *   **并发加速**: 针对 ACL/CVF 等需要逐页访问的网站，采用多线程并发抓取，极大提升效率。

*   **📊 自动化分析与报告**:
    *   **趋势词云**: 为每个任务自动生成词云图，让研究热点一目了然。
    *   **深度分析图表 (实验性)**: 自动生成**主题热度**、**主题质量 (平均分)**、**接收类型分布**和**跨年份趋势**等可视化图表。
    *   **多格式产出**: 自动为每个任务生成精美的 **Markdown 报告** 和 **CSV 数据**。

*   **🔍 本地智能搜索引擎 (实验性)**:
    *   **一键索引**: 提供脚本，可将所有爬取到的论文数据构建为本地的 **SQLite 全文搜索引擎 (FTS5)**。
    *   **高级命令行搜索**: 支持 `author:hinton + title:attention - transformer` 等高级搜索语法，在本地毫秒级检索您的学术知识库。

## 🗺️ 路线图 (Roadmap)

我们有一个清晰的多阶段计划，旨在将 PubCrawler Pro 从一个强大的命令行工具集演进为顶级的智能化学术分析平台。

*   **🧱 第一阶段: 奠定基石 - 命令行工具链 (已完成)**
    *   `[x]` YAML 驱动的集中式任务配置
    *   `[x]` 多源爬虫框架 (API, HTML, 并发)
    *   `[x]` 支持 arXiv, OpenReview, CVF, PMLR, ACL 等
    *   `[x]` 关键词过滤与数量限制
    *   `[x]` 自动化报告 (Markdown, CSV) 与词云分析
    *   `[x]` 自动化趋势分析图表生成
    *   `[x]` 本地全文搜索引擎构建与查询 (SQLite FTS5)

*   **🚀 第二阶段: 走向智能 - 语义理解与交互 (计划中)**
    *   `[ ]` **语义向量生成**: 集成 **Embedding 模型** (如 Sentence Transformers)，为每篇论文生成语义向量并存入数据库。
    *   `[ ]` **语义搜索**: 在本地搜索引擎中加入基于向量余弦相似度的语义搜索功能。
    *   `[ ]` **AI 对话 (AI Chat)**: 基于大语言模型，实现与单篇或多篇论文的深度问答功能。

*   **🌐 第三阶段: 服务化转型 - API 与后台任务 (计划中)**
    *   `[ ]` **后端 API 化**: 使用 FastAPI/Flask 提供服务接口。
    *   `[ ]` **数据库集成**: 使用 SQLAlchemy + PostgreSQL/SQLite 持久化存储数据。
    *   `[ ]` **异步任务核心**: 集成 Celery + Redis 处理所有耗时操作。
    *   `[ ]` **“每日简报”调度器**: 实现定时任务，自动抓取 arXiv 并发送 AI 总结邮件。

*   **🎨 第四阶段: 极致交互 - 现代化 Web 界面 (计划中)**
    *   `[ ]` **现代化前端**: 使用 React/Vue 搭建现代、简洁的 Web 界面。
    *   `[ ]` **可视化任务配置与结果展示**。
    *   `[ ]` **交互式图表**: 创建可交互的趋势分析仪表盘。

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
    ```
    然后运行安装命令：
    ```bash
    # 建议使用国内镜像源以加速
    pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
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

6.  **配置环境变量 (为未来AI功能准备)**
    在项目根目录创建一个 `.env` 文件，并填入您的人工智能模型 API 密钥（例如 Hugging Face 的 Token）：
    ```
    # .env
    HF_API_TOKEN="hf_..."
    ```

### 3. 如何运行 (Execution Flow)

项目当前为命令行驱动，请按以下顺序执行：

#### **第一步: 采集数据与分析**

这是核心步骤。运行主程序，它会自动读取 `configs/tasks.yaml`，执行所有 `enabled: true` 的任务。
```bash
python src/crawlers/run_crawler.py
```
*   **输入**: `configs/tasks.yaml`
*   **输出**: 所有爬取的数据 (`.csv`)、报告 (`.md`)、词云图 (`.png`) 和分析图表 (`.png`) 都将保存在 `output/` 目录下，按会议和年份自动创建子文件夹。

---

#### **第二步 (可选): 构建本地搜索引擎**

如果您想对采集到的所有论文进行快速本地搜索，请运行索引脚本。它会读取 `output/metadata` 目录下的所有 `.csv` 文件，并创建一个名为 `papers.db` 的 SQLite 数据库。
```bash
python src/search/indexer.py
```
*   **输入**: `output/metadata/**/*.csv`
*   **输出**: 项目根目录下的 `papers.db` 文件。

---

#### **第三步 (可选): 使用本地搜索引擎**

运行本地搜索命令行工具，开始查询您的知识库！
```bash
python src/search/search_local.py
```
*   **输入**: 您的搜索查询 (例如 `author:lecun + cnn`)
*   **输出**: 交互式的命令行结果展示，并可选择将搜索结果保存为格式化的 Markdown 文件。

## 🗺️ 论文地图 (Paper Map)

本节旨在提供一个关于人工智能及其相关领域顶级学术会议和研究机构的宏观概览，为您的研究导航。

### 顶级会议概览

| 研究领域 | 会议列表 |
| :--- | :--- |
| **🤖 人工智能 (AI)** | NeurIPS, ICML, ICLR, AAAI, IJCAI, AISTATS, UAI, COLT, CoRL, AutoML, ACML, ALT |
| **💬 计算语言学 (CL)** | ACL, EMNLP, NAACL, COLING, ARR, COLM |
| **👁️ 计算机视觉 (CV)** | CVPR, ICCV, ECCV, WACV, BMVC, 3DV |
| **📈 数据挖掘 (Data Mining)** | KDD |
| **🕸️ 信息检索 (IR)** | WWW, SIGIR |
| **🦾 机器人学 (Robotics)** | ICRA, IROS, RSS |
| **🎨 计算机图形学 (Graphics)** | SIGGRAPH, SIGGRAPH Asia, EUROGRAPHICS |
| **📡 计算机网络 (Networking)** | SIGCOMM |
| **🎬 多媒体 (Multimedia)** | ACM-MM |

### 顶级期刊概览 (Top Journals)

| 研究领域 | 期刊列表 |
| :--- | :--- |
| **🤖 人工智能/机器学习** | JMLR, TPAMI, Artificial Intelligence, Machine Learning, Nature Machine Intelligence |
| **👁️ 计算机视觉** | IJCV, TIP |
| **💬 计算语言学** | Computational Linguistics, TACL |
| **🦾 机器人学** | T-RO, IJRR, Science Robotics |
| **📈 数据挖掘/工程** | TKDD, TKDE |
| **🌐 综合/顶级** | Nature, Science, PNAS |

## 🙌 贡献 (Contributing)

欢迎任何形式的贡献！如果您有好的想法、发现了 Bug 或者想添加对新会议的支持，请随时提交 Pull Request 或创建 Issue。

## 📄 许可证 (License)

本项目采用 [MIT License](LICENSE) 授权。