import logging
from logging.handlers import RotatingFileHandler
import sys

LogFile = "log.txt"
log = logging.getLogger("app_logger")
log.setLevel(logging.INFO)

# --- File handler (UTF-8 safe) ---
file_handler = RotatingFileHandler(
    LogFile,
    maxBytes=5_000_000,
    backupCount=5,
    encoding="utf-8"   # 👈 handles ☑, emojis, etc.
)

# --- Console handler (force UTF-8) ---
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setStream(sys.stdout)  # stdout is safer for UTF-8
try:
    console_handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
except Exception as e:
    print("Console logging setup failed:", e)

formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")

file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

log.addHandler(file_handler)
log.addHandler(console_handler)
