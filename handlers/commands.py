from aiogram import types
from aiogram.dispatcher import FSMContext
from database import db
from config import Config

async def cmd_start(message: types.Message):
    user = message.from_user
    
    if db.user_exists(user.id):
        user_data = db.get_user(user.id)
        await message.answer(
            f"👋 أهلاً بعودتك {user.first_name}!\n"
            f"💰 رصيدك: {user_data['balance']:,} {Config.CURRENCY_SYMBOL}\n\n"
            "📋 **القائمة:**\n"
            "/balance - رصيدي\n"
            "/deposit - شحن رصيد\n" 
            "/withdraw - سحب رصيد\n"
            "/history - السجل\n"
            "/support - الدعم",
            parse_mode="Markdown"
        )
    else:
        await message.answer(
            f"🎉 أهلاً {user.first_name}!\n\n"
            "🤖 **بوت المحفظة الذكية**\n\n"
            "📝 لإنشاء حساب:\n"
            "/register\n\n"
            "✅ المميزات:\n"
            "• شحن رصيد بطرق متعددة\n"
            "• سحب أرباح بسرعة\n"
            "• نظام آمن ومباشر",
            parse_mode="Markdown"
        )

async def cmd_balance(message: types.Message):
    user_data = db.get_user(message.from_user.id)
    
    if not user_data:
        await message.answer("⚠️ ليس لديك حساب. استخدم /register")
        return
    
    await message.answer(
        f"💰 **حسابك الشخصي**\n\n"
        f"💼 الرصيد: {user_data['balance']:,} {Config.CURRENCY_SYMBOL}\n"
        f"📥 الإيداعات: {user_data['total_deposited']:,}\n"
        f"📤 السحوبات: {user_data['total_withdrawn']:,}",
        parse_mode="Markdown"
    )

async def cmd_history(message: types.Message):
    await message.answer(
        "📋 **سجل المعاملات**\n\n"
        "سيتم إضافة هذه الميزة قريباً...",
        parse_mode="Markdown"
    )

async def cmd_support(message: types.Message):
    await message.answer(
        "🛟 **الدعم الفني**\n\n"
        "📞 للإبلاغ عن مشكلة أو استفسار:\n"
        f"{Config.SUPPORT_USERNAME}\n\n"
        "⏰ متاح 24/7",
        parse_mode="Markdown"
    )

async def cancel_handler(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer("✅ تم الإلغاء")
