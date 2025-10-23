import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

# ==============================================================================
# --- 实验配置 ---
# ==============================================================================

# 1. 设置用于测试的线程数列表。脚本将为列表中的每个值运行一次测试。
#    可以根据需要调整这个列表，例如增加 40, 56 等。
THREADS_TO_TEST = [4, 8, 12, 16, 24, 32, 48, 64]

# 2. 选择一个固定的年份进行测试，以保证每次测试的工作量一致。
#    建议选择一个论文数量较多的年份，如 2024 或 2025。
YEAR_FOR_TESTING = 2024

# 3. 设置用于测试的论文数量。数量不宜过少（无法体现差距），也不宜过多（测试时间太长）。
#    100-200 是一个比较理想的范围。
PAPERS_FOR_TESTING = 150

# ==============================================================================

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}
ACL_BASE_URL_PATTERN = "https://aclanthology.org/volumes/{year}.acl-long/"


def get_paper_links_for_workload(year: int, limit: int):
    """
    获取一个固定的工作负载（论文链接列表）用于所有测试。
    """
    target_url = ACL_BASE_URL_PATTERN.format(year=year)
    print(f"[*] 准备实验环境: 正在从 {target_url} 获取论文列表...")

    try:
        response = requests.get(target_url, headers=HEADERS, timeout=30)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'lxml')
        link_tags = soup.select('p.d-sm-flex strong a.align-middle')
        paper_links = [urljoin(target_url, tag['href']) for tag in link_tags if f'{year}.acl-long.0' not in tag['href']]

        actual_found = len(paper_links)
        print(f"[*] 找到了 {actual_found} 篇有效论文。")

        # 智能限制：确保我们有足够的数据，但又不超过实际数量
        actual_limit = min(limit, actual_found)
        if actual_limit < limit:
            print(f"[*] [警告] 期望测试 {limit} 篇，但只找到 {actual_found} 篇。将以 {actual_limit} 篇为准。")

        print(f"[*] 实验工作负载已确定: {actual_limit} 篇论文。")
        return paper_links[:actual_limit]
    except requests.RequestException as e:
        print(f"[!] [错误] 准备工作负载失败: {e}")
        return None


def scrape_single_paper_details(url: str):
    """爬取单个详情页的核心函数。在测试中，我们只关心它是否成功完成。"""
    try:
        # 使用更长的超时，因为并发时网络可能会拥堵
        response = requests.get(url, headers=HEADERS, timeout=25)
        response.raise_for_status()
        # 这里我们不需要解析，只需要确保请求成功返回即可模拟真实耗时
        return True
    except Exception:
        return False


def run_single_test(worker_count: int, urls_to_crawl: list):
    """
    使用指定的线程数，对给定的URL列表执行一次完整的爬取测试。
    """
    print("\n" + "-" * 60)
    print(f"🧪 正在测试: {worker_count} 个并发线程...")

    start_time = time.time()

    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        futures = [executor.submit(scrape_single_paper_details, url) for url in urls_to_crawl]

        # 使用tqdm来可视化进度
        for _ in tqdm(as_completed(futures), total=len(urls_to_crawl), desc=f"   - 进度 ({worker_count}线程)"):
            pass

    end_time = time.time()
    elapsed_time = end_time - start_time

    print(f"   -> 完成! 耗时: {elapsed_time:.2f} 秒")
    return elapsed_time


def main():
    """主函数，调度所有测试并生成最终报告。"""
    print("=" * 60)
    print("      并发线程数性能优化器 for ACL Crawler")
    print("=" * 60)

    # 1. 准备一个固定的、用于所有测试的工作负载
    workload_urls = get_paper_links_for_workload(YEAR_FOR_TESTING, PAPERS_FOR_TESTING)
    if not workload_urls:
        print("[!] 无法继续测试，因为未能获取到论文列表。")
        return

    # 2. 循环执行测试
    experiment_results = []
    for num_threads in THREADS_TO_TEST:
        duration = run_single_test(num_threads, workload_urls)
        experiment_results.append({
            "threads": num_threads,
            "time": duration
        })
        # 在每次测试间歇2秒，避免对服务器造成连续冲击
        time.sleep(2)

    # 3. 分析结果并生成报告
    if not experiment_results:
        print("[!] 没有完成任何测试。")
        return

    print("\n\n" + "#" * 60)
    print("📊            最终性能测试报告")
    print(f"            (测试负载: {len(workload_urls)} 篇论文)")
    print("#" * 60)
    print(f"{'线程数':<10} | {'总耗时 (秒)':<15} | {'每秒爬取论文数':<20}")
    print("-" * 60)

    best_result = None
    best_performance = 0

    for res in experiment_results:
        threads = res['threads']
        total_time = res['time']

        if total_time > 0:
            papers_per_second = len(workload_urls) / total_time
            print(f"{threads:<10} | {total_time:<15.2f} | {papers_per_second:<20.2f}")

            if papers_per_second > best_performance:
                best_performance = papers_per_second
                best_result = res
        else:
            print(f"{threads:<10} | {total_time:<15.2f} | {'N/A'}")

    print("-" * 60)

    # 4. 给出最终建议
    if best_result:
        optimal_threads = best_result['threads']
        print("\n🏆 结论:")
        print(f"根据本次在您当前网络环境下的实测结果：")
        print(f"当线程数设置为 **{optimal_threads}** 时，爬取效率最高，达到了每秒 **{best_performance:.2f}** 篇论文。")
        print(f"建议您在 PubCrawler 的 YAML 配置文件中将 ACL 和 CVF 任务的 `max_workers` 设置为 **{optimal_threads}**。")
    else:
        print("\n[!] 未能确定最佳线程数。")

    print("#" * 60)


if __name__ == "__main__":
    main()