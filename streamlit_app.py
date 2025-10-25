# FILE: streamlit_app.py
# 放置于项目根目录，与 'src' 和 'app.py' 同级。
# 运行: streamlit run streamlit_app.py

import streamlit as st
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any
import logging
import re
import math
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
import traceback  # 用于更详细的错误捕获

# -----------------------------------------------------------------
# 1. 导入项目模块
# -----------------------------------------------------------------
try:
    from src.search.search_service import (
        initialize_components, keyword_search, semantic_search,
        generate_ai_response, get_stats_summary, _initialized,
        ZHIPUAI_API_KEY, SEARCH_RESULTS_DIR
    )
    from src.crawlers.config import METADATA_OUTPUT_DIR, TRENDS_OUTPUT_DIR
    # 【v1.8 核心】从 trends.py 导入分析逻辑
    from src.analysis.trends import _load_trend_config, _create_analysis_df
except ImportError as e:
    st.error(f"导入项目模块失败！错误: {e}\n\n请确保满足所有依赖和文件结构要求。")
    st.stop()

# -----------------------------------------------------------------
# 2. 应用级常量
# -----------------------------------------------------------------
STREAMLIT_AI_CONTEXT_PAPERS = 20
RESULTS_PER_PAGE = 25
ANALYSIS_TOP_N = 50  # 趋势分析图表默认显示 Top N 主题

# -----------------------------------------------------------------
# 3. Streamlit 页面配置与后端初始化
# -----------------------------------------------------------------
st.set_page_config(page_title="PubCrawler Pro 🚀", layout="wide", initial_sidebar_state="expanded")


@st.cache_resource
def load_backend_components():
    print("--- [Streamlit] 正在初始化 PubCrawler 后端服务... ---")
    if not _initialized:
        try:
            initialize_components()
        except Exception as e:
            logging.error(f"后端初始化失败: {e}");
            return False
    if not _initialized: print("--- [Streamlit] 后端初始化失败! ---"); return False
    print("--- [Streamlit] 后端服务准备就绪。 ---")
    return True


backend_ready = load_backend_components()
if not backend_ready:
    st.error("后端服务初始化失败！请检查终端日志。");
    st.stop()

# -----------------------------------------------------------------
# 4. Streamlit 页面状态管理
# -----------------------------------------------------------------
if "chat_history" not in st.session_state: st.session_state.chat_history: List[Dict[str, str]] = []
if "current_search_results" not in st.session_state: st.session_state.current_search_results: List[Dict[str, Any]] = []
if "current_filtered_results" not in st.session_state: st.session_state.current_filtered_results: List[
    Dict[str, Any]] = []
if "current_query" not in st.session_state: st.session_state.current_query: str = ""
if "current_page" not in st.session_state: st.session_state.current_page: int = 1


