from aiogram import types
from aiogram.dispatcher import FSMContext
from database import db
from keyboards.withdraw import *
from keyboards.main import main_menu_keyboard
from handlers.states import WithdrawalStates
from config import Config
from utils.helpers import format_currency, calculate_withdrawal

async def start_withdrawal(message: types.Message):
    """بدء عملية السحب"""
    user_data = db.get_user(message.from_user.id)
    
    if not user_data:
        await message.answer("⚠️ ليس لديك حساب")
        return
    
    if user_data['balance'] < Config.MIN_WITHDRAWAL:
        await message.answer(
            f"❌ رصيدك غير كافي للسحب\n"
            f"📤 الحد الأدنى: {format_currency(Config.MIN_WITHDRAWAL)}\n"
            f"💰 رصيدك: {format_currency(user_data['balance'])}"
        )
        return
    
    await message.answer(
        f"🏧 **سحب الرصيد**\n\n"
        f"💰 **رصيدك:** {format_currency(user_data['balance'])}\n"
        f"📤 **الحد الأدنى:** {format_currency(Config.MIN_WITHDRAWAL)}\n"
        f"💸 **الرسوم:** {Config.WITHDRAWAL_FEE*100}%\n\n"
        f"🔢 **أدخل المبلغ المراد سحبه:**",
        parse_mode="Markdown",
        reply_markup=cancel_keyboard()
    )
    await WithdrawalStates.waiting_for_amount.set()

async def process_withdrawal_amount(message: types.Message, state: FSMContext):
    """معالجة مبلغ السحب"""
    user_data = db.get_user(message.from_user.id)
    
    try:
        amount = float(message.text.replace(',', '').replace(' ', ''))
        
        # التحقق من المبلغ
        if amount < Config.MIN_WITHDRAWAL:
            await message.answer(
                f"❌ الحد الأدنى للسحب: {format_currency(Config.MIN_WITHDRAWAL)}"
            )
            return
        
        if amount > user_data['balance']:
            await message.answer(
                f"❌ رصيدك غير كافي\n"
                f"💰 رصيدك: {format_currency(user_data['balance'])}"
            )
            return
        
        # حساب الرسوم والمبلغ الصافي
        fee, net_amount = calculate_withdrawal(amount)
        
        await state.update_data(
            amount=amount,
            fee=fee,
            net_amount=net_amount,
            current_balance=user_data['balance']
        )
        
        await message.answer(
            f"💰 **المبلغ المطلوب:** {format_currency(amount)}\n"
            f"💸 **الرسوم ({Config.WITHDRAWAL_FEE*100}%):** {format_currency(fee)}\n"
            f"✅ **ستستلم:** {format_currency(net_amount)}\n\n"
            f"💳 **اختر طريقة السحب:**",
            parse_mode="Markdown",
            reply_markup=withdraw_methods_keyboard()
        )
        await WithdrawalStates.waiting_for_method.set()
        
    except ValueError:
        await message.answer("❌ الرجاء إدخال رقم صحيح")

async def process_withdrawal_method(callback: types.CallbackQuery, state: FSMContext):
    """معالجة طريقة السحب"""
    method = callback.data.split('_')[1]
    
    # أسماء الطرق
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
    prompts = {
        'sham': "📱 أرسل رقم شام كاش (مثال: 09XXXXXXXX)",
        'syriatel': "📱 أرسل رقم سيرياتيل كاش",
        'ethereum': "🔗 أرسل عنوان محفظة الإيثيريوم",
        'paypal': "📧 أرسل البريد الإلكتروني المرتبط بحساب PayPal",
        'bank': "🏦 أرسل معلومات الحساب البنكي (الاسم، رقم الحساب، IBAN)"
    }
    
    prompt = prompts.get(method, "🔢 أرسل معلومات الاستلام")
    
    await callback.message.edit_text(
        f"💳 **طريقة السحب:** {method_name}\n\n"
        f"{prompt}:",
        parse_mode="Markdown"
    )
    await WithdrawalStates.waiting_for_wallet.set()
    await callback.answer()

async def process_wallet_info(message: types.Message, state: FSMContext):
    """معالجة معلومات المحفظة"""
    wallet_info = message.text.strip()
    data = await state.get_data()
    user = message.from_user
    
    # التحقق من معلومات المحفظة
    if data['method'] in ['sham', 'syriatel']:
        if not wallet_info.isdigit() or len(wallet_info) != 10 or not wallet_info.startswith('09'):
            await message.answer("❌ رقم هاتف غير صحيح. يجب أن يبدأ بـ 09 ويتكون من 10 أرقام")
            return
    
    # تجميد المبلغ
    user_data = db.get_user(user.id)
    if not db.freeze_balance(user_data['id'], data['amount']):
        await message.answer("❌ فشل في تجميد الرصيد. حاول مرة أخرى")
        return
    
    # إنشاء طلب السحب
    withdrawal_id = db.create_withdrawal(
        user_id=user_data['id'],
        amount=data['amount'],
        fee=data['fee'],
        net_amount=data['net_amount'],
        method=data['method'],
        wallet_info=wallet_info
    )
    
    # إرسال للإدارة
    from bot import bot
    admin_message = f"""
📤 **طلب سحب جديد #{withdrawal_id}**

👤 **المستخدم:** {user.first_name} (@{user.username or user.id})
💰 **المبلغ المطلوب:** {format_currency(data['amount'])}
💸 **الرسوم:** {format_currency(data['fee'])}
✅ **المبلغ الصافي:** {format_currency(data['net_amount'])}
💳 **الطريقة:** {data['method_name']}
📝 **معلومات الاستلام:** {wallet_info}
📅 **الوقت:** {datetime.now().strftime('%Y-%m-%d %H:%M')}

💰 **رصيد المستخدم بعد السحب:** {format_currency(user_data['balance'] - data['amount'])}
"""
    
    for admin_id in Config.ADMIN_IDS:
        try:
            await bot.send_message(
                chat_id=admin_id,
                text=admin_message,
                reply_markup=admin_withdrawal_actions_keyboard(withdrawal_id, user.id)
            )
        except:
            pass
    
    await message.answer(
        f"✅ **تم إرسال طلب السحب للإدارة**\n\n"
        f"📋 **تفاصيل الطلب:**\n"
        f"💰 المبلغ: {format_currency(data['amount'])}\n"
        f"💸 الرسوم: {format_currency(data['fee'])}\n"
        f"✅ ستحصل على: {format_currency(data['net_amount'])}\n"
        f"💳 الطريقة: {data['method_name']}\n"
        f"📝 المحفظة: {wallet_info}\n\n"
        f"⏳ **جاري المعالجة...**\n"
        f"📩 سيتم إعلامك فور الانتهاء",
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard()
    )
    
    await state.finish()

async def confirm_withdrawal_request(callback: types.CallbackQuery):
    """تأكيد طلب السحب (للمستخدم)"""
    withdrawal_id = int(callback.data.split('_')[2])
    await callback.answer("✅ تم تأكيد إرسال الطلب")
