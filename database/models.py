from .db import get_db
from config import ADMIN_ID


class UserDB:
    """Foydalanuvchilar bilan ishlash."""

    @staticmethod
    async def save_user(user_id: int, username: str = None, 
                        first_name: str = None, last_name: str = None,
                        unique_code: str = None) -> None:
        """Foydalanuvchini saqlash yoki yangilash."""
        db = await get_db()
        try:
            existing = await db.execute(
                "SELECT user_id FROM users WHERE user_id = ?", (user_id,)
            )
            row = await existing.fetchone()
            
            if row:
                await db.execute("""
                    UPDATE users 
                    SET username = ?, first_name = ?, last_name = ?, 
                        updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                """, (username, first_name, last_name, user_id))
            else:
                await db.execute("""
                    INSERT INTO users (user_id, username, first_name, last_name, unique_code)
                    VALUES (?, ?, ?, ?, ?)
                """, (user_id, username, first_name, last_name, unique_code))
            
            await db.commit()
        finally:
            await db.close()

    @staticmethod
    async def get_user(user_id: int) -> dict | None:
        """Foydalanuvchi ma'lumotlarini olish."""
        db = await get_db()
        try:
            cursor = await db.execute(
                "SELECT * FROM users WHERE user_id = ?", (user_id,)
            )
            row = await cursor.fetchone()
            if row:
                return dict(row)
            return None
        finally:
            await db.close()

    @staticmethod
    async def get_user_by_code(code: str) -> dict | None:
        """Unique code bo'yicha foydalanuvchini topish."""
        db = await get_db()
        try:
            cursor = await db.execute(
                "SELECT * FROM users WHERE unique_code = ?", (code,)
            )
            row = await cursor.fetchone()
            if row:
                return dict(row)
            return None
        finally:
            await db.close()

    @staticmethod
    async def get_user_by_username(username: str) -> dict | None:
        """Username bo'yicha foydalanuvchini topish."""
        db = await get_db()
        try:
            cursor = await db.execute(
                "SELECT * FROM users WHERE username = ?", (username.lstrip('@'),)
            )
            row = await cursor.fetchone()
            if row:
                return dict(row)
            return None
        finally:
            await db.close()

    @staticmethod
    async def is_blocked(user_id: int) -> bool:
        """Foydalanuvchi bloklangan yoki yo'qligini tekshirish."""
        db = await get_db()
        try:
            cursor = await db.execute(
                "SELECT is_blocked FROM users WHERE user_id = ?", (user_id,)
            )
            row = await cursor.fetchone()
            return bool(row and row["is_blocked"])
        finally:
            await db.close()

    @staticmethod
    async def block_user(user_id: int) -> bool:
        """Foydalanuvchini bloklash."""
        db = await get_db()
        try:
            cursor = await db.execute(
                "UPDATE users SET is_blocked = 1 WHERE user_id = ?", (user_id,)
            )
            await db.commit()
            return cursor.rowcount > 0
        finally:
            await db.close()

    @staticmethod
    async def unblock_user(user_id: int) -> bool:
        """Foydalanuvchini blokdan chiqarish."""
        db = await get_db()
        try:
            cursor = await db.execute(
                "UPDATE users SET is_blocked = 0 WHERE user_id = ?", (user_id,)
            )
            await db.commit()
            return cursor.rowcount > 0
        finally:
            await db.close()

    @staticmethod
    async def get_all_users() -> list:
        """Barcha foydalanuvchilar ro'yxatini olish."""
        db = await get_db()
        try:
            cursor = await db.execute("SELECT * FROM users")
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            await db.close()

    @staticmethod
    async def get_user_count() -> int:
        """Foydalanuvchilar sonini olish."""
        db = await get_db()
        try:
            cursor = await db.execute("SELECT COUNT(*) as count FROM users")
            row = await cursor.fetchone()
            return row["count"] if row else 0
        finally:
            await db.close()


class PrivilegedDB:
    """Imtiyozli (admin/ishonchli) foydalanuvchilar bilan ishlash."""

    @staticmethod
    async def is_privileged(user_id: int) -> bool:
        """Foydalanuvchi admin yoki ishonchli ekanligini tekshirish."""
        if user_id == ADMIN_ID:
            return True
        db = await get_db()
        try:
            cursor = await db.execute(
                "SELECT user_id FROM privileged_users WHERE user_id = ?", (user_id,)
            )
            row = await cursor.fetchone()
            return row is not None
        finally:
            await db.close()

    @staticmethod
    async def add_privileged(user_id: int, granted_by: int, role: str = "trusted") -> bool:
        """Ishonchli inson qo'shish."""
        db = await get_db()
        try:
            await db.execute("""
                INSERT OR REPLACE INTO privileged_users (user_id, role, granted_by)
                VALUES (?, ?, ?)
            """, (user_id, role, granted_by))
            await db.commit()
            return True
        except Exception:
            return False
        finally:
            await db.close()

    @staticmethod
    async def remove_privileged(user_id: int) -> bool:
        """Ishonchli insonni olib tashlash."""
        db = await get_db()
        try:
            cursor = await db.execute(
                "DELETE FROM privileged_users WHERE user_id = ?", (user_id,)
            )
            await db.commit()
            return cursor.rowcount > 0
        finally:
            await db.close()

    @staticmethod
    async def get_all_privileged() -> list:
        """Barcha ishonchli insonlar ro'yxatini olish."""
        db = await get_db()
        try:
            cursor = await db.execute("""
                SELECT p.*, u.username, u.first_name, u.last_name 
                FROM privileged_users p
                LEFT JOIN users u ON p.user_id = u.user_id
            """)
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            await db.close()


class MessageDB:
    """Xabarlar bilan ishlash."""

    @staticmethod
    async def save_message(sender_id: int, receiver_id: int, 
                           bot_message_id: int, message_type: str = "text") -> int:
        """Xabarni saqlash va ID qaytarish."""
        db = await get_db()
        try:
            cursor = await db.execute("""
                INSERT INTO messages (sender_id, receiver_id, bot_message_id, message_type)
                VALUES (?, ?, ?, ?)
            """, (sender_id, receiver_id, bot_message_id, message_type))
            await db.commit()
            return cursor.lastrowid
        finally:
            await db.close()

    @staticmethod
    async def get_sender_by_bot_message(receiver_id: int, bot_message_id: int) -> int | None:
        """Bot xabari ID si bo'yicha yuboruvchini topish (reply uchun)."""
        db = await get_db()
        try:
            cursor = await db.execute("""
                SELECT sender_id FROM messages 
                WHERE receiver_id = ? AND bot_message_id = ?
                ORDER BY created_at DESC LIMIT 1
            """, (receiver_id, bot_message_id))
            row = await cursor.fetchone()
            return row["sender_id"] if row else None
        finally:
            await db.close()

    @staticmethod
    async def get_message_count() -> int:
        """Jami xabarlar sonini olish."""
        db = await get_db()
        try:
            cursor = await db.execute("SELECT COUNT(*) as count FROM messages")
            row = await cursor.fetchone()
            return row["count"] if row else 0
        finally:
            await db.close()

    @staticmethod
    async def get_today_message_count() -> int:
        """Bugungi xabarlar sonini olish."""
        db = await get_db()
        try:
            cursor = await db.execute("""
                SELECT COUNT(*) as count FROM messages 
                WHERE DATE(created_at) = DATE('now')
            """)
            row = await cursor.fetchone()
            return row["count"] if row else 0
        finally:
            await db.close()
