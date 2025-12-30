import asyncio
import logging
import sys
import os
from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import BotCommand
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import Config
from handlers.commands import *
# ... باقي الاستيرادات

async def on_startup(dp):
    """تشغيل عند بدء البوت"""
    logging.info("🚀 البوت يعمل على Render!")
    
    # جدولة مهام تلقائية (اختياري)
    scheduler = AsyncIOScheduler()
    scheduler.add_job(check_pending_requests, 'interval', minutes=30)
    scheduler.start()

async def on_shutdown(dp):
    """تشغيل عند إيقاف البوت"""
    logging.info("⏹️ إيقاف البوت...")
    await dp.storage.close()
    await dp.storage.wait_closed()

async def main():
    # إعدادات التسجيل
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        stream=sys.stdout
    )
    logger = logging.getLogger(__name__)
    
    # التحقق من المتغيرات البيئية
    required_vars = ['BOT_TOKEN', 'ADMIN_IDS']
    for var in required_vars:
        if not os.getenv(var):
            logger.error(f"❌ المتغير البيئي {var} غير معرّف")
            sys.exit(1)
    
    bot = Bot(token=Config.BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(bot, storage=storage)
    
    # تسجيل المعالجين (كما في السابق)
    # ...
    
    try:
        await on_startup(dp)
        await dp.start_polling()
    finally:
        await on_shutdown(dp)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("✅ البوت توقف بشكل طبيعي")
