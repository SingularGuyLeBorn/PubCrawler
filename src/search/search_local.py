# FILE: src/search/search_local.py

import pandas as pd
from pathlib import Path
import time
import textwrap
from datetime import datetime
import re
import os

# --- 配置 ---
PROJECT_ROOT = Path(__file__).parent.parent.parent
METADATA_DIR = PROJECT_ROOT / "output" / "metadata"
SEARCH_RESULTS_DIR = PROJECT_ROOT / "search_results"
# 内存优化：只加载我们搜索和显示所必需的列
REQUIRED_COLUMNS = ['title', 'authors', 'abstract', 'pdf_url', 'conference', 'year', 'source_file']
# 文件分割：每个 Markdown 文件最多存放的论文数量
PAPERS_PER_FILE = 100


def highlight_query(text, query):
    """在文本中高亮显示查询关键词 (Markdown格式)。"""
    if not isinstance(text, str) or not query:
        return text
    # 使用 re.IGNORECASE 进行不区分大小写的替换
    # 使用 `**{match.group(0)}**` 来加粗匹配到的文本
    try:
        highlighted_text = re.sub(f'({re.escape(query)})', r'**\1**', text, flags=re.IGNORECASE)
        return highlighted_text
    except re.error:
        return text  # 如果查询是无效的正则表达式，则返回原文


def load_all_papers_from_csv(directory: Path) -> pd.DataFrame:
    """
    内存优化版的加载函数：只读取必需的列。
    """
    print(f"[*] 正在从 {directory} 加载所有论文数据...")
    if not directory.exists():
        print(f"[!] 错误: 目录不存在: {directory}")
        return None

    csv_files = list(directory.rglob("*_data_*.csv"))
    if not csv_files:
        print(f"[!] 警告: 在目录 {directory} 下没有找到任何 '_data_*.csv' 文件。")
        return None

    print(f"[*] 发现 {len(csv_files)} 个 CSV 文件，开始加载 (内存优化模式)...")
    df_list = []
    total_papers = 0

    for f in csv_files:
        try:
            # 检查文件头以确定可用列
            header = pd.read_csv(f, nrows=0).columns.tolist()
            cols_to_use = [col for col in REQUIRED_COLUMNS if col in header]

            df = pd.read_csv(f, usecols=cols_to_use, dtype=str).fillna('')  # 读取为字符串并填充NA

            if not df.empty:
                # 补全都需要的列，即使CSV中没有
                for col in REQUIRED_COLUMNS:
                    if col not in df.columns:
                        df[col] = ''
                if 'source_file' not in cols_to_use:
                    df['source_file'] = f.name
                df_list.append(df)
                total_papers += len(df)

        except Exception as e:
            print(f"[!] 警告: 加载或处理文件 {f.name} 时出错，已跳过。错误: {e}")

    if not df_list:
        print("\n[✖] 未能加载任何有效的论文数据。")
        return None

    print(f"[✔] 加载完成！共找到 {total_papers} 篇论文记录。")
    return pd.concat(df_list, ignore_index=True)


