# Configuration and constants for the Study app

import os
from pathlib import Path

# Project paths
PROJECT_DIR = Path(__file__).parent
DB_PATH = PROJECT_DIR / "study.db"
TEMP_DIR = PROJECT_DIR / "temp"
TEMP_DIR.mkdir(exist_ok=True)

# LLM Configuration
LLM_CONFIG = {
    "repo_id": "meta-llama/Llama-3.3-70B-Instruct",
    "task": "text-generation",
    "temperature": 0.5,
}

# Text Processing
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

# Embeddings
EMBEDDINGS_MODEL = "BAAI/bge-small-en-v1.5"

# Threading
MAX_WORKERS = 3

# Database
DB_TIMEOUT = 30

# UI
SIDEBAR_WIDTH = 340
MAX_CONTENT_WIDTH = 900

# Chat
MAX_HISTORY_CONTEXT = 5
K_RETRIEVER = 4
