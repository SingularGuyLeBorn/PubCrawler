# FILE: src/analysis/trends.py

import yaml
import re
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import matplotlib.ticker as mtick

from src.crawlers.config import ROOT_DIR, get_logger

logger = get_logger(__name__)
TREND_CONFIG_FILE = ROOT_DIR / "configs" / "trends.yaml"
sns.set_theme(style="whitegrid", context="talk")
plt.rcParams['figure.dpi'] = 300


def _load_trend_config():
    if not TREND_CONFIG_FILE.exists():
        logger.error(f"Trend config file not found: {TREND_CONFIG_FILE}")
        return None
    with open(TREND_CONFIG_FILE, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def _classify_paper_subfields(paper: dict, trend_config: dict) -> list:
    text = str(paper.get('title', '')) + ' ' + str(paper.get('abstract', ''))
    if not text.strip(): return []
    text = text.lower()
    matched = set()
    for field, data in trend_config.items():
        if 'sub_fields' not in data: continue
        for sub_field, keywords in data.get('sub_fields', {}).items():
            if not isinstance(keywords, list): continue
            keyword_pattern = r'\b(' + '|'.join(re.escape(k) for k in keywords) + r')\b'
            if re.search(keyword_pattern, text, re.IGNORECASE):
                matched.add(sub_field)
    return list(matched)


def _create_analysis_df(df: pd.DataFrame, trend_config: dict) -> pd.DataFrame:
    df['sub_fields'] = df.apply(lambda row: _classify_paper_subfields(row, trend_config), axis=1)
    df_exploded = df.explode('sub_fields').dropna(subset=['sub_fields'])
    if df_exploded.empty:
        return pd.DataFrame()

    stats = df_exploded.groupby('sub_fields').size().reset_index(name='paper_count')

    if 'avg_rating' in df_exploded.columns and not df_exploded['avg_rating'].isnull().all():
        avg_ratings = df_exploded.groupby('sub_fields')['avg_rating'].mean().reset_index()
        stats = pd.merge(stats, avg_ratings, on='sub_fields', how='left')

    analysis_df = stats

    if 'decision' in df_exploded.columns:
        decisions = df_exploded.groupby(['sub_fields', 'decision']).size().unstack(fill_value=0)
        analysis_df = pd.merge(analysis_df, decisions, on='sub_fields', how='left').fillna(0)

        for dtype in ['Oral', 'Spotlight', 'Poster', 'Reject', 'N/A']:
            if dtype not in analysis_df.columns:
                analysis_df[dtype] = 0

        accepted = analysis_df.get('Oral', 0) + analysis_df.get('Spotlight', 0) + analysis_df.get('Poster', 0)
        total_decision = accepted + analysis_df.get('Reject', 0)
        analysis_df['acceptance_rate'] = (accepted / total_decision.where(total_decision != 0, np.nan)).fillna(0)

    analysis_df.rename(columns={'sub_fields': 'Topic_Name'}, inplace=True)
    return analysis_df


def _plot_topic_ranking(df, metric, title, path, top_n=40):
    if metric not in df.columns:
        logger.warning(f"Metric '{metric}' not in DataFrame. Skipping plot: {title}")
        return
    df_sorted = df.dropna(subset=[metric]).sort_values(by=metric, ascending=False).head(top_n)
    if df_sorted.empty: return

    # --- 核心修复点: 为这个函数也添加最大高度限制 ---
    height = min(30, max(10, len(df_sorted) * 0.4))

    plt.figure(figsize=(16, height))
    palette = 'viridis' if metric == 'paper_count' else 'plasma_r'
    sns.barplot(x=metric, y='Topic_Name', data=df_sorted, hue='Topic_Name', palette=palette, legend=False)
    plt.title(title, fontsize=22, pad=20)
    plt.xlabel(metric.replace('_', ' ').title(), fontsize=16)
    plt.ylabel('Topic Name', fontsize=16)
    plt.yticks(fontsize=12)
    plt.tight_layout()
    plt.savefig(path)
    plt.close()


def _plot_decision_breakdown(df, title, path, top_n=40):
    if 'acceptance_rate' not in df.columns:
        logger.warning(f"Acceptance rate not available. Skipping plot: {title}")
        return
    df_sorted = df.sort_values(by='acceptance_rate', ascending=False).head(top_n)
    if df_sorted.empty: return
    cols = ['Oral', 'Spotlight', 'Poster', 'Reject', 'N/A']
    plot_data = df_sorted.set_index('Topic_Name')[[c for c in cols if c in df_sorted.columns]]
    plot_norm = plot_data.div(plot_data.sum(axis=1), axis=0)

    # --- 核心修复点: 确保这个函数也保留了最大高度限制 ---
    height = min(30, max(12, len(plot_norm) * 0.5))

    fig, ax = plt.subplots(figsize=(20, height))
    plot_norm.plot(kind='barh', stacked=True, colormap='viridis', width=0.85, ax=ax)
    count_map = df_sorted.set_index('Topic_Name')['paper_count']
    for i, name in enumerate(plot_norm.index):
        ax.text(1.01, i, f"n={count_map.get(name, 0)}", va='center', fontsize=12, fontweight='bold')
    ax.set_title(title, fontsize=24, pad=40)
    ax.set_xlabel('Proportion of Papers', fontsize=16)
    ax.set_ylabel('Topic Name (Sorted by Acceptance Rate)', fontsize=16)
    ax.xaxis.set_major_formatter(mtick.PercentFormatter(1.0))
    ax.set_xlim(0, 1)
    ax.invert_yaxis()
    ax.legend(title='Decision Type', loc='upper center', bbox_to_anchor=(0.5, 1.05), ncol=5, frameon=False)
    plt.tight_layout(rect=[0, 0, 0.95, 1])
    plt.savefig(path)
    plt.close()


def _save_summary_table(df, title, path_base, top_n=65):
    if 'acceptance_rate' not in df.columns:
        logger.warning(f"Acceptance rate not available. Skipping summary table: {title}")
        return
    df_sorted = df.sort_values(by='acceptance_rate', ascending=False).head(top_n)
    if df_sorted.empty: return
    cols = ['Topic_Name', 'paper_count', 'avg_rating', 'acceptance_rate', 'Oral', 'Spotlight', 'Poster', 'Reject',
            'N/A']
    final_table = df_sorted[[c for c in cols if c in df_sorted.columns]]
    final_table.to_csv(f"{path_base}.csv", index=False, encoding='utf-8-sig')
    styler = final_table.style.format({'avg_rating': '{:.2f}', 'acceptance_rate': '{:.2%}'}) \
        .bar(subset=['paper_count'], color='#6495ED', align='zero') \
        .bar(subset=['avg_rating'], color='#FFA07A', align='mean') \
        .background_gradient(subset=['acceptance_rate'], cmap='summer_r') \
        .set_caption(title) \
        .set_table_styles([{'selector': 'th, td', 'props': [('text-align', 'center')]}])
    with open(f"{path_base}.html", 'w', encoding='utf-8') as f:
        f.write(styler.to_html())


def _plot_cross_year_trends(df, title, path):
    df_exploded = df.explode('sub_fields').dropna(subset=['sub_fields'])
    if df_exploded.empty or df_exploded['year'].nunique() < 2:
        logger.warning(f"Skipping cross-year trend plot for '{title}': requires data from at least 2 years.")
        return
    pivot = df_exploded.groupby(['year', 'sub_fields']).size().unstack(fill_value=0)
    top_sub_fields = pivot.sum().nlargest(12).index
    pivot = pivot[top_sub_fields]
    pivot_percent = pivot.div(pivot.sum(axis=1), axis=0) * 100
    pivot_percent.sort_index(inplace=True)
    plt.figure(figsize=(16, 9))
    plt.stackplot(pivot_percent.index, pivot_percent.T.values, labels=pivot_percent.columns, alpha=0.8)
    plt.title(title, fontsize=22, weight='bold')
    plt.xlabel('Year', fontsize=16)
    plt.ylabel('Percentage of Papers (%)', fontsize=16)
    plt.xticks(pivot_percent.index.astype(int))
    plt.legend(title='Top Sub-Fields', bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout(rect=[0, 0, 0.82, 1])
    plt.savefig(path)
    plt.close()


def run_single_task_analysis(papers: list, task_name: str, output_dir: Path):
    trend_config = _load_trend_config()
    if not trend_config or not papers: return

    df = pd.DataFrame(papers)
    analysis_df = _create_analysis_df(df, trend_config)
    if analysis_df.empty:
        logger.warning(f"No topics matched for {task_name}, skipping analysis plots.")
        return

    _plot_topic_ranking(analysis_df, 'paper_count', f"Topic Hotness at {task_name}", output_dir / "1_topic_hotness.png")

    has_review_data = 'avg_rating' in analysis_df.columns and 'acceptance_rate' in analysis_df.columns
    if has_review_data:
        _plot_topic_ranking(analysis_df, 'avg_rating', f"Topic Quality at {task_name}",
                            output_dir / "2_topic_quality.png")
        _plot_decision_breakdown(analysis_df, f"Decision Breakdown at {task_name}",
                                 output_dir / "3_decision_breakdown.png")
        _save_summary_table(analysis_df, f"Summary Table for {task_name}", output_dir / "4_summary_table")
    else:
        # 这个日志只会在没有审稿数据的任务中打印，是正常的
        logger.info(f"Skipping review-based analysis for {task_name}: missing review data.")

    logger.info(f"Single-task analysis for {task_name} completed.")


def run_cross_year_analysis(papers: list, conference_name: str, output_dir: Path):
    trend_config = _load_trend_config()
    if not trend_config or not papers: return

    df = pd.DataFrame(papers)
    if 'year' not in df.columns or df['year'].isnull().all():
        logger.warning(f"Skipping cross-year analysis for {conference_name}: 'year' column not found or is empty.")
        return

    df['sub_fields'] = df.apply(lambda row: _classify_paper_subfields(row, trend_config), axis=1)

    _plot_cross_year_trends(
        df,
        f"Sub-Field Trends at {conference_name} Over Time",
        output_dir / f"trends_{conference_name}.png"
    )
    logger.info(f"Cross-year analysis for {conference_name} completed.")