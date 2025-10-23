# FILE: src/search/search_local.py (v4.3 - .env & sem: disabled)

import sqlite3
import numpy as np
import requests
import time
from sklearn.metrics.pairwise import cosine_similarity
from pathlib import Path
import textwrap
from datetime import datetime
import re
import sys
import math
import os
from dotenv import load_dotenv

# --- 配置 ---
PROJECT_ROOT = Path(__file__).parent.parent.parent
DB_PATH = PROJECT_ROOT / "papers.db"
SEARCH_RESULTS_DIR = PROJECT_ROOT / "search_results"
SEARCH_RESULTS_DIR.mkdir(exist_ok=True)
PAPERS_PER_FILE = 100
RESULTS_PER_PAGE = 10

# --- 【核心修改】修正了 API_URL (v4.3) ---
# 移除了无效的 /pipeline/feature-extraction/ 路径
# 即使暂时禁用, 也保持 URL 正确, 以便未来启用
API_URL = "https://api-inference.huggingface.co/models/sentence-transformers/all-MiniLM-L6-v2"

# --- 从 .env 文件加载环境变量 ---
load_dotenv(dotenv_path=PROJECT_ROOT / '.env')
HF_API_TOKEN = os.getenv("HF_API_TOKEN")
HEADERS = {"Authorization": f"Bearer {HF_API_TOKEN}"}


# --- 颜色代码 (与之前版本相同) ---
class Colors:
    HEADER = '\033[95m';
    OKBLUE = '\033[94m';
    OKCYAN = '\033[96m';
    OKGREEN = '\033[92m'
    WARNING = '\033[93m';
    FAIL = '\033[91m';
    ENDC = '\033[0m';
    BOLD = '\033[1m';
    UNDERLINE = '\033[4m'


# --- 辅助函数 ---
def print_colored(text, color):
    if sys.stdout.isatty():
        print(f"{color}{text}{Colors.ENDC}")
    else:
        print(text)


def print_banner():
    # --- 【修改】更新了 Banner 版本号 ---
    banner_text = ["╔══════════════════════════════════════════════════════════════╗",
                   "║    ____              __            ____                       ║",
                   "║   / __ \\____  / /______/ __ \\__  ______  ____ _____ ___    ║",
                   "║  / /_/ / __ \\/ / ___/ / / / / / / / __ \\/ __ `/ __ `__ \\   ║",
                   "║ / ____/ /_/ / / /__/ / /_/ / /_/ / / / / /_/ / / / / / /   ║",
                   "║/_/    \\____/_/\\___/_/\\___\\_\\__,_/_/ /_/\\__,_/_/ /_/ /_/    ║",
                   "║                                                          ║",
                   "║          Your Local Paper Search Engine v4.3 (.env)        ║",
                   "╚══════════════════════════════════════════════════════════════╝"]
    for line in banner_text: print_colored(line, Colors.HEADER)
    print()


def parse_advanced_query(query: str):
    # FTS5 支持 AND 和 NOT (但 + 和 - 更方便)
    query = query.replace(' +', ' AND ').replace(' -', ' NOT ')

    # 将用户友好的 author: 映射到数据库字段 authors:
    # FTS5 会自动处理 'authors:hinton' 这样的语法
    # --- 【修改】增加了 re.IGNORECASE ---
    query = re.sub(r'author:(\S+)', r'authors:\1', query, flags=re.IGNORECASE)
    query = re.sub(r'title:(\S+)', r'title:\1', query, flags=re.IGNORECASE)
    return query


def keyword_search_db(conn, raw_query):
    advanced_query = parse_advanced_query(raw_query)
    print(f"[*] 正在执行关键词搜索: '{advanced_query}'...")
    start_t = time.time()
    try:
        cursor = conn.execute(
            "SELECT title, authors, abstract, conference, year, pdf_url, source_file FROM papers_fts WHERE papers_fts MATCH ? ORDER BY rank",
            (advanced_query,))
        results = cursor.fetchall()
        end_t = time.time()
        count = len(results)
        print(f"[✔] 耗时 {end_t - start_t:.4f} 秒，找到 {Colors.BOLD}{Colors.OKGREEN}{count}{Colors.ENDC} 个结果。")
        return results
    except sqlite3.OperationalError as e:
        # --- 【修改】增加了更详细的错误提示 ---
        print_colored(f"[!] 搜索语法错误: {e}", Colors.FAIL)
        print_colored("    提示: 确保 AND/NOT/OR 逻辑正确，或字段名(title:/author:)后有内容。", Colors.WARNING)
        return []


