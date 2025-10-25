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
import traceback # 用于更详细的错误捕获

# -----------------------------------------------------------------
# 1. 导入项目模块 (保持不变)
# -----------------------------------------------------------------
try:
    from src.search.search_service import (
        initialize_components, keyword_search, semantic_search,
        generate_ai_response, get_stats_summary, _initialized,
        ZHIPUAI_API_KEY, SEARCH_RESULTS_DIR
    )
    from src.crawlers.config import METADATA_OUTPUT_DIR, TRENDS_OUTPUT_DIR
except ImportError as e:
    st.error(f"导入项目模块失败！错误: {e}\n\n请确保满足所有依赖和文件结构要求。")
    st.stop()

# -----------------------------------------------------------------
# 2. 应用级常量 (保持不变)
# -----------------------------------------------------------------
STREAMLIT_AI_CONTEXT_PAPERS = 20
RESULTS_PER_PAGE = 25
ANALYSIS_TOP_N = 50 # 趋势分析图表默认显示 Top N 主题

# -----------------------------------------------------------------
# 3. Streamlit 页面配置与后端初始化 (保持不变)
# -----------------------------------------------------------------
st.set_page_config(page_title="PubCrawler Pro 🚀", layout="wide", initial_sidebar_state="expanded")

@st.cache_resource
def load_backend_components():
    print("--- [Streamlit] 正在初始化 PubCrawler 后端服务... ---")
    if not _initialized:
        try: initialize_components()
        except Exception as e:
            logging.error(f"后端初始化失败: {e}"); return False
    if not _initialized: print("--- [Streamlit] 后端初始化失败! ---"); return False
    print("--- [Streamlit] 后端服务准备就绪。 ---")
    return True

backend_ready = load_backend_components()
if not backend_ready:
    st.error("后端服务初始化失败！请检查终端日志。"); st.stop()

# -----------------------------------------------------------------
# 4. Streamlit 页面状态管理 (保持不变)
# -----------------------------------------------------------------
if "chat_history" not in st.session_state: st.session_state.chat_history: List[Dict[str, str]] = []
if "current_search_results" not in st.session_state: st.session_state.current_search_results: List[Dict[str, Any]] = []
if "current_filtered_results" not in st.session_state: st.session_state.current_filtered_results: List[Dict[str, Any]] = []
if "current_query" not in st.session_state: st.session_state.current_query: str = ""
if "current_page" not in st.session_state: st.session_state.current_page: int = 1

