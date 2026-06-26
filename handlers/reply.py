from aiogram import Router, Bot, F
from aiogram.types import Message

from database.models import MessageDB, UserDB, PrivilegedDB
from utils.helpers import format_sender_info, get_message_type

router = Router()


@router.message(F.reply_to_message)
async def handle_reply(message: Message, bot: Bot):
    """
    Anonim xabarga javob berish.
    Foydalanuvchi bot xabariga reply qilganda — javob asl yuboruvchiga qaytadi.
    """
    user_id = message.from_user.id
    replied_msg_id = message.reply_to_message.message_id

    # Asl yuboruvchini topish
    sender_id = await MessageDB.get_sender_by_bot_message(user_id, replied_msg_id)

    if not sender_id:
        # Bu bot xabariga reply emas yoki ma'lumot topilmadi
        return

    # Javob yuboruvchining ma'lumotini tekshirish
    is_sender_privileged = await PrivilegedDB.is_privileged(sender_id)
    replier_data = await UserDB.get_user(user_id)

    replier_info = ""
    if is_sender_privileged and replier_data:
        replier_info = format_sender_info(replier_data)

    msg_type = get_message_type(message)
    bot_msg = None

    try:
        if msg_type == "text":
            text = f"💬 <b>Anonim xabaringizga javob:</b>\n\n{message.text}"
            if replier_info:
                text += f"\n\n{replier_info}"
            bot_msg = await bot.send_message(
                chat_id=sender_id,
                text=text,
                parse_mode="HTML"
            )

        elif msg_type == "photo":
            caption = f"💬 <b>Anonim xabaringizga javob:</b>"
            if message.caption:
                caption += f"\n\n{message.caption}"
            if replier_info:
                caption += f"\n\n{replier_info}"
            bot_msg = await bot.send_photo(
                chat_id=sender_id,
                photo=message.photo[-1].file_id,
                caption=caption,
                parse_mode="HTML"
            )

        elif msg_type == "video":
            caption = f"💬 <b>Anonim xabaringizga javob:</b>"
            if message.caption:
                caption += f"\n\n{message.caption}"
            if replier_info:
                caption += f"\n\n{replier_info}"
            bot_msg = await bot.send_video(
                chat_id=sender_id,
                video=message.video.file_id,
                caption=caption,
                parse_mode="HTML"
            )

        elif msg_type == "voice":
            bot_msg = await bot.send_voice(
                chat_id=sender_id,
                voice=message.voice.file_id,
                caption=f"💬 <b>Anonim xabaringizga javob (ovozli)</b>{('\n\n' + replier_info) if replier_info else ''}",
                parse_mode="HTML"
            )

        elif msg_type == "audio":
            caption = f"💬 <b>Anonim xabaringizga javob (audio)</b>"
            if message.caption:
                caption += f"\n\n{message.caption}"
            if replier_info:
                caption += f"\n\n{replier_info}"
            bot_msg = await bot.send_audio(
                chat_id=sender_id,
                audio=message.audio.file_id,
                caption=caption,
                parse_mode="HTML"
            )

        elif msg_type == "document":
            caption = f"💬 <b>Anonim xabaringizga javob (fayl)</b>"
            if message.caption:
                caption += f"\n\n{message.caption}"
            if replier_info:
                caption += f"\n\n{replier_info}"
            bot_msg = await bot.send_document(
                chat_id=sender_id,
                document=message.document.file_id,
                caption=caption,
                parse_mode="HTML"
            )

        elif msg_type == "sticker":
            bot_msg = await bot.send_sticker(
                chat_id=sender_id,
                sticker=message.sticker.file_id
            )
            await bot.send_message(
                chat_id=sender_id,
                text=f"💬 <b>Anonim xabaringizga sticker bilan javob berildi</b>{('\n\n' + replier_info) if replier_info else ''}",
                parse_mode="HTML",
                reply_to_message_id=bot_msg.message_id
            )

        elif msg_type == "video_note":
            bot_msg = await bot.send_video_note(
                chat_id=sender_id,
                video_note=message.video_note.file_id
            )
            if replier_info:
                await bot.send_message(
                    chat_id=sender_id,
                    text=f"💬 <b>Video xabarga javob</b>\n\n{replier_info}",
                    parse_mode="HTML",
                    reply_to_message_id=bot_msg.message_id
                )

        elif msg_type == "animation":
            caption = f"💬 <b>Anonim xabaringizga javob (GIF)</b>"
            if message.caption:
                caption += f"\n\n{message.caption}"
            if replier_info:
                caption += f"\n\n{replier_info}"
            bot_msg = await bot.send_animation(
                chat_id=sender_id,
                animation=message.animation.file_id,
                caption=caption,
                parse_mode="HTML"
            )

        else:
            text = f"💬 <b>Anonim xabaringizga javob:</b>\n\n{message.text or '(bo\'sh)'}"
            if replier_info:
                text += f"\n\n{replier_info}"
            bot_msg = await bot.send_message(
                chat_id=sender_id,
                text=text,
                parse_mode="HTML"
            )

        if bot_msg:
            # Javobni ham bazaga saqlash (qayta reply uchun)
            await MessageDB.save_message(
                sender_id=user_id,
                receiver_id=sender_id,
                bot_message_id=bot_msg.message_id,
                message_type=msg_type
            )

            await message.answer(
                "✅ Javobingiz anonim yuborildi! 👻"
            )
        else:
            await message.answer("❌ Javobni yuborib bo'lmadi.")

    except Exception as e:
        print(f"Javob yuborishda xatolik: {e}")
        await message.answer(
            "❌ Javobni yuborib bo'lmadi.\n"
            "Foydalanuvchi botni bloklagan bo'lishi mumkin."
        )
