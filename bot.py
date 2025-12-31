import os
import sys
import asyncio
import logging

# إعدادات التسجيل
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
        logger.error("❌ BOT_TOKEN غير موجود في Environment Variables")
        logger.info("🔧 أضفه في Render Dashboard → Environment")
        return
    
    logger.info(f"✅ التوكن: {BOT_TOKEN[:10]}...")
    
    # محاولة استيراد aiogram
    try:
        from aiogram import Bot, Dispatcher, types
        from aiogram.contrib.fsm_storage.memory import MemoryStorage
        logger.info("✅ تم تحميل aiogram بنجاح")
    except ImportError:
        logger.error("❌ aiogram غير مثبت")
        logger.info("🔧 جاري التثبيت...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "aiogram[fast]"])
        from aiogram import Bot, Dispatcher, types
        from aiogram.contrib.fsm_storage.memory import MemoryStorage
        logger.info("✅ تم تثبيت aiogram")
    
    # تهيئة البوت
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(bot, storage=MemoryStorage())
    
    # الأوامر الأساسية
    @dp.message_handler(commands=['start'])
    async def cmd_start(message: types.Message):
        await message.answer("🎉 **البوت شغال على Render!**\n\n/help للمساعدة", parse_mode="Markdown")
    
    @dp.message_handler(commands=['help'])
    async def cmd_help(message: types.Message):
        await message.answer(
            "📋 **الأوامر المتاحة:**\n"
            "/start - بدء البوت\n"
            "/deposit - شحن الرصيد\n"
            "/withdraw - سحب الأرباح\n"
            "/balance - رصيدي\n"
            "/admin - لوحة الإدارة",
            parse_mode="Markdown"
        )
    
    @dp.message_handler(commands=['deposit'])
    async def cmd_deposit(message: types.Message):
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        
        keyboard = InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            InlineKeyboardButton("💳 شام كاش", callback_data="deposit_sham"),
            InlineKeyboardButton("📱 سيرياتيل", callback_data="deposit_syriatel")
        )
        
        await message.answer(
            "💳 **اختر طريقة الدفع:**\n\n"
            "💰 الحد الأدنى: 25,000 S.P",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    
    # التحقق من الإدارة
    ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "8219716285").split(',')]
    
    @dp.message_handler(commands=['admin'])
    async def cmd_admin(message: types.Message):
        if message.from_user.id in ADMIN_IDS:
            await message.answer("👑 **لوحة الإدارة**\n\n📊 جاهزة للاستخدام", parse_mode="Markdown")
        else:
            await message.answer("⛔ غير مصرح لك")
    
    # بدء البوت
    logger.info("🤖 البوت جاهز لاستقبال الرسائل...")
    await dp.start_polling()

if __name__ == "__main__":
    if os.getenv('RENDER'):
        logger.info("🌐 التشغيل على Render.com")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("⏹️ إيقاف البوت...")
    except Exception as e:
        logger.error(f"❌ خطأ: {e}")
