# FILE: src/main.py (Optimized for Memory)

import time
import yaml
import re
import pandas as pd
from collections import defaultdict
from pathlib import Path
from tqdm import tqdm

# --- 导入所有独立的 Scraper ---
from src.scrapers.iclr_scraper import IclrScraper
from src.scrapers.neurips_scraper import NeuripsScraper
from src.scrapers.icml_scraper import IcmlScraper
from src.scrapers.acl_scraper import AclScraper
from src.scrapers.arxiv_scraper import ArxivScraper
from src.scrapers.cvf_scraper import CvfScraper
from src.scrapers.aaai_scraper import AaaiScraper
from src.scrapers.kdd_scraper import KddScraper

from src.crawlers.config import get_logger, CONFIG_FILE, METADATA_OUTPUT_DIR, PDF_DOWNLOAD_DIR, TRENDS_OUTPUT_DIR, \
    LOG_DIR
from src.scrapers.tpami_scraper import TpamiScraper
# --- 【修改点】: 导入 save_as_markdown 和 generate_wordcloud_from_papers ---
from src.utils.formatter import save_as_csv, save_as_markdown
from src.analysis.analyzer import generate_wordcloud_from_papers
# ----------------------------------------------------------------------
from src.utils.downloader import download_single_pdf
from src.analysis.trends import run_single_task_analysis, run_cross_year_analysis
from src.utils.console_logger import print_banner, COLORS

OPERATION_MODE = "collect_and_analyze"

logger = get_logger(__name__)

# --- Scraper 和 Conference 定义 (保持不变) ---
SCRAPER_MAPPING = {"iclr": IclrScraper, "neurips": NeuripsScraper, "icml": IcmlScraper, "acl": AclScraper,
                   "cvf": CvfScraper, "aaai": AaaiScraper, "kdd": KddScraper, "arxiv": ArxivScraper,
                   "tpami": TpamiScraper}
CONF_TO_DEF_SOURCE = {'ICLR': 'openreview', 'NeurIPS': 'openreview', 'ICML': 'html_pmlr', 'ACL': 'html_acl',
                      'EMNLP': 'html_acl', 'NAACL': 'html_acl', 'CVPR': 'html_cvf', 'ICCV': 'html_cvf',
                      'AAAI': 'selenium', 'KDD': 'selenium'}

# 定义哪些爬虫类型支持并发优化，以便在主程序中给出提示
CONCURRENT_SCRAPER_TYPES = ['acl', 'cvf']


def load_config():
    if not CONFIG_FILE.exists():
        logger.error(f"[✖ ERROR] Config file not found at {CONFIG_FILE}")
        return None
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def build_task_info(task: dict, source_definitions: dict) -> dict:
    # 此函数逻辑保持不变
    task_info = task.copy()
    conf, year, source_type = task.get('conference'), task.get('year'), task.get('source_type')
    if source_type in ['arxiv', 'tpami']: return task_info
    if not conf or not year:
        logger.error(f"[✖ ERROR] Task '{task.get('name')}' is missing 'conference' or 'year'.");
        return None
    def_source_key = CONF_TO_DEF_SOURCE.get(conf)
    if not def_source_key:
        logger.error(f"[✖ ERROR] No definition source found for conference '{conf}'.");
        return None
    if 'url_override' not in task:
        try:
            definition = source_definitions[def_source_key][conf]
            if isinstance(definition, dict):
                if 'venue_id' in definition:
                    task_info['venue_id'] = definition['venue_id'].replace('YYYY', str(year))
                    task_info['api_version'] = 'v1' if year in definition.get('api_v1_years', []) else 'v2'
                elif 'pattern_map' in definition:
                    base_url = "https://aclanthology.org/"
                    pattern = definition['pattern_map'].get(year)
                    if not pattern:
                        logger.error(f"[✖ ERROR] No URL pattern defined for {conf} in year {year}");
                        return None
                    task_info['url'] = f"{base_url}{pattern}/"
            else:
                task_info['url'] = definition.replace('YYYY', str(year))
        except KeyError:
            logger.error(f"[✖ ERROR] No definition for source='{def_source_key}' and conf='{conf}'");
            return None
    else:
        task_info['url'] = task['url_override']
    return task_info


