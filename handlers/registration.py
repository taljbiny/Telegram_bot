from aiogram import types
from aiogram.dispatcher import FSMContext
from database import db
from handlers.states import RegistrationStates
from config import Config
import hashlib
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def skip_phone_keyboard():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("⏭️ تخطي", callback_data="skip_phone"))
    return keyboard

async def start_registration(message: types.Message):
    if db.user_exists(message.from_user.id):
        await message.answer("✅ لديك حساب بالفعل!")
        return
    
    await message.answer(
        "📝 **إنشاء حساب جديد**\n\n"
        "👤 **الخطوة 1:** أرسل اسم المستخدم\n"
        "(3-20 حرف، إنجليزية وأرقام و _)",
        parse_mode="Markdown"
    )
    await RegistrationStates.waiting_for.username.set()

async def process_username(message: types.Message, state: FSMContext):
    username = message.text.strip()
    
    if len(username) < 3 or len(username) > 20:
        await message.answer("❌ الاسم يجب أن يكون 3-20 حرف")
        return
    
    if not username.replace('_', '').isalnum():
        await message.answer("❌ أحرف إنجليزية وأرقام و _ فقط")
        return
    
    if db.username_taken(username):
        await message.answer("❌ الاسم مستخدم. اختر غيره")
        return
    
    await state.update_data(username=username)
    
    await message.answer(
        "🔐 **الخطوة 2:** أرسل كلمة السر\n"
        "(6-30 حرف)",
        parse_mode="Markdown"
    )
    await RegistrationStates.waiting_for_password.set()

async def process_password(message: types.Message, state: FSMContext):
    password = message.text.strip()
    
    if len(password) < 6 or len(password) > 30:
        await message.answer("❌ كلمة السر 6-30 حرف")
        return
    
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    await state.update_data(password_hash=password_hash)
    
    await message.answer(
        "📱 **الخطوة 3 (اختياري):** أرسل رقم هاتفك\n"
        "مثال: 0991234567\n\n"
        "أو اضغط تخطي:",
        reply_markup=skip_phone_keyboard(),
        parse_mode="Markdown"
    )
    await RegistrationStates.waiting_for_phone.set()

async def process_phone(message: types.Message, state: FSMContext):
    phone = message.text.strip()
    
    if not phone.isdigit() or len(phone) != 10 or not phone.startswith('09'):
        await message.answer("❌ رقم غير صحيح. مثال: 0991234567")
        return
    
    await create_user_account(message, state, phone)

async def skip_phone(callback: types.CallbackQuery, state: FSMContext):
    await create_user_account(callback.message, state, None)
    await callback.answer()

async def create_user_account(message, state, phone):
    data = await state.get_data()
    user = message.from_user if hasattr(message, 'from_user') else callback.message.from_user
    
    success = db.create_user(
        telegram_id=user.id,
        username=data['username'],
        password_hash=data['password_hash'],
        phone=phone
    )
    
    if success:
        text = (
            f"🎉 **تم إنشاء حسابك!**\n\n"
            f"👤 **اسم المستخدم:** {data['username']}\n"
            f"📱 **الهاتف:** {phone if phone else 'غير مضاف'}\n"
            f"💰 **رصيدك:** 0 {Config.CURRENCY_SYMBOL}\n\n"
            f"✅ **يمكنك الآن:**\n"
            f"• /deposit - شحن الرصيد\n"
            f"• /withdraw - سحب الأرباح"
        )
    else:
        text = "❌ فشل إنشاء الحساب. حاول مجدداً"
    
    if hasattr(message, 'answer'):
        await message.answer(text, parse_mode="Markdown")
    else:
        await message.edit_text(text, parse_mode="Markdown")
    
    await state.finish()
