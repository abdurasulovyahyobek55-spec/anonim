import os
from aiohttp import web  # Buni qo'shish kerak
import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from config import BOT_TOKEN
from database.db import init_db
from middlewares.logging import UserLoggingMiddleware
from handlers.start import router as start_router
from handlers.admin import router as admin_router
from handlers.message import router as message_router
from handlers.reply import router as reply_router
async def handle(request):
    return web.Response(text="Bot is running!")

async def main():
    # Logging sozlash
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

    if not BOT_TOKEN:
        logging.error("XATO: .env faylida BOT_TOKEN topilmadi!")
        return
# 2. Render uchun portni ochish (Veb-serverni ishga tushirish)
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    # Render avtomatik PORT o'zgaruvchisini beradi, bo'lmasa 8080 ishlatiladi
    site = web.TCPSite(runner, '0.0.0.0', int(os.environ.get("PORT", 8080)))
    await site.start()
    logging.info("Veb-server (port) ishga tushdi.")
    
    # Ma'lumotlar bazasini ishga tushirish
    await init_db()
    logging.info("Ma'lumotlar bazasi muvaffaqiyatli ishga tushirildi.")

    # Bot va Dispatcher yaratish
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()

    # Middleware ro'yxatdan o'tkazish
    dp.message.middleware(UserLoggingMiddleware())

    # Routerlarni ulash (tartib muhim!)
    dp.include_router(admin_router)
    dp.include_router(start_router)
    dp.include_router(reply_router)
    dp.include_router(message_router)  # Message oxirida tursin, chunki u "/" bo'lmagan barcha matnlarni tutadi

   # Polling boshlash
    logging.info("Bot ishga tushmoqda...")
    try:
        # Eski so'rovlarni tozalash (Conflict oldini olish uchun)
        await bot.delete_webhook(drop_pending_updates=True) 
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
