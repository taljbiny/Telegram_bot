from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import ReplyKeyboardRemove
from database import db
from keyboards.registration import *
from keyboards.main import main_menu_keyboard
from handlers.states import RegistrationStates
from utils.helpers import hash_password, validate_phone
from config import Config

async def start_registration(message: types.Message):
    """بدء عملية التسجيل"""
    # التحقق إذا كان لديه حساب
    if db.user_exists(message.from_user.id):
        await message.answer("✅ لديك حساب بالفعل!", reply_markup=main_menu_keyboard())
        return
    
    await message.answer(
        "📝 **إنشاء حساب جديد**\n\n"
        "لإنشاء حساب، نحتاج للمعلومات التالية:\n\n"
        "👤 **الخطوة 1:** أرسل اسم المستخدم المطلوب\n"
        "⚡ يجب أن يكون بين 3-20 حرفاً\n"
        "⚡ يمكن أن يحتوي على أحرف إنجليزية وأرقام و _",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove()
    )
    await RegistrationStates.waiting_for_username.set()

async def process_username(message: types.Message, state: FSMContext):
    """معالجة اسم المستخدم"""
    username = message.text.strip()
    
    # التحقق من الطول
    if len(username) < 3 or len(username) > 20:
        await message.answer("❌ اسم المستخدم يجب أن يكون بين 3-20 حرفاً")
        return
    
    # التحقق من الأحرف المسموحة
    if not username.replace('_', '').isalnum():
        await message.answer("❌ يمكن استخدام أحرف إنجليزية وأرقام و _ فقط")
        return
    
    # التحقق إذا كان الاسم مستخدم
    if db.username_taken(username):
        await message.answer("❌ هذا الاسم مستخدم بالفعل. اختر اسماً آخر")
        return
    
    await state.update_data(username=username)
    
    await message.answer(
        "🔐 **الخطوة 2:** أرسل كلمة السر\n"
        "⚡ يجب أن تكون بين 6-30 حرفاً\n"
        "⚡ يفضل أن تحتوي على أحرف وأرقام",
        parse_mode="Markdown"
    )
    await RegistrationStates.waiting_for_password.set()

async def process_password(message: types.Message, state: FSMContext):
    """معالجة كلمة السر"""
    password = message.text.strip()
    
    if len(password) < 6 or len(password) > 30:
        await message.answer("❌ كلمة السر يجب أن تكون بين 6-30 حرفاً")
        return
    
    # تشفير كلمة السر
    password_hash = hash_password(password)
    
    await state.update_data(password_hash=password_hash)
    
    await message.answer(
        "📱 **الخطوة 3 (اختياري):** أرسل رقم هاتفك\n\n"
        "💡 يمكنك تخطي هذه الخطوة بالضغط على الزر أدناه\n"
        "📞 مثال: 0991234567",
        parse_mode="Markdown",
        reply_markup=skip_phone_keyboard()
    )
    await RegistrationStates.waiting_for_phone.set()

async def process_phone(message: types.Message, state: FSMContext):
    """معالجة رقم الهاتف"""
    phone = message.text.strip()
    
    if not validate_phone(phone):
        await message.answer("❌ رقم الهاتف غير صحيح. يجب أن يبدأ بـ 09 ويتكون من 10 أرقام")
        return
    
    await state.update_data(phone=phone)
    
    # عرض البيانات للمراجعة
    data = await state.get_data()
    
    summary = f"""
📋 **مراجعة البيانات**

👤 **اسم المستخدم:** {data['username']}
📱 **الهاتف:** {phone}
    
✅ **هل البيانات صحيحة؟**"""
    
    await message.answer(
        summary,
        parse_mode="Markdown",
        reply_markup=confirm_registration_keyboard()
    )

async def skip_phone(callback: types.CallbackQuery, state: FSMContext):
    """تخطي إضافة الهاتف"""
    await state.update_data(phone=None)
    
    data = await state.get_data()
    
    summary = f"""
📋 **مراجعة البيانات**

👤 **اسم المستخدم:** {data['username']}
📱 **الهاتف:** غير مضاف
    
✅ **هل البيانات صحيحة؟**"""
    
    await callback.message.edit_text(
        summary,
        reply_markup=confirm_registration_keyboard()
    )
    await callback.answer()

async def confirm_registration(callback: types.CallbackQuery, state: FSMContext):
    """تأكيد التسجيل وإنشاء الحساب"""
    data = await state.get_data()
    user = callback.from_user
    
    # إنشاء الحساب
    success = db.create_user(
        telegram_id=user.id,
        username=data['username'],
        password_hash=data['password_hash'],
        phone=data.get('phone')
    )
    
    if success:
        await callback.message.edit_text(
            f"🎉 **تم إنشاء حسابك بنجاح!**\n\n"
            f"👤 **اسم المستخدم:** {data['username']}\n"
            f"💰 **الرصيد الحالي:** {Config.CURRENCY_SYMBOL}0\n\n"
            f"✅ **يمكنك الآن:**\n"
            f"• استخدام /deposit لشحن الرصيد\n"
            f"• استخدام /withdraw لسحب الأرباح\n"
            f"• استخدام /balance لعرض رصيدك",
            parse_mode="Markdown"
        )
        
        # إرسال إشعار للإدارة
        from bot import bot
        admin_message = f"""
👤 **مستخدم جديد**

🆔 **ID:** {user.id}
👤 **الاسم:** {user.first_name}
🆔 **Username:** @{user.username or 'لا يوجد'}
📝 **اسم المستخدم:** {data['username']}
📱 **الهاتف:** {data.get('phone') or 'غير مضاف'}
📅 **التاريخ:** {datetime.now().strftime('%Y-%m-%d %H:%M')}
"""
        
        for admin_id in Config.ADMIN_IDS:
            try:
                await bot.send_message(admin_id, admin_message)
            except:
                pass
    else:
        await callback.message.edit_text(
            "❌ **حدث خطأ!**\n\n"
            "لم نتمكن من إنشاء حسابك.\n"
            "قد يكون اسم المستخدم مستخدم بالفعل.\n\n"
            "حاول مرة أخرى باستخدام /register"
        )
    
    await state.finish()
    await callback.answer()
