# FILE: src/selective_recon.py

import requests
from bs4 import BeautifulSoup
import openreview
import openreview.api
import pprint
import logging
import time
from urllib.parse import urljoin
import os

# Selenium imports for advanced scraping
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# --- CONFIGURATION ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
pp = pprint.PrettyPrinter(indent=2)
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
YEARS_TO_SCAN = range(2019, 2027)  # 2019 to 2026


# --- CORE BATTLE-TESTED FUNCTIONS ---

def test_openreview(conf_name: str, year: int, config: dict):
    """Deep-dives OpenReview using the appropriate API version."""
    api_version = config.get("api", "v2")  # Default to v2
    venue_id = config["venue_id"].format(year=year)
    print(f"\n--- [DEEP DIVE] OpenReview (API v{api_version}): {conf_name} {year} ---")
    print(f"Venue ID: {venue_id}")

    try:
        notes_list = []
        if api_version == "v1":
            client = openreview.Client(baseurl='https://api.openreview.net')
            notes_iterator = None
            if config.get("use_blind", False):
                invitation = f"{venue_id}/-/Blind_Submission"
                print(f"Using Blind Submission: {invitation}")
                notes_iterator = client.get_all_notes(invitation=invitation)
            else:
                notes_iterator = client.get_all_notes(content={'venueid': venue_id})
            notes_list = list(notes_iterator)
        else:  # API v2
            client = openreview.api.OpenReviewClient(baseurl='https://api2.openreview.net')
            notes_iterator = client.get_all_notes(content={'venueid': venue_id})
            notes_list = list(notes_iterator)

        if not notes_list:
            print("[RESULT] No papers found.")
            return

        note = notes_list[0]
        print(f"[SUCCESS] Found {len(notes_list)} papers. Logging first paper...")
        print("\n--- [DEEP DIVE LOG] Full Paper Note Object ---")
        pp.pprint(note.to_json())

    except Exception as e:
        print(f"[ERROR] OpenReview test failed: {e}")


def test_cvf(url: str, year: int, conference: str):
    """Deep-dives a CVF conference using a two-stage strategy."""
    print(f"\n--- [DEEP DIVE] CVF: {conference} {year} ---")
    print(f"Index URL: {url}")
    try:
        index_response = requests.get(url, headers=HEADERS, timeout=15)
        if index_response.status_code == 404:
            print("[RESULT] Index page not found (404 Error).")
            return
        index_response.raise_for_status()
        soup = BeautifulSoup(index_response.content, 'lxml')
        first_paper_link = soup.select_one('dt.ptitle > a[href$=".html"]')
        if not first_paper_link:
            print("[ERROR] Could not find any paper link on the index page.")
            return
        absolute_url = urljoin(url, first_paper_link['href'])
        print(f"Found sample paper URL: {absolute_url}")
        test_html_page(absolute_url, year, conference, 'cvf')
    except Exception as e:
        print(f"[ERROR] CVF test failed: {e}")


def test_html_page(url: str, year: int, conference: str, parser_type: str):
    """Deep-dives a single HTML page for known platforms (PMLR, ACL, CVF-detail)."""
    if parser_type != 'cvf':
        print(f"\n--- [DEEP DIVE] HTML Page: {conference} {year} ---")
        print(f"URL: {url}")

    parsers = {
        'cvf': {"title": "#papertitle", "authors": "#authors > b > i", "abstract": "#abstract",
                "pdf_link": 'meta[name="citation_pdf_url"]'},
        'pmlr': {"title": "title", "authors": "span.authors", "abstract": "div.abstract",
                 "pdf_link": 'meta[name="citation_pdf_url"]'},
        'acl': {"title": "h2#title > a", "authors": "p.lead", "abstract": 'div.acl-abstract > span',
                "pdf_link": 'meta[name="citation_pdf_url"]'}
    }

    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        if response.status_code == 404:
            print("[RESULT] Page not found (404 Error).")
            return
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'lxml')
        parser_map = parsers[parser_type]
        extracted_data = {}
        all_found = True
        for key, selector in parser_map.items():
            element = soup.select_one(selector)
            if element:
                value = element.get('content') if element.name == 'meta' and 'pdf' in key else element.get_text(
                    strip=True)
                extracted_data[key] = value
            else:
                extracted_data[key] = f"--- NOT FOUND with selector: '{selector}' ---"
                all_found = False

        print("\n--- [DEEP DIVE LOG] Extracted Data ---")
        pp.pprint(extracted_data)
        print(
            f"[{'SUCCESS' if all_found else 'FAIL'}] All elements were {'' if all_found else 'not'} found for {conference} {year}.")
    except Exception as e:
        print(f"[ERROR] HTML page test failed: {e}")


