# FILE: src/search/indexer.py

import sqlite3
import pandas as pd
from pathlib import Path
from tqdm import tqdm
import time

# --- 配置 ---
PROJECT_ROOT = Path(__file__).parent.parent.parent
METADATA_DIR = PROJECT_ROOT / "output" / "metadata"
DB_PATH = PROJECT_ROOT / "papers.db"  # 数据库文件将保存在项目根目录

# 定义需要的列，与数据库表结构对应
REQUIRED_COLUMNS = ['title', 'authors', 'abstract', 'conference', 'year', 'pdf_url', 'source_file']


def create_fts_table(conn):
    """创建支持全文搜索的 FTS5 虚拟表"""
    cursor = conn.cursor()
    # 如果表已存在，先删除它，确保每次重建索引都是最新的
    cursor.execute("DROP TABLE IF EXISTS papers_fts")
    # 创建 FTS5 表。这里定义了我们想对其进行全文搜索的所有字段。
    cursor.execute("""
        CREATE VIRTUAL TABLE papers_fts USING fts5(
            title,
            authors,
            abstract,
            conference UNINDEXED,  -- UNINDEXED 表示这个字段存储但不建立全文索引(节省空间)，因为我们通常不需要全文搜它
            year UNINDEXED,
            pdf_url UNINDEXED,
            source_file UNINDEXED,
            tokenize='porter'      -- 使用 porter 分词器，支持英文词干提取(例如搜 searching 能匹配 search)
        )
    """)
    conn.commit()


def index_csv_files():
    print(f"[*] 开始构建索引...")
    print(f"    - 数据源目录: {METADATA_DIR}")
    print(f"    - 数据库路径: {DB_PATH}")

    csv_files = list(METADATA_DIR.rglob("*_data_*.csv"))
    if not csv_files:
        print("[!] 错误: 没有找到任何 CSV 文件。请先运行爬虫采集数据。")
        return

    conn = sqlite3.connect(str(DB_PATH))
    create_fts_table(conn)

    total_files = len(csv_files)
    total_papers = 0
    start_time = time.time()

    print(f"[*] 发现 {total_files} 个文件，开始处理...")

    for i, csv_path in enumerate(csv_files, 1):
        try:
            # 使用 chunksize 分块读取，核心内存优化点！
            # 每次只读 5000 行到内存，处理完就释放，绝不爆内存。
            chunk_iterator = pd.read_csv(csv_path, chunksize=5000, dtype=str)

            for chunk_df in chunk_iterator:
                if chunk_df.empty: continue

                # 数据清洗和标准化
                chunk_df = chunk_df.fillna('')
                if 'source_file' not in chunk_df.columns:
                    chunk_df['source_file'] = csv_path.name

                # 确保所有需要的列都存在
                for col in REQUIRED_COLUMNS:
                    if col not in chunk_df.columns:
                        chunk_df[col] = ''

                # 选取并排序特定的列以匹配数据库结构
                data_to_insert = chunk_df[REQUIRED_COLUMNS].values.tolist()

                # 批量插入数据
                conn.executemany(
                    "INSERT INTO papers_fts(title, authors, abstract, conference, year, pdf_url, source_file) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    data_to_insert
                )
                total_papers += len(data_to_insert)

            print(f"    [{i}/{total_files}] 已索引: {csv_path.name}")

        except Exception as e:
            print(f"    [!] 处理文件失败 {csv_path.name}: {e}")

    # 提交事务并进行优化
    print("[*] 正在提交并优化数据库 (可能需要一点时间)...")
    conn.commit()
    # Optimize 命令会重组数据库文件，使其在搜索时更快
    conn.execute("INSERT INTO papers_fts(papers_fts) VALUES('optimize')")
    conn.close()

    end_time = time.time()
    print(f"\n[✔] 索引构建完成！")
    print(f"    - 总计索引论文: {total_papers} 篇")
    print(f"    - 总耗时: {end_time - start_time:.2f} 秒")
    print(f"    - 数据库文件大小: {DB_PATH.stat().st_size / (1024 * 1024):.2f} MB")


if __name__ == "__main__":
    index_csv_files()