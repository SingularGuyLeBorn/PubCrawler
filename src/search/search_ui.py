# FILE: src/search/search_ai_assistant.py (v7.3 - AI Module Separated)

import sqlite3
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from pathlib import Path
import textwrap
import time
import sys
import re
import torch
import math
from datetime import datetime
from collections import Counter
import os
from dotenv import load_dotenv

# --- 【核心修改】: 导入新的AI服务模块 ---
from src.ai.glm_chat_service import start_ai_chat_session, print_colored, Colors

# ------------------------------------

# --- 配置 (大部分不变，但不再需要AI_CONTEXT_PAPERS和ZHIPUAI_API_KEY的全局导入) ---
PROJECT_ROOT = Path(__file__).parent.parent.parent
DB_DIR = PROJECT_ROOT / "database"
SEARCH_RESULTS_DIR = PROJECT_ROOT / "search_results"
DB_PATH = DB_DIR / "papers.db"
CHROMA_DB_PATH = str(DB_DIR / "chroma_db")
MODEL_NAME = 'sentence-transformers/all-MiniLM-L6-v2'
COLLECTION_NAME = "papers"
RESULTS_PER_PAGE = 10


# --- 【删除】: 不再需要在此文件中加载ZHIPUAI_API_KEY ---
# ZHIPUAI_API_KEY = os.getenv("ZHIPUAI_API_KEY")
# --------------------------------------------------------------------------

# --- 颜色和打印函数 (这里只需保留print_banner，print_colored和Colors从ai_chat_service导入) ---
# class Colors: ... (这部分可以直接删除，因为它现在是从ai_chat_service导入的)
# def print_colored(text, color): ... (这部分可以直接删除)

def print_banner():
    banner_text = "--- PubCrawler v7.3: AI Research Assistant (Module Refactored) ---"
    print_colored(banner_text, Colors.HEADER)
    SEARCH_RESULTS_DIR.mkdir(exist_ok=True)
    print_colored(f"[*] 结果将保存至: {SEARCH_RESULTS_DIR.resolve()}", Colors.UNDERLINE)


# --- 文件保存、统计、分页模块 (无变化，但注意print_colored现在是导入的) ---
def save_results_to_markdown(results, query, session_dir):
    if not results: return []
    safe_query = re.sub(r'[\\/*?:"<>|]', "", query).replace(" ", "_")[:50]
    filename = session_dir / f"search_{safe_query}.md"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(f"# 搜索查询: \"{query}\"\n\n**共找到 {len(results)} 条相关结果**\n\n---\n\n")
        for idx, paper in enumerate(results, 1):
            title, authors, abstract = paper.get('title', 'N/A'), paper.get('authors', 'N/A'), paper.get('abstract',
                                                                                                         'N/A')
            conf, year = paper.get('conference', 'N/A'), paper.get('year', 'N/A')
            similarity_str = f"- **语义相似度**: {paper['similarity']:.2f}\n" if 'similarity' in paper else ""
            f.write(
                f"### {idx}. {title}\n\n- **作者**: {authors}\n- **会议/年份**: {conf} {year}\n{similarity_str}\n**摘要:**\n> {abstract}\n\n---\n\n")
    print_colored(f"\n[✔] 结果已成功保存到 Markdown 文件!", Colors.OKGREEN)
    print_colored(f"      -> {filename.resolve()}", Colors.UNDERLINE)


def print_stats_summary(results):
    if not results: return
    total_found = len(results)
    print_colored("\n--- 查询结果统计 ---", Colors.HEADER)
    print(f"总计找到 {Colors.BOLD}{total_found}{Colors.ENDC} 篇相关论文。")
    conf_year_counter = Counter([(p.get('conference', 'N/A'), p.get('year', 'N/A')) for p in results])
    if conf_year_counter:
        print("分布情况:")
        for (conf, year), count in conf_year_counter.most_common():
            print(f"  - {conf} {year}: {count} 篇")
    print_colored("--------------------", Colors.HEADER)


