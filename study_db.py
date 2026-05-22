# Database operations for the Study app
import sqlite3
from datetime import datetime
from typing import List, Tuple, Optional
from pathlib import Path
import json

from study_config import DB_PATH, DB_TIMEOUT


class StudyDB:
    """SQLite database handler for Study app"""

    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize database schema"""
        conn = sqlite3.connect(self.db_path, timeout=DB_TIMEOUT)
        cursor = conn.cursor()

        # Chat history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mode TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT
            )
        """)

        # Uploads table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS uploads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mode TEXT NOT NULL,
                filename TEXT NOT NULL,
                file_path TEXT NOT NULL,
                upload_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                processed BOOLEAN DEFAULT 0,
                metadata TEXT
            )
        """)

        # YouTube videos table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS videos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                video_id TEXT UNIQUE NOT NULL,
                url TEXT NOT NULL,
                title TEXT,
                transcript TEXT,
                cached_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT
            )
        """)

        # Sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mode TEXT NOT NULL,
                resource_id TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT
            )
        """)

        conn.commit()
        conn.close()

    def add_chat_message(self, mode: str, role: str, content: str, metadata: dict = None) -> int:
        """Add a message to chat history"""
        conn = sqlite3.connect(self.db_path, timeout=DB_TIMEOUT)
        cursor = conn.cursor()

        meta_json = json.dumps(metadata) if metadata else None
        cursor.execute(
            "INSERT INTO chat_history (mode, role, content, metadata) VALUES (?, ?, ?, ?)",
            (mode, role, content, meta_json)
        )
        conn.commit()
        msg_id = cursor.lastrowid
        conn.close()
        return msg_id

    def get_chat_history(self, mode: str, limit: int = 50) -> List[Tuple[str, str]]:
        """Retrieve chat history for a mode"""
        conn = sqlite3.connect(self.db_path, timeout=DB_TIMEOUT)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT role, content FROM chat_history WHERE mode = ? ORDER BY timestamp ASC LIMIT ?",
            (mode, limit)
        )
        messages = cursor.fetchall()
        conn.close()
        return messages

    def clear_chat_history(self, mode: str):
        """Clear chat history for a mode"""
        conn = sqlite3.connect(self.db_path, timeout=DB_TIMEOUT)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM chat_history WHERE mode = ?", (mode,))
        conn.commit()
        conn.close()

    def add_upload(self, mode: str, filename: str, file_path: str, metadata: dict = None) -> int:
        """Record a file upload"""
        conn = sqlite3.connect(self.db_path, timeout=DB_TIMEOUT)
        cursor = conn.cursor()

        meta_json = json.dumps(metadata) if metadata else None
        cursor.execute(
            "INSERT INTO uploads (mode, filename, file_path, metadata) VALUES (?, ?, ?, ?)",
            (mode, filename, file_path, meta_json)
        )
        conn.commit()
        upload_id = cursor.lastrowid
        conn.close()
        return upload_id

    def mark_upload_processed(self, upload_id: int):
        """Mark an upload as processed"""
        conn = sqlite3.connect(self.db_path, timeout=DB_TIMEOUT)
        cursor = conn.cursor()
        cursor.execute("UPDATE uploads SET processed = 1 WHERE id = ?", (upload_id,))
        conn.commit()
        conn.close()

    def get_recent_uploads(self, mode: str, limit: int = 10) -> List[dict]:
        """Get recent uploads for a mode"""
        conn = sqlite3.connect(self.db_path, timeout=DB_TIMEOUT)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM uploads WHERE mode = ? ORDER BY upload_time DESC LIMIT ?",
            (mode, limit)
        )
        uploads = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return uploads

    def cache_video(self, video_id: str, url: str, transcript: str, title: str = None, metadata: dict = None):
        """Cache a YouTube video transcript"""
        conn = sqlite3.connect(self.db_path, timeout=DB_TIMEOUT)
        cursor = conn.cursor()

        meta_json = json.dumps(metadata) if metadata else None
        cursor.execute(
            "INSERT OR REPLACE INTO videos (video_id, url, title, transcript, metadata) VALUES (?, ?, ?, ?, ?)",
            (video_id, url, title, transcript, meta_json)
        )
        conn.commit()
        conn.close()

    def get_cached_video(self, video_id: str) -> Optional[dict]:
        """Retrieve cached video transcript"""
        conn = sqlite3.connect(self.db_path, timeout=DB_TIMEOUT)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM videos WHERE video_id = ?", (video_id,))
        video = dict(cursor.fetchone()) if cursor.fetchone() else None
        conn.close()
        return video

    def create_session(self, mode: str, resource_id: str = None, metadata: dict = None) -> int:
        """Create a new session"""
        conn = sqlite3.connect(self.db_path, timeout=DB_TIMEOUT)
        cursor = conn.cursor()

        meta_json = json.dumps(metadata) if metadata else None
        cursor.execute(
            "INSERT INTO sessions (mode, resource_id, metadata) VALUES (?, ?, ?)",
            (mode, resource_id, meta_json)
        )
        conn.commit()
        session_id = cursor.lastrowid
        conn.close()
        return session_id
