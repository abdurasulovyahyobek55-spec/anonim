from aiogram import Router, F, Bot
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart, Command, CommandObject

from database.models import UserDB, PrivilegedDB
from utils.helpers import generate_unique_code

router = Router()

# Aktiv sessiyalar: {sender_id: receiver_id}
# Bu dict bot.py da import qilinadi va message handler da ishlatiladi
active_sessions: dict[int, int] = {}


@router.message(CommandStart(deep_link=True))
async def start_with_link(message: Message, command: CommandObject, bot: Bot):
    """Foydalanuvchi boshqa birovning havolasini bosganida."""
    code = command.args
    user = message.from_user

    # Havola egasini topish
    target_user = await UserDB.get_user_by_code(code)

    if not target_user:
        await message.answer(
            "❌ Bu havola noto'g'ri yoki eskirgan.\n"
            "Botdan foydalanish uchun /start buyrug'ini bosing."
        )
        return

    # O'zining havolasini bosgan bo'lsa
    if target_user["user_id"] == user.id:
        await show_main_menu(message, bot)
        return

    # Sessiyani boshlash
    active_sessions[user.id] = target_user["user_id"]

    target_name = target_user.get("first_name", "Foydalanuvchi")

    await message.answer(
        f"👻 <b>Anonim rejim faollashtirildi!</b>\n\n"
        f"Siz hozir <b>{target_name}</b> ga anonim xabar yozmoqdasiz.\n\n"
        f"📝 Xabaringizni yozing — u anonim tarzda yetkaziladi.\n"
        f"📎 Matn, rasm, video, audio — barchasi qo'llab-quvvatlanadi.\n\n"
        f"🔙 Bekor qilish uchun: /cancel\n"
        f"🏠 Bosh menyu: /start",
        parse_mode="HTML"
    )


@router.message(CommandStart())
async def start_command(message: Message, bot: Bot):
    """Asosiy /start buyrug'i — bosh menyu."""
    # Sessiyani tozalash
    active_sessions.pop(message.from_user.id, None)
    await show_main_menu(message, bot)


async def show_main_menu(message: Message, bot: Bot):
    """Bosh menyu ko'rsatish."""
    user = message.from_user

    # Foydalanuvchi ma'lumotlarini olish
    user_data = await UserDB.get_user(user.id)
    if not user_data:
        code = generate_unique_code()
        await UserDB.save_user(
            user_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            unique_code=code
        )
        user_data = await UserDB.get_user(user.id)

    unique_code = user_data["unique_code"]
    bot_info = await bot.get_me()
    bot_username = bot_info.username
    link = f"https://t.me/{bot_username}?start={unique_code}"

    is_priv = await PrivilegedDB.is_privileged(user.id)

    welcome_text = (
        f"👋 <b>Assalomu alaykum, {user.first_name}!</b>\n\n"
        f"🤖 Bu bot orqali siz <b>anonim xabarlar</b> qabul qilishingiz mumkin.\n\n"
        f"🔗 <b>Sizning shaxsiy havolangiz:</b>\n"
        f"<code>{link}</code>\n\n"
        f"☝️ Bu havolani do'stlaringiz, ijtimoiy tarmoqlarda yoki bio'ngizda ulashing.\n"
        f"Havolani bosgan har bir inson sizga <b>anonim xabar</b> yuborishi mumkin!\n\n"
    )

    if is_priv:
        welcome_text += (
            f"🔐 <b>Sizda maxsus huquq mavjud!</b>\n"
            f"Sizga kelgan anonim xabarlarning yuboruvchisini ko'rishingiz mumkin.\n\n"
        )

    welcome_text += (
        f"📋 <b>Buyruqlar:</b>\n"
        f"├ /start — Bosh menyu\n"
        f"├ /help — Yordam\n"
        f"├ /myid — Sizning Telegram ID\n"
        f"├ /mylink — Sizning havola\n"
        f"└ /cancel — Anonim yozishni bekor qilish"
    )

    if is_priv:
        welcome_text += (
            f"\n\n🛡️ <b>Admin buyruqlari:</b>\n"
            f"├ /grant &lt;user_id&gt; — Huquq berish\n"
            f"├ /revoke &lt;user_id&gt; — Huquqni olish\n"
            f"├ /admins — Ishonchli insonlar\n"
            f"├ /block &lt;user_id&gt; — Bloklash\n"
            f"├ /unblock &lt;user_id&gt; — Blokdan chiqarish\n"
            f"└ /stats — Statistika"
        )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔗 Havolani ulashish", url=f"https://t.me/share/url?url={link}&text=Menga%20anonim%20xabar%20yuboring%20👻")],
    ])

    await message.answer(welcome_text, parse_mode="HTML", reply_markup=keyboard)


