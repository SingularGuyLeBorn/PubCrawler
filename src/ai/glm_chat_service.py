# FILE: src/ai/glm_chat_service.py (CLI AI Interaction Layer - v1.1)

import sys
from typing import List, Dict, Any

# --- 从 search_service 导入必要的AI相关功能和配置 ---
from src.search.search_service import (
    generate_ai_response,
    AI_CONTEXT_PAPERS,
    ZHIPUAI_API_KEY,
    Colors,  # 颜色定义
    _ai_enabled  # 检查AI是否已初始化成功
)


# --- 定义CLI专属的 print_colored 函数 ---
# 确保在AI对话循环中能够正确打印彩色文本
def print_colored(text, color, end='\n'):
    if sys.stdout.isatty():
        print(f"{color}{text}{Colors.ENDC}", end=end)
    else:
        print(text, end=end)


def start_ai_chat_session(search_results: List[Dict[str, Any]]):
    """
    启动一个AI对话会话，处理CLI中的多轮交互。
    Args:
        search_results (list): 当前搜索结果的论文列表。
    """
    if not ZHIPUAI_API_KEY:
        print_colored("[!] 错误: 未找到 ZHIPUAI_API_KEY。请在 .env 文件中配置。", Colors.FAIL)
        return
    if not _ai_enabled:
        print_colored("[!] 错误: AI客户端初始化失败，无法启动对话。", Colors.FAIL)
        return
    if not search_results:
        print_colored("[!] 没有可供对话的搜索结果，请先执行一次查询。", Colors.WARNING)
        return

    print_colored("\n--- 🤖 AI 对话模式 ---", Colors.HEADER)
    print_colored(f"我已经阅读了与您查询最相关的 {AI_CONTEXT_PAPERS} 篇论文，请就这些论文向我提问。", Colors.OKCYAN)
    print_colored("输入 'exit' 或 'quit' 结束对话。", Colors.OKCYAN)

    messages = []

    initial_assistant_message = "好的，我已经理解了这几篇论文的核心内容。请问您想了解什么？"
    print(f"\nAI助手 > {initial_assistant_message}")
    messages.append({"role": "assistant", "content": initial_assistant_message})

    while True:
        try:
            user_question = input(f"\n{Colors.BOLD}您的问题是?{Colors.ENDC} > ").strip()
            if not user_question: continue
            if user_question.lower() in ['exit', 'quit']: break

            messages.append({"role": "user", "content": user_question})

            print_colored("🤖 GLM-4.5 正在思考...", Colors.OKCYAN, end="", flush=True)

            ai_response_content = generate_ai_response(
                chat_history=messages,
                search_results_context=search_results
            )

            print("\r" + " " * 30 + "\r", end="")  # 清除 "思考中..." 提示

            if ai_response_content.startswith("[!]"):
                print_colored(f"\nAI助手 > {ai_response_content}", Colors.FAIL)
            else:
                print_colored(f"\nAI助手 > {ai_response_content}")
                messages.append({"role": "assistant", "content": ai_response_content})

        except KeyboardInterrupt:
            break
        except Exception as e:
            print_colored(f"\n[!] 调用AI时出错: {e}", Colors.FAIL)
            break