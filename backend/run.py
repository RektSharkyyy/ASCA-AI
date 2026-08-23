"""
ASCA AI — Backend startup script.

Usage:
    # from the /backend directory with the virtual environment active:
    python run.py

    # or directly:
    .venv/bin/python run.py
"""

import uvicorn
from src.infrastructure.config import config

if __name__ == "__main__":
    uvicorn.run(
        "src.api.main:app",
        host=config.env.API_HOST,
        port=config.env.API_PORT,
        reload=True,
        log_level="info",
    )
