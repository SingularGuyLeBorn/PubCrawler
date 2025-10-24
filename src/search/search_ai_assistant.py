# FILE: src/search/search_ai_assistant.py (CLI Launcher - v1.1)

import sys
import math
import textwrap
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

# --- 从 search_service 导入所有功能和配置 ---
from src.search.search_service import (
    initialize_components,
    keyword_search,
    semantic_search,
    get_stats_summary,
    save_results_to_markdown,
    _sqlite_conn,
    PROJECT_ROOT,
    SEARCH_RESULTS_DIR,
    RESULTS_PER_PAGE,
    Colors, # 导入Colors
    _initialized
)
# --- 导入CLI专属的AI对话交互函数 ---
from src.ai.glm_chat_service import start_ai_chat_session

# --- 定义CLI专属的 print_colored 函数 ---
# 确保在CLI交互中能够正确打印彩色文本
def print_colored(text, color, end='\n'):
    if sys.stdout.isatty():
        print(f"{color}{text}{Colors.ENDC}", end=end)
    else:
        print(text, end=end)

# --- CLI特有的Banner ---
def print_banner():
    banner_text = "--- PubCrawler v7.4: CLI AI Assistant (Refactored) ---"
    print_colored(banner_text, Colors.HEADER)
    SEARCH_RESULTS_DIR.mkdir(exist_ok=True)
    print_colored(f"[*] 结果将保存至: {SEARCH_RESULTS_DIR.resolve()}", Colors.UNDERLINE)

# --- CLI特有的结果统计打印 ---
def print_cli_stats_summary(stats_summary: Dict[str, Any]):
    if not stats_summary['total_found']: return
    print_colored("\n--- 查询结果统计 ---", Colors.HEADER)
    print(f"总计找到 {Colors.BOLD}{stats_summary['total_found']}{Colors.ENDC} 篇相关论文。")
    if stats_summary['distribution']:
        print("分布情况:")
        for conf_year, count in stats_summary['distribution'].items():
            print(f"  - {conf_year}: {count} 篇")
    print_colored("--------------------", Colors.HEADER)

# --- CLI特有的分页逻辑 ---
def interactive_pagination_cli(results: List[Dict[str, Any]], query: str, session_dir: Path):
    num_results = len(results)
    if num_results == 0:
        print_colored("[!] 未找到相关结果。", Colors.WARNING)
        return

    stats_summary = get_stats_summary(results)
    print_cli_stats_summary(stats_summary)

    total_pages = math.ceil(num_results / RESULTS_PER_PAGE)
    current_page = 1

    while True:
        start_idx, end_idx = (current_page - 1) * RESULTS_PER_PAGE, current_page * RESULTS_PER_PAGE
        page_results = results[start_idx:end_idx]

        print_colored(f"\n--- 结果预览 (第 {current_page}/{total_pages} 页) ---", Colors.HEADER)
        for i, paper in enumerate(page_results, start=start_idx + 1):
            title, authors, conf, year = paper.get('title', 'N/A'), paper.get('authors', 'N/A'), paper.get('conference', 'N/A'), paper.get('year', 'N/A')
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
                start_ai_chat_session(results)
                print_colored("\n[i] AI对话结束，返回结果列表。", Colors.OKBLUE)
                continue
            current_page += 1
        except KeyboardInterrupt:
            return

    if input(f"\n是否将这 {num_results} 条结果全部保存到 Markdown? (y/n, 默认y): ").lower() != 'n':
        save_results_to_markdown(results, query)

# --- 主程序 (CLI入口) ---
def main():
    # 确保在main函数开始时调用初始化，而不是在模块加载时
    initialize_components()

    if not _initialized: # 检查初始化是否成功
        print_colored(f"[{Colors.FAIL}✖{Colors.ENDC}] 严重错误: 搜索后端服务初始化失败，无法运行CLI。", Colors.FAIL)
        sys.exit(1)

    session_dir = SEARCH_RESULTS_DIR / f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    session_dir.mkdir(exist_ok=True)

    print_banner()
    print_colored("\n--- 搜索语法 (AI已集成 & FTS5已修正) ---", Colors.OKBLUE)
    print("  - `transformer author:vaswani`   (关键词 + 作者字段搜索)")
    print("  - `title:\"vision transformer\"`     (精确标题搜索)")
    print("  - `\"large language model\" AND efficient` (短语和关键词组合)")
    print(f"  - `{Colors.BOLD}sem:{Colors.ENDC} efficiency of few-shot learning` (语义搜索！)")

    while True:
        try:
            q = input(f"\n🔍 {Colors.BOLD}请输入查询{Colors.ENDC} (或 'exit' 退出): ").strip()
            if not q: continue
            if q.lower() == 'exit': break

            results = []
            if q.lower().startswith('sem:'):
                semantic_query = q[4:].strip()
                if semantic_query: results, _ = semantic_search(semantic_query)
            else:
                results, _ = keyword_search(q)

            interactive_pagination_cli(results, q, session_dir)

        except KeyboardInterrupt:
            break
        except Exception as e:
            print_colored(f"发生未知错误: {e}", Colors.FAIL)

    if _sqlite_conn:
        _sqlite_conn.close()
        print_colored("\n[✔] SQLite连接已关闭。", Colors.OKBLUE)
    print("\n再见！")


if __name__ == "__main__":
    main()