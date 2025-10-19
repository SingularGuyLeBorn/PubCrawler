# FILE: src/main.py (Downloader Tqdm Integrated)

import time
import yaml
import re
import pandas as pd
from collections import defaultdict
from pathlib import Path
from tqdm import tqdm

from src.scrapers.html_scraper import HTMLScraper
from src.scrapers.openreview_scraper import OpenReviewScraper
from src.scrapers.selenium_scraper import SeleniumScraper
from src.scrapers.arxiv_scraper import ArxivScraper
from src.config import get_logger, CONFIG_FILE, OUTPUT_DIR
from src.utils.formatter import save_as_csv
# --- 核心修改点: 导入单个下载函数 ---
from src.utils.downloader import download_single_pdf
from src.analysis.trends import run_single_task_analysis, run_cross_year_analysis
from src.utils.console_logger import print_banner, COLORS

OPERATION_MODE = "collect_and_analyze"

logger = get_logger(__name__)
PAPERS_OUTPUT_DIR = OUTPUT_DIR / "papers"
TRENDS_OUTPUT_DIR = OUTPUT_DIR / "trends"

SCRAPER_MAPPING = {
    "openreview": OpenReviewScraper, "html_cvf": HTMLScraper, "html_pmlr": HTMLScraper,
    "html_acl": HTMLScraper, "html_other": HTMLScraper, "selenium": SeleniumScraper, "arxiv": ArxivScraper
}


def load_config():
    if not CONFIG_FILE.exists():
        logger.error(f"[✖ ERROR] Config file not found at {CONFIG_FILE}")
        return None
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def build_task_info(task: dict, source_definitions: dict) -> dict:
    task_info = task.copy()
    source_type = task['source_type']
    if source_type == 'arxiv': return task_info
    conf, year = task.get('conference'), task.get('year')
    if not conf or not year:
        logger.error(f"[✖ ERROR] Task '{task.get('name')}' is missing 'conference' or 'year'.")
        return None
    if 'url_override' not in task:
        try:
            definition = source_definitions[source_type][conf]
            if isinstance(definition, dict):
                if 'venue_id' in definition:
                    pattern = definition['venue_id']
                    task_info['venue_id'] = pattern.replace('YYYY', str(year))
                    task_info['api_version'] = 'v1' if year in definition.get('api_v1_years', []) else 'v2'
                elif 'pattern_map' in definition:
                    base_url = "https://aclanthology.org/"
                    pattern = definition['pattern_map'].get(year)
                    if not pattern:
                        logger.error(f"[✖ ERROR] No URL pattern for {conf} year {year}");
                        return None
                    task_info['url'] = f"{base_url}{pattern}/"
                else:
                    logger.error(f"[✖ ERROR] Unknown complex definition for {conf}");
                    return None
            else:
                task_info['url'] = definition.replace('YYYY', str(year))
        except KeyError:
            logger.error(f"[✖ ERROR] No source definition for type='{source_type}' and conf='{conf}'");
            return None
    else:
        task_info['url'] = task['url_override']
    if source_type.startswith('html_'): task_info['parser_type'] = source_type.split('_', 1)[1]
    if source_type == 'selenium': task_info['parser_type'] = conf
    return task_info


def filter_papers(papers: list, filters: list) -> list:
    if not filters: return papers
    original_count = len(papers)
    filter_regex = re.compile('|'.join(filters), re.IGNORECASE)
    filtered_papers = [p for p in papers if filter_regex.search(p.get('title', '') + ' ' + p.get('abstract', ''))]
    logger.info(
        f"    {COLORS['STEP']}-> Filtered papers: {original_count} -> {len(filtered_papers)} using filters: {filters}")
    return filtered_papers


def collect_papers_from_tasks(tasks_to_run: list, source_definitions: dict) -> dict:
    results_by_task = defaultdict(list)
    for task in tasks_to_run:
        task_name = task.get('name', f"{task.get('conference')}_{task.get('year')}")
        if not task.get('enabled', False):
            continue

        logger.info(f"{COLORS['TASK_START']}[▶] STARTING TASK: {task_name}{COLORS['RESET']}")
        task_info = build_task_info(task, source_definitions)
        if not task_info:
            logger.error(
                f"{COLORS['ERROR']}[✖ FAILURE] Could not build task info for '{task_name}'.{COLORS['RESET']}\n");
            continue
        scraper_class = SCRAPER_MAPPING.get(task['source_type'])
        if not scraper_class:
            logger.error(f"{COLORS['ERROR']}[✖ FAILURE] No scraper for type: {task['source_type']}{COLORS['RESET']}\n");
            continue
        try:
            scraper = scraper_class(task_info, logger)
            papers = scraper.scrape()
            papers = filter_papers(papers, task.get('filters', []))
            if papers:
                for paper in papers:
                    paper['year'], paper['conference'] = task.get('year'), task.get('conference')
                results_by_task[task_name] = (papers, task)
                logger.info(f"    {COLORS['STEP']}-> Successfully processed {len(papers)} papers.")
            else:
                logger.warning(f"[⚠ WARNING] No papers found for task: {task_name} (or none matched filters)")
        except Exception as e:
            logger.error(f"[✖ FAILURE] Unexpected error in task {task_name}: {e}", exc_info=True)

        if task_name in results_by_task:
            logger.info(f"{COLORS['SUCCESS']}[✔ SUCCESS] Task '{task_name}' completed.{COLORS['RESET']}\n")
        else:
            logger.info(f"{COLORS['WARNING']}[!] Task '{task_name}' finished with no results.{COLORS['RESET']}\n")
        time.sleep(0.5)
    return results_by_task


