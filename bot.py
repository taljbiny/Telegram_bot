import os
import sys
import asyncio
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

async def main():
    logger.info("🚀 بدء تشغيل البوت على Render...")
    
    # الحصول على التوكن
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN غير موجود")
        return
    
    logger.info(f"✅ التوكن: {BOT_TOKEN[:10]}...")
    
    # تثبيت aiogram 2.x إذا لم يكن مثبت
    try:
        from aiogram import Bot, Dispatcher, types
        from aiogram.contrib.fsm_storage.memory import MemoryStorage
        logger.info("✅ aiogram 2.x محمل")
    except ImportError:
        logger.info("🔧 تثبيت aiogram 2.x...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "aiogram==2.25.1"])
        from aiogram import Bot, Dispatcher, types
        from aiogram.contrib.fsm_storage.memory import MemoryStorage
    
    # إنشاء البوت
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(bot, storage=MemoryStorage())
    
    @dp.message_handler(commands=['start'])
    async def cmd_start(message: types.Message):
        await message.answer("🎉 **البوت شغال!**\n\n✅ التسجيل: /register\n💰 الإيداع: /deposit")
    
    @dp.message_handler(commands=['register'])
    async def cmd_register(message: types.Message):
        await message.answer("📝 **التسجيل:**\nأرسل اسم المستخدم:")
    
    @dp.message_handler(commands=['deposit'])
    async def cmd_deposit(message: types.Message):
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        
        keyboard = InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            InlineKeyboardButton("💳 شام كاش", callback_data="deposit_sham"),
            InlineKeyboardButton("📱 سيرياتيل", callback_data="deposit_syriatel"),
            InlineKeyboardButton("₿ Ethereum", callback_data="deposit_ethereum")
        )
        
        await message.answer("💳 **اختر طريقة الدفع:**", reply_markup=keyboard)
    
    @dp.callback_query_handler(lambda c: c.data.startswith('deposit_'))
    async def process_deposit(callback_query: types.CallbackQuery):
        method = callback_query.data.split('_')[1]
        methods = {
            'sham': 'شام كاش: 19f013ef640f4ab20aace84b8a617bd6',
            'syriatel': 'سيرياتيل: 0996099355',
            'ethereum': 'Ethereum: 0x2abf01f2d131b83f7a9b2b9642638ebcaab67c43'
        }
        
        await callback_query.message.answer(
            f"💳 **{method}**\n\n"
            f"🆔 **الحساب:**\n{methods[method]}\n\n"
            f"💰 **أدخل المبلغ:**",
            parse_mode="Markdown"
        )
        await callback_query.answer()
    
    # التحقق من الإدارة
    ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "8219716285").split(',')]
    
    @dp.message_handler(commands=['admin'])
    async def cmd_admin(message: types.Message):
        if message.from_user.id in ADMIN_IDS:
            await message.answer("👑 **لوحة الإدارة**\n\n📊 الإحصائيات قريباً...")
        else:
            await message.answer("⛔ غير مصرح")
    
    logger.info("🤖 البوت جاهز...")
    await dp.start_polling()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("⏹️ إيقاف البوت")
    except Exception as e:
        logger.error(f"❌ خطأ: {e}")
