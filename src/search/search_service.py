# FILE: src/search/search_service.py (Core Backend Services - v1.1)

import sqlite3
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from pathlib import Path
import time
import re
import torch
from datetime import datetime
from collections import Counter
import os
from dotenv import load_dotenv
from zai import ZhipuAiClient
from typing import List, Dict, Any, Optional, Tuple

# --- 全局配置 (统一管理，其他模块通过导入这个文件来访问) ---
PROJECT_ROOT = Path(__file__).parent.parent.parent
DB_DIR = PROJECT_ROOT / "database"
SEARCH_RESULTS_DIR = PROJECT_ROOT / "search_results"
DB_PATH = DB_DIR / "papers.db"
CHROMA_DB_PATH = str(DB_DIR / "chroma_db")
MODEL_NAME = 'sentence-transformers/all-MiniLM-L6-v2'
COLLECTION_NAME = "papers"
RESULTS_PER_PAGE = 10  # 用于分页的默认值
AI_CONTEXT_PAPERS = 5  # 每次提问时，发送给AI的最相关的论文数量

# --- 加载环境变量 ---
load_dotenv(PROJECT_ROOT / '.env')
ZHIPUAI_API_KEY = os.getenv("ZHIPUAI_API_KEY")

# --- 全局可访问的后端组件实例 (使用单例模式，通过 initialize_components 函数初始化) ---
_sqlite_conn: Optional[sqlite3.Connection] = None
_sentence_transformer_model: Optional[SentenceTransformer] = None
_chroma_collection: Optional[chromadb.api.models.Collection.Collection] = None
_zhipu_ai_client: Optional[ZhipuAiClient] = None
_ai_enabled: bool = False
_initialized: bool = False  # 标记是否已初始化


# --- 颜色定义 (保留在服务层，作为通用常量) ---
class Colors:
    HEADER = '\033[95m';
    OKBLUE = '\033[94m';
    OKCYAN = '\033[96m';
    OKGREEN = '\033[92m'
    WARNING = '\033[93m';
    FAIL = '\033[91m';
    ENDC = '\033[0m';
    BOLD = '\033[1m';
    UNDERLINE = '\033[4m'


# --- 初始化函数 (所有后端组件的单一入口，确保只初始化一次) ---
def initialize_components() -> None:
    """
    初始化所有搜索和AI后端组件。确保只运行一次。
    此函数会打印状态信息，但颜色和输出方式由调用者决定。
    """
    global _sqlite_conn, _sentence_transformer_model, _chroma_collection, _zhipu_ai_client, _ai_enabled, _initialized

    if _initialized:
        # print("搜索后端服务已初始化，跳过重复初始化。") # 调试用
        return

    print(f"[{Colors.OKBLUE}*{Colors.ENDC}] 正在初始化搜索后端服务...")

    # 1. 初始化SQLite连接
    try:
        _sqlite_conn = sqlite3.connect(str(DB_PATH), uri=True, check_same_thread=False)
        print(f"[{Colors.OKGREEN}✔{Colors.ENDC}] SQLite数据库 '{DB_PATH.name}' 连接成功。")
    except Exception as e:
        print(f"[{Colors.FAIL}✖{Colors.ENDC}] 错误: 无法连接SQLite数据库: {e}")
        _sqlite_conn = None
        _initialized = True
        return

        # 2. 初始化SentenceTransformer模型和ChromaDB
    try:
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        _sentence_transformer_model = SentenceTransformer(MODEL_NAME, device=device)
        print(f"[{Colors.OKGREEN}✔{Colors.ENDC}] SentenceTransformer模型 '{MODEL_NAME}' ({device}) 加载成功。")

        _chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH, settings=Settings(anonymized_telemetry=False))
        _chroma_collection = _chroma_client.get_or_create_collection(name=COLLECTION_NAME,
                                                                     metadata={"hnsw:space": "cosine"})
        print(
            f"[{Colors.OKGREEN}✔{Colors.ENDC}] ChromaDB集合 '{COLLECTION_NAME}' ({_chroma_collection.count()} 个向量) 已加载。")
    except Exception as e:
        print(f"[{Colors.FAIL}✖{Colors.ENDC}] 错误: 无法初始化语义搜索组件: {e}")
        _sentence_transformer_model = None
        _chroma_collection = None
        _initialized = True
        if _sqlite_conn: _sqlite_conn.close()
        return

    # 3. 初始化智谱AI客户端
    if ZHIPUAI_API_KEY:
        try:
            _zhipu_ai_client = ZhipuAiClient(api_key=ZHIPUAI_API_KEY)
            _ai_enabled = True
            print(f"[{Colors.OKGREEN}✔{Colors.ENDC}] 智谱AI客户端初始化成功。")
        except Exception as e:
            print(f"[{Colors.WARNING}⚠{Colors.ENDC}] 警告: 无法初始化智谱AI客户端: {e}. AI对话功能将不可用。")
            _zhipu_ai_client = None
            _ai_enabled = False
    else:
        print(f"[{Colors.WARNING}⚠{Colors.ENDC}] 警告: 未设置 ZHIPUAI_API_KEY. AI对话功能将不可用。")
        _ai_enabled = False

    _initialized = True
    print(f"[{Colors.OKBLUE}*{Colors.ENDC}] 搜索后端服务初始化完成。")