# -----------------------------------------------------------------
# 5. 辅助函数
# -----------------------------------------------------------------
@st.cache_data(ttl=300)  # 缓存5分钟
def find_analysis_files():
    """
    扫描 output/ 目录查找分析 CSV 文件。
    v1.8: 改进了文件类型识别逻辑，使其更精确。
    返回:
        analysis_data (dict): 按 会议/年份 组织的 {"csvs": [{"path": Path, "type": str}]} 字典。
        all_conferences (list): 找到的所有会议名称列表。
        all_years (list): 找到的所有年份列表。
    """
    scan_dirs = {"metadata": METADATA_OUTPUT_DIR, "trends": TRENDS_OUTPUT_DIR}
    analysis_data = {}
    all_conferences = set();
    all_years = set()

    for dir_type, base_path in scan_dirs.items():
        if not base_path.exists(): continue
        all_csv_files_in_dir = list(base_path.rglob("*.csv"))

        for f in all_csv_files_in_dir:
            try:
                conf, year, csv_type = None, None, "unknown"
                relative_path = f.relative_to(base_path)
                parts = relative_path.parts

                # ---【v1.8 核心改进：识别逻辑】---
                if dir_type == "metadata":
                    # 规则 1: analysis/4_summary_table... or analysis/summary_table... -> "summary_table"
                    if "analysis" in parts and ("summary_table" in f.name or "4_summary_table" in f.name):
                        csv_type = "summary_table"
                        year = parts[-3]
                        conf = parts[-4]
                    # 规则 2: *_data_*.csv -> "raw_data"
                    elif "_data_" in f.name:
                        csv_type = "raw_data"
                        year = parts[-2]
                        conf = parts[-3]
                    # 规则 3: 其他在 analysis/ 下的文件 -> "analysis_other"
                    elif "analysis" in parts:
                        csv_type = "analysis_other"
                        year = parts[-3]
                        conf = parts[-4]

                elif dir_type == "trends":
                    # 规则 4: 在 trends/<conf>/ 下的 csv -> "trends"
                    if len(parts) == 2:
                        csv_type = "trends"
                        year = "Cross-Year"
                        conf = parts[-2]

                # --- 存储找到的文件信息 ---
                if conf and year:
                    all_conferences.add(conf);
                    all_years.add(year)
                    if conf not in analysis_data: analysis_data[conf] = {}
                    if year not in analysis_data[conf]: analysis_data[conf][year] = {"csvs": []}
                    file_entry = {"path": f, "type": csv_type}
                    if not any(item["path"] == f for item in analysis_data[conf][year]["csvs"]):
                        analysis_data[conf][year]["csvs"].append(file_entry)
            except Exception as scan_e:
                logging.warning(f"扫描文件 {f} 时出错: {scan_e}")

    return analysis_data, sorted(list(all_conferences)), sorted(list(all_years),
                                                                key=lambda y: "9999" if y == "Cross-Year" else y,
                                                                reverse=True)


def save_results_to_markdown_fixed(results: List[Dict[str, Any]], query: str) -> str:
    """ 保存 Markdown，包含摘要和 PDF 链接。"""
    if not results: return "没有搜索结果可保存。"
    SEARCH_RESULTS_DIR.mkdir(exist_ok=True)
    session_dir = SEARCH_RESULTS_DIR / f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    session_dir.mkdir(exist_ok=True)
    safe_query = re.sub(r'[\\/*?:"<>|]', "", query).replace(" ", "_")[:50]
    filename = session_dir / f"search_{safe_query}.md"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(f"# 搜索查询: \"{query}\"\n\n**共找到 {len(results)} 条相关结果**\n\n---\n\n")
        for idx, paper in enumerate(results, 1):
            title = paper.get('title', 'N/A');
            authors = paper.get('authors', 'N/A')
            abstract = paper.get('abstract', 'N/A');
            conf = paper.get('conference', 'N/A')
            year = paper.get('year', 'N/A');
            pdf_url = paper.get('pdf_url', '#')
            f.write(f"### {idx}. {title}\n\n");
            f.write(f"- **作者**: {authors}\n")
            f.write(f"- **会议/年份**: {conf} {year}\n")
            if 'similarity' in paper: f.write(f"- **语义相似度**: {paper['similarity']:.3f}\n")
            if pdf_url and pdf_url != '#':
                pdf_display_name = pdf_url.split('/')[-1] if '/' in pdf_url else "链接"
                f.write(f"- **PDF 链接**: [{pdf_display_name}]({pdf_url})\n")
            f.write(f"\n**摘要:**\n> {abstract}\n\n---\n\n")
    return str(filename.resolve())


# -----------------------------------------------------------------
# 6. 页面渲染函数
# -----------------------------------------------------------------

