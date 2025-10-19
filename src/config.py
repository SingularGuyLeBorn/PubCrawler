# FILE: src/config.py (应用了 Tqdm 安全日志)

import logging
import sys
from pathlib import Path

# 导入新的 Tqdm 日志处理器
from src.utils.tqdm_logger import TqdmLoggingHandler
# 保留彩色格式化器，因为它将被 Tqdm 处理器使用
from src.utils.console_logger import ColoredFormatter

# --- Project Structure ---
ROOT_DIR = Path(__file__).parent.parent
OUTPUT_DIR = ROOT_DIR / "output"
LOG_DIR = ROOT_DIR / "logs"
CONFIG_FILE = ROOT_DIR / "configs" / "tasks.yaml"

# --- Create Directories ---
OUTPUT_DIR.mkdir(exist_ok=True)
LOG_DIR.mkdir(exist_ok=True)
(ROOT_DIR / "configs").mkdir(exist_ok=True)


# --- Logging Configuration ---
def get_logger(name: str, log_file: Path = LOG_DIR / "pubcrawler.log") -> logging.Logger:
    """Configures and returns a logger with TQDM-safe colored console output."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)

        # --- 核心修改点: 使用 TqdmLoggingHandler ---

        # 1. 控制台处理器 (使用 Tqdm 安全处理器和彩色格式)
        tqdm_handler = TqdmLoggingHandler()
        tqdm_handler.setLevel(logging.INFO)
        console_format = '%(message)s'
        console_formatter = ColoredFormatter(console_format)
        tqdm_handler.setFormatter(console_formatter)

        # 2. 文件处理器 (保持不变)
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        file_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        file_formatter = logging.Formatter(file_format)
        file_handler.setFormatter(file_formatter)

        logger.addHandler(tqdm_handler)
        logger.addHandler(file_handler)

        logger.propagate = False

    return logger