def interactive_pagination(results, query, session_dir):
    num_results = len(results)
    if num_results == 0: return
    print_stats_summary(results)
    total_pages, current_page = math.ceil(num_results / RESULTS_PER_PAGE), 1
    while True:
        start_idx, end_idx = (current_page - 1) * RESULTS_PER_PAGE, current_page * RESULTS_PER_PAGE
        page_results = results[start_idx:end_idx]
        print_colored(f"\n--- 结果预览 (第 {current_page}/{total_pages} 页) ---", Colors.HEADER)
        for i, paper in enumerate(page_results, start=start_idx + 1):
            title, authors, conf, year = paper.get('title', 'N/A'), paper.get('authors', 'N/A'), paper.get('conference',
                                                                                                           'N/A'), paper.get(
                'year', 'N/A')
            display_line = f"  {Colors.OKCYAN}{conf} {year}{Colors.ENDC} | 作者: {textwrap.shorten(authors, 70)}"
            if 'similarity' in paper: display_line = f"  {Colors.OKGREEN}相似度: {paper['similarity']:.2f}{Colors.ENDC} |" + display_line
            print(f"\n{Colors.BOLD}[{i}]{Colors.ENDC} {title}\n{display_line}")
        if current_page >= total_pages: print("\n--- 已是最后一页 ---"); break
        try:
            choice = input(
                f"\n按 {Colors.BOLD}[Enter]{Colors.ENDC} 下一页, '{Colors.BOLD}s{Colors.ENDC}' 保存, '{Colors.BOLD}ai{Colors.ENDC}' 对结果提问, '{Colors.BOLD}q{Colors.ENDC}' 返回: ").lower()
            if choice == 'q': return
            if choice == 's': break
            if choice == 'ai':
                start_ai_chat_session(results)  # <-- 调用新的AI服务函数
                print_colored("\n[i] AI对话结束，返回结果列表。", Colors.OKBLUE)
                continue
            current_page += 1
        except KeyboardInterrupt:
            return
    if input(f"\n是否将这 {num_results} 条结果全部保存到 Markdown? (y/n, 默认y): ").lower() != 'n':
        save_results_to_markdown(results, query, session_dir)


# --- 搜索核心 (无变化) ---
def keyword_search(conn, raw_query):
    COLUMN_MAP = {'author': 'authors', 'title': 'title', 'abstract': 'abstract'}
    parsed_query_parts = []
    pattern = re.compile(r'(\b\w+):(?:"([^"]*)"|(\S+))')
    remaining_query = raw_query
    for match in list(pattern.finditer(raw_query)):
        full_match_text = match.group(0)
        field_alias = match.group(1).lower()
        value = match.group(2) if match.group(2) is not None else match.group(3)
        if field_alias in COLUMN_MAP:
            db_column = COLUMN_MAP[field_alias]
            safe_value = value.replace('"', '""')
            if ' ' in value or not value.isalnum():
                parsed_query_parts.append(f'{db_column}:"{safe_value}"')
            else:
                parsed_query_parts.append(f'{db_column}:{safe_value}')
            remaining_query = re.sub(re.escape(full_match_text), '', remaining_query, 1)
    general_terms = re.findall(r'"[^"]*"|\S+', remaining_query.strip())
    for term in general_terms:
        safe_term = term.replace('"', '""')
        if term.startswith('"') and term.endswith('"'):
            parsed_query_parts.append(f'{safe_term}')
        else:
            parsed_query_parts.append(safe_term)
    final_fts_query = ' AND '.join(filter(None, parsed_query_parts))
    if not final_fts_query:
        print_colored("[!] 关键词搜索查询为空或解析失败，无法执行。", Colors.WARNING);
        return []
    print(f"[*] 正在执行关键词搜索 (FTS5 Query: '{final_fts_query}')...")
    try:
        cursor = conn.execute(
            "SELECT title, authors, abstract, conference, year FROM papers_fts WHERE papers_fts MATCH ? ORDER BY rank",
            (final_fts_query,))
        results = [{"title": r[0], "authors": r[1], "abstract": r[2], "conference": r[3], "year": r[4]} for r in
                   cursor.fetchall()]
        return results
    except sqlite3.OperationalError as e:
        print_colored(f"[!] 关键词搜索失败: {e}", Colors.FAIL)
        print_colored(f"    原始查询: '{raw_query}'", Colors.WARNING)
        print_colored(f"    生成的FTS5查询: '{final_fts_query}'", Colors.WARNING)
        print_colored("    提示: FTS5查询语法严格，请检查 'AND/OR/NOT', 短语引号或字段名是否有误。", Colors.WARNING);
        return []


