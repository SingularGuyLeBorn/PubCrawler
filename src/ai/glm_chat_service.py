# FILE: src/ai/ai_chat_service.py

import os
from dotenv import load_dotenv
from zai import ZhipuAiClient
import sys

# --- 配置 (从主脚本中提取) ---
PROJECT_ROOT = Path(__file__).parent.parent.parent  # 假设ai/ai_chat_service.py在src/ai下
load_dotenv(PROJECT_ROOT / '.env')
ZHIPUAI_API_KEY = os.getenv("ZHIPUAI_API_KEY")
AI_CONTEXT_PAPERS = 5  # 每次提问时，发送给AI的最相关的论文数量


# --- 颜色和打印函数 (从主脚本中提取) ---
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


def print_colored(text, color):
    # 此函数不应接收 'end' 参数
    if sys.stdout.isatty():
        print(f"{color}{text}{Colors.ENDC}")
    else:
        print(text)


def format_papers_for_prompt(papers):
    """将论文列表格式化为清晰的字符串，作为AI的上下文。"""
    context = ""
    for i, paper in enumerate(papers, 1):
        context += f"[论文 {i}]\n"
        context += f"标题: {paper.get('title', 'N/A')}\n"
        context += f"作者: {paper.get('authors', 'N/A')}\n"
        context += f"摘要: {paper.get('abstract', 'N/A')}\n\n"
    return context


def start_ai_chat_session(search_results: list):
    """
    启动一个AI对话会话。
    Args:
        search_results (list): 当前搜索结果的论文列表。
    """
    if not ZHIPUAI_API_KEY:
        print_colored("[!] 错误: 未找到 ZHIPUAI_API_KEY。请在 .env 文件中配置。", Colors.FAIL)
        return
    if not search_results:
        print_colored("[!] 没有可供对话的搜索结果，请先执行一次查询。", Colors.WARNING)
        return

    client = ZhipuAiClient(api_key=ZHIPUAI_API_KEY)

    context_papers = search_results[:AI_CONTEXT_PAPERS]
    formatted_context = format_papers_for_prompt(context_papers)

    print_colored("\n--- 🤖 AI 对话模式 ---", Colors.HEADER)
    print_colored(f"我已经阅读了与您查询最相关的 {len(context_papers)} 篇论文，请就这些论文向我提问。", Colors.OKCYAN)
    print_colored("输入 'exit' 或 'quit' 结束对话。", Colors.OKCYAN)

    messages = [
        {"role": "system",
         "content": "你是一个专业的AI学术研究助手。请根据下面提供的论文摘要信息，精准、深入地回答用户的问题。你的回答必须严格基于提供的材料，不要编造信息。"},
        {"role": "user", "content": f"这是我为你提供的背景知识，请仔细阅读：\n\n{formatted_context}"},
        {"role": "assistant", "content": "好的，我已经理解了这几篇论文的核心内容。请问您想了解什么？"}
    ]

    while True:
        try:
            user_question = input(f"\n{Colors.BOLD}您的问题是?{Colors.ENDC} > ").strip()
            if not user_question: continue
            if user_question.lower() in ['exit', 'quit']: break

            messages.append({"role": "user", "content": user_question})

            # 使用 print() 来打印彩色文本并带 end=""，因为 print_colored 不支持 end
            print(f"{Colors.OKCYAN}🤖 GLM-4.5 正在思考...{Colors.ENDC}", end="", flush=True)

            response = client.chat.completions.create(
                model="glm-4.5-flash",
                messages=messages,
                stream=True,
                temperature=0.7,
            )

            print("\r" + " " * 30 + "\r", end="")  # 清除 "思考中..." 提示

            full_response = ""
            for chunk in response:
                delta_content = chunk.choices[0].delta.content
                if delta_content:
                    print(delta_content, end="", flush=True)
                    full_response += delta_content

            print()  # 换行
            messages.append({"role": "assistant", "content": full_response})

        except KeyboardInterrupt:
            break
        except Exception as e:
            print_colored(f"\n[!] 调用AI时出错: {e}", Colors.FAIL)
            break


# 这是为了在ai_chat_service.py文件中也能访问到Path对象
from pathlib import Path