def filter_papers(papers: list, filters: list) -> list:
    # 此函数逻辑保持不变
    if not filters: return papers
    original_count = len(papers)
    filter_regex = re.compile('|'.join(filters), re.IGNORECASE)
    filtered_papers = [p for p in papers if filter_regex.search(p.get('title', '') + ' ' + p.get('abstract', ''))]
    logger.info(
        f"    {COLORS['STEP']}-> Filtered papers: {original_count} -> {len(filtered_papers)} using filters: {filters}")
    return filtered_papers


def run_tasks_sequentially(tasks_to_run: list, source_definitions: dict, perform_single_analysis: bool) -> list:
    """
    顺序执行每个任务，并在每个任务完成后立即处理和保存结果，以节省内存。
    返回所有任务收集到的论文总列表，用于后续的跨年分析。
    """
    all_collected_papers = []

    for task in tasks_to_run:
        task_name = task.get('name', f"{task.get('conference')}_{task.get('year')}")
        if not task.get('enabled', False):
            continue

        logger.info(f"{COLORS['TASK_START']}[▶] STARTING TASK: {task_name}{COLORS['RESET']}")

        # --- 新增的提示信息 ---
        source_type = task.get('source_type')
        if source_type in CONCURRENT_SCRAPER_TYPES:
            max_workers = task.get('max_workers', 1)  # 默认为1保证安全
            logger.info(f"    {COLORS['STEP']}[!] 注意: 此任务类型 ({source_type}) 需要逐一访问论文详情页。")
            logger.info(
                f"    {COLORS['STEP']}    已启用 {max_workers} 个并发线程进行加速。尽管如此，如果论文数量庞大，仍可能需要较长时间。")

        scraper_class = SCRAPER_MAPPING.get(source_type)
        if not scraper_class:
            logger.error(
                f"{COLORS['ERROR']}[✖ FAILURE] No scraper for source: '{task['source_type']}'{COLORS['RESET']}\n");
            continue

        task_info = build_task_info(task, source_definitions)
        if not task_info:
            logger.error(
                f"{COLORS['ERROR']}[✖ FAILURE] Could not build task info for '{task_name}'.{COLORS['RESET']}\n");
            continue

        try:
            scraper = scraper_class(task_info, logger)
            papers = scraper.scrape()
            papers = filter_papers(papers, task.get('filters', []))

            if papers:
                for paper in papers:
                    paper['year'] = task.get('year')
                    paper['conference'] = task.get('conference')

                logger.info(f"    {COLORS['STEP']}-> Successfully processed {len(papers)} papers for '{task_name}'.")

                logger.info(f"{COLORS['PHASE']}--- Processing & Saving Results for '{task_name}' ---{COLORS['RESET']}")
                conf, year = task.get('conference', 'Misc'), task.get('year', 'Latest')

                metadata_dir = METADATA_OUTPUT_DIR / conf / str(year)
                metadata_dir.mkdir(exist_ok=True, parents=True)

                # --- 【新增功能】: 生成词云图和Markdown报告 ---
                logger.info(f"    -> Generating word cloud...")
                wordcloud_path = metadata_dir / f"{task_name}_wordcloud.png"
                wordcloud_success = generate_wordcloud_from_papers(papers, wordcloud_path)
                final_wordcloud_path = str(wordcloud_path) if wordcloud_success else None

                logger.info(f"    -> Saving results to Markdown report...")
                save_as_markdown(papers, task_name, metadata_dir, wordcloud_path=final_wordcloud_path)
                # ----------------------------------------------------

                logger.info(f"    -> Saving metadata to {metadata_dir}")
                save_as_csv(papers, task_name, metadata_dir)

                if task.get('download_pdfs', False):
                    logger.info(f"    -> Starting PDF download...")
                    pdf_dir = PDF_DOWNLOAD_DIR / conf / str(year)
                    pdf_dir.mkdir(exist_ok=True, parents=True)
                    pbar_desc = f"    -> Downloading PDFs for {task_name}"
                    for paper in tqdm(papers, desc=pbar_desc, leave=True):
                        download_single_pdf(paper, pdf_dir)

                if perform_single_analysis:
                    analysis_output_dir = metadata_dir / "analysis"
                    analysis_output_dir.mkdir(exist_ok=True)
                    logger.info(f"    -> Running single-task analysis...")
                    run_single_task_analysis(papers, task_name, analysis_output_dir)

                all_collected_papers.extend(papers)
                logger.info(
                    f"{COLORS['SUCCESS']}[✔ SUCCESS] Task '{task_name}' completed and saved.{COLORS['RESET']}\n")

            else:
                logger.warning(f"[⚠ WARNING] No papers found for task: {task_name} (or none matched filters)")
                logger.info(f"{COLORS['WARNING']}[!] Task '{task_name}' finished with no results.{COLORS['RESET']}\n")

        except Exception as e:
            logger.critical(f"任务 '{task_name}' 遭遇严重错误，已终止。错误: {e}")
            logger.info(f"详细的错误堆栈信息已记录到日志文件: {LOG_DIR / 'pubcrawler.log'}")

        time.sleep(0.5)

    return all_collected_papers