def explore_with_selenium(url: str, name: str, year: int):
    """Uses Selenium to explore and saves the full HTML source for later analysis."""
    print(f"\n--- [EXPLORE with Selenium] {name} {year} ---")
    print(f"URL: {url}")
    driver = None
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument(f"user-agent={HEADERS['User-Agent']}")
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)

        driver.get(url)
        time.sleep(8)
        title = driver.title

        if "403" in title or "Forbidden" in title or "Error" in title or "Page not Found" in title:
            print(f"[FAIL] Page access denied or not found. Title: '{title}'")
            return

        print(f"[SUCCESS] Page is accessible. Title: '{title}'")
        filename = f"_recon_dump_{name.replace(' ', '_')}_{year}.html"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        print(f"[ANALYSIS] Selenium bypassed blocks. Full HTML source saved to '{filename}' for your review.")
    except Exception as e:
        print(f"[FAIL] Selenium exploration failed: {e}")
    finally:
        if driver:
            driver.quit()


# ==============================================================================
# ---  MASTER TASK DEFINITIONS "THE ENCYCLOPEDIA" ---
# ==============================================================================
TASK_DEFINITIONS = {
    # --- Tier 1 Platforms (Known Good, Deep Dive Parsers Exist) ---
    'ICLR': {"type": "openreview", "config": {"api_versions": {
        y: ({"api": "v1", "venue_id": "ICLR.cc/{year}/Conference", "use_blind": True}) for y in range(2019, 2024)}} | {
                                                 y: ({"api": "v2", "venue_id": f"ICLR.cc/{y}/Conference"}) for y in
                                                 range(2024, 2027)}},
    'NeurIPS': {"type": "openreview", "config": {"api_versions": {
        y: ({"api": "v1", "venue_id": "NeurIPS.cc/{year}/Conference"}) for y in range(2019, 2023)}} | {
                                                    y: ({"api": "v2", "venue_id": f"NeurIPS.cc/{y}/Conference"}) for y
                                                    in range(2023, 2027)}},
    'CVPR': {"type": "cvf", "url_pattern": "https://openaccess.thecvf.com/CVPR{year}?day=all"},
    'ICCV': {"type": "cvf", "url_pattern": "https://openaccess.thecvf.com/ICCV{year}?day=all"},
    'ICML': {"type": "pmlr", "url_samples": {2019: "https://proceedings.mlr.press/v97/acharya19a.html",
                                             2020: "https://proceedings.mlr.press/v119/agrawal20a.html",
                                             2021: "https://proceedings.mlr.press/v139/agarwal21a.html",
                                             2022: "https://proceedings.mlr.press/v162/abbe22a.html",
                                             2023: "https://proceedings.mlr.press/v202/zhang23y.html",
                                             2024: "https://proceedings.mlr.press/v235/acharya24a.html"}},
    'AISTATS': {"type": "pmlr", "url_samples": {2019: "https://proceedings.mlr.press/v89/aba-abdaoui19a.html",
                                                2020: "https://proceedings.mlr.press/v108/abad20a.html",
                                                2021: "https://proceedings.mlr.press/v130/aher21a.html",
                                                2022: "https://proceedings.mlr.press/v151/abbas22a.html",
                                                2023: "https://proceedings.mlr.press/v206/sakaue23a.html",
                                                2024: "https://proceedings.mlr.press/v238/abbas24a.html"}},
    'ACL': {"type": "acl", "url_pattern": "https://aclanthology.org/{year}.acl-long.1/"},
    'EMNLP': {"type": "acl", "url_pattern": "https://aclanthology.org/{year}.emnlp-main.1/"},
    'NAACL': {"type": "acl_special",
              "patterns": {2019: "2019.naacl-main.1", 2021: "2021.naacl-main.1", 2022: "2022.naacl-main.1",
                           2024: "2024.naacl-long.1", 2025: "2025.naacl-long.1"}},

    # --- Tier 2 Platforms (Selenium Required for Exploration) ---
    'TPAMI': {"type": "selenium", "url_pattern": "https://www.computer.org/csdl/journal/tp/past-issues/{year}"},
    'IJCV': {"type": "selenium", "url_pattern": "https://link.springer.com/journal/11263/volumes-and-issues"},
    'ECCV': {"type": "selenium", "url_pattern": "https://link.springer.com/conference/eccv"},
    'AAAI': {"type": "selenium", "url_pattern": "https://aaai.org/aaai-publications/aaai-conference-proceedings/"},
    'KDD': {"type": "selenium", "url_pattern": "https://dl.acm.org/conference/kdd/proceedings"},
    'SIGIR': {"type": "selenium", "url_pattern": "https://dl.acm.org/conference/sigir/proceedings"},
    'WWW': {"type": "selenium", "url_pattern": "https://dl.acm.org/conference/www/proceedings"},
    'CHI': {"type": "selenium", "url_pattern": "https://dl.acm.org/conference/chi/proceedings"},
    'ICRA': {"type": "selenium", "url_pattern": "https://ieeexplore.ieee.org/xpl/conhome/all-proceedings.html"},

    # --- Tier 3 Platforms (Static HTML, Need New Parsers) ---
    'JMLR': {"type": "static_html", "url_pattern": "https://jmlr.org/papers/v{vol}/",
             "vol_map": {y: 20 + (y - 2019) for y in YEARS_TO_SCAN}},
    'TACL': {"type": "static_html", "url_pattern": "https://aclanthology.org/venues/tacl/"},
    'IJCAI': {"type": "static_html", "url_pattern": "https://www.ijcai.org/proceedings/{year}/"},
    'MLSys': {"type": "static_html", "url_pattern": "https://mlsys.org/virtual/{year}/papers.html"},
}