def get_embedding_from_api(text: str):
    """(此函数在 v4.3 中未被 main() 调用)"""
    payload = {"inputs": text, "options": {"wait_for_model": True}}
    try:
        response = requests.post(API_URL, headers=HEADERS, json=payload, timeout=20)

        # --- 【修改】增加了更明确的错误处理 ---
        if response.status_code == 401:
            print_colored("\n[!] API 错误: 401 - Token 无效。请检查 .env 文件中的 HF_API_TOKEN。", Colors.FAIL)
            return None
        if response.status_code == 404:
            print_colored(f"\n[!] API 错误: 404 - 未找到模型。请检查 API_URL: {API_URL}", Colors.FAIL)
            return None

        response.raise_for_status()  # 捕获 429 (限速), 5xx (服务器错误) 等

        result = response.json()
        if isinstance(result, list) and isinstance(result[0], list):
            return np.array(result[0], dtype=np.float32)

    except requests.exceptions.RequestException as e:
        print_colored(f"\n[!] API 请求失败: {e}", Colors.FAIL)
        return None
    except Exception as e:
        print_colored(f"\n[!] API 响应处理失败: {e}", Colors.FAIL)
        return None
    return None


def semantic_search_db(conn, query, top_k=50):
    """(此函数在 v4.3 中未被 main() 调用)"""
    print(f"[*] 正在执行语义搜索: '{query}'...")
    start_t = time.time()

    query_embedding = get_embedding_from_api(query)
    if query_embedding is None:
        print_colored("[!] 错误: 从 API 获取查询向量失败。请检查您的 Token 和网络连接。", Colors.FAIL)
        return []

    cursor = conn.cursor()
    cursor.execute("SELECT paper_id, embedding FROM embeddings")
    all_embeddings_data = cursor.fetchall()
    if not all_embeddings_data:
        # --- 【修改】增加了对 embedding 表为空的检查 ---
        print_colored("[!] 错误: 数据库中没有找到语义向量。", Colors.FAIL)
        print_colored("    请先运行 embedder.py 生成向量。", Colors.WARNING)
        return []

    paper_ids = [row[0] for row in all_embeddings_data]
    db_embeddings = np.array([np.frombuffer(row[1], dtype=np.float32) for row in all_embeddings_data])

    similarities = cosine_similarity(query_embedding.reshape(1, -1), db_embeddings)[0]
    top_k_indices = np.argsort(similarities)[-top_k:][::-1]
    top_paper_ids = [paper_ids[i] for i in top_k_indices]
    top_scores = [similarities[i] for i in top_k_indices]

    placeholders = ','.join('?' for _ in top_paper_ids)
    sql = f"SELECT rowid, title, authors, abstract, conference, year, pdf_url, source_file FROM papers_fts WHERE rowid IN ({placeholders})"

    # FTS rowid 映射到 (title, authors, ...)
    raw_results_dict = {row[0]: row[1:] for row in cursor.execute(sql, top_paper_ids).fetchall()}

    final_results = []
    # 按相似度顺序重新组合结果
    for i, paper_id in enumerate(top_paper_ids):
        details = raw_results_dict.get(paper_id)
        if details:
            # (title, authors, abstract, conf, year, pdf, src)
            # 在标题前加入相似度得分
            scored_title = f"(相似度: {top_scores[i]:.2f}) {details[0]}"
            final_results.append((scored_title,) + details[1:])

    end_t = time.time()
    print(f"[✔] 耗时 {end_t - start_t:.4f} 秒，找到 {len(final_results)} 个语义相关结果。")
    return final_results


def interactive_pagination(results, query):
    num_results = len(results)
    if num_results == 0: return "quit"
    total_pages = math.ceil(num_results / RESULTS_PER_PAGE)
    current_page = 1
    while True:
        start_idx = (current_page - 1) * RESULTS_PER_PAGE
        end_idx = start_idx + RESULTS_PER_PAGE
        page_results = results[start_idx:end_idx]
        print_colored(f"\n--- 结果预览 (第 {current_page}/{total_pages} 页) ---", Colors.HEADER)
        for i, row in enumerate(page_results, start=start_idx + 1):
            print(f"\n{Colors.BOLD}[{i}]{Colors.ENDC} {row[0]}")
            print(f"  {Colors.OKCYAN}{row[3]} {row[4]}{Colors.ENDC} | 作者: {textwrap.shorten(row[1], 80)}")
            if row[5]: print(f"  PDF: {row[5]}")

        if current_page >= total_pages:
            print("\n--- 已是最后一页 ---")
            return "end_of_list"
        try:
            choice = input(
                f"\n按 {Colors.BOLD}[Enter]{Colors.ENDC} 下一页, '{Colors.BOLD}s{Colors.ENDC}' 保存, '{Colors.BOLD}q{Colors.ENDC}' 退出: ").lower()
            if choice == 'q':
                return "quit"
            elif choice == 's':
                return "save"
            current_page += 1
        except KeyboardInterrupt:
            break
    return "quit"


