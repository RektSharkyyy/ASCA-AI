import sys
from pathlib import Path
from loguru import logger
from src.infrastructure.config import config

LOG_DIR = Path(__file__).resolve().parent.parent.parent / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

logger.remove()

# Console logger with UTF-8 encoding support for Sinhala characters
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level=config.env.LOG_LEVEL,
)

# File logger
logger.add(
    LOG_DIR / "asca_ai.log",
    rotation="10 MB",
    retention="1 week",
    level="DEBUG",
    encoding="utf-8",
)

def get_logger():
    return logger