# ==============================================================================
# ---  THE BATTLE PLAN ---
# ==============================================================================
# INSTRUCTIONS:
# 1. Uncomment or add the 'Conference_Year' keys you want to test below.
# 2. This list is your command center. What you enable here is what gets run.
# ==============================================================================
BATTLE_PLAN = [
    # --- Your Core Targets ---
    # 'ICLR_2019', 'ICLR_2020', 'ICLR_2021', 'ICLR_2022', 'ICLR_2023', 'ICLR_2024', 'ICLR_2025', 'ICLR_2026',
    # 'NeurIPS_2019', 'NeurIPS_2020', 'NeurIPS_2021', 'NeurIPS_2022', 'NeurIPS_2023', 'NeurIPS_2024', 'NeurIPS_2025',
    # 'NeurIPS_2026',  # Use NeurIPS or NIPS, both work
    'ICML_2019', 'ICML_2020', 'ICML_2021', 'ICML_2022', 'ICML_2023', 'ICML_2024', 'ICML_2025', 'ICML_2026',
    'ACL_2019', 'ACL_2020', 'ACL_2021', 'ACL_2022', 'ACL_2023', 'ACL_2024', 'ACL_2025', 'ACL_2026',

    # --- THE GRAND MENU (Copy from here to the list above) ---
    # 'CVPR_2019', 'CVPR_2020', 'CVPR_2021', 'CVPR_2022', 'CVPR_2023', 'CVPR_2024', 'CVPR_2025', 'CVPR_2026',
    # 'ICCV_2019', 'ICCV_2021', 'ICCV_2023', 'ICCV_2025', # Note: Biennial
    # 'EMNLP_2019', 'EMNLP_2020', 'EMNLP_2021', 'EMNLP_2022', 'EMNLP_2023', 'EMNLP_2024', 'EMNLP_2025', 'EMNLP_2026',
    # 'NAACL_2019', 'NAACL_2021', 'NAACL_2022', 'NAACL_2024', # Note: Irregular years
    # 'AISTATS_2019', 'AISTATS_2020', 'AISTATS_2021', 'AISTATS_2022', 'AISTATS_2023', 'AISTATS_2024', 'AISTATS_2025', 'AISTATS_2026',

    # --- Tier 2 (Selenium required) ---
    # 'TPAMI_2024', 'IJCV_2024', 'ECCV_2024', 'AAAI_2024', 'KDD_2024', 'SIGIR_2024', 'WWW_2024', 'CHI_2024', 'ICRA_2024',

    # --- Tier 3 (New parser needed) ---
    # 'JMLR_2024', 'TACL_2024', 'IJCAI_2024', 'MLSys_2024',
]

