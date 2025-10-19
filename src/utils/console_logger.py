# FILE: src/utils/console_logger.py (Banner Updated)

import logging
import sys

# 尝试导入 colorama，如果失败则优雅降级
try:
    import colorama
    from colorama import Fore, Style, Back

    colorama.init(autoreset=True)

    # 定义颜色常量
    COLORS = {
        'DEBUG': Style.DIM + Fore.WHITE,
        'INFO': Style.NORMAL + Fore.WHITE,
        'WARNING': Style.BRIGHT + Fore.YELLOW,
        'ERROR': Style.BRIGHT + Fore.RED,
        'CRITICAL': Style.BRIGHT + Back.RED + Fore.WHITE,
        'RESET': Style.RESET_ALL,

        # 自定义颜色，用于特殊高亮
        'BANNER_BLUE': Style.BRIGHT + Fore.BLUE,
        'BANNER_CYAN': Style.BRIGHT + Fore.CYAN,
        'BANNER_GREEN': Style.BRIGHT + Fore.GREEN,
        'BANNER_WHITE': Style.BRIGHT + Fore.WHITE,
        'PHASE': Style.BRIGHT + Fore.BLUE,
        'TASK_START': Style.BRIGHT + Fore.MAGENTA,
        'SUCCESS': Style.BRIGHT + Fore.GREEN,
        'STEP': Style.DIM + Fore.WHITE,
    }

    IS_COLORAMA_AVAILABLE = True

except ImportError:
    # 如果没有安装 colorama，则所有颜色代码都为空字符串
    COLORS = {key: '' for key in
              ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL', 'RESET', 'BANNER_BLUE', 'BANNER_CYAN', 'BANNER_GREEN',
               'BANNER_WHITE', 'PHASE', 'TASK_START', 'SUCCESS',
               'STEP']}
    IS_COLORAMA_AVAILABLE = False


class ColoredFormatter(logging.Formatter):
    """
    一个自定义的日志格式化器，用于在控制台输出中添加颜色。
    """

    def __init__(self, fmt, datefmt=None, style='%'):
        super().__init__(fmt, datefmt, style)

    def format(self, record):
        # 获取原始的日志消息
        log_message = super().format(record)

        if IS_COLORAMA_AVAILABLE:
            # 根据日志级别应用不同的颜色
            level_color = COLORS.get(record.levelname, COLORS['INFO'])
            return f"{level_color}{log_message}{COLORS['RESET']}"
        else:
            return log_message


def print_banner():
    """打印项目启动的 ASCII Art 横幅，带有渐变色效果。"""
    banner_text = r"""
  ██████╗ ██╗   ██╗██████╗  ██████╗██████╗  ██╗      ██████╗ ██╗     ███████╗██████╗ 
  ██╔══██╗██║   ██║██╔══██╗██╔════╝██╔══██╗██║     ██╔═══██╗██║     ██╔════╝██╔══██╗
  ██████╔╝██║   ██║██████╔╝██║     ██████╔╝██║     ██║   ██║██║     █████╗  ██████╔╝
  ██╔═══╝ ██║   ██║██╔══██╗██║     ██╔═══╝ ██║     ██║   ██║██║     ██╔══╝  ██╔══██╗
  ██║     ╚██████╔╝██████╔╝╚██████╗██║     ███████╗╚██████╔╝███████╗███████╗██║  ██║
  ╚═╝      ╚═════╝ ╚═════╝  ╚═════╝╚═╝     ╚══════╝ ╚═════╝ ╚══════╝╚══════╝╚═╝  ╚═╝ 
"""
    if IS_COLORAMA_AVAILABLE:
        # 定义渐变色序列
        gradient_colors = [
            COLORS['BANNER_GREEN'],
            COLORS['BANNER_GREEN'],
            COLORS['BANNER_CYAN'],
            COLORS['BANNER_BLUE'],
            COLORS['BANNER_BLUE'],
            COLORS['BANNER_WHITE'],
        ]

        # 按行打印，并应用不同的颜色
        lines = banner_text.strip('\n').split('\n')
        # 确保 banner_text 前后的空行被正确处理
        print()  # 打印一个前置空行
        for i, line in enumerate(lines):
            # 使用 modulo 循环颜色
            color = gradient_colors[i % len(gradient_colors)]
            print(f"{color}{line}{COLORS['RESET']}")
        print()  # 打印一个后置空行

    else:
        # 如果 colorama 不可用，则打印无色版本
        print(banner_text)