# -----------------------------------------------------------------
# 5. 辅助函数
# -----------------------------------------------------------------
def find_analysis_files():
    """
    扫描 output/ 目录查找分析 CSV 文件，无缓存。
    v1.7: 更精确地识别 CSV 类型，增加调试信息。
    返回:
        analysis_data (dict): 按 会议/年份 组织的 {"csvs": [{"path": Path, "type": str}]} 字典。
        all_conferences (list): 找到的所有会议名称列表。
        all_years (list): 找到的所有年份列表。
    """
    print("--- [Streamlit] 正在扫描分析文件 (v1.7 - 无缓存)... ---")
    # st.write("--- [Streamlit] 正在扫描分析文件 (v1.7 - 无缓存)... ---") # 调试时取消注释
    scan_dirs = {"metadata": METADATA_OUTPUT_DIR, "trends": TRENDS_OUTPUT_DIR}
    analysis_data = {}
    all_conferences = set(); all_years = set()
    found_files_debug = [] # 用于调试

    for dir_type, base_path in scan_dirs.items():
        if not base_path.exists(): continue
        # 统一查找所有 CSV 文件
        all_csv_files_in_dir = list(base_path.rglob("*.csv"))

        for f in all_csv_files_in_dir:
            try:
                conf, year = None, None
                csv_type = "unknown" # 默认类型

                relative_path = f.relative_to(METADATA_OUTPUT_DIR if dir_type == "metadata" else TRENDS_OUTPUT_DIR)
                parts = relative_path.parts

                # ---【v1.7 核心改进：识别逻辑】---
                if dir_type == "metadata":
                    # 规则 1: 路径是否匹配 <conf>/<year>/analysis/<filename>.csv
                    if len(parts) >= 3 and parts[-2] == "analysis":
                        year = parts[-3]
                        conf = parts[-4] if len(parts) >= 4 else None # e.g., output/metadata/ICLR/2025/analysis/file.csv
                        if conf:
                             # 根据文件名进一步细化
                            if "summary_table" in f.name or "4_summary_table" in f.name:
                                csv_type = "summary_table"
                            else:
                                csv_type = "analysis_other" # 其他在 analysis 下的文件
                    # 规则 2: 文件名是否包含 _data_ 且路径匹配 <conf>/<year>/<filename>.csv
                    elif "_data_" in f.name and len(parts) == 3:
                        year = parts[-2]
                        conf = parts[-3]
                        csv_type = "raw_data"
                    # 可选：添加其他规则来识别 metadata 下的其他类型 CSV

                elif dir_type == "trends":
                    # 规则 3: 路径是否匹配 <conf>/<filename>.csv
                    if len(parts) == 2:
                        conf = parts[-2]
                        year = "Cross-Year"
                        csv_type = "trends"

                # --- 存储找到的文件信息 ---
                if conf and year:
                    all_conferences.add(conf); all_years.add(year)
                    if conf not in analysis_data: analysis_data[conf] = {}
                    if year not in analysis_data[conf]: analysis_data[conf][year] = {"csvs": []}
                    file_entry = {"path": f, "type": csv_type}
                    # 调试信息: 记录每个文件的路径和识别出的类型
                    found_files_debug.append(f"Path: {relative_path}, Conf: {conf}, Year: {year}, Type: {csv_type}")
                    if not any(item["path"] == f for item in analysis_data[conf][year]["csvs"]):
                        analysis_data[conf][year]["csvs"].append(file_entry)
            except Exception as scan_e:
                print(f"扫描文件 {f} 时出错: {scan_e}")
                # st.write(f"扫描文件 {f} 时出错: {scan_e}") # 调试时取消注释


    # ---【v1.7 调试输出】---
    # print("\n--- 文件扫描调试信息 ---")
    # for entry in found_files_debug:
    #     print(entry)
    # print("--- 调试结束 ---\n")
    # # 在 Streamlit 界面显示调试信息（调试完成后注释掉）
    # with st.expander("文件扫描调试信息 (v1.7)", expanded=False):
    #      st.json(analysis_data) # 更结构化地显示结果
    #      st.write(found_files_debug) # 显示原始调试列表

    print(f"--- [Streamlit] 扫描完成，找到会议: {list(all_conferences)}, 年份: {list(all_years)} ---")
    return analysis_data, sorted(list(all_conferences)), sorted(list(all_years), key=lambda y: "9999" if y == "Cross-Year" else y, reverse=True)


def save_results_to_markdown_fixed(results: List[Dict[str, Any]], query: str) -> str:
    """ (v1.3) 保存 Markdown，包含摘要和 PDF 链接。"""
    # ... (内部逻辑保持不变) ...
    if not results: return "没有搜索结果可保存。"
    SEARCH_RESULTS_DIR.mkdir(exist_ok=True)
    session_dir = SEARCH_RESULTS_DIR / f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    session_dir.mkdir(exist_ok=True)
    safe_query = re.sub(r'[\\/*?:"<>|]', "", query).replace(" ", "_")[:50]
    filename = session_dir / f"search_{safe_query}.md"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(f"# 搜索查询: \"{query}\"\n\n**共找到 {len(results)} 条相关结果**\n\n---\n\n")
        for idx, paper in enumerate(results, 1):
            title = paper.get('title', 'N/A'); authors = paper.get('authors', 'N/A')
            abstract = paper.get('abstract', 'N/A'); conf = paper.get('conference', 'N/A')
            year = paper.get('year', 'N/A'); pdf_url = paper.get('pdf_url', '#')
            f.write(f"### {idx}. {title}\n\n"); f.write(f"- **作者**: {authors}\n")
            f.write(f"- **会议/年份**: {conf} {year}\n")
            if 'similarity' in paper: f.write(f"- **语义相似度**: {paper['similarity']:.3f}\n")
            if pdf_url and pdf_url != '#':
                pdf_display_name = pdf_url.split('/')[-1] if '/' in pdf_url else "链接"
                f.write(f"- **PDF 链接**: [{pdf_display_name}]({pdf_url})\n")
            f.write(f"\n**摘要:**\n> {abstract}\n\n---\n\n")
    return str(filename.resolve())


