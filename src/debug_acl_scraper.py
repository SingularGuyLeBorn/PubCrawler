# FILE: debug_acl_scraper.py (最终修正版)
import requests
from bs4 import BeautifulSoup

# --- 配置 ---
TARGET_URL = 'https://aclanthology.org/volumes/2024.acl-long/'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# 之前的错误选择器
OLD_SELECTOR = 'p.d-sm-flex > strong > a'

# --- 核心修复点 ---
# 根据您提供的 HTML 结构和 "align-middle" 关键提示，这才是正确的选择器。
# 它寻找在 class 包含 "d-sm-flex" 的 <p> 标签内部，class 为 "align-middle" 的 <a> 标签。
NEW_SELECTOR = 'p.d-sm-flex a.align-middle'


def run_debug():
    """
    执行 ACL 爬取逻辑的调试。
    """
    print("=" * 60)
    print("=      ACL Scraper Debugger (v3 - Final)      =")
    print(f"= Target URL: {TARGET_URL}  =")
    print("=" * 60)

    try:
        print(f"\n[STEP 1] Fetching content from the URL...")
        response = requests.get(TARGET_URL, headers=HEADERS, timeout=20)
        response.raise_for_status()
        print(f"  -> Success! Received status code: {response.status_code}")

        html_content = response.text
        with open('debug_acl_page.html', 'w', encoding='utf-8') as f:
            f.write(html_content)
        print("\n[STEP 2] Saved the raw HTML content to 'debug_acl_page.html'.")

        soup = BeautifulSoup(html_content, 'lxml')
        print("\n[STEP 3] Parsed HTML content.")

        print(f"\n[STEP 4] Testing the PREVIOUS (failing) selector: '{OLD_SELECTOR}'")
        old_links = soup.select(OLD_SELECTOR)
        print(f"  -> RESULT: Found {len(old_links)} links. (Confirms previous failure)")

        print(f"\n[STEP 5] Testing the NEW (Corrected) selector: '{NEW_SELECTOR}'")
        new_links = soup.select(NEW_SELECTOR)
        print(f"  -> RESULT: Found {len(new_links)} links. (Expected: > 0)")
        if new_links:
            print("  -> DIAGNOSIS: Success! The new selector works as expected.")
            print("\n  -> Sample of found links (first 5):")
            for i, link in enumerate(new_links[:5]):
                title = link.get_text(strip=True)
                href = link.get('href')
                print(f"    {i+1}. Text: '{title[:70]}...' | Href: '{href}'")
        else:
            print("  -> DIAGNOSIS: CRITICAL FAILURE! Please re-check the HTML structure in 'debug_acl_page.html'.")

        print("\n" + "=" * 60)
        print("=      DEBUGGING COMPLETE      =")
        print("=" * 60)

    except Exception as e:
        print(f"\n[ERROR] An error occurred: {e}")


if __name__ == "__main__":
    run_debug()