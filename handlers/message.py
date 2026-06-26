from aiogram import Router, Bot, F
from aiogram.types import Message

from database.models import UserDB, PrivilegedDB, MessageDB
from utils.helpers import format_sender_info, get_message_type
from handlers.start import active_sessions

router = Router()


async def send_anonymous_message(message: Message, bot: Bot, receiver_id: int, sender_id: int) -> int | None:
    """
    Anonim xabarni qabul qiluvchiga yuborish.
    Agar qabul qiluvchi admin/ishonchli bo'lsa — yuboruvchi ma'lumotini ko'rsatish.
    Qaytaradi: bot_message_id (reply tracking uchun)
    """
    is_receiver_privileged = await PrivilegedDB.is_privileged(receiver_id)
    sender_data = await UserDB.get_user(sender_id)

    sender_info = ""
    if is_receiver_privileged and sender_data:
        sender_info = format_sender_info(sender_data)

    msg_type = get_message_type(message)
    bot_msg = None

    try:
        if msg_type == "text":
            # Matnli xabar
            text = f"📩 <b>Anonim xabar:</b>\n\n{message.text}"
            if sender_info:
                text += f"\n\n{sender_info}"
            bot_msg = await bot.send_message(
                chat_id=receiver_id,
                text=text,
                parse_mode="HTML"
            )

        elif msg_type == "photo":
            caption = f"📩 <b>Anonim xabar:</b>"
            if message.caption:
                caption += f"\n\n{message.caption}"
            if sender_info:
                caption += f"\n\n{sender_info}"
            bot_msg = await bot.send_photo(
                chat_id=receiver_id,
                photo=message.photo[-1].file_id,
                caption=caption,
                parse_mode="HTML"
            )

        elif msg_type == "video":
            caption = f"📩 <b>Anonim xabar:</b>"
            if message.caption:
                caption += f"\n\n{message.caption}"
            if sender_info:
                caption += f"\n\n{sender_info}"
            bot_msg = await bot.send_video(
                chat_id=receiver_id,
                video=message.video.file_id,
                caption=caption,
                parse_mode="HTML"
            )

        elif msg_type == "voice":
            bot_msg = await bot.send_voice(
                chat_id=receiver_id,
                voice=message.voice.file_id,
                caption=f"📩 <b>Anonim ovozli xabar</b>{('\n\n' + sender_info) if sender_info else ''}",
                parse_mode="HTML"
            )

        elif msg_type == "audio":
            caption = f"📩 <b>Anonim audio</b>"
            if message.caption:
                caption += f"\n\n{message.caption}"
            if sender_info:
                caption += f"\n\n{sender_info}"
            bot_msg = await bot.send_audio(
                chat_id=receiver_id,
                audio=message.audio.file_id,
                caption=caption,
                parse_mode="HTML"
            )

        elif msg_type == "document":
            caption = f"📩 <b>Anonim fayl</b>"
            if message.caption:
                caption += f"\n\n{message.caption}"
            if sender_info:
                caption += f"\n\n{sender_info}"
            bot_msg = await bot.send_document(
                chat_id=receiver_id,
                document=message.document.file_id,
                caption=caption,
                parse_mode="HTML"
            )

        elif msg_type == "sticker":
            # Sticker uchun — avval sticker, keyin info
            bot_msg = await bot.send_sticker(
                chat_id=receiver_id,
                sticker=message.sticker.file_id
            )
            # Sticker uchun alohida info xabari
            info_text = "📩 <b>Anonim sticker yuborildi</b>"
            if sender_info:
                info_text += f"\n\n{sender_info}"
            await bot.send_message(
                chat_id=receiver_id,
                text=info_text,
                parse_mode="HTML",
                reply_to_message_id=bot_msg.message_id
            )

        elif msg_type == "video_note":
            bot_msg = await bot.send_video_note(
                chat_id=receiver_id,
                video_note=message.video_note.file_id
            )
            if sender_info:
                await bot.send_message(
                    chat_id=receiver_id,
                    text=f"📩 <b>Anonim video xabar</b>\n\n{sender_info}",
                    parse_mode="HTML",
                    reply_to_message_id=bot_msg.message_id
                )

        elif msg_type == "animation":
            caption = f"📩 <b>Anonim GIF</b>"
            if message.caption:
                caption += f"\n\n{message.caption}"
            if sender_info:
                caption += f"\n\n{sender_info}"
            bot_msg = await bot.send_animation(
                chat_id=receiver_id,
                animation=message.animation.file_id,
                caption=caption,
                parse_mode="HTML"
            )

        elif msg_type == "contact":
            bot_msg = await bot.send_contact(
                chat_id=receiver_id,
                phone_number=message.contact.phone_number,
                first_name="Anonim"
            )

        elif msg_type == "location":
            bot_msg = await bot.send_location(
                chat_id=receiver_id,
                latitude=message.location.latitude,
                longitude=message.location.longitude
            )

        else:
            # Noma'lum tur — matn sifatida yuborish
            text = f"📩 <b>Anonim xabar:</b>\n\n{message.text or '(bo\'sh xabar)'}"
            if sender_info:
                text += f"\n\n{sender_info}"
            bot_msg = await bot.send_message(
                chat_id=receiver_id,
                text=text,
                parse_mode="HTML"
            )

        return bot_msg.message_id if bot_msg else None

    except Exception as e:
        print(f"Xabar yuborishda xatolik (receiver={receiver_id}): {e}")
        return None


@router.message(~F.text.startswith("/"))
async def handle_anonymous_message(message: Message, bot: Bot):
    """
    Anonim xabarni qayta ishlash.
    Faqat foydalanuvchi aktiv sessiyada bo'lganda ishlaydi.
    """
    sender_id = message.from_user.id

    # Aktiv sessiya tekshirish
    if sender_id not in active_sessions:
        await message.answer(
            "🤔 Anonim xabar yuborish uchun biror kishining havolasini bosing.\n\n"
            "🏠 Bosh menyu: /start\n"
            "🔗 Havolangiz: /mylink"
        )
        return

    receiver_id = active_sessions[sender_id]

    # Bloklangan tekshirish
    if await UserDB.is_blocked(sender_id):
        await message.answer("🚫 Siz bloklangansiz va xabar yubora olmaysiz.")
        active_sessions.pop(sender_id, None)
        return

    # Xabarni anonim yuborish
    bot_message_id = await send_anonymous_message(message, bot, receiver_id, sender_id)

    if bot_message_id:
        # Xabarni bazaga saqlash (reply tracking uchun)
        msg_type = get_message_type(message)
        await MessageDB.save_message(
            sender_id=sender_id,
            receiver_id=receiver_id,
            bot_message_id=bot_message_id,
            message_type=msg_type
        )

        await message.answer(
            "✅ Xabaringiz anonim yuborildi! 👻\n\n"
            "📝 Yana xabar yozishingiz mumkin.\n"
            "🔙 Bekor qilish: /cancel\n"
            "🏠 Bosh menyu: /start"
        )
    else:
        await message.answer(
            "❌ Xabarni yuborib bo'lmadi.\n"
            "Foydalanuvchi botni bloklagan bo'lishi mumkin."
        )
