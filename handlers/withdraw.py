from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from database import db
from keyboards.withdraw_advanced import *
from config import Config

class AdvancedWithdrawalStates(StatesGroup):
    waiting_for_amount = State()
    waiting_for_method = State()
    waiting_for_wallet = State()

async def start_advanced_withdrawal(message: types.Message):
    """بدء سحب متقدم"""
    user_data = db.get_user(message.from_user.id)
    
    if not user_data:
        await message.answer("⚠️ الرجاء إنشاء حساب أولاً")
        return
    
    if user_data['balance'] < Config.MIN_WITHDRAWAL:
        await message.answer(
            f"❌ رصيدك غير كافي للسحب\n"
            f"الحد الأدنى: {Config.CURRENCY_SYMBOL}{Config.MIN_WITHDRAWAL:,.0f}\n"
            f"رصيدك: {Config.CURRENCY_SYMBOL}{user_data['balance']:,.0f}"
        )
        return
    
    await message.answer(
        f"🏧 **طلب سحب رصيد**\n\n"
        f"💰 **رصيدك الحالي:** {Config.CURRENCY_SYMBOL}{user_data['balance']:,.0f}\n"
        f"📤 **الحد الأدنى:** {Config.CURRENCY_SYMBOL}{Config.MIN_WITHDRAWAL:,.0f}\n"
        f"💸 **الرسوم:** {Config.WITHDRAWAL_FEE*100}%\n\n"
        f"🔢 **أدخل المبلغ المراد سحبه:**",
        parse_mode="Markdown",
        reply_markup=cancel_withdrawal_keyboard()
    )
    await AdvancedWithdrawalStates.waiting_for_amount.set()

async def process_withdrawal_amount_advanced(message: types.Message, state: FSMContext):
    """معالجة مبلغ السحب"""
    user_data = db.get_user(message.from_user.id)
    
    try:
        amount = float(message.text.replace(',', '').strip())
        
        # التحقق من المبلغ
        if amount < Config.MIN_WITHDRAWAL:
            await message.answer(
                f"❌ الحد الأدنى للسحب: {Config.CURRENCY_SYMBOL}{Config.MIN_WITHDRAWAL:,.0f}"
            )
            return
        
        if amount > user_data['balance']:
            await message.answer(
                f"❌ رصيدك غير كافي\n"
                f"رصيدك: {Config.CURRENCY_SYMBOL}{user_data['balance']:,.0f}"
            )
            return
        
        # حساب الرسوم والمبلغ الصافي
        fee = amount * Config.WITHDRAWAL_FEE
        net_amount = amount - fee
        
        await state.update_data(
            amount=amount,
            fee=fee,
            net_amount=net_amount,
            current_balance=user_data['balance']
        )
        
        await message.answer(
            f"💰 **المبلغ:** {Config.CURRENCY_SYMBOL}{amount:,.0f}\n"
            f"💸 **الرسوم ({Config.WITHDRAWAL_FEE*100}%):** {Config.CURRENCY_SYMBOL}{fee:,.0f}\n"
            f"✅ **ستستلم:** {Config.CURRENCY_SYMBOL}{net_amount:,.0f}\n\n"
            f"💳 **اختر طريقة السحب:**",
            parse_mode="Markdown",
            reply_markup=withdrawal_methods_advanced_keyboard()
        )
        await AdvancedWithdrawalStates.waiting_for_method.set()
        
    except ValueError:
        await message.answer("❌ الرجاء إدخال رقم صحيح")