# ==============================================================================
# ---  MAIN EXECUTION BLOCK  ---
# ==============================================================================
if __name__ == "__main__":
    print("=" * 80)
    print("=      PubCrawler Checklist-Driven Reconnaissance      =")
    print(f"=    Executing {len(BATTLE_PLAN)} selected tasks from your battle plan...     =")
    print("=" * 80)

    for task_key in BATTLE_PLAN:
        parts = task_key.split('_')
        if len(parts) != 2 or not parts[1].isdigit():
            print(f"\n[ERROR] Invalid task key format: '{task_key}'. Should be 'Conference_Year'. Skipping.")
            continue

        conf_name, year_str = parts
        year = int(year_str)

        base_conf_name = 'NeurIPS' if conf_name.upper() in ['NIPS', 'NEURIPS'] else conf_name

        if base_conf_name not in TASK_DEFINITIONS:
            print(f"\n[ERROR] No configuration found for conference: '{base_conf_name}'. Skipping task '{task_key}'.")
            continue

        config = TASK_DEFINITIONS[base_conf_name]
        job_type = config["type"]

        if job_type == "openreview":
            if year in config["config"]["api_versions"]:
                api_config = config["config"]["api_versions"][year]
                test_openreview(base_conf_name, year, api_config)
            else:
                print(f"\n[INFO] No OpenReview API configuration for {base_conf_name} {year}. Skipping.")

        elif job_type == "cvf":
            url = config["url_pattern"].format(year=year)
            test_cvf(url, year, base_conf_name)

        elif job_type == "pmlr":
            if year in config["url_samples"]:
                url = config["url_samples"][year]
                test_html_page(url, year, base_conf_name, 'pmlr')
            else:
                print(f"\n[INFO] No sample URL configured for {base_conf_name} {year}. Skipping.")

        elif job_type == "acl":
            url = config["url_pattern"].format(year=year)
            test_html_page(url, year, base_conf_name, 'acl')

        elif job_type == "acl_special":
            if year in config["patterns"]:
                pattern = config["patterns"][year]
                url = f"https://aclanthology.org/{pattern}/"
                test_html_page(url, year, base_conf_name, 'acl')
            else:
                print(f"\n[INFO] No URL pattern configured for {base_conf_name} {year}. Skipping.")

        elif job_type in ["selenium", "static_html"]:
            url = config["url_pattern"]
            if "{year}" in url:
                url = url.format(year=year)
            elif "vol_map" in config:
                vol = config["vol_map"].get(year)
                if not vol:
                    print(f"\n[INFO] No volume mapping for {base_conf_name} {year}. Skipping.")
                    continue
                url = url.format(vol=vol)

            if job_type == "selenium":
                explore_with_selenium(url, base_conf_name, year)
            else:  # static_html
                test_html_page(url, year, base_conf_name, 'generic')

    print("\n" + "=" * 80)
    print("All selected tasks from the Battle Plan are complete.")
    print("=" * 80)

# END OF FILE: src/selective_recon.py