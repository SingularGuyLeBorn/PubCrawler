# FILE: scripts/test_arxiv.py
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime


def test_arxiv_api_advanced():
    """
    一个用于测试 arXiv API 高级查询并解析其返回结果的脚本。
    此版本旨在提取尽可能多的详细信息，包括发表信息。
    """
    # API 的基础 URL
    base_url = 'http://export.arxiv.org/api/query?'

    # --- 高级查询示例 ---
    # 目标: 查找作者 Geoffrey Hinton 在 cs.LG (机器学习) 或 cs.AI (人工智能) 分类下发表的，
    # 并且标题中包含 capsule 或 contrastive 的论文。
    author = 'Hinton'
    category = '(cat:cs.LG OR cat:cs.AI)'
    title_keyword = '(ti:capsule OR ti:contrastive)'

    search_query_raw = f'au:{author} AND {category} AND {title_keyword}'
    search_query = urllib.parse.quote(search_query_raw)

    start = 0
    max_results = 5

    query_params = f'search_query={search_query}&start={start}&max_results={max_results}&sortBy=submittedDate&sortOrder=descending'
    full_url = base_url + query_params

    print(f"正在访问的 URL (解码后查询: '{search_query_raw}')")
    print(f"完整 URL: {full_url}\n")

    try:
        with urllib.request.urlopen(full_url) as response:
            if response.status != 200:
                print(f"HTTP 请求失败，状态码: {response.status}")
                return

            xml_data = response.read().decode('utf-8')

            print("--- API 返回的原始 XML (部分) ---")
            print(xml_data[:1000] + "...\n")

            # 定义 XML 命名空间
            ns = {
                'atom': 'http://www.w3.org/2005/Atom',
                'opensearch': 'http://a9.com/-/spec/opensearch/1.1/',
                'arxiv': 'http://arxiv.org/schemas/atom'
            }

            root = ET.fromstring(xml_data)

            total_results = root.find('opensearch:totalResults', ns).text
            print(f"查询命中总数: {total_results}\n")

            entries = root.findall('atom:entry', ns)

            if not entries:
                print("未找到任何满足条件的论文。")
                return

            print(f"--- 解析到的 {len(entries)} 篇论文信息 ---\n")

            for i, entry in enumerate(entries):
                print(f"--- 论文 #{i + 1} ---")

                # --- 提取字段 ---
                entry_id = entry.find('atom:id', ns).text.strip()
                print(f"ID: {entry_id}")

                updated_str = entry.find('atom:updated', ns).text
                updated_dt = datetime.fromisoformat(updated_str.replace('Z', '+00:00'))
                print(f"更新时间 (Updated): {updated_dt.strftime('%Y-%m-%d %H:%M:%S %Z')}")

                published_str = entry.find('atom:published', ns).text
                published_dt = datetime.fromisoformat(published_str.replace('Z', '+00:00'))
                print(f"发布时间 (Published): {published_dt.strftime('%Y-%m-%d %H:%M:%S %Z')}")

                title = entry.find('atom:title', ns).text.strip().replace('\n', ' ').replace('  ', ' ')
                print(f"标题 (Title): {title}")

                summary = entry.find('atom:summary', ns).text.strip().replace('\n', ' ').replace('  ', ' ')
                print(f"摘要 (Summary): {summary[:200]}...")

                # 提取作者及所属机构
                authors = entry.findall('atom:author', ns)
                author_details = []
                for author in authors:
                    name = author.find('atom:name', ns).text
                    affiliation_element = author.find('arxiv:affiliation', ns)
                    if affiliation_element is not None and affiliation_element.text:
                        affiliation = affiliation_element.text.strip()
                        author_details.append(f"{name} ({affiliation})")
                    else:
                        author_details.append(name)
                print(f"作者 (Authors): {', '.join(author_details)}")

                # --- 新增：提取发表信息 ---

                # 1. 期刊/会议引用 (Journal Reference)
                journal_ref_element = entry.find('arxiv:journal_ref', ns)
                journal_ref = journal_ref_element.text.strip() if journal_ref_element is not None else "N/A"
                print(f"期刊/会议引用 (Journal Ref): {journal_ref}")

                # 2. DOI (Digital Object Identifier)
                doi_element = entry.find('arxiv:doi', ns)
                doi = doi_element.text.strip() if doi_element is not None else "N/A"
                print(f"DOI: {doi}")

                # 3. 评论区 (包含额外信息)
                comment_element = entry.find('arxiv:comment', ns)
                comment = comment_element.text.strip() if comment_element is not None else "N/A"
                print(f"评论 (Comment): {comment}")

                # --- 其他信息 ---
                primary_category_element = entry.find('arxiv:primary_category', ns)
                primary_category = primary_category_element.attrib[
                    'term'] if primary_category_element is not None else "N/A"
                print(f"主要分类 (Primary Category): {primary_category}")

                categories = entry.findall('atom:category', ns)
                category_terms = [cat.attrib['term'] for cat in categories]
                print(f"所有分类 (Categories): {', '.join(category_terms)}")

                pdf_link = ""
                links = entry.findall('atom:link', ns)
                for link in links:
                    if link.attrib.get('title') == 'pdf':
                        pdf_link = link.attrib.get('href')
                        break
                print(f"PDF链接 (PDF Link): {pdf_link}")

                print("\n")

    except urllib.error.URLError as e:
        print(f"访问 arXiv API 失败: {e.reason}")
    except ET.ParseError as e:
        print(f"XML 解析失败: {e}")
    except Exception as e:
        print(f"发生未知错误: {e}")


if __name__ == '__main__':
    test_arxiv_api_advanced()

# END OF FILE: scripts/test_arxiv.py