# --- 核心搜索功能 ---

def keyword_search(raw_query: str) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    执行关键词搜索，返回结果列表和统计摘要。
    """
    if not _initialized or _sqlite_conn is None:
        return [], {"error": "搜索服务未初始化或SQLite连接失败。"}

    COLUMN_MAP = {'author': 'authors', 'title': 'title', 'abstract': 'abstract'}
    parsed_query_parts = []
    pattern = re.compile(r'(\b\w+):(?:"([^"]*)"|(\S+))')
    remaining_query = raw_query

    for match in list(pattern.finditer(raw_query)):
        full_match_text = match.group(0)
        field_alias = match.group(1).lower()
        value = match.group(2) if match.group(2) is not None else match.group(3)
        if field_alias in COLUMN_MAP:
            db_column = COLUMN_MAP[field_alias]
            safe_value = value.replace('"', '""')
            if ' ' in value or not value.isalnum():
                parsed_query_parts.append(f'{db_column}:"{safe_value}"')
            else:
                parsed_query_parts.append(f'{db_column}:{safe_value}')
            remaining_query = re.sub(re.escape(full_match_text), '', remaining_query, 1)

    general_terms = re.findall(r'"[^"]*"|\S+', remaining_query.strip())
    for term in general_terms:
        safe_term = term.replace('"', '""')
        if term.startswith('"') and term.endswith('"'):
            parsed_query_parts.append(f'{safe_term}')
        else:
            parsed_query_parts.append(safe_term)

    final_fts_query = ' AND '.join(filter(None, parsed_query_parts))

    if not final_fts_query:
        return [], {"total_found": 0, "distribution": {}, "message": "关键词搜索查询为空或解析失败。"}

    try:
        cursor = _sqlite_conn.execute(
            "SELECT title, authors, abstract, conference, year FROM papers_fts WHERE papers_fts MATCH ? ORDER BY rank",
            (final_fts_query,)
        )
        raw_results = cursor.fetchall()
        results = [{"title": r[0], "authors": r[1], "abstract": r[2], "conference": r[3], "year": r[4]} for r in
                   raw_results]

        stats = get_stats_summary(results)
        stats['message'] = f"关键词搜索完成，找到 {len(results)} 篇。"
        return results, stats
    except sqlite3.OperationalError as e:
        return [], {"total_found": 0, "distribution": {},
                    "message": f"关键词搜索失败: {e}. FTS5 Query: '{final_fts_query}'"}


def semantic_search(query: str, top_n: int = 20) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    执行语义搜索，返回结果列表和统计摘要。
    """
    if not _initialized or _sentence_transformer_model is None or _chroma_collection is None or _sqlite_conn is None:
        return [], {"error": "搜索服务未初始化或组件失败。"}

    start_t = time.time()
    query_embedding = _sentence_transformer_model.encode(query, convert_to_tensor=False)
    chroma_results = _chroma_collection.query(query_embeddings=[query_embedding.tolist()], n_results=top_n)

    ids_found, distances = chroma_results['ids'][0], chroma_results['distances'][0]
    if not ids_found: return [], get_stats_summary([])

    placeholders = ','.join('?' for _ in ids_found)
    sql_query = f"SELECT rowid, title, authors, abstract, conference, year FROM papers_fts WHERE rowid IN ({placeholders})"
    cursor = _sqlite_conn.cursor()
    raw_sqlite_results = {str(r[0]): r[1:] for r in cursor.execute(sql_query, ids_found).fetchall()}

    final_results = []
    for i, paper_id in enumerate(ids_found):
        details = raw_sqlite_results.get(paper_id)
        if details:
            final_results.append({
                "title": details[0],
                "authors": details[1],
                "abstract": details[2],
                "conference": details[3],
                "year": details[4],
                "similarity": 1 - distances[i]
            })
    end_t = time.time()

    stats = get_stats_summary(final_results)
    stats['message'] = f"语义搜索完成 (耗时: {end_t - start_t:.4f} 秒, 找到 {len(final_results)} 篇)。"
    return final_results, stats


