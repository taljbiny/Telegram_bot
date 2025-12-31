import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import BotCommand

from config import Config
from database import db

# استيراد المعالجات
from handlers.commands import *
from handlers.registration import *
from handlers.deposit import *
from handlers.withdraw import *
from handlers.admin import *

# استيراد الحالات
from handlers.states import *

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def set_bot_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description="بدء البوت"),
        BotCommand(command="balance", description="رصيدي"),
        BotCommand(command="deposit", description="شحن الرصيد"),
        BotCommand(command="withdraw", description="سحب الأرباح"),
        BotCommand(command="history", description="السجل"),
        BotCommand(command="support", description="الدعم"),
        BotCommand(command="admin", description="الإدارة")
    ]
    await bot.set_my_commands(commands)

async def main():
    # التحقق من التوكن
    if not Config.BOT_TOKEN:
        logger.error("❌ لم يتم تعيين BOT_TOKEN في ملف .env")
        print("🔧 أضف التوكن في ملف .env:")
        print("BOT_TOKEN=توكن_البوت_هنا")
        return
    
    bot = Bot(token=Config.BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(bot, storage=storage)
    
    await set_bot_commands(bot)
    
    # ===== تسجيل المعالجات =====
    
    # الأوامر الأساسية
    dp.register_message_handler(cmd_start, commands=['start'])
    dp.register_message_handler(cmd_balance, commands=['balance'])
    dp.register_message_handler(cmd_history, commands=['history'])
    dp.register_message_handler(cmd_support, commands=['support'])
    
    # التسجيل
    dp.register_message_handler(start_registration, commands=['register'])
    dp.register_message_handler(process_username, state=RegistrationStates.waiting_for_username)
    dp.register_message_handler(process_password, state=RegistrationStates.waiting_for_password)
    dp.register_message_handler(process_phone, state=RegistrationStates.waiting_for_phone)
    dp.register_callback_query_handler(skip_phone, lambda c: c.data == 'skip_phone')
    
    # الإيداع
    dp.register_message_handler(start_deposit, commands=['deposit'])
    dp.register_callback_query_handler(process_deposit_method, lambda c: c.data.startswith('deposit_'))
    dp.register_message_handler(process_deposit_amount, state=DepositStates.waiting_for_amount)
    dp.register_message_handler(process_transaction_id, state=DepositStates.waiting_for_transaction_id)
    dp.register_callback_query_handler(cancel_deposit, lambda c: c.data == 'cancel_deposit')
    
    # السحب
    dp.register_message_handler(start_withdrawal, commands=['withdraw'])
    dp.register_message_handler(process_withdrawal_amount, state=WithdrawalStates.waiting_for_amount)
    dp.register_callback_query_handler(process_withdrawal_method, lambda c: c.data.startswith('withdraw_'))
    dp.register_message_handler(process_wallet_info, state=WithdrawalStates.waiting_for_wallet)
    
    # الإدارة
    dp.register_message_handler(admin_panel, commands=['admin'])
    dp.register_message_handler(admin_deposits, commands=['admin_deposits'])
    dp.register_message_handler(admin_withdrawals, commands=['admin_withdrawals'])
    dp.register_callback_query_handler(admin_approve_deposit, lambda c: c.data.startswith('admin_approve_deposit_'))
    dp.register_callback_query_handler(admin_approve_withdrawal, lambda c: c.data.startswith('admin_approve_withdrawal_'))
    
    # إلغاء
    dp.register_message_handler(cancel_handler, commands=['cancel'], state="*")
    
    # بدء البوت
    logger.info("🚀 بدء تشغيل البوت...")
    try:
        await dp.start_polling()
    finally:
        await dp.storage.close()
        await dp.storage.wait_closed()

if __name__ == '__main__':
    asyncio.run(main())
