# FILE: src/utils/formatter.py

import pandas as pd
from pathlib import Path
from datetime import datetime


def save_as_markdown(papers: list, task_name: str, output_dir: Path):
    """Saves a list of paper dictionaries as a formatted Markdown file."""
    if not papers:
        return

    report_dir = output_dir / task_name
    report_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d")
    filename = report_dir / f"{task_name}_report_{timestamp}.md"

    with open(filename, 'w', encoding='utf-8') as f:
        f.write(f"# {task_name} Papers ({timestamp})\n\n")
        f.write(f"Total papers found: **{len(papers)}**\n\n")
        f.write("---\n\n")

        for i, paper in enumerate(papers, 1):
            title = paper.get('title', 'N/A').replace('\n', ' ')
            authors = paper.get('authors', 'N/A').replace('\n', ' ')
            abstract = paper.get('abstract', 'N/A').replace('\n', ' ')
            pdf_url = paper.get('pdf_url', '#')

            f.write(f"### {i}. {title}\n\n")
            f.write(f"**Authors:** *{authors}*\n\n")

            if pdf_url and pdf_url != '#':
                f.write(f"**[PDF Link]({pdf_url})**\n\n")

            f.write(f"**Abstract:**\n")
            f.write(f"> {abstract}\n\n")
            f.write("---\n\n")

    print(f"Successfully saved Markdown report to {filename}")


def save_as_summary_txt(papers: list, task_name: str, output_dir: Path):
    """Saves a list of paper dictionaries as a formatted TXT file."""
    if not papers:
        return

    report_dir = output_dir / task_name
    report_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d")
    filename = report_dir / f"{task_name}_summary_{timestamp}.txt"

    with open(filename, 'w', encoding='utf-8') as f:
        f.write(f"--- {task_name} Summary ({timestamp}) ---\n")
        f.write(f"Total papers found: {len(papers)}\n")
        f.write("=" * 40 + "\n\n")

        for i, paper in enumerate(papers, 1):
            title = paper.get('title', 'N/A').replace('\n', ' ')
            authors = paper.get('authors', 'N/A').replace('\n', ' ')
            abstract = paper.get('abstract', 'N/A').replace('\n', ' ')
            pdf_url = paper.get('pdf_url', 'N/A')

            f.write(f"[{i}] Title: {title}\n")
            f.write(f"    Authors: {authors}\n")
            f.write(f"    PDF URL: {pdf_url}\n")
            f.write(f"    Abstract: {abstract}\n\n")

    print(f"Successfully saved TXT summary to {filename}")


def save_as_csv(papers: list, task_name: str, output_dir: Path):
    """Saves a list of paper dictionaries as a CSV file."""
    if not papers:
        return

    report_dir = output_dir / task_name
    report_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d")
    filename = report_dir / f"{task_name}_data_{timestamp}.csv"

    df = pd.DataFrame(papers)

    # Standardize column order
    cols = ['title', 'authors', 'abstract', 'pdf_url', 'keywords', 'source_url']
    df_cols = [c for c in cols if c in df.columns] + [c for c in df.columns if c not in cols]
    df = df[df_cols]

    df.to_csv(filename, index=False, encoding='utf-8-sig')
    print(f"Successfully saved CSV data to {filename}")

# END OF FILE: src/utils/formatter.py