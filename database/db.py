import os
import aiosqlite
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DB_PATH


async def init_db():
    """Ma'lumotlar bazasini ishga tushirish va jadvallarni yaratish."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                unique_code TEXT UNIQUE NOT NULL,
                is_blocked INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS privileged_users (
                user_id INTEGER PRIMARY KEY,
                role TEXT DEFAULT 'trusted' CHECK(role IN ('admin', 'trusted')),
                granted_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender_id INTEGER NOT NULL,
                receiver_id INTEGER NOT NULL,
                bot_message_id INTEGER,
                message_type TEXT DEFAULT 'text',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (sender_id) REFERENCES users(user_id),
                FOREIGN KEY (receiver_id) REFERENCES users(user_id)
            );

            CREATE INDEX IF NOT EXISTS idx_messages_receiver_bot_msg 
                ON messages(receiver_id, bot_message_id);
            CREATE INDEX IF NOT EXISTS idx_users_code 
                ON users(unique_code);
        """)
        await db.commit()


async def get_db():
    """Database ulanishni qaytarish."""
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
    return db