@router.message(Command("help"))
async def help_command(message: Message):
    """Yordam buyrug'i."""
    is_priv = await PrivilegedDB.is_privileged(message.from_user.id)

    text = (
        "📖 <b>Botdan foydalanish yo'riqnomasi</b>\n\n"
        "1️⃣ /start buyrug'ini bosing va shaxsiy havolangizni oling\n"
        "2️⃣ Havolani do'stlaringizga yuboring\n"
        "3️⃣ Ular havola orqali sizga anonim xabar yozadi\n"
        "4️⃣ Siz xabarga reply qiling — javob yuboruvchiga boradi\n\n"
        "💡 <b>Muhim:</b>\n"
        "• Rasm, video, audio, sticker — barchasi qo'llab-quvvatlanadi\n"
        "• Anonim xabarga reply qiling — javob yuboruvchiga qaytadi\n"
        "• /cancel — anonim yozish rejimini bekor qiladi"
    )

    if is_priv:
        text += (
            "\n\n🛡️ <b>Admin buyruqlari:</b>\n"
            "• /grant <user_id> — foydalanuvchiga ko'rish huquqi berish\n"
            "• /revoke <user_id> — huquqni olib tashlash\n"
            "• /admins — ishonchli insonlar ro'yxati\n"
            "• /block <user_id> — foydalanuvchini bloklash\n"
            "• /unblock <user_id> — blokdan chiqarish\n"
            "• /stats — bot statistikasi\n"
            "• /broadcast <xabar> — barchaga xabar yuborish"
        )

    await message.answer(text, parse_mode="HTML")


@router.message(Command("myid"))
async def myid_command(message: Message):
    """Foydalanuvchiga o'z ID sini ko'rsatish."""
    await message.answer(
        f"🆔 <b>Sizning Telegram ID:</b>\n"
        f"<code>{message.from_user.id}</code>",
        parse_mode="HTML"
    )


@router.message(Command("mylink"))
async def mylink_command(message: Message, bot: Bot):
    """Foydalanuvchiga shaxsiy havolasini ko'rsatish."""
    user_data = await UserDB.get_user(message.from_user.id)
    if not user_data:
        await message.answer("❌ Avval /start buyrug'ini bosing.")
        return

    bot_info = await bot.get_me()
    link = f"https://t.me/{bot_info.username}?start={user_data['unique_code']}"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔗 Havolani ulashish", url=f"https://t.me/share/url?url={link}&text=Menga%20anonim%20xabar%20yuboring%20👻")],
    ])

    await message.answer(
        f"🔗 <b>Sizning shaxsiy havolangiz:</b>\n\n"
        f"<code>{link}</code>\n\n"
        f"Bu havolani ulashib, anonim xabarlar qabul qiling! 👻",
        parse_mode="HTML",
        reply_markup=keyboard
    )


@router.message(Command("cancel"))
async def cancel_command(message: Message):
    """Anonim yozish rejimini bekor qilish."""
    if message.from_user.id in active_sessions:
        active_sessions.pop(message.from_user.id)
        await message.answer(
            "✅ Anonim yozish rejimi bekor qilindi.\n"
            "🏠 Bosh menyu uchun: /start"
        )
    else:
        await message.answer(
            "ℹ️ Siz hozir hech kimga anonim yozmayapsiz.\n"
            "🏠 Bosh menyu uchun: /start"
        )
