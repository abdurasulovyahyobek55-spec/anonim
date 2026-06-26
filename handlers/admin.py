from aiogram import Router, Bot
from aiogram.types import Message
from aiogram.filters import Command

from config import ADMIN_ID
from database.models import UserDB, PrivilegedDB, MessageDB

router = Router()


def is_main_admin(user_id: int) -> bool:
    """Asosiy admin ekanligini tekshirish."""
    return user_id == ADMIN_ID


@router.message(Command("grant"))
async def grant_command(message: Message):
    """Foydalanuvchiga ko'rish huquqi berish. Faqat asosiy admin uchun."""
    if not is_main_admin(message.from_user.id):
        return  # Hech narsa ko'rsatmaslik — maxfiy buyruq

    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer(
            "📋 <b>Foydalanish:</b>\n"
            "<code>/grant 123456789</code> — ID bo'yicha\n"
            "<code>/grant @username</code> — username bo'yicha",
            parse_mode="HTML"
        )
        return

    target = args[1].strip()

    # Username yoki ID bo'yicha topish
    if target.startswith("@"):
        user_data = await UserDB.get_user_by_username(target)
        if not user_data:
            await message.answer(f"❌ <code>{target}</code> topilmadi.", parse_mode="HTML")
            return
        target_id = user_data["user_id"]
    else:
        try:
            target_id = int(target)
        except ValueError:
            await message.answer("❌ Noto'g'ri format. ID raqam bo'lishi kerak.")
            return

    if target_id == ADMIN_ID:
        await message.answer("ℹ️ Siz asosiy adminsiz, huquq berishning hojati yo'q.")
        return

    success = await PrivilegedDB.add_privileged(target_id, message.from_user.id)
    if success:
        user_data = await UserDB.get_user(target_id)
        name = "Nomaʼlum"
        if user_data:
            name = user_data.get("first_name", "") or "Nomaʼlum"
            if user_data.get("username"):
                name += f" (@{user_data['username']})"

        await message.answer(
            f"✅ <b>{name}</b> ga ko'rish huquqi berildi!\n"
            f"🆔 ID: <code>{target_id}</code>\n\n"
            f"Endi u o'ziga kelgan anonim xabarlarning yuboruvchisini ko'ra oladi.",
            parse_mode="HTML"
        )
    else:
        await message.answer("❌ Xatolik yuz berdi.")


@router.message(Command("revoke"))
async def revoke_command(message: Message):
    """Foydalanuvchidan ko'rish huquqini olish. Faqat asosiy admin uchun."""
    if not is_main_admin(message.from_user.id):
        return

    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer(
            "📋 <b>Foydalanish:</b>\n"
            "<code>/revoke 123456789</code> — ID bo'yicha\n"
            "<code>/revoke @username</code> — username bo'yicha",
            parse_mode="HTML"
        )
        return

    target = args[1].strip()

    if target.startswith("@"):
        user_data = await UserDB.get_user_by_username(target)
        if not user_data:
            await message.answer(f"❌ <code>{target}</code> topilmadi.", parse_mode="HTML")
            return
        target_id = user_data["user_id"]
    else:
        try:
            target_id = int(target)
        except ValueError:
            await message.answer("❌ Noto'g'ri format. ID raqam bo'lishi kerak.")
            return

    success = await PrivilegedDB.remove_privileged(target_id)
    if success:
        await message.answer(
            f"✅ <code>{target_id}</code> dan ko'rish huquqi olib tashlandi.",
            parse_mode="HTML"
        )
    else:
        await message.answer("❌ Bu foydalanuvchi ishonchli insonlar ro'yxatida topilmadi.")


@router.message(Command("admins"))
async def admins_command(message: Message):
    """Ishonchli insonlar ro'yxatini ko'rsatish."""
    if not is_main_admin(message.from_user.id):
        return

    privileged = await PrivilegedDB.get_all_privileged()

    text = "🛡️ <b>Ishonchli insonlar ro'yxati:</b>\n\n"
    text += f"👑 <b>Asosiy admin:</b> <code>{ADMIN_ID}</code>\n\n"

    if privileged:
        for i, p in enumerate(privileged, 1):
            name = p.get("first_name", "") or "Nomaʼlum"
            username = f"@{p['username']}" if p.get("username") else "username yo'q"
            text += f"{i}. {name} ({username})\n   🆔 <code>{p['user_id']}</code> | 📋 {p['role']}\n\n"
    else:
        text += "📭 Hozircha ishonchli inson qo'shilmagan.\n"
        text += "\n💡 Qo'shish: <code>/grant user_id</code>"

    await message.answer(text, parse_mode="HTML")


