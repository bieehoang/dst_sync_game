import sqlite3
import asyncio
from datetime import datetime, timedelta
from src.logger import logger

class ChannelMemory:
    def __init__(self, db_path="wyvern_memory.db"):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.create_tables()

    def create_tables(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_id INTEGER,
                message_id INTEGER,
                author TEXT,
                content TEXT,
                timestamp TEXT
            )
        """)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS summaries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_id INTEGER,
                summary TEXT,
                created_at TEXT
            )
        """)
        self.conn.commit()

    async def add_message(self, channel_id: int, message_id: int, author: str, content: str):
        try:
            self.conn.execute(
                "INSERT INTO messages (channel_id, message_id, author, content, timestamp) VALUES (?, ?, ?, ?, ?)",
                (channel_id, message_id, author, content, datetime.utcnow().isoformat())
            )
            self.conn.commit()
        except Exception as e:
            logger.error(f"Memory add error: {e}")

    async def get_recent_messages(self, channel_id: int, limit: int = 120):
        cursor = self.conn.execute(
            "SELECT author, content FROM messages WHERE channel_id = ? ORDER BY id DESC LIMIT ?",
            (channel_id, limit)
        )
        return cursor.fetchall()

    async def get_lastest_summary(self, channel_id: int):
        cursor = self.conn.execute(
            "SELECT summary FROM summaries WHERE channel_id = ? ORDER BY created_at DESC LIMIT 1",
            (channel_id,)
        )
        row = cursor.fetchone()
        return row[0] if row else ""

    async def save_summary(self, channel_id: int, summary: str):
        self.conn.execute(
            "INSERT INTO summaries (channel_id, summary, created_at) VALUES (?, ?, ?)",
            (channel_id, summary, datetime.utcnow().isoformat())
        )
        self.conn.commit()
        logger.info(f"✅ Saved new summary for channel {channel_id}")

    async def cleanup_old_messages(self, days: int = 7):
        """Xóa tin nhắn cũ hơn 7 ngày để tiết kiệm dung lượng"""
        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
        self.conn.execute("DELETE FROM messages WHERE timestamp < ?", (cutoff,))
        self.conn.commit()