async def process_withdrawal_method_advanced(callback: types.CallbackQuery, state: FSMContext):
    """معالجة طريقة السحب"""
    method = callback.data.split('_')[1]  # withdraw_sham, withdraw_syriatel, etc.
    
    method_names = {
        'sham': 'شام كاش',
        'syriatel': 'سيرياتيل كاش',
        'ethereum': 'Ethereum',
        'paypal': 'PayPal',
        'bank': 'تحويل بنكي'
    }
    
    method_name = method_names.get(method, method)
    await state.update_data(method=method, method_name=method_name)
    
    # طلب معلومات المحفظة بناءً على الطريقة
    wallet_prompts = {
        'sham': "📱 أرسل رقم شام كاش (مثال: 09XXXXXXXX)",
        'syriatel': "📱 أرسل رقم سيرياتيل كاش",
        'ethereum': "🔗 أرسل عنوان محفظة الإيثيريوم",
        'paypal': "📧 أرسل البريد الإلكتروني المرتبط بحساب PayPal",
        'bank': "🏦 أرسل معلومات الحساب البنكي (الاسم، رقم الحساب، IBAN)"
    }
    
    prompt = wallet_prompts.get(method, "🔢 أرسل معلومات الاستلام")
    
    await callback.message.edit_text(
        f"💳 **طريقة السحب:** {method_name}\n\n"
        f"{prompt}:",
        parse_mode="Markdown"
    )
    await AdvancedWithdrawalStates.waiting_for_wallet.set()
    await callback.answer()

async def process_wallet_info(message: types.Message, state: FSMContext):
    """معالجة معلومات المحفظة"""
    wallet_info = message.text.strip()
    data = await state.get_data()
    user = message.from_user
    
    # التحقق من صحة المعلومات بناءً على الطريقة
    if data['method'] in ['sham', 'syriatel']:
        if not wallet_info.isdigit() or len(wallet_info) != 10 or not wallet_info.startswith('09'):
            await message.answer("❌ رقم هاتف غير صحيح. يجب أن يبدأ بـ 09 ويتكون من 10 أرقام")
            return
    
    # خصم المبلغ من الرصيد مؤقتاً
    db.freeze_balance(user.id, data['amount'])
    
    # إنشاء طلب السحب
    withdrawal_id = db.create_withdrawal_request_advanced(
        user_id=user.id,
        amount=data['amount'],
        fee=data['fee'],
        net_amount=data['net_amount'],
        payment_method=data['method'],
        wallet_info=wallet_info
    )
    
    # إرسال للإدارة
    from bot import bot
    admin_message = f"""
📤 **طلب سحب جديد #{withdrawal_id}**

👤 **المستخدم:** {user.first_name} (@{user.username or user.id})
💰 **المبلغ المطلوب:** {Config.CURRENCY_SYMBOL}{data['amount']:,.0f}
💸 **الرسوم:** {Config.CURRENCY_SYMBOL}{data['fee']:,.0f}
✅ **المبلغ الصافي:** {Config.CURRENCY_SYMBOL}{data['net_amount']:,.0f}
💳 **الطريقة:** {data['method_name']}
📝 **معلومات الاستلام:** {wallet_info}
📅 **الوقت:** {datetime.now().strftime('%Y-%m-%d %H:%M')}
    """
    
    for admin_id in Config.ADMIN_IDS:
        try:
            await bot.send_message(
                chat_id=admin_id,
                text=admin_message,
                reply_markup=admin_withdrawal_approval_keyboard(withdrawal_id, user.id),
                parse_mode="Markdown"
            )
        except:
            pass
    
    await message.answer(
        f"✅ **تم إرسال طلب السحب للإدارة**\n\n"
        f"📋 **تفاصيل الطلب:**\n"
        f"💰 المبلغ: {Config.CURRENCY_SYMBOL}{data['amount']:,.0f}\n"
        f"💸 الرسوم: {Config.CURRENCY_SYMBOL}{data['fee']:,.0f}\n"
        f"✅ ستحصل على: {Config.CURRENCY_SYMBOL}{data['net_amount']:,.0f}\n"
        f"💳 الطريقة: {data['method_name']}\n"
        f"📝 المحفظة: {wallet_info}\n\n"
        f"⏳ جاري المعالجة...\n"
        f"📩 سيتم إعلامك فور الانتهاء",
        parse_mode="Markdown"
    )
    
    await state.finish()