@router.message(Command("block"))
async def block_command(message: Message):
    """Foydalanuvchini bloklash."""
    if not await PrivilegedDB.is_privileged(message.from_user.id):
        return

    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer(
            "📋 <b>Foydalanish:</b> <code>/block user_id</code>",
            parse_mode="HTML"
        )
        return

    try:
        target_id = int(args[1].strip())
    except ValueError:
        await message.answer("❌ Noto'g'ri format. ID raqam bo'lishi kerak.")
        return

    if target_id == ADMIN_ID:
        await message.answer("❌ Asosiy adminni bloklash mumkin emas.")
        return

    success = await UserDB.block_user(target_id)
    if success:
        await message.answer(
            f"🚫 <code>{target_id}</code> bloklandi.\n"
            f"Bu foydalanuvchi endi anonim xabar yubora olmaydi.",
            parse_mode="HTML"
        )
    else:
        await message.answer("❌ Foydalanuvchi topilmadi.")


@router.message(Command("unblock"))
async def unblock_command(message: Message):
    """Foydalanuvchini blokdan chiqarish."""
    if not await PrivilegedDB.is_privileged(message.from_user.id):
        return

    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer(
            "📋 <b>Foydalanish:</b> <code>/unblock user_id</code>",
            parse_mode="HTML"
        )
        return

    try:
        target_id = int(args[1].strip())
    except ValueError:
        await message.answer("❌ Noto'g'ri format. ID raqam bo'lishi kerak.")
        return

    success = await UserDB.unblock_user(target_id)
    if success:
        await message.answer(
            f"✅ <code>{target_id}</code> blokdan chiqarildi.",
            parse_mode="HTML"
        )
    else:
        await message.answer("❌ Foydalanuvchi topilmadi.")


@router.message(Command("stats"))
async def stats_command(message: Message):
    """Bot statistikasini ko'rsatish."""
    if not await PrivilegedDB.is_privileged(message.from_user.id):
        return

    user_count = await UserDB.get_user_count()
    msg_count = await MessageDB.get_message_count()
    today_count = await MessageDB.get_today_message_count()
    privileged = await PrivilegedDB.get_all_privileged()

    await message.answer(
        f"📊 <b>Bot statistikasi</b>\n\n"
        f"👥 Jami foydalanuvchilar: <b>{user_count}</b>\n"
        f"📩 Jami xabarlar: <b>{msg_count}</b>\n"
        f"📅 Bugungi xabarlar: <b>{today_count}</b>\n"
        f"🛡️ Ishonchli insonlar: <b>{len(privileged)}</b>",
        parse_mode="HTML"
    )


@router.message(Command("broadcast"))
async def broadcast_command(message: Message, bot: Bot):
    """Barcha foydalanuvchilarga xabar yuborish. Faqat asosiy admin."""
    if not is_main_admin(message.from_user.id):
        return

    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer(
            "📋 <b>Foydalanish:</b> <code>/broadcast Xabar matni</code>",
            parse_mode="HTML"
        )
        return

    broadcast_text = args[1]
    users = await UserDB.get_all_users()

    sent = 0
    failed = 0

    status_msg = await message.answer(f"📤 Xabar yuborilmoqda... 0/{len(users)}")

    for user in users:
        try:
            await bot.send_message(
                chat_id=user["user_id"],
                text=f"📢 <b>Bot xabarnomasi:</b>\n\n{broadcast_text}",
                parse_mode="HTML"
            )
            sent += 1
        except Exception:
            failed += 1

    await status_msg.edit_text(
        f"✅ <b>Broadcast yakunlandi!</b>\n\n"
        f"📤 Yuborildi: <b>{sent}</b>\n"
        f"❌ Xatolik: <b>{failed}</b>\n"
        f"👥 Jami: <b>{len(users)}</b>",
        parse_mode="HTML"
    )
