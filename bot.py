import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import BotCommand

from config import Config
from handlers.commands import *
from handlers.callbacks import *
from handlers.admin import *
from handlers.payment import *
from handlers.support import *
from handlers.states import *

# إعدادات التسجيل
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def set_bot_commands(bot: Bot):
    """تعيين أوامر البوت"""
    commands = [
        BotCommand(command="start", description="بدء استخدام البوت"),
        BotCommand(command="balance", description="عرض الرصيد"),
        BotCommand(command="deposit", description="شحن الرصيد"),
        BotCommand(command="withdraw", description="سحب الرصيد"),
        BotCommand(command="history", description="سجل المعاملات"),
        BotCommand(command="support", description="الدعم الفني"),
        BotCommand(command="admin", description="لوحة الإدارة")
    ]
    await bot.set_my_commands(commands)

async def main():
    # التحقق من التوكن
    if not Config.BOT_TOKEN or Config.BOT_TOKEN == "ضع_التوكن_الجديد_هنا":
        logger.error("❌ لم يتم تعيين توكن البوت في ملف .env")
        return
    
    # تهيئة البوت
    bot = Bot(token=Config.BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(bot, storage=storage)
    
    # تعيين أوامر البوت
    await set_bot_commands(bot)
    
    # === تسجيل معالجي الأوامر ===
    
    # أوامر المستخدم
    dp.register_message_handler(cmd_start, commands=['start', 'register'])
    dp.register_message_handler(cmd_balance, commands=['balance'])
    dp.register_message_handler(cmd_deposit, commands=['deposit'])
    dp.register_message_handler(cmd_withdraw, commands=['withdraw'])
    dp.register_message_handler(cmd_history, commands=['history'])
    dp.register_message_handler(cmd_support, commands=['support'])
    
    # أوامر الإدارة
    dp.register_message_handler(admin_panel, commands=['admin'], state="*")
    
    # === تسجيل معالجي الدفع ===
    dp.register_message_handler(start_deposit, commands=['deposit'], state="*")
    dp.register_message_handler(process_deposit_amount, state=DepositStates.waiting_for_amount)
    dp.register_message_handler(process_deposit_receipt, content_types=['photo'], state=DepositStates.waiting_for_receipt)
    
    # === تسجيل معالجي الكال باك ===
    dp.register_callback_query_handler(process_deposit_method, lambda c: c.data.startswith('deposit_'), state=DepositStates.waiting_for_method)
    dp.register_callback_query_handler(process_admin_callback, lambda c: c.data.startswith('admin_'))
    dp.register_callback_query_handler(process_support_callback, lambda c: c.data.startswith('support_'))
    
    # === تسجيل معالجي الحالات ===
    dp.register_message_handler(cancel_handler, state="*", commands=['cancel'])
    
    # بدء البوت
    try:
        logger.info("🚀 بدء تشغيل البوت...")
        await dp.start_polling()
    except Exception as e:
        logger.error(f"❌ خطأ في تشغيل البوت: {e}")
    finally:
        await dp.storage.close()
        await dp.storage.wait_closed()
        await bot.session.close()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("⏹️ إيقاف البوت...")
