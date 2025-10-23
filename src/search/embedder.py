# FILE: src/search/embedder.py (API Version with .env)
# 【已修改】添加了更强的速率限制和智能重试逻辑

import sqlite3
import numpy as np
import requests
import time
from pathlib import Path
from tqdm import tqdm
import os
from dotenv import load_dotenv

# --- 配置 ---
PROJECT_ROOT = Path(__file__).parent.parent.parent
DB_PATH = PROJECT_ROOT / "papers.db"
API_URL = "https://api-inference.huggingface.co/models/sentence-transformers/all-MiniLM-L6-v2"

# --- 【核心修改】从 .env 文件加载环境变量 ---
load_dotenv(dotenv_path=PROJECT_ROOT / '.env')
HF_API_TOKEN = os.getenv("HF_API_TOKEN")

if not HF_API_TOKEN:
    print("！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！")
    print("错误: 未能从 .env 文件中加载 HF_API_TOKEN。")
    print("请确保在项目根目录创建了 .env 文件，并写入 HF_API_TOKEN=\"hf_...\"")
    print("！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！")
    exit()

HEADERS = {"Authorization": f"Bearer {HF_API_TOKEN}"}


def create_embeddings_table(conn):
    cursor = conn.cursor()
    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS embeddings
                   (
                       paper_id
                       INTEGER
                       PRIMARY
                       KEY,
                       embedding
                       BLOB
                       NOT
                       NULL
                   )
                   """)
    conn.commit()


def get_embedding_from_api(text: str, max_retries=5):
    payload = {"inputs": text, "options": {"wait_for_model": True}}
    for attempt in range(max_retries):
        try:
            response = requests.post(API_URL, headers=HEADERS, json=payload, timeout=60)
            if response.status_code == 429:
                wait_time = 60
                print(f"\n[警告] 速率限制 (429)。暂停 {wait_time} 秒...")
                time.sleep(wait_time)
                continue
            if response.status_code in [404, 401, 403]:
                print(f"\n[致命] 错误 {response.status_code}: 检查 URL/Token。响应: {response.text}")
                return None
            response.raise_for_status()
            result = response.json()
            if isinstance(result, list) and isinstance(result[0], list):
                return np.array(result[0], dtype=np.float32)
            else:
                if 'error' in result:
                    print(f"\n[警告] 错误: {result['error']}. 重试...")
                    time.sleep(15 * (attempt + 1))
                    continue
                raise ValueError(f"意外格式: {result}")
        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                wait_time = 10 * (attempt + 1)
                print(f"\n[警告] 失败 ({e})。重试 {wait_time} 秒...")
                time.sleep(wait_time)
            else:
                print("\n[错误] 最大重试失败。")
                return None
        except (ValueError, KeyError) as e:
            print(f"\n[错误] 处理响应出错: {e}")
            return None
    return None


def generate_and_store_embeddings():
    if not DB_PATH.exists():
        print(f"[!] 错误: 数据库文件 {DB_PATH} 不存在。")
        return

    print("[*] 开始通过 API 生成语义向量 (已启用限速模式)...")
    conn = sqlite3.connect(str(DB_PATH))
    create_embeddings_table(conn)
    cursor = conn.cursor()

    cursor.execute("SELECT rowid, title, abstract FROM papers_fts")
    papers = cursor.fetchall()
    if not papers:
        print("[!] 数据库中没有论文。")
        conn.close()
        return

    print(f"[*] 共找到 {len(papers)} 篇论文，开始逐一请求 API 生成向量...")

    embedding_data = []
    failed_papers = 0

    for paper in tqdm(papers, desc="生成向量 (API限速)"):
        paper_id, title, abstract = paper
        text_to_embed = f"{title}. {abstract}"

        embedding = get_embedding_from_api(text_to_embed)

        if embedding is not None:
            embedding_blob = embedding.tobytes()
            embedding_data.append((paper_id, embedding_blob))
        else:
            failed_papers += 1

        # --- [核心修复 2]：主动限速 ---
        # 0.1秒太快了！免费API绝对会封禁你。
        # 我们在每次请求后强制等待 3 秒，以尊重API限制。
        time.sleep(1)

    print(f"[*] 向量生成完毕，正在存入数据库... (成功: {len(embedding_data)}, 失败: {failed_papers})")

    if embedding_data:
        cursor.executemany(
            "INSERT OR REPLACE INTO embeddings (paper_id, embedding) VALUES (?, ?)",
            embedding_data
        )
        conn.commit()

    conn.close()

    print(f"\n[✔] 任务完成！")


if __name__ == "__main__":
    generate_and_store_embeddings()