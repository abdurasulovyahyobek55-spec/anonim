import string
import random
from aiogram.types import Message


def generate_unique_code(length: int = 8) -> str:
    """Tasodifiy unikal kod yaratish (havola uchun)."""
    chars = string.ascii_letters + string.digits
    return ''.join(random.choices(chars, k=length))


def format_sender_info(user_data: dict) -> str:
    """Yuboruvchi haqida ma'lumot formatlash (admin/ishonchli uchun)."""
    name_parts = []
    if user_data.get("first_name"):
        name_parts.append(user_data["first_name"])
    if user_data.get("last_name"):
        name_parts.append(user_data["last_name"])
    full_name = " ".join(name_parts) or "Nomaʼlum"

    username = user_data.get("username")
    username_str = f"@{username}" if username else "yo'q"
    user_id = user_data.get("user_id", "nomaʼlum")

    # Telegram profiliga havola (tg://user?id yoki t.me/username)
    if username:
        profile_link = f"<a href='https://t.me/{username}'>🔗 Profilni ochish</a>"
    else:
        profile_link = f"<a href='tg://user?id={user_id}'>🔗 Profilni ochish</a>"

    return (
        f"\n╔══════════════════════╗\n"
        f"║  🔍 YUBORUVCHI MA'LUMOTI\n"
        f"╠══════════════════════╣\n"
        f"║  👤 Ism: {full_name}\n"
        f"║  📎 Username: {username_str}\n"
        f"║  🆔 ID: <code>{user_id}</code>\n"
        f"║  🔗 Profil: {profile_link}\n"
        f"╚══════════════════════╝"
    )


def get_message_type(message: Message) -> str:
    """Xabar turini aniqlash."""
    if message.photo:
        return "photo"
    elif message.video:
        return "video"
    elif message.voice:
        return "voice"
    elif message.audio:
        return "audio"
    elif message.document:
        return "document"
    elif message.sticker:
        return "sticker"
    elif message.video_note:
        return "video_note"
    elif message.animation:
        return "animation"
    elif message.contact:
        return "contact"
    elif message.location:
        return "location"
    else:
        return "text"
