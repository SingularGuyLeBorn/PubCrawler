# FILE: src/utils/tqdm_logger.py

import logging
from tqdm import tqdm

class TqdmLoggingHandler(logging.Handler):
    """
    一个自定义的日志处理器，它能将日志消息通过 tqdm.write() 输出，
    从而避免与 tqdm 进度条的显示发生冲突。
    """
    def __init__(self, level=logging.NOTSET):
        super().__init__(level)

    def emit(self, record):
        try:
            msg = self.format(record)
            # 使用 tqdm.write 来打印消息，它会自动处理换行，且不会干扰进度条
            tqdm.write(msg)
            self.flush()
        except Exception:
            self.handleError(record)