def render_search_and_chat_page():
    """ 渲染 "AI 助手 & 搜索" 页面 """
    st.header("🔍 PubCrawler Pro: AI 助手 & 搜索", divider="rainbow")
    _, conf_list, year_list = find_analysis_files()
    search_query = st.text_input("搜索本地学术知识库...", key="search_input",
                                 placeholder="输入关键词或 'sem:' 前缀进行语义搜索",
                                 help="关键词搜索: `transformer author:vaswani` | 语义搜索: `sem: few-shot learning efficiency`")
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        selected_conferences = st.multiselect("筛选会议", options=conf_list, key="filter_conf")
    with col_f2:
        selected_years = st.multiselect("筛选年份", options=year_list, key="filter_year")
    is_new_search = (st.session_state.search_input != st.session_state.current_query)
    if is_new_search:
        with st.spinner(f"正在搜索: {st.session_state.search_input}..."):
            results, stats = [], {};
            query = st.session_state.search_input.strip()
            if query.lower().startswith('sem:'):
                query_text = query[4:].strip();
                if query_text: results, stats = semantic_search(query_text)
            elif query:
                results, stats = keyword_search(query)
            st.session_state.current_search_results = results
            st.session_state.current_query = st.session_state.search_input
            st.session_state.chat_history = [];
            st.session_state.current_page = 1
            st.toast(stats.get('message', '搜索完成!'))
    if st.session_state.current_search_results:
        temp_filtered_results = st.session_state.current_search_results
        if selected_conferences: temp_filtered_results = [p for p in temp_filtered_results if
                                                          p.get('conference') in selected_conferences]
        if selected_years: temp_filtered_results = [p for p in temp_filtered_results if
                                                    str(p.get('year')) in selected_years]
        st.session_state.current_filtered_results = temp_filtered_results
    else:
        st.session_state.current_filtered_results = []
    if is_new_search: st.session_state.current_page = 1
    col_results, col_chat = st.columns([0.6, 0.4])
    with col_results:
        results_to_display = st.session_state.current_filtered_results
        st.subheader(
            f"搜索结果 (筛选后: {len(results_to_display)} 篇 / 原始: {len(st.session_state.current_search_results)} 篇)")
        if results_to_display:
            with st.container(border=True, height=300):
                stats = get_stats_summary(results_to_display);
                c1, c2 = st.columns(2)
                c1.metric("筛选后找到", f"{stats['total_found']} 篇")
                if c2.button("📥 保存当前 *筛选后* 的结果到 Markdown", use_container_width=True):
                    with st.spinner("正在保存..."):
                        save_path = save_results_to_markdown_fixed(results_to_display, st.session_state.current_query)
                        st.success(f"结果已保存到: {save_path}")
                st.write("**会议/年份分布 (筛选后):**");
                st.dataframe(pd.DataFrame(stats['distribution'].items(), columns=['来源', '论文数']),
                             use_container_width=True, hide_index=True)
            st.divider()
            total_items = len(results_to_display);
            total_pages = math.ceil(total_items / RESULTS_PER_PAGE)
            if st.session_state.current_page > total_pages: st.session_state.current_page = max(1, total_pages)
            page_display_text = f"第 {st.session_state.current_page} / {total_pages} 页 ({total_items} 条)" if total_pages > 0 else "无结果"
            col_page1, col_page2, col_page3 = st.columns([1, 2, 1])
            with col_page1:
                if st.button("上一页", disabled=st.session_state.current_page <= 1,
                             use_container_width=True): st.session_state.current_page -= 1; st.rerun()
            with col_page2:
                st.markdown(f"<div style='text-align: center; margin-top: 8px;'>{page_display_text}</div>",
                            unsafe_allow_html=True)
            with col_page3:
                if st.button("下一页", disabled=st.session_state.current_page >= total_pages,
                             use_container_width=True): st.session_state.current_page += 1; st.rerun()
            start_idx = (st.session_state.current_page - 1) * RESULTS_PER_PAGE;
            end_idx = start_idx + RESULTS_PER_PAGE
            paginated_results = results_to_display[start_idx:end_idx]
            for i, paper in enumerate(paginated_results, start=start_idx + 1):
                with st.expander(f"**{i}. {paper.get('title', 'N/A')}**"):
                    if 'similarity' in paper: st.markdown(f"**语义相似度**: `{paper['similarity']:.3f}`")
                    st.markdown(f"**作者**: *{paper.get('authors', 'N/A')}*");
                    st.markdown(f"**会议/年份**: {paper.get('conference', 'N/A')} {paper.get('year', 'N/A')}")
                    abstract_text = paper.get('abstract', None)
                    if abstract_text is None or abstract_text == '' or abstract_text == 'N/A' or pd.isna(abstract_text):
                        st.markdown(
                            f"**摘要**: <span style='color:orange; font-style: italic;'>[摘要信息缺失或为空]</span>",
                            unsafe_allow_html=True)
                    else:
                        st.markdown(f"**摘要**: \n> {abstract_text}")
                    pdf_url = paper.get('pdf_url', '#');
                    if pdf_url and pdf_url != '#': st.link_button("🔗 打开 PDF 链接", pdf_url)
        elif st.session_state.current_query:
            st.info("未找到相关结果（或被筛选条件过滤）。")
        else:
            st.info("请输入查询以开始搜索。")
    with col_chat:
        st.subheader(f"🤖 AI 对话助手");
        st.info(f"AI 将基于上文搜索到的 **Top {STREAMLIT_AI_CONTEXT_PAPERS}** 篇论文进行回答。")
        chat_container = st.container(height=500, border=True)
        with chat_container:
            for message in st.session_state.chat_history:
                with st.chat_message(message["role"]): st.markdown(message["content"])
        if not ZHIPUAI_API_KEY:
            st.error("未配置 ZHIPUAI_API_KEY!"); chat_disabled = True
        elif not st.session_state.current_filtered_results:
            st.info("请先搜索并确保有结果再对话。"); chat_disabled = True
        else:
            chat_disabled = False
        if prompt := st.chat_input("基于搜索结果提问...", disabled=chat_disabled, key="chat_input"):
            st.session_state.chat_history.append({"role": "user", "content": prompt});
            st.rerun()
        if st.session_state.chat_history and st.session_state.chat_history[-1]["role"] == "user":
            with chat_container:
                for message in st.session_state.chat_history:
                    with st.chat_message(message["role"]): st.markdown(message["content"])
                with st.chat_message("assistant"):
                    with st.spinner("AI 正在思考..."):
                        response = generate_ai_response(st.session_state.chat_history,
                                                        st.session_state.current_filtered_results[
                                                            :STREAMLIT_AI_CONTEXT_PAPERS])
                        st.markdown(response)
            st.session_state.chat_history.append({"role": "assistant", "content": response});
            st.rerun()
        if st.session_state.chat_history and not chat_disabled:
            if st.button("清除对话历史", use_container_width=True): st.session_state.chat_history = []; st.rerun()


