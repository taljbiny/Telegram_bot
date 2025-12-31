from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ReplyKeyboardRemove
from database import db
from keyboards.registration_simple import *
from config import Config
import hashlib

class SimpleRegistrationStates(StatesGroup):
    waiting_for_username = State()
    waiting_for_password = State()
    waiting_for_phone = State()  # اختياري

async def start_simple_registration(message: types.Message):
    """بدء تسجيل مبسط"""
    user = db.get_user(message.from_user.id)
    
    if user:
        await message.answer("✅ لديك حساب نشط بالفعل!")
        return
    
    await message.answer(
        "📝 **إنشاء حساب جديد**\n\n"
        "لإنشاء حساب، أدخل المعلومات التالية:\n\n"
        "👤 **الخطوة 1:** أرسل اسم المستخدم المطلوب\n"
        "⚡ يجب أن يكون بين 3-20 حرفاً\n"
        "⚡ يمكن أن يحتوي على أحرف وأرقام و _",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove()
    )
    await SimpleRegistrationStates.waiting_for_username.set()

async def process_username(message: types.Message, state: FSMContext):
    """معالجة اسم المستخدم"""
    username = message.text.strip()
    
    # التحقق من صحة اسم المستخدم
    if len(username) < 3 or len(username) > 20:
        await message.answer("❌ اسم المستخدم يجب أن يكون بين 3-20 حرفاً")
        return
    
    if not username.replace('_', '').isalnum():
        await message.answer("❌ يمكن استخدام أحرف إنجليزية وأرقام و _ فقط")
        return
    
    # التحقق إذا كان اسم المستخدم مستخدم مسبقاً
    if db.is_username_taken(username):
        await message.answer("❌ اسم المستخدم هذا مستخدم بالفعل. اختر اسماً آخر")
        return
    
    await state.update_data(username=username)
    
    await message.answer(
        "🔐 **الخطوة 2:** أرسل كلمة السر\n"
        "⚡ يجب أن تكون بين 6-30 حرفاً\n"
        "⚡ يفضل أن تحتوي على أحرف وأرقام",
        parse_mode="Markdown"
    )
    await SimpleRegistrationStates.waiting_for_password.set()

async def process_password(message: types.Message, state: FSMContext):
    """معالجة كلمة السر"""
    password = message.text.strip()
    
    if len(password) < 6 or len(password) > 30:
        await message.answer("❌ كلمة السر يجب أن تكون بين 6-30 حرفاً")
        return
    
    # تشفير كلمة السر
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    await state.update_data(password_hash=password_hash)
    
    await message.answer(
        "📱 **الخطوة 3 (اختياري):** أرسل رقم هاتفك\n\n"
        "💡 يمكنك تخطي هذه الخطوة بالضغط على /skip\n"
        "📞 مثال: 0991234567",
        parse_mode="Markdown",
        reply_markup=skip_phone_keyboard()
    )
    await SimpleRegistrationStates.waiting_for_phone.set()

async def process_phone_or_skip(message: types.Message, state: FSMContext):
    """معالجة رقم الهاتف أو التخطي"""
    if message.text == '/skip':
        phone = None
    else:
        phone = message.text.strip()
        
        # تحقق بسيط من رقم الهاتف
        if not phone.isdigit() or len(phone) != 10 or not phone.startswith('09'):
            await message.answer("❌ رقم الهاتف غير صحيح. استخدم /skip للتخطي")
            return
        
        if db.is_phone_registered(phone):
            await message.answer("❌ هذا الرقم مسجل بالفعل. استخدم /skip للتخطي")
            return
    
    data = await state.get_data()
    
    # إنشاء الحساب
    db.create_simple_user(
        telegram_id=message.from_user.id,
        username=data['username'],
        password_hash=data['password_hash'],
        phone_number=phone,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name
    )
    
    await message.answer(
        f"🎉 **تم إنشاء حسابك بنجاح!**\n\n"
        f"👤 **اسم المستخدم:** {data['username']}\n"
        f"📱 **الهاتف:** {phone if phone else 'غير مضاف'}\n"
        f"💰 **الرصيد الحالي:** {Config.CURRENCY_SYMBOL}0\n\n"
        f"✅ يمكنك الآن استخدام جميع الخدمات:\n"
        f"• /deposit - شحن الرصيد\n"
        f"• /balance - عرض الرصيد\n"
        f"• /withdraw - سحب الأرباح",
        parse_mode="Markdown",
        reply_markup=main_menu_after_registration()
    )
    
    await state.finish()
