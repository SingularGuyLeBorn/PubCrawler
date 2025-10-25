# FILE: src/test/test_iclr_scraper.py
#
# -----------------------------------------------------------------------------
# [独立的 ICLR 爬虫测试脚本 - 两阶段测试]
#
# 目  的:
#   快速、独立地测试 IclrScraper 的核心功能，并验证两种不同的数据获取模式。
#
# 功  能:
#   1.  **阶段一 (广度测试)**:
#       - 为每一年份抓取最多 100 篇论文的核心元数据（标题、作者、摘要等）。
#       - 不获取审稿意见和PDF链接，以保证速度。
#       - 验证大规模数据拉取的基本流程。
#
#   2.  **阶段二 (深度测试)**:
#       - 为每一年份抓取 3 篇论文的 **全部** 信息。
#       - **获取审稿意见和PDF链接**。
#       - 验证耗时较长、逻辑较复杂的数据提取功能。
#
# 如何运行:
#   在项目根目录下，执行:
#   python -m src.test.test_iclr_scraper
#
# -----------------------------------------------------------------------------

import sys
import time
from pathlib import Path
from pprint import pprint
from dataclasses import asdict

# 将项目根目录添加到 Python 路径中，以确保能够导入 src 下的模块
# resolve() 使路径更明确，并检查路径是否已存在，避免重复添加
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from src.scrapers.iclr_scraper import IclrScraper
from src.crawlers.config import get_logger
from src.crawlers.models import Paper

# --- 测试配置 ---
YEARS_TO_TEST = [2022, 2023, 2024, 2025]
METADATA_PAPER_LIMIT = 100  # 阶段一：元数据测试的论文数量
FULL_DETAIL_PAPER_LIMIT = 3  # 阶段二：完整信息测试的论文数量

# 将配置信息集中管理，便于未来扩展和维护
# OpenReview 在 2024 年左右开始推广使用 V2 API
CONFIG_MAP = {
    2022: {'api_version': 'v1'},
    2023: {'api_version': 'v1'},
    2024: {'api_version': 'v2'},
    2025: {'api_version': 'v2'},
}


def run_test():
    """执行 ICLR 爬虫的两阶段测试套件"""
    logger = get_logger("ICLR_Scraper_Test")
    print("\n" + "=" * 80)
    print("🚀 开始执行 ICLR Scraper 独立测试 (两阶段模式)...")
    print(f"   将测试年份: {YEARS_TO_TEST}")
    print(f"   阶段一: 最多获取 {METADATA_PAPER_LIMIT} 篇论文的元数据")
    print(f"   阶段二: 最多获取 {FULL_DETAIL_PAPER_LIMIT} 篇论文的完整信息 (含审稿意见)")
    print("=" * 80 + "\n")

    for year in YEARS_TO_TEST:
        print(f"\n" + "─" * 40 + f" [ ICLR {year} ] " + "─" * 40)

        year_config = CONFIG_MAP.get(year)
        if not year_config:
            print(f"  [!] 跳过 ICLR {year}，因为未在 CONFIG_MAP 中找到配置。")
            continue

        base_task_info = {
            'conference': 'ICLR',
            'year': year,
            'source_type': 'iclr',
            'venue_id': f'ICLR.cc/{year}/Conference',
            'api_version': year_config['api_version'],
        }

        # --- 阶段一: 广度测试 (仅元数据) ---
        print(f"  [▶ Phase 1/2] 正在测试: 元数据获取 (Limit: {METADATA_PAPER_LIMIT})")
        try:
            task_info_meta = base_task_info.copy()
            task_info_meta.update({
                'limit': METADATA_PAPER_LIMIT,
                'fetch_reviews': False
            })

            logger.info(f"为 ICLR {year} (元数据测试) 生成的配置: {task_info_meta}")

            scraper_meta = IclrScraper(task_info_meta, logger)
            results_meta = scraper_meta.scrape()

            if results_meta:
                print(f"    [✔ SUCCESS] 成功获取 {len(results_meta)} 篇论文的元数据。")
                print("    --- 样本数据 (第一篇，不含审稿意见) ---")
                pprint(asdict(results_meta[0]), indent=4, width=100)
                print("    --------------------------------------\n")
            else:
                print(f"    [⚠ WARNING] 未能获取任何论文。这可能是因为该年份暂无数据或配置错误。")

        except Exception as e:
            print(f"    [✖ ERROR] 测试 ICLR {year} (元数据) 时遭遇严重错误: {e}")
            logger.error(f"ICLR {year} metadata test failed.", exc_info=True)

        # 友好等待
        time.sleep(2)

        # --- 阶段二: 深度测试 (完整信息) ---
        print(f"  [▶ Phase 2/2] 正在测试: 完整信息获取 (Limit: {FULL_DETAIL_PAPER_LIMIT})")
        try:
            task_info_full = base_task_info.copy()
            task_info_full.update({
                'limit': FULL_DETAIL_PAPER_LIMIT,
                'fetch_reviews': True
            })

            logger.info(f"为 ICLR {year} (完整信息测试) 生成的配置: {task_info_full}")

            scraper_full = IclrScraper(task_info_full, logger)
            results_full = scraper_full.scrape()

            if results_full:
                print(f"    [✔ SUCCESS] 成功获取 {len(results_full)} 篇论文的完整信息。")
                print("    --- 样本数据 (第一篇，应包含 pdf_url 和 reviews) ---")
                pprint(asdict(results_full[0]), indent=4, width=100)
                print("    --------------------------------------------------\n")
            else:
                print(f"    [⚠ WARNING] 未能获取任何论文。")

        except Exception as e:
            print(f"    [✖ ERROR] 测试 ICLR {year} (完整信息) 时遭遇严重错误: {e}")
            logger.error(f"ICLR {year} full detail test failed.", exc_info=True)

        # 友好等待
        time.sleep(2)

    print("\n" + "=" * 80)
    print("✅ ICLR Scraper 测试套件执行完毕。")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    run_test()

# END OF FILE: src/test/test_iclr_scraper.py