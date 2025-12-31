from aiogram import types
from aiogram.dispatcher import FSMContext
from database import db
from keyboards.main import main_menu_keyboard
from config import Config
from utils.helpers import format_currency

async def cmd_start(message: types.Message):
    """بدء البوت والترحيب"""
    user = message.from_user
    
    # التحقق إذا كان المستخدم مسجل
    existing_user = db.get_user(user.id)
    
    if existing_user:
        welcome_text = f"""
👋 **أهلاً بعودتك {user.first_name}!**

💰 **رصيدك الحالي:** {format_currency(existing_user['balance'])}

اختر من القائمة أدناه 👇"""
        
        await message.answer(
            welcome_text,
            reply_markup=main_menu_keyboard(),
            parse_mode="Markdown"
        )
    else:
        await message.answer(
            f"🎉 **مرحباً {user.first_name}!**\n\n"
            f"🤖 **بوت المحفظة الإلكترونية**\n\n"
            f"✅ **مميزات البوت:**\n"
            f"• شحن رصيد بطرق متعددة\n"
            f"• سحب أرباح بسرعة\n"
            f"• نظام دعم فني 24/7\n"
            f"• أمان عالي\n\n"
            f"📝 **لإنشاء حساب:**\n"
            f"اضغط /register",
            parse_mode="Markdown"
        )

async def cmd_balance(message: types.Message):
    """عرض الرصيد"""
    user_data = db.get_user(message.from_user.id)
    
    if not user_data:
        await message.answer("⚠️ ليس لديك حساب. استخدم /register لإنشاء حساب")
        return
    
    balance_text = f"""
💰 **حسابك الشخصي**

💼 **الرصيد المتاح:** {format_currency(user_data['balance'])}
⏸️ **المجمد:** {format_currency(user_data['frozen_balance'])}
📥 **إجمالي الإيداعات:** {format_currency(user_data['total_deposited'])}
📤 **إجمالي السحوبات:** {format_currency(user_data['total_withdrawn'])}

📊 **الإجمالي:** {format_currency(user_data['balance'] + user_data['frozen_balance'])}
"""
    
    await message.answer(balance_text, parse_mode="Markdown")

async def cmd_history(message: types.Message):
    """سجل المعاملات"""
    user_data = db.get_user(message.from_user.id)
    
    if not user_data:
        await message.answer("⚠️ ليس لديك حساب")
        return
    
    # هنا يمكن إضافة استعلام لقاعدة البيانات
    await message.answer(
        "📋 **سجل المعاملات**\n\n"
        "سيتم إضافة هذه الميزة قريباً...",
        parse_mode="Markdown"
    )

async def cmd_settings(message: types.Message):
    """إعدادات الحساب"""
    user_data = db.get_user(message.from_user.id)
    
    if not user_data:
        await message.answer("⚠️ ليس لديك حساب")
        return
    
    settings_text = f"""
⚙️ **إعدادات الحساب**

👤 **اسم المستخدم:** {user_data['username']}
📱 **الهاتف:** {user_data['phone'] or 'غير مضاف'}
📅 **تاريخ التسجيل:** {user_data['created_at'][:10]}
💰 **حالة الحساب:** {user_data['status']}
"""
    
    await message.answer(settings_text, parse_mode="Markdown")

async def cancel_handler(message: types.Message, state: FSMContext):
    """إلغاء العملية الحالية"""
    current_state = await state.get_state()
    if current_state is None:
        return
    
    await state.finish()
    await message.answer("✅ تم الإلغاء", reply_markup=main_menu_keyboard())

async def cancel_handler_callback(callback: types.CallbackQuery, state: FSMContext):
    """إلغاء عبر كال باك"""
    await state.finish()
    await callback.message.edit_text("✅ تم الإلغاء")
    await callback.answer()
