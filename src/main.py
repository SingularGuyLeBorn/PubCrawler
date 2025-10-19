# FILE: src/main.py

import time
import yaml
from collections import defaultdict
import re

from src.scrapers.html_scraper import HTMLScraper
from src.scrapers.openreview_scraper import OpenReviewScraper
from src.scrapers.selenium_scraper import SeleniumScraper
from src.scrapers.arxiv_scraper import ArxivScraper # MODIFIED: Import ArxivScraper
from src.config import get_logger, CONFIG_FILE, OUTPUT_DIR
from src.utils.formatter import save_as_markdown, save_as_csv, save_as_summary_txt
from src.utils.downloader import download_pdfs
from src.analysis.analyzer import generate_wordcloud_from_papers

logger = get_logger(__name__)

# --- Scraper Mapping ---
SCRAPER_MAPPING = {
    "openreview": OpenReviewScraper,
    "html_cvf": HTMLScraper,
    "html_pmlr": HTMLScraper,
    "html_acl": HTMLScraper,
    "html_other": HTMLScraper,
    "selenium": SeleniumScraper,
    "arxiv": ArxivScraper, # MODIFIED: Register the new ArxivScraper
}


def load_config():
    """Loads and validates the YAML config file."""
    if not CONFIG_FILE.exists():
        logger.error(f"Config file not found at {CONFIG_FILE}")
        return None
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def build_task_info(task: dict, source_definitions: dict) -> dict:
    """Constructs the specific info dictionary needed by a scraper from the task config."""
    task_info = task.copy()
    source_type = task['source_type']

    # MODIFIED: Add a special handler for 'arxiv' to bypass conference/year logic
    if source_type == 'arxiv':
        logger.debug("ArXiv task detected. Bypassing conference/year URL construction.")
        return task_info

    conf = task['conference']
    year = task['year']

    if 'url_override' in task:
        task_info['url'] = task['url_override']
    else:
        try:
            definition = source_definitions[source_type][conf]

            if isinstance(definition, dict):
                if 'venue_id' in definition:  # OpenReview
                    pattern = definition['venue_id']
                    task_info['venue_id'] = pattern.replace('YYYY', str(year))
                    task_info['api_version'] = 'v1' if year in definition.get('api_v1_years', []) else 'v2'
                elif 'pattern_map' in definition:  # Special cases like NAACL
                    base_url = "https://aclanthology.org/"
                    pattern = definition['pattern_map'].get(year)
                    if not pattern:
                        logger.error(f"No URL pattern found for {conf} year {year}")
                        return None
                    task_info['url'] = f"{base_url}{pattern}/"
                else:
                    logger.error(f"Unknown complex definition for {conf}")
                    return None
            else:
                # Handle simple URL string definitions
                pattern = definition
                entry_point = pattern.replace('YYYY', str(year))
                task_info['url'] = entry_point

        except KeyError:
            logger.error(f"No source definition found for source_type='{source_type}' and conference='{conf}'")
            return None

    if source_type.startswith('html_'):
        task_info['parser_type'] = source_type.split('_', 1)[1]

    if source_type == 'selenium':
        task_info['parser_type'] = conf

    return task_info


def filter_papers(papers: list, filters: list) -> list:
    """Filters a list of papers based on keywords in title or abstract."""
    if not filters:
        return papers

    filtered_papers = []
    # Join filters with '|' to create an OR condition regex
    filter_regex = re.compile('|'.join(filters), re.IGNORECASE)

    for paper in papers:
        text_to_search = paper.get('title', '') + ' ' + paper.get('abstract', '')
        if filter_regex.search(text_to_search):
            filtered_papers.append(paper)

    logger.info(f"Filtered papers: {len(papers)} -> {len(filtered_papers)} using filters: {filters}")
    return filtered_papers


def main():
    """Main execution function driven by the YAML config."""
    logger.info("Starting PubCrawler...")
    config = load_config()
    if not config: return

    source_definitions = config.get('source_definitions', {})
    tasks_to_run = config.get('tasks', [])

    results_by_task = defaultdict(list)

    for task in tasks_to_run:
        # MODIFIED: Handle task naming for non-conference tasks like arXiv
        task_name = task.get('name', f"{task.get('conference', task.get('source_type'))}_{task.get('year', 'latest')}")
        if not task.get('enabled', False):
            logger.info(f"Skipping disabled task: {task_name}")
            continue

        logger.info(f"Processing task: {task_name}")
        task_info = build_task_info(task, source_definitions)
        if not task_info: continue

        scraper_class = SCRAPER_MAPPING.get(task['source_type'])
        if not scraper_class:
            logger.error(f"No scraper found for source type: {task['source_type']}")
            continue

        try:
            scraper = scraper_class(task_info)
            papers = scraper.scrape()

            # Apply filters first
            papers = filter_papers(papers, task.get('filters', []))

            # Then apply limit to the filtered results
            limit = task.get('limit')
            if papers and limit is not None and len(papers) > limit:
                logger.info(f"Limiting final results for {task_name} from {len(papers)} to {limit} papers.")
                papers = papers[:limit]

            if papers:
                logger.info(f"Successfully processed {len(papers)} papers for {task_name}.")
                results_by_task[task_name] = (papers, task)
            else:
                logger.warning(f"No papers found for task: {task_name} (or none matched filters)")

        except Exception as e:
            logger.error(f"Failed to process task {task_name}: {e}", exc_info=True)

        time.sleep(1)

    if not results_by_task:
        logger.info("All tasks finished. No papers were collected.")
        return

    logger.info("All scraping tasks finished. Now processing results...")
    total_papers = 0
    for task_name, (papers, task_config) in results_by_task.items():
        total_papers += len(papers)
        task_output_dir = OUTPUT_DIR / task_name
        task_output_dir.mkdir(exist_ok=True)

        # --- Analysis Step ---
        logger.info(f"Analyzing trends for {task_name}...")
        wc_path = task_output_dir / f"{task_name}_wordcloud.png"
        analysis_done = generate_wordcloud_from_papers(papers, wc_path)

        # --- Reporting Step ---
        logger.info(f"Saving reports for {task_name}...")
        wc_relative_path = wc_path.name if analysis_done else None
        save_as_markdown(papers, task_name, task_output_dir, wordcloud_path=wc_relative_path)
        save_as_csv(papers, task_name, task_output_dir)
        save_as_summary_txt(papers, task_name, task_output_dir)

        if task_config.get('download_pdfs', False):
            logger.info(f"Starting PDF download for {task_name}...")
            download_pdfs(papers, task_name, task_output_dir)  # Save PDFs inside task-specific folder
        else:
            logger.info(f"PDF download disabled for {task_name}. Skipping.")

    logger.info(f"Processing complete. Total papers collected: {total_papers}")
    logger.info(f"All reports saved in: {OUTPUT_DIR.resolve()}")


if __name__ == "__main__":
    main()
# END OF FILE: src/main.py