# FILE: src/config.py (Structured Logging)

import logging
from pathlib import Path

# 导入 Tqdm 日志处理器和彩色格式化器
from src.utils.tqdm_logger import TqdmLoggingHandler
from src.utils.console_logger import ColoredFormatter, COLORS

# --- Project Structure ---
ROOT_DIR = Path(__file__).parent.parent
OUTPUT_DIR = ROOT_DIR / "output"
LOG_DIR = ROOT_DIR / "logs"
CONFIG_FILE = ROOT_DIR / "configs" / "tasks.yaml"

METADATA_OUTPUT_DIR = OUTPUT_DIR / "metadata"
PDF_DOWNLOAD_DIR = OUTPUT_DIR / "pdfs"
TRENDS_OUTPUT_DIR = OUTPUT_DIR / "trends"

# --- Create Directories ---
OUTPUT_DIR.mkdir(exist_ok=True)
LOG_DIR.mkdir(exist_ok=True)
(ROOT_DIR / "configs").mkdir(exist_ok=True)
METADATA_OUTPUT_DIR.mkdir(exist_ok=True)
PDF_DOWNLOAD_DIR.mkdir(exist_ok=True)
TRENDS_OUTPUT_DIR.mkdir(exist_ok=True)


# --- Logging Configuration (核心修改点) ---
def get_logger(name: str, log_file: Path = LOG_DIR / "pubcrawler.log") -> logging.Logger:
    """
    配置并返回一个日志记录器。
    - 控制台输出: 简洁、彩色、结构化的信息。
    - 文件输出: 包含完整 Traceback 的详细信息，用于调试。
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)

        # 1. 控制台处理器 (使用 Tqdm 安全处理器和新的结构化彩色格式)
        tqdm_handler = TqdmLoggingHandler()
        tqdm_handler.setLevel(logging.INFO)
        # --- 新的结构化格式 ---
        # %(levelname)s 会被 ColoredFormatter 转换成带颜色的标识
        console_format = f"{COLORS['STEP']}[%(levelname)s]{COLORS['RESET']} %(message)s"
        console_formatter = ColoredFormatter(console_format)
        tqdm_handler.setFormatter(console_formatter)

        # 2. 文件处理器 (保持不变，用于记录全部细节)
        file_handler = logging.FileHandler(log_file, 'a', encoding='utf-8') # 使用 'a' 模式追加日志
        file_handler.setLevel(logging.INFO)
        file_format = '%(asctime)s - %(name)s - [%(levelname)s] - %(message)s'
        file_formatter = logging.Formatter(file_format)
        file_handler.setFormatter(file_formatter)

        logger.addHandler(tqdm_handler)
        logger.addHandler(file_handler)

        logger.propagate = False # 防止日志向上传播到 root logger

    return logger