def get_numeric_columns(df): return df.select_dtypes(include=['number']).columns.tolist()
def get_categorical_columns(df): return df.select_dtypes(include=['object', 'category']).columns.tolist()

# -----------------------------------------------------------------
# 6. 页面渲染函数
# -----------------------------------------------------------------

def render_search_and_chat_page():
    """ 渲染 "AI 助手 & 搜索" 页面 (v1.7 逻辑) """
    # ... (大部分逻辑不变) ...
    st.header("🔍 PubCrawler Pro: AI 助手 & 搜索", divider="rainbow")
    _, conf_list, year_list = find_analysis_files()
    search_query = st.text_input("搜索本地学术知识库...", key="search_input", placeholder="输入关键词或 'sem:' 前缀进行语义搜索", help="关键词搜索: `transformer author:vaswani` | 语义搜索: `sem: few-shot learning efficiency`")
    col_f1, col_f2 = st.columns(2)
    with col_f1: selected_conferences = st.multiselect("筛选会议", options=conf_list, key="filter_conf")
    with col_f2: selected_years = st.multiselect("筛选年份", options=year_list, key="filter_year")
    is_new_search = (st.session_state.search_input != st.session_state.current_query)
    if is_new_search:
        with st.spinner(f"正在搜索: {st.session_state.search_input}..."):
            results, stats = [], {}; query = st.session_state.search_input.strip()
            if query.lower().startswith('sem:'):
                query_text = query[4:].strip();
                if query_text: results, stats = semantic_search(query_text)
            elif query: results, stats = keyword_search(query)
            st.session_state.current_search_results = results
            st.session_state.current_query = st.session_state.search_input
            st.session_state.chat_history = []; st.session_state.current_page = 1
            st.toast(stats.get('message', '搜索完成!'))
    if st.session_state.current_search_results:
        temp_filtered_results = st.session_state.current_search_results
        if selected_conferences: temp_filtered_results = [p for p in temp_filtered_results if p.get('conference') in selected_conferences]
        if selected_years: temp_filtered_results = [p for p in temp_filtered_results if str(p.get('year')) in selected_years]
        st.session_state.current_filtered_results = temp_filtered_results
    else: st.session_state.current_filtered_results = []
    if is_new_search: st.session_state.current_page = 1
    col_results, col_chat = st.columns([0.6, 0.4])
    with col_results:
        results_to_display = st.session_state.current_filtered_results
        st.subheader(f"搜索结果 (筛选后: {len(results_to_display)} 篇 / 原始: {len(st.session_state.current_search_results)} 篇)")
        if results_to_display:
            with st.container(border=True, height=300):
                stats = get_stats_summary(results_to_display); c1, c2 = st.columns(2)
                c1.metric("筛选后找到", f"{stats['total_found']} 篇")
                if c2.button("📥 保存当前 *筛选后* 的结果到 Markdown", use_container_width=True):
                    with st.spinner("正在保存..."):
                        save_path = save_results_to_markdown_fixed(results_to_display, st.session_state.current_query)
                        st.success(f"结果已保存到: {save_path}")
                st.write("**会议/年份分布 (筛选后):**"); st.dataframe(pd.DataFrame(stats['distribution'].items(), columns=['来源', '论文数']), use_container_width=True, hide_index=True)
            st.divider()
            total_items = len(results_to_display); total_pages = math.ceil(total_items / RESULTS_PER_PAGE)
            if st.session_state.current_page > total_pages: st.session_state.current_page = max(1, total_pages)
            page_display_text = f"第 {st.session_state.current_page} / {total_pages} 页 ({total_items} 条)" if total_pages > 0 else "无结果"
            col_page1, col_page2, col_page3 = st.columns([1, 2, 1])
            with col_page1:
                 if st.button("上一页", disabled=st.session_state.current_page <= 1, use_container_width=True): st.session_state.current_page -= 1; st.rerun()
            with col_page2: st.markdown(f"<div style='text-align: center; margin-top: 8px;'>{page_display_text}</div>", unsafe_allow_html=True)
            with col_page3:
                 if st.button("下一页", disabled=st.session_state.current_page >= total_pages, use_container_width=True): st.session_state.current_page += 1; st.rerun()
            start_idx = (st.session_state.current_page - 1) * RESULTS_PER_PAGE; end_idx = start_idx + RESULTS_PER_PAGE
            paginated_results = results_to_display[start_idx:end_idx]
            for i, paper in enumerate(paginated_results, start=start_idx + 1):
                with st.expander(f"**{i}. {paper.get('title', 'N/A')}**"):
                    if 'similarity' in paper: st.markdown(f"**语义相似度**: `{paper['similarity']:.3f}`")
                    st.markdown(f"**作者**: *{paper.get('authors', 'N/A')}*"); st.markdown(f"**会议/年份**: {paper.get('conference', 'N/A')} {paper.get('year', 'N/A')}")
                    abstract_text = paper.get('abstract', None)
                    if abstract_text is None or abstract_text == '' or abstract_text == 'N/A' or pd.isna(abstract_text):
                        st.markdown(f"**摘要**: <span style='color:orange; font-style: italic;'>[摘要信息缺失或为空]</span>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"**摘要**: \n> {abstract_text}")
                    pdf_url = paper.get('pdf_url', '#');
                    if pdf_url and pdf_url != '#': st.link_button("🔗 打开 PDF 链接", pdf_url)
        elif st.session_state.current_query: st.info("未找到相关结果（或被筛选条件过滤）。")
        else: st.info("请输入查询以开始搜索。")
    with col_chat:
        st.subheader(f"🤖 AI 对话助手"); st.info(f"AI 将基于上文搜索到的 **Top {STREAMLIT_AI_CONTEXT_PAPERS}** 篇论文进行回答。")
        chat_container = st.container(height=500, border=True)
        with chat_container:
            for message in st.session_state.chat_history:
                with st.chat_message(message["role"]): st.markdown(message["content"])
        if not ZHIPUAI_API_KEY: st.error("未配置 ZHIPUAI_API_KEY!"); chat_disabled = True
        elif not st.session_state.current_filtered_results: st.info("请先搜索并确保有结果再对话。"); chat_disabled = True
        else: chat_disabled = False
        if prompt := st.chat_input("基于搜索结果提问...", disabled=chat_disabled, key="chat_input"):
            st.session_state.chat_history.append({"role": "user", "content": prompt}); st.rerun()
        if st.session_state.chat_history and st.session_state.chat_history[-1]["role"] == "user":
            with chat_container:
                for message in st.session_state.chat_history:
                    with st.chat_message(message["role"]): st.markdown(message["content"])
                with st.chat_message("assistant"):
                    with st.spinner("AI 正在思考..."):
                        response = generate_ai_response(st.session_state.chat_history, st.session_state.current_filtered_results[:STREAMLIT_AI_CONTEXT_PAPERS])
                        st.markdown(response)
            st.session_state.chat_history.append({"role": "assistant", "content": response}); st.rerun()
        if st.session_state.chat_history and not chat_disabled:
            if st.button("清除对话历史", use_container_width=True): st.session_state.chat_history = []; st.rerun()

def render_analysis_dashboard_page():
    """
    渲染 "趋势分析仪表盘" 页面 (v1.7 - 改进 CSV 类型识别)
    """
    st.header("📊 趋势分析仪表盘 (核心图表)", divider="rainbow")
    st.info(
        "选择会议、年份和具体的 CSV 分析文件，自动生成核心趋势图表或展示原始数据。"
    )

    analysis_data, all_conferences, _ = find_analysis_files()

    if not analysis_data:
        st.warning("未找到任何分析文件。请先运行 `run_crawler.py`。")
        st.stop()

    # --- 用户选择 ---
    selected_conf = st.selectbox("1. 选择会议", options=sorted(analysis_data.keys()))
    if not selected_conf: st.stop()

    conf_data = analysis_data[selected_conf]
    sorted_years = sorted(conf_data.keys(), key=lambda y: "9999" if y == "Cross-Year" else y, reverse=True)
    selected_year = st.selectbox(f"2. 选择 {selected_conf} 的年份或跨年数据", options=sorted_years)
    if not selected_year: st.stop()

    # 检查所选年份是否存在数据
    if selected_year not in conf_data or not conf_data[selected_year]["csvs"]:
        st.warning(f"未找到 {selected_conf} {selected_year} 的 CSV 数据文件。")
        st.stop()

    files_info = conf_data[selected_year]

    # ---【v1.7】改进 CSV 文件选择 ---
    # 使用更清晰的标签，优先显示 summary_table
    csv_options_sorted = sorted(files_info["csvs"], key=lambda item: 0 if item['type'] == 'summary_table' else (1 if item['type'] == 'trends' else 2))
    csv_options = {f"{item['path'].name} ({item['type']})": item for item in csv_options_sorted}
    selected_csv_label = st.selectbox("3. 选择要分析的 CSV 文件", options=csv_options.keys())
    if not selected_csv_label: st.stop()

    selected_csv_info = csv_options[selected_csv_label]
    csv_path = selected_csv_info["path"]
    csv_type = selected_csv_info["type"]

    st.markdown(f"#### 正在分析: `{csv_path.name}` (识别类型: `{csv_type}`)")

    # --- 加载并处理 CSV ---
    try:
        df = pd.read_csv(csv_path)

        if df.empty:
            st.warning("CSV 文件为空。"); st.stop()

        # --- 【核心 v1.7】根据识别出的 CSV 类型决定展示内容 ---
        st.markdown("---")

        # <<< --- A. 如果识别为分析汇总文件 (summary_table) --- >>>
        if csv_type == "summary_table":
            st.subheader("📈 核心分析图表")
            # ... (图表生成逻辑与 v1.6 相同，但增加了更严格的列检查) ...

            # 图表 1: 主题热度 (按论文数)
            required_cols_heat = ['Topic_Name', 'paper_count']
            if all(col in df.columns for col in required_cols_heat):
                st.markdown(f"##### 1. 主题热度排名 (Top {ANALYSIS_TOP_N} 论文数)")
                # 检查数据类型是否正确
                if pd.api.types.is_numeric_dtype(df['paper_count']) and pd.api.types.is_string_dtype(df['Topic_Name']):
                    df_sorted_count = df.sort_values(by='paper_count', ascending=False).head(ANALYSIS_TOP_N)
                    fig_bar_count = px.bar(df_sorted_count, x='paper_count', y='Topic_Name', orientation='h',
                                     title=f'{selected_conf} {selected_year} - Top {ANALYSIS_TOP_N} 热门主题 (论文数量)',
                                     labels={'paper_count': '论文数量', 'Topic_Name': '主题'},
                                     text_auto=True, height=max(600, len(df_sorted_count)*20))
                    fig_bar_count.update_layout(yaxis={'categoryorder':'total ascending'})
                    st.plotly_chart(fig_bar_count, use_container_width=True)
                else:
                    st.caption(f"无法生成主题热度图：`paper_count` 列必须是数值，`Topic_Name` 列必须是文本。")
            else:
                st.caption(f"无法生成主题热度图：CSV 文件 `{csv_path.name}` 缺少必需的列: {required_cols_heat}")

            # 图表 2: 主题质量 (按平均分)
            required_cols_quality = ['Topic_Name', 'avg_rating']
            if all(col in df.columns for col in required_cols_quality):
                 if pd.api.types.is_numeric_dtype(df['avg_rating']) and df['avg_rating'].notna().any():
                    st.markdown(f"##### 2. 主题质量排名 (Top {ANALYSIS_TOP_N} 平均审稿分)")
                    df_sorted_rating = df.dropna(subset=['avg_rating']).sort_values(by='avg_rating', ascending=False).head(ANALYSIS_TOP_N)
                    if not df_sorted_rating.empty:
                        fig_bar_rating = px.bar(df_sorted_rating, x='avg_rating', y='Topic_Name', orientation='h',
                                         title=f'{selected_conf} {selected_year} - Top {ANALYSIS_TOP_N} 主题 (平均审稿分)',
                                         labels={'avg_rating': '平均审稿分', 'Topic_Name': '主题'},
                                         text_auto='.2f', height=max(600, len(df_sorted_rating)*20))
                        fig_bar_rating.update_layout(yaxis={'categoryorder':'total ascending'})
                        st.plotly_chart(fig_bar_rating, use_container_width=True)
                    else: st.caption("未能生成主题质量图：筛选/排序后数据为空。")
                 elif not df['avg_rating'].notna().any():
                     st.caption("无法生成主题质量图：'avg_rating' 列没有有效数据。")
                 else: # avg_rating 不是数值类型
                     st.caption("无法生成主题质量图：'avg_rating' 列必须是数值类型。")
            else:
                st.caption(f"无法生成主题质量图：CSV 文件 `{csv_path.name}` 缺少必需的列: {required_cols_quality}")

            # 图表 3: 决策构成 (按接收率)
            decision_cols = ['Oral', 'Spotlight', 'Poster', 'Reject', 'N/A']
            present_decision_cols = [col for col in decision_cols if col in df.columns]
            required_cols_decision_base = ['Topic_Name', 'acceptance_rate']
            if present_decision_cols and all(col in df.columns for col in required_cols_decision_base):
                 if pd.api.types.is_numeric_dtype(df['acceptance_rate']):
                    st.markdown(f"##### 3. 主题接收构成 (Top {ANALYSIS_TOP_N} 按接收率排序)")
                    df_sorted_accept = df.dropna(subset=['acceptance_rate']).sort_values(by='acceptance_rate', ascending=False).head(ANALYSIS_TOP_N)
                    if not df_sorted_accept.empty:
                        df_plot = df_sorted_accept.set_index('Topic_Name')[present_decision_cols]
                        df_plot = df_plot.loc[df_plot.sum(axis=1) > 0]
                        if not df_plot.empty:
                            # 确保所有决策列都是数值类型
                            valid_plot = True
                            for col in present_decision_cols:
                                if not pd.api.types.is_numeric_dtype(df_plot[col]):
                                    st.caption(f"无法生成决策构成图：决策列 '{col}' 必须是数值类型。")
                                    valid_plot = False; break
                            if valid_plot:
                                df_plot_normalized = df_plot.apply(lambda x: x / x.sum(), axis=1)
                                fig_stack = px.bar(df_plot_normalized, y=df_plot_normalized.index, x=df_plot_normalized.columns,
                                                   orientation='h', title=f'{selected_conf} {selected_year} - Top {ANALYSIS_TOP_N} 主题决策构成 (按接收率排序)',
                                                   labels={'value': '论文比例', 'variable': '决策类型', 'y': '主题'},
                                                   height=max(600, len(df_plot_normalized)*25), text_auto='.1%')
                                fig_stack.update_layout(yaxis={'categoryorder':'total ascending'}, xaxis_tickformat=".0%", legend_title_text='决策类型')
                                fig_stack.update_traces(hovertemplate='<b>%{y}</b><br>%{variable}: %{x:.1%}<extra></extra>')
                                st.plotly_chart(fig_stack, use_container_width=True)
                        else: st.caption("未能生成决策构成图：筛选掉全零数据后为空。")
                    else: st.caption("未能生成决策构成图：按接受率筛选/排序后数据为空。")
                 else: # acceptance_rate 不是数值
                      st.caption("无法生成决策构成图：'acceptance_rate' 列必须是数值类型。")
            elif not present_decision_cols: st.caption(f"无法生成决策构成图：CSV 文件 `{csv_path.name}` 缺少决策列 (如 Oral, Poster 等)。")
            else: st.caption(f"无法生成决策构成图：CSV 文件 `{csv_path.name}` 缺少 'Topic_Name' 或 'acceptance_rate' 列。")

        # <<< --- B. 如果识别为跨年趋势文件 (trends) --- >>>
        elif csv_type == "trends":
            st.subheader("📈 跨年份趋势图")
            # ... (趋势图生成逻辑与 v1.6 相同) ...
            try:
                if 'year' in df.columns: df_indexed = df.set_index('year')
                elif df.index.name != 'year':
                     potential_year_col = df.columns[0]
                     if pd.api.types.is_numeric_dtype(df[potential_year_col]):
                          df_indexed = df.set_index(potential_year_col)
                          df_indexed.index.name = 'year'
                     else: raise ValueError("无法自动识别年份列/索引")
                else: df_indexed = df # 已经是年份索引

                if df_indexed.index.name == 'year' and len(df_indexed.columns) > 0:
                    numeric_topic_cols = get_numeric_columns(df_indexed)
                    if numeric_topic_cols:
                        top_topics = df_indexed[numeric_topic_cols].sum().nlargest(15).index
                        df_top = df_indexed[top_topics]
                        fig_line = px.line(df_top, x=df_top.index, y=df_top.columns, markers=True,
                                           title=f'{selected_conf} - Top 15 主题历年论文数趋势',
                                           labels={'year': '年份', 'value': '论文数量', 'variable': '主题'})
                        fig_line.update_layout(xaxis_type='category')
                        st.plotly_chart(fig_line, use_container_width=True)
                    else:
                         st.warning("趋势文件中没有找到数值类型的主题列用于绘图。")
                else:
                    st.warning(f"无法为 `{csv_path.name}` 生成趋势折线图。请确保 CSV 格式正确。")
            except Exception as trend_e:
                st.error(f"生成跨年趋势图时出错: {trend_e}")
                st.error(traceback.format_exc())


        # <<< --- C. 如果识别为原始数据文件 (raw_data) 或其他 --- >>>
        else: # 包括 'raw_data', 'analysis_other', 'unknown'
            st.subheader("📄 数据预览")
            st.info(f"检测到文件类型为 **{csv_type}**。此类文件通常不包含用于生成标准分析图表的聚合数据，因此仅提供数据表格预览。")
            st.dataframe(df, height=500, use_container_width=True)


        # --- 显示/下载原始数据表格 (适用于所有类型) ---
        st.markdown("---")
        with st.expander("查看/下载当前 CSV 数据表格"):
            st.dataframe(df, height=300, use_container_width=True)
            st.download_button(
                label=f"📥 下载数据 {csv_path.name}",
                data=df.to_csv(index=False).encode('utf-8-sig'),
                file_name=csv_path.name,
                mime='text/csv',
                key=f"download_{csv_path.stem}" # 添加唯一 key
            )

    except pd.errors.EmptyDataError:
        st.warning(f"文件 {csv_path.name} 为空，跳过。")
    except Exception as e:
        st.error(f"处理 CSV 文件 {csv_path.name} 时失败: {e}")
        st.error(traceback.format_exc()) # 显示详细错误信息

# -----------------------------------------------------------------
# 7. 主应用逻辑：侧边栏导航 (保持不变)
# -----------------------------------------------------------------
st.sidebar.title("PubCrawler Pro 🚀"); st.sidebar.caption("v1.7 - Robust CSV Handling")
page = st.sidebar.radio("选择功能页面", ["🤖 AI 助手 & 搜索", "📊 趋势分析仪表盘"], key="page_selection")
st.sidebar.divider()
analysis_data_sidebar, conf_list_sidebar, _ = find_analysis_files()
if conf_list_sidebar:
    with st.sidebar.expander("目前已索引的会议", expanded=True):
        st.dataframe(conf_list_sidebar, use_container_width=True, hide_index=True, column_config={"value": "会议名称"})
if page == "🤖 AI 助手 & 搜索": render_search_and_chat_page()
elif page == "📊 趋势分析仪表盘": render_analysis_dashboard_page()

