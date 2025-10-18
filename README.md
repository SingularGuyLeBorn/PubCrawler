<div align="center">
  <img src="./logo.png" alt="PubCrawler Pro Logo" width="150"/>
  <h1>PubCrawler Pro</h1>
  <p>
    <strong>您的下一代 AI 学术趋势分析助手 🚀</strong>
  </p>
  <p>
    自动化爬取、分析并洞察顶级学术会议的最新研究动态。
  </p>
  <p>
    <img src="https://img.shields.io/badge/Python-3.9+-blue.svg" alt="Python Version">
    <img src="https://img.shields.io/badge/Framework-Flask/Celery-orange" alt="Framework">
    <img src="https://img.shields.io/badge/AI%20Powered-Analysis-blueviolet" alt="AI Powered">
    <img src="https://img.shields.io/badge/Knowledge%20Base-YAML-informational" alt="Knowledge Base">
    <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License">
    <img src="https://img.shields.io/badge/build-passing-brightgreen" alt="Build Status">
  </p>
</div>

---

## 🧐 项目简介 (Introduction)

您是否曾为追踪顶级学术会议（如 NeurIPS, ICLR, CVPR）的最新动态而感到力不从心？是否想快速了解某一特定领域（如“大语言模型”或“扩散模型”）的年度研究热点？

**PubCrawler Pro** 正是为此而生。它不仅仅是一个论文爬虫，更是一个集自动化数据采集、智能过滤、AI 深度分析和趋势可视化于一体的强大研究工具。只需一份 `YAML` 配置文件，您就可以指挥它为您完成所有繁重的工作，最终生成图文并茂的分析报告。✨

## 🌟 核心功能 (Core Features)

*   **⚙️ YAML 驱动**: 所有任务均在 `configs/tasks.yaml` 中定义，与代码完全分离，配置极其灵活。
*   **🌐 多源爬取**: 内置支持 OpenReview, CVF (CVPR/ICCV), PMLR (ICML), ACL Anthology 等主流平台，并可通过 Selenium 应对动态加载的复杂网站。当然，arXiv 也在我们的计划之中！
*   **🔍 智能过滤**: 可为每个任务设置关键词 `filters`，只抓取您关心的特定领域论文，实现精准打击。
*   **🧠 AI 深度分析**: （即将推出）集成大语言模型（LLM），一键为每篇论文生成核心摘要、技术评估和“值得读指数”，帮您从海量信息中快速筛选出最有价值的文献。
*   **📊 自动化报告与词云**: 为每个任务自动生成格式精美的 Markdown 报告，并嵌入直观的词云图，让年度研究热点一目了然。
*   **📈 趋势可视化**: （未来规划）通过交互式仪表盘，洞察特定技术或研究领域在不同会议、不同年份的演进趋势。
*   **🕒 后台任务处理**: 集成 Celery 和 Redis，所有耗时任务都在后台异步执行，提供流畅的前端交互体验。

## 🚀 快速开始 (Getting Started)

### 1. 环境准备

*   Python 3.9+
*   Redis (用于 Celery 任务队列)

### 2. 安装步骤
1. 克隆项目
```bash
# 1. 克隆项目
git clone https://github.com/SingularGuyLeBorn/PubCrawler.git
cd PubCrawler
```

2. 创建并激活虚拟环境
```bash
python -m venv .venv
source .venv/bin/activate  # on Windows: .\.venv\Scripts\activate
```
3. 安装所有依赖
```bash
uv pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

4. 【重要】下载 NLTK 数据包
```bash
# 首次运行时，需要手动下载停用词数据
python -m nltk.downloader stopwords```
```

### 3. 配置

*   **任务配置**: 打开 `configs/tasks.yaml` 文件，根据您的需求修改 `source_definitions` 和 `tasks` 列表。您可以启用/禁用任务，设置 `limit` 和 `filters` 等。
*   **环境变量**: (针对未来AI功能) 创建一个 `.env` 文件，并填入您的 AI 模型 API 密钥：
    ```
    OPENAI_API_KEY="sk-..."
    ```

### 4. 运行项目

```bash
# 启动 Celery Worker (在独立的终端中)
celery -A src.tasks worker --loglevel=info

# 启动 Flask Web 服务器 (在另一个终端中)
flask --app src.app run
```
*注意: 上述命令为未来 API 化阶段的示例。当前阶段仍使用 `python -m src.main` 运行。*

## 🛠️ 如何使用 (Usage)

当前阶段，项目由命令行驱动：

1.  **编辑 `configs/tasks.yaml`**: 这是您的指挥中心。在 `tasks` 列表下，找到您想运行的任务，将 `enabled` 设置为 `true`。您可以按需修改 `limit`, `download_pdfs` 和 `filters`。

2.  **运行主程序**:
    ```bash
    python -m src.main
    ```

3.  **查看成果**:
    所有产出文件都将保存在 `output/` 目录下，并以任务名自动创建子文件夹。

## 🗺️ 路线图 (Roadmap)

我们有一个清晰的多阶段计划，将 PubCrawler Pro 打造成顶级的学术分析平台：

*   **🧱 第一阶段: 奠定基石 (已完成)**
    *   [x] YAML 驱动的配置系统
    *   [x] 多源爬虫框架 (Requests, Selenium)
    *   [x] 关键词过滤与数量限制
    *   [x] 自动化报告生成 (Markdown, CSV, TXT)
    *   [x] 词云分析与可视化

*   **🎨 第二阶段: 核心交互 (进行中)**
    *   [ ] 后端 API 化 (Flask/FastAPI)
    *   [ ] 数据库集成 (SQLite/PostgreSQL)
    *   [ ] 异步任务队列 (Celery + Redis)
    *   [ ] 现代化前端 UI，用于任务配置和结果展示
    *   [ ] 论文卡片式结果布局

*   **✨ 第三阶段: 智能升维**
    *   [ ] 集成大语言模型 (LLM) API
    *   [ ] "AI 分析"功能：自动总结、评分、提取关键信息
    *   [ ] 分析结果缓存，避免重复调用

*   **📊 第四阶段: 宏观洞察**
    *   [ ] 趋势分析仪表盘 (Dashboard) UI
    *   [ ] 后端数据聚合 API
    *   [ ] 交互式图表（折线图、条形图、饼图）展示跨年份、跨会议的技术趋势

## 🙌 贡献 (Contributing)

欢迎任何形式的贡献！如果您有好的想法、发现了 Bug 或者想添加对新会议的支持，请随时提交 Pull Request 或创建 Issue。

## 📄 许可证 (License)

本项目采用 [MIT License](LICENSE) 授权。
