from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ReplyKeyboardRemove, ContentType
from database import db
from keyboards.registration import *
from config import Config
import re

class RegistrationStates(StatesGroup):
    waiting_for_phone = State()
    waiting_for_email = State()
    waiting_for_country = State()
    waiting_for_id_card = State()
    waiting_for_selfie = State()
    waiting_for_confirmation = State()

async def start_registration(message: types.Message):
    """بدء عملية التسجيل"""
    # التحقق إذا كان لدى المستخدم حساب مرفوض
    user = db.get_user(message.from_user.id)
    
    if user and user['status'] == 'rejected':
        await message.answer(
            f"⚠️ طلب التسجيل السابق مرفوض\n"
            f"السبب: {user['rejection_reason']}\n\n"
            f"هل تريد إعادة التسجيل؟",
            reply_markup=retry_registration_keyboard()
        )
        return
    
    if user and user['status'] == 'active':
        await message.answer("✅ لديك حساب نشط بالفعل!")
        return
    
    await message.answer(
        "📝 **إنشاء حساب جديد**\n\n"
        "لإنشاء حساب، نحتاج للمعلومات التالية:\n"
        "1. رقم الهاتف\n"
        "2. البريد الإلكتروني\n"
        "3. الدولة\n"
        "4. صورة الهوية\n"
        "5. سيلفي مع الهوية\n\n"
        "📱 **الخطوة الأولى:** أرسل رقم هاتفك (مثال: 0996099355)",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove()
    )
    await RegistrationStates.waiting_for_phone.set()

async def process_phone(message: types.Message, state: FSMContext):
    """معالجة رقم الهاتف"""
    phone = message.text.strip()
    
    # التحقق من رقم الهاتف السوري
    if not re.match(r'^09\d{8}$', phone):
        await message.answer("❌ رقم الهاتف غير صحيح. الرجاء إدخال رقم سوري صحيح (مثال: 0996099355)")
        return
    
    # التحقق إذا الرقم مسجل مسبقاً
    if db.is_phone_registered(phone):
        await message.answer("❌ هذا الرقم مسجل بالفعل في حساب آخر")
        return
    
    await state.update_data(phone=phone)
    await message.answer(
        "📧 **الخطوة الثانية:** أرسل بريدك الإلكتروني",
        parse_mode="Markdown"
    )
    await RegistrationStates.waiting_for_email.set()

async def process_email(message: types.Message, state: FSMContext):
    """معالجة البريد الإلكتروني"""
    email = message.text.strip()
    
    # تحقق بسيط من صحة الإيميل
    if '@' not in email or '.' not in email:
        await message.answer("❌ البريد الإلكتروني غير صحيح. الرجاء إدخال بريد صحيح")
        return
    
    if db.is_email_registered(email):
        await message.answer("❌ هذا البريد مسجل بالفعل في حساب آخر")
        return
    
    await state.update_data(email=email)
    await message.answer(
        "🌍 **الخطوة الثالثة:** أرسل اسم دولتك",
        parse_mode="Markdown",
        reply_markup=country_keyboard()
    )
    await RegistrationStates.waiting_for_country.set()

async def process_country(message: types.Message, state: FSMContext):
    """معالجة الدولة"""
    country = message.text.strip()
    await state.update_data(country=country)
    await message.answer(
        "🆔 **الخطوة الرابعة:** أرسل صورة هويتك (جواز سفر أو رخصة قيادة أو هوية)\n\n"
        "⚠️ يجب أن تكون الصورة واضحة وتظهر جميع البيانات",
        parse_mode="Markdown"
    )
    await RegistrationStates.waiting_for_id_card.set()

async def process_id_card(message: types.Message, state: FSMContext):
    """معالجة صورة الهوية"""
    if not message.photo:
        await message.answer("❌ الرجاء إرسال صورة الهوية")
        return
    
    # حفظ صورة الهوية
    id_card_file_id = message.photo[-1].file_id
    await state.update_data(id_card=id_card_file_id)
    
    await message.answer(
        "🤳 **الخطوة الخامسة:** أرسل سيلفي مع هويتك\n\n"
        "⚠️ يجب أن تكون واضحة وتظهر وجهك والهوية معاً",
        parse_mode="Markdown"
    )
    await RegistrationStates.waiting_for_selfie.set()

async def process_selfie(message: types.Message, state: FSMContext):
    """معالجة صورة السيلفي"""
    if not message.photo:
        await message.answer("❌ الرجاء إرسال صورة السيلفي")
        return
    
    selfie_file_id = message.photo[-1].file_id
    await state.update_data(selfie=selfie_file_id)
    
    # عرض جميع البيانات للمراجعة
    data = await state.get_data()
    
    summary = f"""
📋 **ملخص البيانات للمراجعة:**

📱 **الهاتف:** {data['phone']}
📧 **الإيميل:** {data['email']}
🌍 **الدولة:** {data['country']}
🆔 **الهوية:** ✅ مرفوعة
🤳 **السيلفي:** ✅ مرفوع

⚠️ **ملاحظة:** سيتم مراجعة طلبك من الإدارة خلال 24 ساعة
✅ **سيتم إعلامك فور الموافقة**
    """
    
    await message.answer_photo(
        photo=selfie_file_id,
        caption=summary,
        parse_mode="Markdown",
        reply_markup=confirm_registration_keyboard()
    )
    await RegistrationStates.waiting_for_confirmation.set()

async def confirm_registration(callback: types.CallbackQuery, state: FSMContext):
    """تأكيد التسجيل وإرساله للإدارة"""
    data = await state.get_data()
    user = callback.from_user
    
    # حفظ المستخدم بحالة pending
    db.create_pending_user(
        telegram_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        phone=data['phone'],
        email=data['email'],
        country=data['country'],
        id_card_image=data['id_card'],
        selfie_image=data['selfie']
    )
    
    # إرسال للإدارة للموافقة
    from bot import bot
    admin_message = f"""
📋 **طلب تسجيل جديد #{user.id}**

👤 **المستخدم:** {user.first_name} {user.last_name or ''}
🆔 **Username:** @{user.username or 'لا يوجد'}
📱 **الهاتف:** {data['phone']}
📧 **الإيميل:** {data['email']}
🌍 **الدولة:** {data['country']}
📅 **التاريخ:** {datetime.now().strftime('%Y-%m-%d %H:%M')}
    """
    
    for admin_id in Config.ADMIN_IDS:
        try:
            # إرسال صورة الهوية
            await bot.send_photo(
                chat_id=admin_id,
                photo=data['id_card'],
                caption=f"{admin_message}\n\n🆔 **صورة الهوية:**"
            )
            
            # إرسال صورة السيلفي
            await bot.send_photo(
                chat_id=admin_id,
                photo=data['selfie'],
                caption="🤳 **صورة السيلفي مع الهوية**",
                reply_markup=admin_approval_keyboard(user.id)
            )
        except Exception as e:
            print(f"خطأ في إرسال للإدارة: {e}")
    
    await callback.message.edit_caption(
        "✅ **تم إرسال طلب التسجيل للإدارة**\n\n"
        "⏳ جاري مراجعة البيانات...\n"
        "📩 سيتم إعلامك فور الموافقة على حسابك",
        reply_markup=None
    )
    await state.finish()
    await callback.answer()