def render_analysis_dashboard_page():
    """
    渲染 "趋势分析仪表盘" 页面 (v1.8 - 统一原始数据和汇总数据的分析流程)
    """
    st.header("📊 趋势分析仪表盘", divider="rainbow")
    st.info(
        "选择会议、年份和分析文件。系统将自动识别文件类型，并为 **原始数据** 或 **汇总数据** 生成可交互的趋势图表。"
    )

    analysis_data, _, _ = find_analysis_files()
    if not analysis_data:
        st.warning("未找到任何分析文件。请先运行 `run_crawler.py` 采集数据。");
        st.stop()

    # --- 用户选择 ---
    selected_conf = st.selectbox("1. 选择会议", options=sorted(analysis_data.keys()))
    if not selected_conf: st.stop()

    conf_data = analysis_data[selected_conf]
    sorted_years = sorted(conf_data.keys(), key=lambda y: "9999" if y == "Cross-Year" else y, reverse=True)
    selected_year = st.selectbox(f"2. 选择 {selected_conf} 的年份或跨年数据", options=sorted_years)
    if not selected_year: st.stop()

    if selected_year not in conf_data or not conf_data[selected_year]["csvs"]:
        st.warning(f"未找到 {selected_conf} {selected_year} 的 CSV 数据文件。");
        st.stop()

    files_info = conf_data[selected_year]
    csv_options_sorted = sorted(files_info["csvs"], key=lambda item: (
        0 if item['type'] == 'raw_data' else 1 if item['type'] == 'summary_table' else 2))
    csv_options = {f"{item['path'].name} (类型: {item['type']})": item for item in csv_options_sorted}
    selected_csv_label = st.selectbox("3. 选择要分析的 CSV 文件", options=csv_options.keys())
    if not selected_csv_label: st.stop()

    selected_csv_info = csv_options[selected_csv_label]
    csv_path = selected_csv_info["path"]
    csv_type = selected_csv_info["type"]

    st.markdown(f"#### 正在分析: `{csv_path.name}`")

    # --- 加载并处理 CSV ---
    try:
        df = pd.read_csv(csv_path)
        if df.empty:
            st.warning("CSV 文件为空。");
            st.stop()

        # --- 【v1.8 核心改动：统一分析流程】---
        st.markdown("---")
        analysis_df = None
        is_analyzed = False

        if csv_type == "summary_table":
            st.success("✔️ 检测到 **汇总分析文件**。直接使用其数据生成图表。")
            analysis_df = df
            is_analyzed = True

        elif csv_type == "raw_data":
            st.info("💡 检测到 **原始数据文件**。正在进行即时趋势分析...")
            trend_config = _load_trend_config()
            if trend_config:
                with st.spinner("正在基于 `trends.yaml` 配置分析原始论文数据..."):
                    analysis_df = _create_analysis_df(df, trend_config)
                if not analysis_df.empty:
                    st.success("✔️ 即时分析完成！已生成下方图表。")
                    is_analyzed = True
                else:
                    st.warning("分析完成，但未能从原始数据中匹配到任何 `trends.yaml` 中定义的关键词。")
            else:
                st.error("无法加载 `configs/trends.yaml` 配置文件，分析中止。")

        # --- 统一绘图逻辑 ---
        if is_analyzed and analysis_df is not None:
            # 图表 1: 主题热度 (按论文数)
            st.markdown(f"##### 1. 主题热度排名 (Top {ANALYSIS_TOP_N} 论文数)")
            if 'paper_count' in analysis_df.columns and 'Topic_Name' in analysis_df.columns:
                fig_hotness = px.bar(analysis_df.sort_values(by='paper_count', ascending=False).head(ANALYSIS_TOP_N),
                                     x='paper_count', y='Topic_Name', orientation='h',
                                     title=f'{selected_conf} {selected_year} - Top {ANALYSIS_TOP_N} 热门主题 (论文数量)',
                                     labels={'paper_count': '论文数量', 'Topic_Name': '主题'},
                                     text_auto=True, height=max(600, len(analysis_df.head(ANALYSIS_TOP_N)) * 20))
                fig_hotness.update_layout(yaxis={'categoryorder': 'total ascending'})
                st.plotly_chart(fig_hotness, use_container_width=True)
            else:
                st.caption("无法生成图表：缺少 `paper_count` 或 `Topic_Name` 列。")

            # 图表 2: 主题质量 (按平均分)
            if 'avg_rating' in analysis_df.columns and analysis_df['avg_rating'].notna().any():
                st.markdown(f"##### 2. 主题质量排名 (Top {ANALYSIS_TOP_N} 平均审稿分)")
                df_quality = analysis_df.dropna(subset=['avg_rating']).sort_values(by='avg_rating',
                                                                                   ascending=False).head(ANALYSIS_TOP_N)
                if not df_quality.empty:
                    fig_quality = px.bar(df_quality, x='avg_rating', y='Topic_Name', orientation='h',
                                         title=f'{selected_conf} {selected_year} - Top {ANALYSIS_TOP_N} 主题 (平均审稿分)',
                                         labels={'avg_rating': '平均审稿分', 'Topic_Name': '主题'},
                                         text_auto='.2f', height=max(600, len(df_quality) * 20))
                    fig_quality.update_layout(yaxis={'categoryorder': 'total ascending'})
                    st.plotly_chart(fig_quality, use_container_width=True)
                else:
                    st.caption("未能生成图表：筛选后数据为空。")
            else:
                st.caption("主题质量图表不可用 (缺少 `avg_rating` 数据)。")

            # 图表 3: 决策构成
            decision_cols = [col for col in ['Oral', 'Spotlight', 'Poster', 'Reject', 'N/A'] if
                             col in analysis_df.columns]
            if 'acceptance_rate' in analysis_df.columns and decision_cols:
                st.markdown(f"##### 3. 主题接收构成 (Top {ANALYSIS_TOP_N} 按接收率排序)")
                df_decision = analysis_df.dropna(subset=['acceptance_rate']).sort_values(by='acceptance_rate',
                                                                                         ascending=False).head(
                    ANALYSIS_TOP_N)
                if not df_decision.empty:
                    df_plot = df_decision.set_index('Topic_Name')[decision_cols].copy()
                    df_plot = df_plot.loc[(df_plot.sum(axis=1) > 0)]
                    if not df_plot.empty:
                        df_plot_normalized = df_plot.div(df_plot.sum(axis=1), axis=0)
                        fig_stack = px.bar(df_plot_normalized, y=df_plot_normalized.index, x=df_plot_normalized.columns,
                                           orientation='h',
                                           title=f'{selected_conf} {selected_year} - Top {ANALYSIS_TOP_N} 主题决策构成 (按接收率排序)',
                                           labels={'value': '论文比例', 'variable': '决策类型', 'y': '主题'},
                                           height=max(600, len(df_plot_normalized) * 25), text_auto='.1%')
                        fig_stack.update_layout(yaxis={'categoryorder': 'total ascending'}, xaxis_tickformat=".0%",
                                                legend_title_text='决策类型')
                        fig_stack.update_traces(hovertemplate='<b>%{y}</b><br>%{variable}: %{x:.1%}<extra></extra>')
                        st.plotly_chart(fig_stack, use_container_width=True)
                else:
                    st.caption("未能生成决策构成图：筛选后数据为空。")
            else:
                st.caption("主题决策构成图表不可用 (缺少 `acceptance_rate` 或决策列数据)。")

        # --- 跨年份趋势文件处理逻辑 (保持独立) ---
        elif csv_type == "trends":
            st.subheader("📈 跨年份趋势图")
            if 'year' in df.columns or df.index.name == 'year':
                df_indexed = df.set_index('year') if 'year' in df.columns else df
                numeric_cols = df_indexed.select_dtypes(include='number').columns
                if not numeric_cols.empty:
                    top_topics = df_indexed[numeric_cols].sum().nlargest(15).index
                    df_top = df_indexed[top_topics]
                    fig_line = px.line(df_top, x=df_top.index, y=df_top.columns, markers=True,
                                       title=f'{selected_conf} - Top 15 主题历年论文数趋势',
                                       labels={'year': '年份', 'value': '论文数量', 'variable': '主题'})
                    fig_line.update_layout(xaxis_type='category')
                    st.plotly_chart(fig_line, use_container_width=True)
                else:
                    st.warning("趋势文件中没有找到可用于绘图的数值列。")
            else:
                st.warning(f"无法为 `{csv_path.name}` 生成趋势折线图。请确保 CSV 有一个年份列/索引。")

        # --- 其他文件类型的预览逻辑 ---
        else:  # 'analysis_other', 'unknown'
            st.subheader("📄 数据预览")
            st.info(f"检测到文件类型为 **{csv_type}**。此类文件不适用于标准图表生成，仅提供数据表格预览。")
            st.dataframe(df, height=500, use_container_width=True)

        # --- 显示/下载原始数据表格 (适用于所有类型) ---
        st.markdown("---")
        with st.expander("查看/下载当前 CSV 的原始数据"):
            st.dataframe(df, height=300, use_container_width=True)
            st.download_button(
                label=f"📥 下载数据: {csv_path.name}",
                data=df.to_csv(index=False).encode('utf-8-sig'),
                file_name=csv_path.name,
                mime='text/csv',
                key=f"download_{csv_path.stem}"
            )

    except Exception as e:
        st.error(f"处理或可视化文件 {csv_path.name} 时出错: {e}")
        st.error(traceback.format_exc())


# -----------------------------------------------------------------
# 7. 主应用逻辑：侧边栏导航
# -----------------------------------------------------------------
st.sidebar.title("PubCrawler Pro 🚀");
st.sidebar.caption("v1.8 - Unified Analysis")
page = st.sidebar.radio("选择功能页面", ["📊 趋势分析仪表盘", "🤖 AI 助手 & 搜索"], key="page_selection")
st.sidebar.divider()
analysis_data_sidebar, conf_list_sidebar, _ = find_analysis_files()
if conf_list_sidebar:
    with st.sidebar.expander("目前已索引的会议", expanded=True):
        st.dataframe(pd.DataFrame({"会议名称": conf_list_sidebar}), use_container_width=True, hide_index=True)

if page == "🤖 AI 助手 & 搜索":
    render_search_and_chat_page()
elif page == "📊 趋势分析仪表盘":
    render_analysis_dashboard_page()
# END OF FILE: streamlit_app.py