import asyncio
import logging
import os
import sys
from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import BotCommand

from config import Config
from database import db

# استيراد جميع المعالجات
from handlers.commands import *
from handlers.registration import *
from handlers.deposit import *
from handlers.withdraw import *
from handlers.admin import *
from handlers.support import *

# استيراد الحالات
from handlers.states import *

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

async def set_bot_commands(bot: Bot):
    """تعيين أوامر البوت"""
    commands = [
        BotCommand(command="start", description="بدء/إنشاء حساب"),
        BotCommand(command="balance", description="عرض الرصيد"),
        BotCommand(command="deposit", description="شحن الرصيد"),
        BotCommand(command="withdraw", description="سحب الأرباح"),
        BotCommand(command="history", description="سجل المعاملات"),
        BotCommand(command="support", description="الدعم الفني"),
        BotCommand(command="admin", description="لوحة الإدارة")
    ]
    await bot.set_my_commands(commands)

def setup_handlers(dp: Dispatcher):
    """إعداد جميع المعالجات"""
    # الأوامر الأساسية
    dp.register_message_handler(cmd_start, commands=['start'])
    dp.register_message_handler(cmd_balance, commands=['balance'])
    dp.register_message_handler(cmd_history, commands=['history'])
    dp.register_message_handler(cmd_settings, commands=['settings'])
    
    # التسجيل
    dp.register_message_handler(start_registration, commands=['register'])
    dp.register_message_handler(process_username, state=RegistrationStates.waiting_for_username)
    dp.register_message_handler(process_password, state=RegistrationStates.waiting_for_password)
    dp.register_message_handler(process_phone, state=RegistrationStates.waiting_for_phone)
    dp.register_callback_query_handler(confirm_registration, lambda c: c.data == 'confirm_registration')
    dp.register_callback_query_handler(skip_phone, lambda c: c.data == 'skip_phone')
    
    # الإيداع
    dp.register_message_handler(start_deposit, commands=['deposit'])
    dp.register_callback_query_handler(process_deposit_method, lambda c: c.data.startswith('deposit_'))
    dp.register_message_handler(process_deposit_amount, state=DepositStates.waiting_for_amount)
    dp.register_message_handler(process_transaction_id, state=DepositStates.waiting_for_transaction_id)
    dp.register_callback_query_handler(confirm_deposit_request, lambda c: c.data.startswith('confirm_deposit_'))
    
    # السحب
    dp.register_message_handler(start_withdrawal, commands=['withdraw'])
    dp.register_message_handler(process_withdrawal_amount, state=WithdrawalStates.waiting_for_amount)
    dp.register_callback_query_handler(process_withdrawal_method, lambda c: c.data.startswith('withdraw_'))
    dp.register_message_handler(process_wallet_info, state=WithdrawalStates.waiting_for_wallet)
    dp.register_callback_query_handler(confirm_withdrawal_request, lambda c: c.data.startswith('confirm_withdrawal_'))
    
    # الدعم
    dp.register_message_handler(support_menu, commands=['support'])
    dp.register_callback_query_handler(contact_support, lambda c: c.data == 'contact_support')
    dp.register_message_handler(process_support_message, state=SupportStates.waiting_for_message)
    
    # الإدارة
    dp.register_message_handler(admin_panel, commands=['admin'])
    dp.register_callback_query_handler(admin_stats, lambda c: c.data == 'admin_stats')
    dp.register_callback_query_handler(admin_deposits, lambda c: c.data == 'admin_deposits')
    dp.register_callback_query_handler(admin_withdrawals, lambda c: c.data == 'admin_withdrawals')
    dp.register_callback_query_handler(admin_tickets, lambda c: c.data == 'admin_tickets')
    dp.register_callback_query_handler(admin_approve_deposit, lambda c: c.data.startswith('approve_deposit_'))
    dp.register_callback_query_handler(admin_reject_deposit, lambda c: c.data.startswith('reject_deposit_'))
    dp.register_callback_query_handler(admin_approve_withdrawal, lambda c: c.data.startswith('approve_withdrawal_'))
    dp.register_callback_query_handler(admin_reject_withdrawal, lambda c: c.data.startswith('reject_withdrawal_'))
    dp.register_callback_query_handler(admin_reply_ticket, lambda c: c.data.startswith('reply_ticket_'))
    
    # إلغاء
    dp.register_message_handler(cancel_handler, commands=['cancel'], state="*")
    dp.register_callback_query_handler(cancel_handler_callback, lambda c: c.data.startswith('cancel'), state="*")

async def main():
    # التحقق من التوكن
    if not Config.BOT_TOKEN or Config.BOT_TOKEN == "ضع_التوكن_هنا":
        logger.error("❌ لم يتم تعيين توكن البوت في ملف .env")
        # على Render، استخدم متغيرات البيئة
        token = os.getenv('BOT_TOKEN')
        if not token:
            logger.error("❌ لم يتم العثور على BOT_TOKEN في متغيرات البيئة")
            return
        # تحديث التوكن في Config
        Config.BOT_TOKEN = token
    
    bot = Bot(token=Config.BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(bot, storage=storage)
    
    await set_bot_commands(bot)
    setup_handlers(dp)
    
    try:
        logger.info("🚀 بدء تشغيل البوت على Render...")
        await dp.start_polling()
    except Exception as e:
        logger.error(f"❌ خطأ في تشغيل البوت: {e}")
    finally:
        await dp.storage.close()
        await dp.storage.wait_closed()

if __name__ == '__main__':
    # التحقق من أننا على Render
    if os.getenv('RENDER'):
        logger.info("🌐 التشغيل على Render")
    
    asyncio.run(main())