def save_results_to_files(results_df: pd.DataFrame, query: str, session_dir: Path):
    """
    将搜索结果保存到一个或多个 Markdown 文件中，每个文件最多 PAPERS_PER_FILE 篇。
    """
    safe_query = re.sub(r'[\\/*?:"<>|]', "", query).replace(" ", "_")
    num_results = len(results_df)

    # 计算需要分割成多少个文件
    num_files = (num_results + PAPERS_PER_FILE - 1) // PAPERS_PER_FILE

    saved_files = []

    for i in range(num_files):
        start_index = i * PAPERS_PER_FILE
        end_index = start_index + PAPERS_PER_FILE
        chunk_df = results_df.iloc[start_index:end_index]

        part_num_str = f"_part_{i + 1}" if num_files > 1 else ""
        filename = session_dir / f"search_{safe_query[:30]}{part_num_str}.md"
        saved_files.append(filename)

        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"# 搜索结果: \"{query}\"\n\n")
            f.write(f"**总计找到 {num_results} 个匹配项。** (此文件为第 {i + 1}/{num_files} 部分)\n\n")
            f.write("---\n\n")

            for index, row in chunk_df.iterrows():
                # 使用 highlight_query 高亮标题和摘要
                title = highlight_query(row.get('title', 'N/A'), query)
                abstract = highlight_query(row.get('abstract', '无摘要'), query)

                f.write(f"### {start_index + index + 1}. {title}\n\n")
                f.write(f"- **作者**: {row.get('authors', 'N/A')}\n")
                f.write(f"- **会议/期刊**: {row.get('conference', 'N/A')} {row.get('year', '')}\n")

                pdf_url = row.get('pdf_url')
                if pdf_url:
                    f.write(f"- **PDF链接**: [{pdf_url}]({pdf_url})\n")

                f.write("\n**摘要:**\n")
                f.write(f"> {abstract}\n\n")
                f.write(f"*来源文件: `{row.get('source_file', 'N/A')}`*\n\n")
                f.write("---\n\n")

    return saved_files


def search_papers(df: pd.DataFrame, query: str, session_dir: Path):
    """
    执行搜索、高亮、分页保存和预览。
    """
    print(f"\n[*] 正在搜索关键词: '{query}'...")
    start_time = time.time()

    # 在搜索前确保列是字符串类型，避免.str属性错误
    df['title'] = df['title'].astype(str)
    df['abstract'] = df['abstract'].astype(str)

    results_mask = df['title'].str.contains(query, case=False, na=False) | \
                   df['abstract'].str.contains(query, case=False, na=False)
    results_df = df[results_mask].reset_index(drop=True)

    end_time = time.time()
    num_results = len(results_df)

    print(f"[✔] 搜索完成，耗时 {end_time - start_time:.4f} 秒。共找到 {num_results} 个匹配项。")

    if num_results == 0:
        return

    try:
        saved_files = save_results_to_files(results_df, query, session_dir)
        if len(saved_files) == 1:
            print(f"[✔] 详细结果已保存至文件: {saved_files[0]}")
        else:
            print(f"[✔] 详细结果已分割并保存至 {len(saved_files)} 个文件中 (位于 {session_dir})")
    except Exception as e:
        print(f"[!] 错误: 保存结果文件失败: {e}")

    preview_count = min(3, num_results)
    print(f"\n--- 结果预览 (前 {preview_count} 条，关键词已用'**'高亮) ---")

    for index, row in results_df.head(preview_count).iterrows():
        print(f"\n[{index + 1}] {highlight_query(row['title'], query)}")
        print(f"  - 会议/期刊: {row.get('conference', 'N/A')} {row.get('year', '')}")
        abstract_preview = textwrap.shorten(row.get('abstract', ''), width=200, placeholder="...")
        print(f"  - 摘要预览: {highlight_query(abstract_preview, query)}")
        print("-" * 20)

    if num_results > preview_count:
        print(f"\n[...] 更多结果请查看已保存的文件。")


def main():
    """主函数，包含会话管理。"""
    paper_database = load_all_papers_from_csv(METADATA_DIR)
    if paper_database is None:
        return

    # --- 会话管理 ---
    session_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_dir = SEARCH_RESULTS_DIR / f"session_{session_timestamp}"
    session_dir.mkdir(exist_ok=True)

    print("\n" + "=" * 50)
    print("      欢迎使用 PubCrawler 本地论文搜索引擎 v2.0")
    print("=" * 50)
    print(f"[*] 本次会话的所有搜索结果将保存在: \n    {session_dir}")

    while True:
        try:
            user_query = input("\n请输入搜索关键词 (或输入 'exit' 退出): ").strip()
            if user_query.lower() == 'exit':
                break
            if not user_query:
                continue

            search_papers(paper_database, user_query, session_dir)

        except KeyboardInterrupt:
            print("\n[👋] 收到退出信号，再见！")
            break


if __name__ == "__main__":
    main()