def process_and_save_results(results_by_task: dict, base_output_dir: Path, perform_single_analysis: bool):
    base_output_dir.mkdir(exist_ok=True, parents=True)
    for task_name, (papers, task_config) in results_by_task.items():
        conf, year = task_config.get('conference', 'Misc'), task_config.get('year', 'Latest')
        task_output_dir = base_output_dir / conf / str(year)
        task_output_dir.mkdir(exist_ok=True, parents=True)

        logger.info(f"    -> Saving reports for '{task_name}' to {task_output_dir}")
        save_as_csv(papers, task_name, task_output_dir)

        if task_config.get('download_pdfs', False):
            logger.info(f"    -> Starting PDF download for '{task_name}'...")
            pdf_dir = task_output_dir / "pdfs"
            pdf_dir.mkdir(exist_ok=True)
            # --- 核心修复点: 在 main.py 中创建和控制 tqdm ---
            pbar_desc = f"    -> Downloading PDFs for {task_name}"
            for paper in tqdm(papers, desc=pbar_desc, leave=True):
                download_single_pdf(paper, pdf_dir)

        if perform_single_analysis:
            analysis_output_dir = task_output_dir / "analysis"
            analysis_output_dir.mkdir(exist_ok=True)
            logger.info(f"    -> Running single-task analysis for '{task_name}'...")
            run_single_task_analysis(papers, task_name, analysis_output_dir)


def load_all_data_for_cross_analysis(papers_dir: Path) -> dict:
    if not papers_dir.exists():
        logger.error(f"[✖ ERROR] Data directory not found: {papers_dir}.");
        return {}
    all_data_by_conf = defaultdict(list)
    csv_files = list(papers_dir.rglob("*_data_*.csv"))
    if not csv_files:
        logger.warning("[⚠ WARNING] No CSV data files found for cross-year analysis.");
        return {}
    logger.info(f"    -> Loading {len(csv_files)} previously collected CSV file(s)...")
    for csv_path in csv_files:
        try:
            conference = csv_path.parent.parent.name
            df = pd.read_csv(csv_path)
            df.fillna('', inplace=True)
            if 'year' in df.columns:
                df['year'] = pd.to_numeric(df['year'], errors='coerce').astype('Int64')
            all_data_by_conf[conference].extend(df.to_dict('records'))
        except Exception as e:
            logger.error(f"[✖ ERROR] Failed to load data from {csv_path}: {e}")
    return all_data_by_conf


def main():
    print_banner()
    logger.info("=====================================================================================")
    logger.info(f"Starting PubCrawler in mode: '{OPERATION_MODE}'")
    logger.info("=====================================================================================\n")

    if OPERATION_MODE in ["collect", "collect_and_analyze"]:
        config = load_config()
        if not config: return
        logger.info(f"{COLORS['PHASE']}+----------------------------------------------------------+")
        logger.info(f"|    PHASE 1: PAPER COLLECTION & SINGLE-TASK ANALYSIS      |")
        logger.info(f"+----------------------------------------------------------+{COLORS['RESET']}\n")
        collected_results = collect_papers_from_tasks(config.get('tasks', []), config.get('source_definitions', {}))
        if collected_results:
            logger.info(f"{COLORS['PHASE']}--- Processing & Saving Collected Results ---{COLORS['RESET']}")
            process_and_save_results(collected_results, PAPERS_OUTPUT_DIR, perform_single_analysis=True)

    if OPERATION_MODE in ["analyze", "collect_and_analyze"]:
        logger.info(f"\n{COLORS['PHASE']}+----------------------------------------------------------+")
        logger.info(f"|          PHASE 2: CROSS-YEAR TREND ANALYSIS              |")
        logger.info(f"+----------------------------------------------------------+{COLORS['RESET']}\n")
        all_data_by_conf = load_all_data_for_cross_analysis(PAPERS_OUTPUT_DIR)
        if not all_data_by_conf:
            logger.warning("[⚠ WARNING] No data found to perform cross-year analysis.")
        else:
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