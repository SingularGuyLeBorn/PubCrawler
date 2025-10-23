# FILE: src/utils/console_logger.py (Banner Updated to Tech Pattern)

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
        'STEP': Style.DIM + Fore.WHITE,  # <-- 我们会用这个
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
    """打印项目启动的 ASCII Art 横幅 (科技感图案版)。"""

    # -------------------【修改点在这里】-------------------
    # 按用户要求，改为科技感图案，放弃大字母块
    # V7: 科技-网络节点 (亮蓝色/亮白色)

    # 我们使用 f-string 来嵌入颜色代码
    banner_art = f"""
{COLORS['BANNER_BLUE']}
        .--.
       / .. \\
    --(  PC  )--  {COLORS['BANNER_WHITE']}PubCrawler{COLORS['RESET']}
       \\ .. /    {COLORS['STEP']}[Initializing...]{COLORS['RESET']}
        '--'
{COLORS['RESET']}
"""

    # -------------------【修改结束】-------------------

    if IS_COLORAMA_AVAILABLE:
        print(banner_art)  # 直接打印包含颜色的 f-string

    else:
        # 如果 colorama 不可用，打印一个手动去除颜色代码的无色版本
        no_color_art = r"""
        .--.
       / .. \
    --(  PC  )--  PubCrawler
       \ .. /    [Initializing...]
        '--'
"""
        print(no_color_art)