def semantic_search(conn, collection, model, query, top_n=20):
    print(f"[*] 正在执行语义搜索: '{query}'...")
    start_t = time.time()
    query_embedding = model.encode(query, convert_to_tensor=False)
    chroma_results = collection.query(query_embeddings=[query_embedding.tolist()], n_results=top_n)
    ids_found, distances = chroma_results['ids'][0], chroma_results['distances'][0]
    if not ids_found: return []
    placeholders = ','.join('?' for _ in ids_found)
    sql_query = f"SELECT rowid, title, authors, abstract, conference, year FROM papers_fts WHERE rowid IN ({placeholders})"
    cursor = conn.cursor()
    raw_sqlite_results = {str(r[0]): r[1:] for r in cursor.execute(sql_query, ids_found).fetchall()}
    final_results = []
    for i, paper_id in enumerate(ids_found):
        details = raw_sqlite_results.get(paper_id)
        if details:
            final_results.append(
                {"title": details[0], "authors": details[1], "abstract": details[2], "conference": details[3],
                 "year": details[4], "similarity": 1 - distances[i]})
    end_t = time.time()
    print(f"[✔] 耗时 {end_t - start_t:.4f} 秒，找到并组合了 {len(final_results)} 个结果。")
    return final_results


# --- 主程序 (需要进行一些调整，因为print_colored和Colors现在从外部导入) ---
def main():
    # 之前这里是检查ZHIPUAI_API_KEY，现在由ai_chat_service.py内部检查

    try:
        conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        model = SentenceTransformer(MODEL_NAME, device=device)
        client = chromadb.PersistentClient(path=CHROMA_DB_PATH, settings=Settings(anonymized_telemetry=False))
        collection = client.get_collection(name=COLLECTION_NAME)
    except Exception as e:
        print_colored(f"\n[!] 无法初始化模块: {e}", Colors.FAIL); return

    session_dir = SEARCH_RESULTS_DIR / f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    session_dir.mkdir(exist_ok=True)

    print_banner()
    print_colored("\n--- 搜索语法 (AI已集成 & FTS5已修正) ---", Colors.OKBLUE)
    print("  - `transformer author:vaswani`   (关键词 + 作者字段搜索)")
    print("  - `title:\"vision transformer\"`     (精确标题搜索)")
    print("  - `\"large language model\" AND efficient` (短语和关键词组合)")
    print(f"  - `{Colors.BOLD}sem:{Colors.ENDC} efficiency of few-shot learning` (语义搜索！)")

    # last_results 不再需要在此处存储，因为 ai_chat_session 直接接收结果

    while True:
        try:
            q = input(f"\n🔍 {Colors.BOLD}请输入查询{Colors.ENDC} (或 'exit' 退出): ").strip()
            if not q: continue
            if q.lower() == 'exit': break

            results = []
            if q.lower().startswith('sem:'):
                semantic_query = q[4:].strip()
                if semantic_query: results = semantic_search(conn, collection, model, semantic_query)
            else:
                results = keyword_search(conn, q)

            # last_results = results # 不再需要赋值给 last_results
            interactive_pagination(results, q, session_dir)

        except KeyboardInterrupt:
            break
        except Exception as e:
            print_colored(f"发生未知错误: {e}", Colors.FAIL)

    conn.close()
    print("\n再见！")


if __name__ == "__main__":
    main()