def save_results_to_files(results, query, session_dir):
    safe_query = re.sub(r'[\\/*?:"<>|]', "", query).replace(" ", "_")
    num_results = len(results)
    num_files = (num_results + PAPERS_PER_FILE - 1) // PAPERS_PER_FILE
    saved_files = []
    for i in range(num_files):
        start_index = i * PAPERS_PER_FILE
        chunk = results[start_index: start_index + PAPERS_PER_FILE]
        filename = session_dir / f"search_{safe_query[:50]}{'_part_' + str(i + 1) if num_files > 1 else ''}.md"
        saved_files.append(filename)
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"# 搜索: \"{query}\"\n\n**找到 {num_results} 结果 (部分 {i + 1}/{num_files})**\n\n---\n\n")
            for idx, row in enumerate(chunk, start=start_index + 1):
                title, authors, abstract, conf, year, pdf, src = row
                f.write(f"### {idx}. {title}\n\n- **作者**: {authors}\n- **会议**: {conf} {year}\n")
                if pdf and str(pdf).strip(): f.write(f"- **PDF**: [{pdf}]({pdf})\n")
                f.write(f"\n**摘要:**\n> {abstract}\n\n*来源: `{src}`*\n\n---\n\n")
    return saved_files


def main():
    if not HF_API_TOKEN:
        print_colored("错误: 未能从 .env 文件中加载 HF_API_TOKEN。", Colors.FAIL)
        print_colored("请确保在项目根目录创建了 .env 文件，并写入 HF_API_TOKEN=\"hf_...\"", Colors.FAIL)
        return
    if not DB_PATH.exists():
        print_colored(f"\n[!] 数据库不存在: {DB_PATH}", Colors.FAIL)
        return

    # 以只读模式连接
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    session_dir = SEARCH_RESULTS_DIR / f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    session_dir.mkdir(exist_ok=True)

    print_banner()
    print(f"[*] 索引已加载: {Colors.OKCYAN}{DB_PATH.resolve()}{Colors.ENDC}")
    print_colored(f"[*] 结果将保存至: {session_dir.resolve()}", Colors.UNDERLINE)

    # --- 【修改】扩充了搜索语法示例 ---
    print_colored("\n--- 关键词搜索语法 (FTS5) ---", Colors.OKBLUE)
    print("  - `transformer`                 (包含 transformer)")
    print("  - `\"large language model\"`      (包含短语)")
    print("  - `author:hinton`               (作者字段包含 hinton)")
    print("  - `title:attention`             (标题字段包含 attention)")
    print("  - `author:hinton + title:rnn`   (作者 hinton 且 标题 rnn)")
    print("  - `transformer - author:vaswani` (包含 transformer 但排除作者 vaswani)")
    print("  - `(author:lecun OR author:bengio) + cnn` (复杂逻辑)")
    print_colored("\n  - `sem:...` (语义搜索功能暂时禁用)\n", Colors.WARNING)

    while True:
        try:
            q = input(f"🔍 {Colors.BOLD}请输入关键词{Colors.ENDC} (或 'exit' 退出): ").strip()
            if not q: continue
            if q.lower() == 'exit': break

            results = []

            # --- 【修改】禁用了语义搜索 ---
            if q.lower().startswith('sem:'):
                print_colored("\n[!] 语义搜索 (sem:) 功能暂时禁用。", Colors.WARNING)
                print_colored("    请使用上方的关键词搜索语法 (如: title:..., author:..., +, -)。\n", Colors.WARNING)
                continue  # 跳过本次循环，等待新输入
            else:
                results = keyword_search_db(conn, q)

            if not results: continue

            pagination_result = interactive_pagination(results, q)

            if pagination_result in ["save", "end_of_list"]:
                if input(f"\n保存这 {len(results)} 条结果? (y/n, 默认y): ").lower() != 'n':
                    files = save_results_to_files(results, q, session_dir)
                    print_colored("\n[✔] 结果已保存!", Colors.OKGREEN)
                    for f in files: print_colored(f"      -> {f.resolve()}", Colors.UNDERLINE)

            print()  # 在两次搜索之间添加一个空行

        except KeyboardInterrupt:
            break
        except Exception as e:
            print_colored(f"发生未知错误: {e}", Colors.FAIL)

    conn.close()
    print("\n再见！")


if __name__ == "__main__":
    main()