def load_all_data_for_cross_analysis(metadata_dir: Path) -> list:
    """在 'analyze' 模式下，从磁盘加载所有之前保存的 CSV 文件。"""
    if not metadata_dir.exists():
        logger.error(f"[✖ ERROR] Data directory not found: {metadata_dir}.");
        return []

    all_papers = []
    csv_files = list(metadata_dir.rglob("*_data_*.csv"))
    if not csv_files:
        logger.warning("[⚠ WARNING] No CSV data files found for cross-year analysis.");
        return []

    logger.info(f"    -> Loading {len(csv_files)} previously collected CSV file(s) from disk...")
    for csv_path in csv_files:
        try:
            df = pd.read_csv(csv_path)
            df.fillna('', inplace=True)
            all_papers.extend(df.to_dict('records'))
        except Exception as e:
            logger.error(f"[✖ ERROR] Failed to load data from {csv_path}: {e}")
    return all_papers


def main():
    print_banner()
    logger.info("=====================================================================================")
    logger.info(f"Starting PubCrawler in mode: '{OPERATION_MODE}'")
    logger.info("=====================================================================================\n")

    config = load_config()
    if not config: return

    all_papers_for_analysis = []

    if OPERATION_MODE in ["collect", "collect_and_analyze"]:
        logger.info(f"{COLORS['PHASE']}+----------------------------------------------------------+")
        logger.info(f"|    PHASE 1: PAPER COLLECTION & SINGLE-TASK ANALYSIS      |")
        logger.info(f"+----------------------------------------------------------+{COLORS['RESET']}\n")

        all_papers_for_analysis = run_tasks_sequentially(
            config.get('tasks', []),
            config.get('source_definitions', {}),
            perform_single_analysis=True
        )

    if OPERATION_MODE in ["analyze", "collect_and_analyze"]:
        logger.info(f"\n{COLORS['PHASE']}+----------------------------------------------------------+")
        logger.info(f"|          PHASE 2: CROSS-YEAR TREND ANALYSIS              |")
        logger.info(f"+----------------------------------------------------------+{COLORS['RESET']}\n")

        if OPERATION_MODE == "collect_and_analyze" and not all_papers_for_analysis:
            logger.warning("[⚠ WARNING] No data was collected in Phase 1 to perform cross-year analysis.")

        elif OPERATION_MODE == "analyze":
            all_papers_for_analysis = load_all_data_for_cross_analysis(METADATA_OUTPUT_DIR)

        if all_papers_for_analysis:
            all_data_by_conf = defaultdict(list)
            for paper in all_papers_for_analysis:
                if paper.get('conference'):
                    all_data_by_conf[paper['conference']].append(paper)

            for conference, papers in all_data_by_conf.items():
                if not papers: continue
                conf_trend_dir = TRENDS_OUTPUT_DIR / conference
                conf_trend_dir.mkdir(exist_ok=True, parents=True)
                logger.info(f"{COLORS['TASK_START']}[▶] Analyzing trends for: {conference}{COLORS['RESET']}")
                run_cross_year_analysis(papers, conference, conf_trend_dir)
                logger.info(
                    f"{COLORS['SUCCESS']}[✔ SUCCESS] Cross-year analysis for '{conference}' completed.{COLORS['RESET']}\n")

    logger.info("=====================================================================================")
    logger.info("PubCrawler run finished successfully.")
    logger.info("=====================================================================================")


if __name__ == "__main__":
    main()