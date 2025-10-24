# FILE: src/api/main.py (FastAPI Backend for PubCrawler)

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import sys

# --- 从 search_service 导入核心逻辑和初始化函数 ---
from src.search.search_service import (
    keyword_search,
    semantic_search,
    get_stats_summary,
    generate_ai_response,
    _initialize_search_components,
    _sqlite_conn  # 用于FastAPI关闭时关闭连接
)
from src.search.search_service import ZHIPUAI_API_KEY  # 导入API Key，用于检查AI可用性

# --- FastAPI 应用实例 ---
app = FastAPI(
    title="PubCrawler AI Assistant API",
    description="为AI学术研究助手提供搜索、统计和AI对话功能。",
    version="1.0.0",
)


# --- Pydantic 模型用于请求体和响应 ---
class SearchQuery(BaseModel):
    query: str = Field(..., description="搜索查询字符串，以 'sem:' 开头表示语义搜索，否则为关键词搜索。")
    top_n: int = Field(20, description="语义搜索时返回的最相关论文数量。", ge=1, le=100)


class SearchResultPaper(BaseModel):
    title: str
    authors: str
    abstract: str
    conference: str
    year: str
    similarity: Optional[float] = None  # 语义搜索结果可能包含相似度


class SearchStats(BaseModel):
    total_found: int
    distribution: Dict[str, int]


class SearchResponse(BaseModel):
    results: List[SearchResultPaper]
    stats: SearchStats
    message: str = "搜索成功。"


class AIChatMessage(BaseModel):
    role: str
    content: str


class AIChatRequest(BaseModel):
    chat_history: List[AIChatMessage] = Field(..., description="之前的聊天历史，不包含当前用户消息。")
    current_message: str = Field(..., description="用户当前的最新消息。")
    search_results_context: List[SearchResultPaper] = Field(..., description="提供给AI作为上下文的搜索结果论文列表。")


class AIChatResponse(BaseModel):
    response: str
    message: str = "AI响应成功。"


# --- 生命周期事件 (启动时初始化组件，关闭时清理资源) ---
@app.on_event("startup")
async def startup_event():
    print("[*] FastAPI应用启动中，正在初始化搜索组件...")
    try:
        _initialize_search_components()
        print("[✔] 搜索组件初始化完成。")
    except Exception as e:
        print(f"[✖] 搜索组件初始化失败: {e}")
        # 这里可以选择终止应用启动，或者在后续API调用中处理错误


@app.on_event("shutdown")
async def shutdown_event():
    print("[*] FastAPI应用关闭中，正在清理资源...")
    if _sqlite_conn:
        _sqlite_conn.close()
        print("[✔] SQLite连接已关闭。")


# --- API 路由 ---
@app.post("/search", response_model=SearchResponse)
async def perform_search(search_query: SearchQuery):
    """
    执行关键词或语义搜索，并返回论文列表及统计信息。
    - 以 'sem:' 开头的查询字符串将触发语义搜索。
    - 其他查询字符串将触发关键词搜索。
    """
    query_text = search_query.query.strip()

    if query_text.lower().startswith('sem:'):
        actual_query = query_text[4:].strip()
        if not actual_query:
            raise HTTPException(status_code=400, detail="语义搜索查询内容不能为空。")
        results = semantic_search(actual_query, top_n=search_query.top_n)
    else:
        results = keyword_search(query_text)

    if not results:
        return SearchResponse(results=[], stats={"total_found": 0, "distribution": {}}, message="未找到相关结果。")

    stats_summary = get_stats_summary(results)
    return SearchResponse(results=results, stats=stats_summary, message="搜索成功。")


@app.post("/chat", response_model=AIChatResponse)
async def chat_with_ai(chat_request: AIChatRequest):
    """
    与AI助手进行对话，提供聊天历史和搜索结果作为上下文。
    """
    if not ZHIPUAI_API_KEY:
        raise HTTPException(status_code=503, detail="智谱AI API Key未配置，AI服务不可用。")

    if not chat_request.search_results_context:
        raise HTTPException(status_code=400, detail="未提供搜索结果上下文，AI无法进行对话。")

    # 构造完整的消息历史，包括系统消息和用户背景消息，然后传入AI服务
    # generate_ai_response 函数会处理系统消息和背景知识的注入

    # chat_history 包含之前的对话，current_message 是用户最新输入
    full_chat_history_for_service = chat_request.chat_history + [
        {"role": "user", "content": chat_request.current_message}]

    ai_response_text = generate_ai_response(
        chat_history=full_chat_history_for_service,
        search_results_context=[p.dict() for p in chat_request.search_results_context]  # 确保传递的是字典列表
    )

    if ai_response_text.startswith("[!]"):
        raise HTTPException(status_code=500, detail=ai_response_text)

    return AIChatResponse(response=ai_response_text)