# --- 辅助功能 (与CLI和Web UI共享) ---

def get_stats_summary(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    生成查询结果的统计摘要。
    """
    total_found = len(results)

    conf_year_counter = Counter([(p.get('conference', 'N/A'), p.get('year', 'N/A')) for p in results])
    distribution = {f"{conf} {year}": count for (conf, year), count in conf_year_counter.most_common()}

    return {"total_found": total_found, "distribution": distribution}


def format_papers_for_prompt(papers: List[Dict[str, Any]]) -> str:
    """将论文列表格式化为清晰的字符串，作为AI的上下文。"""
    context = ""
    for i, paper in enumerate(papers, 1):
        context += f"[论文 {i}]\n"
        context += f"标题: {paper.get('title', 'N/A')}\n"
        context += f"作者: {paper.get('authors', 'N/A')}\n"
        context += f"摘要: {paper.get('abstract', 'N/A')}\n\n"
    return context


def save_results_to_markdown(results: List[Dict[str, Any]], query: str) -> str:
    """将搜索结果保存为Markdown文件。"""
    if not results: return "没有搜索结果可保存。"

    session_dir = SEARCH_RESULTS_DIR / f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    session_dir.mkdir(exist_ok=True)

    safe_query = re.sub(r'[\\/*?:"<>|]', "", query).replace(" ", "_")[:50]
    filename = session_dir / f"search_{safe_query}.md"

    with open(filename, 'w', encoding='utf-8') as f:
        f.write(f"# 搜索查询: \"{query}\"\n\n**共找到 {len(results)} 条相关结果**\n\n---\n\n")
        for idx, paper in enumerate(results, 1):
            title, authors, abstract = paper.get('title', 'N/A'), paper.get('authors', 'N/A'), paper.get('abstract',
                                                                                                         'N/A')
            conf, year = paper.get('conference', 'N/A'), paper.get('year', 'N/A')
            similarity_str = f"- **语义相似度**: {paper['similarity']:.2f}\n" if 'similarity' in paper else ""
            f.write(
                f"### {idx}. {title}\n\n- **作者**: {authors}\n- **会议/年份**: {conf} {year}\n{similarity_str}\n**摘要:**\n> {abstract}\n\n---\n\n")

    return f"结果已保存到: {filename.resolve()}"


# --- AI响应生成器 (服务模块的核心逻辑) ---
def generate_ai_response(chat_history: List[Dict[str, str]], search_results_context: List[Dict[str, Any]]) -> str:
    """
    根据搜索结果上下文和聊天历史生成AI响应。
    chat_history: 仅包含用户消息和AI响应，不包含系统消息和初始背景。
    search_results_context: 原始的论文结果列表。
    """
    global _ai_enabled, _zhipu_ai_client  # 确保可以访问全局变量

    if not _ai_enabled or _zhipu_ai_client is None:
        return "[!] 错误: AI对话功能未启用或智谱AI客户端初始化失败，请检查您的ZHIPUAI_API_KEY。"
    if not search_results_context:
        return "[!] 没有可供AI对话的搜索结果上下文。"

    context_papers = search_results_context[:AI_CONTEXT_PAPERS]
    formatted_context = format_papers_for_prompt(context_papers)

    full_messages = [
        {"role": "system",
         "content": "你是一个专业的AI学术研究助手。请根据下面提供的论文摘要信息，精准、深入地回答用户的问题。你的回答必须严格基于提供的材料，不要编造信息。"},
        {"role": "user", "content": f"这是我为你提供的背景知识，请仔细阅读：\n\n{formatted_context}"},
        {"role": "assistant", "content": "好的，我已经理解了这几篇论文的核心内容。请问您想了解什么？"}
    ]
    full_messages.extend(chat_history)

    try:
        response_generator = _zhipu_ai_client.chat.completions.create(
            model="glm-4.5-flash",
            messages=full_messages,
            stream=True,
            temperature=0.7,
        )

        full_response_content = ""
        for chunk in response_generator:
            delta_content = chunk.choices[0].delta.content
            if delta_content:
                full_response_content += delta_content
        return full_response_content
    except Exception as e:
        return f"[!] 调用AI时出错: {e}"


# 模块加载时自动初始化组件 (确保在任何函数被调用前完成)
initialize_components()