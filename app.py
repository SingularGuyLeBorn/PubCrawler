# FILE: app.py (Gradio Web UI for PubCrawler - v1.2.3 - Final Fixes)

import gradio as gr
import sys
import textwrap
from typing import List, Dict, Any, Tuple

# --- 从 search_service 导入所有功能和配置 ---
from src.search.search_service import (
    initialize_components,
    keyword_search,
    semantic_search,
    save_results_to_markdown,
    generate_ai_response,
    _sqlite_conn,
    _initialized,
    ZHIPUAI_API_KEY,
    SEARCH_RESULTS_DIR
)

# Gradio启动时调用初始化函数 (确保在任何函数被Gradio调用前完成)
initialize_components()

# --- Gradio UI 核心逻辑 ---

# 全局变量用于存储当前搜索结果，以便AI和保存功能访问
current_search_results: List[Dict[str, Any]] = []
current_query_string: str = ""


def perform_search_and_reset_chat(query_input: str) -> Tuple[
    gr.Dataframe, str, str, gr.Column, gr.Accordion, gr.Button]:
    """
    在Gradio UI中执行搜索并更新UI组件。
    """
    global current_search_results, current_query_string
    current_query_string = query_input
    current_search_results = []

    results: List[Dict[str, Any]] = []
    stats: Dict[str, Any] = {"total_found": 0, "distribution": {}, "message": "搜索未执行。"}

    if not _initialized:
        error_msg = "后端服务未成功初始化。"
        return gr.Dataframe(value=[]), error_msg, "初始化失败，无法搜索。", gr.Column(visible=False), gr.Accordion(
            open=False), gr.Button(interactive=False)

    if query_input.lower().startswith('sem:'):
        semantic_query = query_input[4:].strip()
        if semantic_query:
            results, stats = semantic_search(semantic_query)
        else:
            stats['message'] = "语义搜索查询内容不能为空。"
    else:
        results, stats = keyword_search(query_input)

    current_search_results = results

    # 格式化统计信息
    stats_markdown = f"**总计找到 {stats['total_found']} 篇相关论文。**\n\n"
    if stats['distribution']:
        stats_markdown += "**分布情况:**\n"
        for conf_year, count in stats['distribution'].items():
            stats_markdown += f"- {conf_year}: {count} 篇\n"
    else:
        stats_markdown += "无结果分布信息。\n"

    # 格式化结果为Gradio表格
    table_data = []
    for paper in results:
        authors = textwrap.shorten(paper.get('authors', 'N/A'), width=50, placeholder="...")
        title = textwrap.shorten(paper.get('title', 'N/A'), width=80, placeholder="...")
        similarity = f"{paper['similarity']:.2f}" if 'similarity' in paper and paper[
            'similarity'] is not None else "N/A"
        table_data.append([title, authors, paper.get('conference', 'N/A'), paper.get('year', 'N/A'), similarity])

    # 根据是否有结果和API Key来决定AI按钮是否可用
    ai_button_interactive = bool(results and ZHIPUAI_API_KEY)

    return (gr.Dataframe(value=table_data, headers=["标题", "作者", "会议", "年份", "相似度"]),
            stats.get('message', "搜索完成。"),
            stats_markdown,
            gr.Column(visible=False),
            gr.Accordion(open=False),
            gr.Button(interactive=ai_button_interactive))


def save_current_results_gradio() -> str:
    """
    Gradio UI中保存当前搜索结果的回调函数。
    """
    global current_search_results, current_query_string
    if not current_search_results:
        return "没有搜索结果可保存。"
    return save_results_to_markdown(current_search_results, current_query_string)


# --- 【重要修改】: AI 对话函数适配 `type="messages"` ---
def handle_chat_interaction(user_message: str, chat_history: List[Dict[str, str]]):
    """
    处理用户的聊天输入，调用AI服务，并返回响应。
    现在的 chat_history 是一个字典列表，例如: [{"role": "user", "content": "你好"}]
    """
    global current_search_results
    if not current_search_results:
        chat_history.append({"role": "user", "content": user_message})
        chat_history.append({"role": "assistant", "content": "错误：没有可供对话的搜索结果。"})
        return chat_history

    chat_history.append({"role": "user", "content": user_message})

    # generate_ai_response 函数本身就需要这种格式，所以现在无需转换
    ai_response = generate_ai_response(
        chat_history=chat_history,
        search_results_context=current_search_results
    )

    chat_history.append({"role": "assistant", "content": ai_response})
    return chat_history


