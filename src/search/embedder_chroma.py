# FILE: src/search/embedder_multiprocess.py (Final Version with LIMIT and Incremental Update)

import sqlite3
import chromadb
from sentence_transformers import SentenceTransformer, util
from pathlib import Path
import time
import torch
import os

# --- 配置 ---
PROJECT_ROOT = Path(__file__).parent.parent.parent
DB_DIR = PROJECT_ROOT / "database"
DB_PATH = DB_DIR / "papers.db"
CHROMA_DB_PATH = str(DB_DIR / "chroma_db")
MODEL_NAME = 'sentence-transformers/all-MiniLM-L6-v2'
COLLECTION_NAME = "papers"

# --- 【核心控制开关】 ---
# 设置为数字 (如 2000) 来开启“快速测试模式”，只处理指定数量的论文。
# 设置为 None 来开启“智能增量模式”，自动处理所有新论文。
PAPER_LIMIT = None


# ------------------------

def embed_and_store_parallel():
    if not DB_PATH.exists():
        print(f"[!] 错误: SQLite数据库文件 {DB_PATH} 不存在。请先运行 indexer.py。")
        return

    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f"[*] 1. 初始化模型 '{MODEL_NAME}' (设备: {device})...")
    model = SentenceTransformer(MODEL_NAME, device=device)
    print("[✔] 模型加载成功。")

    print(f"[*] 2. 连接并设置ChromaDB (路径: {CHROMA_DB_PATH})...")
    client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    collection = client.get_or_create_collection(name=COLLECTION_NAME, metadata={"hnsw:space": "cosine"})
    print(f"[✔] ChromaDB集合 '{COLLECTION_NAME}' 准备就绪。")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    papers_to_process = []

    # --- 【核心逻辑：模式选择】 ---
    if PAPER_LIMIT:
        # 模式一：快速测试模式
        print(f"[*] [快速测试模式] 已启用，将强制处理数据库中的前 {PAPER_LIMIT} 篇论文。")
        cursor.execute(f"SELECT rowid, title, abstract, conference, year, source_file FROM papers_fts LIMIT ?",
                       (PAPER_LIMIT,))
        papers_to_process = cursor.fetchall()

    else:
        # 模式二：智能增量模式
        print(f"[*] [智能增量模式] 启动，开始计算需要更新的论文...")

        # 1. 从ChromaDB获取已存在的ID
        existing_ids_in_chroma = set(collection.get(include=[])['ids'])
        print(f"    -> ChromaDB中已存在 {len(existing_ids_in_chroma)} 个向量。")

        # 2. 从SQLite获取所有ID
        cursor.execute("SELECT rowid FROM papers_fts")
        all_ids_in_sqlite = {str(row[0]) for row in cursor.fetchall()}
        print(f"    -> SQLite中总共有 {len(all_ids_in_sqlite)} 篇论文。")

        # 3. 计算差集，得到需要处理的新ID
        new_paper_ids = list(all_ids_in_sqlite - existing_ids_in_chroma)

        if not new_paper_ids:
            print("\n[✔] 数据库已是最新，无需更新。任务结束。")
            conn.close()
            return

        print(f"[✔] 发现 {len(new_paper_ids)} 篇新论文需要处理。")

        # 4. 只从SQLite中获取这些新论文的详细信息
        placeholders = ','.join('?' for _ in new_paper_ids)
        query = f"SELECT rowid, title, abstract, conference, year, source_file FROM papers_fts WHERE rowid IN ({placeholders})"
        cursor.execute(query, new_paper_ids)
        papers_to_process = cursor.fetchall()

    conn.close()

    if not papers_to_process:
        print("[!] 本次运行没有需要处理的论文。任务结束。")
        return

    print(f"[✔] 本次共需处理 {len(papers_to_process)} 篇论文。")

    worker_processes = 2  # 固定使用2个进程
    print(f"[*] 将使用 {worker_processes} 个进程进行并行处理。")

    print("[*] 4. 启动多进程池...")
    pool = model.start_multi_process_pool(target_devices=[device] * worker_processes)
    print("[✔] 进程池已启动。")

    print("[*] 5. 开始并行生成向量...")
    start_time = time.time()

    documents_to_embed = [f"{p[1]}. {p[2]}" for p in papers_to_process]
    embeddings = model.encode_multi_process(documents_to_embed, pool, batch_size=64)

    end_time_encoding = time.time()
    print(f"[✔] 向量生成完毕! 耗时: {end_time_encoding - start_time:.2f} 秒。")

    model.stop_multi_process_pool(pool)
    print("[✔] 进程池已关闭。")

    print("[*] 6. 开始将向量批量存入ChromaDB...")
    start_time_storing = time.time()

    ids = [str(p[0]) for p in papers_to_process]
    metadatas = [{"title": p[1], "conference": p[3], "year": p[4], "source_file": p[5]} for p in papers_to_process]

    # ChromaDB的add方法是幂等的，如果ID已存在，它会更新内容。对于我们的场景，用upsert更语义化。
    db_batch_size = 1024
    for i in range(0, len(papers_to_process), db_batch_size):
        collection.upsert(
            ids=ids[i:i + db_batch_size],
            embeddings=embeddings[i:i + db_batch_size].tolist(),
            metadatas=metadatas[i:i + db_batch_size],
            documents=documents_to_embed[i:i + db_batch_size]
        )

    end_time_storing = time.time()
    print(f"[✔] 数据存储/更新完毕! 耗时: {end_time_storing - start_time_storing:.2f} 秒。")

    print("\n" + "=" * 50)
    print(f"[✔] 所有任务完成！")
    print(f"    - 本次处理论文: {len(papers_to_process)} 篇")
    print(f"    - 向量数据库中的条目总数: {collection.count()}")
    print(f"    - 总耗时: {end_time_storing - start_time:.2f} 秒")
    print("=" * 50)


if __name__ == "__main__":
    try:
        import torch
    except ImportError:
        print("错误: PyTorch 未安装。请运行 'uv pip install torch'")
        exit()

    embed_and_store_parallel()