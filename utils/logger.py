import sys
import logging
import time

start_time = time.time()
sys.dont_write_bytecode = True

def get_runtime() -> float:
    return time.time() - start_time

formatter = logging.Formatter(
    "|TXT-EDITOR|%(asctime)s|%(levelname)s|%(filename)s|%(message)s"
)

class RuntimeFilter(logging.Filter):
    def filter(self, record):
        record.runtime = f"{get_runtime():.2f}"
        return True


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

console_hander = logging.StreamHandler()
console_hander.setLevel(logging.DEBUG)

file_hander = logging.FileHandler(
    "editor-running.log", mode="w", encoding="UTF-8"
)

file_hander.setLevel(logging.DEBUG)

console_hander.setFormatter(formatter)
file_hander.setFormatter(formatter)

logger.addFilter(RuntimeFilter())

logger.addHandler(console_hander)
logger.addHandler(file_hander)