def clear_chat():
    """清空聊天记录"""
    return [], ""


# --- Gradio UI 布局 ---
with gr.Blocks(title="PubCrawler AI Assistant") as demo:
    gr.Markdown(
        """
        # 📚 PubCrawler AI 学术助手
        欢迎使用 PubCrawler！在这里，您可以搜索学术论文，查看统计信息，并将结果保存或与AI进行对话。

        ---

        ### 搜索语法:
        - `关键词` 或 `短语` (例如: `transformer`, `"large language model"`)
        - `字段搜索`: `author:vaswani`, `title:"vision transformer"`, `abstract:diffusion`
        - `逻辑组合`: `transformer AND author:vaswani`, `"large language model" OR efficient`
        - `语义搜索`: 在查询前加上 `sem:` (例如: `sem: efficiency of few-shot learning`)
        """
    )

    with gr.Row():
        query_input = gr.Textbox(
            label="请输入您的查询",
            placeholder="例如: transformer author:vaswani 或 sem: efficiency of few-shot learning",
            scale=4
        )
        search_button = gr.Button("搜索", variant="primary", scale=1)

    status_output = gr.Textbox(label="状态/消息", interactive=False)

    with gr.Row():
        stats_markdown_output = gr.Markdown(
            value="--- 查询结果统计 --- \n总计找到 0 篇相关论文。\n无结果分布信息。",
            label="结果统计"
        )

    results_dataframe = gr.Dataframe(
        headers=["标题", "作者", "会议", "年份", "相似度"],
        col_count=(5, "fixed"),
        interactive=False,
        label="搜索结果"
    )

    with gr.Row():
        save_button = gr.Button("保存当前结果到 Markdown")
        start_chat_button = gr.Button("与AI对话 (需先搜索)", interactive=False)

    with gr.Accordion("🤖 AI 对话窗口", open=False) as chat_accordion:
        with gr.Column(visible=True) as chat_interface_column:
            # 【重要修改】: 修复 UserWarning
            chatbot = gr.Chatbot(label="与AI的对话", type="messages")
            chat_input = gr.Textbox(label="你的问题", placeholder="例如：请总结一下这些论文的核心贡献。")
            with gr.Row():
                chat_submit_btn = gr.Button("发送", variant="primary")
                chat_clear_btn = gr.Button("清除对话")

    # --- 绑定事件 ---
    search_button.click(
        fn=perform_search_and_reset_chat,
        inputs=query_input,
        outputs=[results_dataframe, status_output, stats_markdown_output, chat_interface_column, chat_accordion,
                 start_chat_button]
    )

    query_input.submit(
        fn=perform_search_and_reset_chat,
        inputs=query_input,
        outputs=[results_dataframe, status_output, stats_markdown_output, chat_interface_column, chat_accordion,
                 start_chat_button]
    )

    save_button.click(
        fn=save_current_results_gradio,
        inputs=[],
        outputs=status_output
    )

    start_chat_button.click(
        fn=lambda: (gr.Accordion(open=True), gr.Column(visible=True)),
        inputs=None,
        outputs=[chat_accordion, chat_interface_column]
    )

    chat_submit_btn.click(
        fn=handle_chat_interaction,
        inputs=[chat_input, chatbot],
        outputs=[chatbot]
    ).then(lambda: "", inputs=None, outputs=chat_input)

    chat_input.submit(
        fn=handle_chat_interaction,
        inputs=[chat_input, chatbot],
        outputs=[chatbot]
    ).then(lambda: "", inputs=None, outputs=chat_input)

    chat_clear_btn.click(
        fn=clear_chat,
        inputs=None,
        outputs=[chatbot, chat_input]
    )

# 运行Gradio应用
if __name__ == "__main__":
    if not _initialized:
        print(f"无法启动Gradio应用，后端初始化失败。请检查错误信息。")
        sys.exit(1)
    else:
        SEARCH_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        # 【重要修改】: 添加 inbrowser=True
        demo.launch(share=True, inbrowser=True)
