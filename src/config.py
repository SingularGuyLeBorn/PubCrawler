# FILE: src/config.py

import logging
import sys
from pathlib import Path

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
    """Configures and returns a logger."""
    logger = logging.getLogger(name)
    if not logger.handlers:  # Avoid adding handlers multiple times
        logger.setLevel(logging.INFO)
        # Console handler
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setLevel(logging.INFO)
        # File handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        # Formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        stream_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)

        logger.addHandler(stream_handler)
        logger.addHandler(file_handler)

    return logger

# END OF FILE: src/config.py