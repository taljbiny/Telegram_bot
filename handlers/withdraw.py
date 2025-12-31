from aiogram import types
from aiogram.dispatcher import FSMContext
from database import db
from handlers.states import WithdrawalStates
from config import Config
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def withdraw_methods_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("💳 شام كاش", callback_data="withdraw_sham"),
        InlineKeyboardButton("📱 سيرياتيل", callback_data="withdraw_syriatel"),
        InlineKeyboardButton("₿ Ethereum", callback_data="withdraw_ethereum")
    )
    return keyboard

async def start_withdrawal(message: types.Message):
    user_data = db.get_user(message.from_user.id)
    
    if not user_data:
        await message.answer("⚠️ ليس لديك حساب")
        return
    
    if user_data['balance'] < Config.MIN_WITHDRAWAL:
        await message.answer(
            f"❌ رصيدك غير كافي\n"
            f"📤 الحد الأدنى: {Config.MIN_WITHDRAWAL:,} {Config.CURRENCY_SYMBOL}\n"
            f"💰 رصيدك: {user_data['balance']:,} {Config.CURRENCY_SYMBOL}"
        )
        return
    
    await message.answer(
        f"🏧 **سحب الأرباح**\n\n"
        f"💰 **رصيدك:** {user_data['balance']:,} {Config.CURRENCY_SYMBOL}\n"
        f"📤 **الحد الأدنى:** {Config.MIN_WITHDRAWAL:,} {Config.CURRENCY_SYMBOL}\n"
        f"💸 **الرسوم:** {Config.WITHDRAWAL_FEE*100}%\n\n"
        f"🔢 **أدخل المبلغ المراد سحبه:**",
        parse_mode="Markdown"
    )
    await WithdrawalStates.waiting_for_amount.set()

async def process_withdrawal_amount(message: types.Message, state: FSMContext):
    user_data = db.get_user(message.from_user.id)
    
    try:
        amount = float(message.text.replace(',', '').replace(' ', ''))
        
        if amount < Config.MIN_WITHDRAWAL:
            await message.answer(f"❌ الحد الأدنى: {Config.MIN_WITHDRAWAL:,} {Config.CURRENCY_SYMBOL}")
            return
        
        if amount > user_data['balance']:
            await message.answer(f"❌ رصيدك: {user_data['balance']:,} {Config.CURRENCY_SYMBOL}")
            return
        
        # حساب الرسوم
        fee = amount * Config.WITHDRAWAL_FEE
        net_amount = amount - fee
        
        await state.update_data(
            amount=amount,
            fee=fee,
            net_amount=net_amount
        )
        
        await message.answer(
            f"💰 **المبلغ المطلوب:** {amount:,} {Config.CURRENCY_SYMBOL}\n"
            f"💸 **الرسوم ({Config.WITHDRAWAL_FEE*100}%):** {fee:,} {Config.CURRENCY_SYMBOL}\n"
            f"✅ **ستستلم:** {net_amount:,} {Config.CURRENCY_SYMBOL}\n\n"
            f"💳 **اختر طريقة السحب:**",
            reply_markup=withdraw_methods_keyboard(),
            parse_mode="Markdown"
        )
        await WithdrawalStates.waiting_for_method.set()
        
    except ValueError:
        await message.answer("❌ أدخل رقم صحيح")

async def process_withdrawal_method(callback: types.CallbackQuery, state: FSMContext):
    method = callback.data.split('_')[1]
    
    methods_info = {
        'sham': {'name': 'شام كاش', 'prompt': '📱 أرسل رقم شام كاش:'},
        'syriatel': {'name': 'سيرياتيل كاش', 'prompt': '📱 أرسل رقم سيرياتيل:'},
        'ethereum': {'name': 'Ethereum', 'prompt': '🔗 أرسل عنوان محفظة الإيثيريوم:'}
    }
    
    if method not in methods_info:
        await callback.answer("❌ طريقة غير متاحة")
        return
    
    info = methods_info[method]
    await state.update_data(
        withdraw_method=method,
        withdraw_method_name=info['name']
    )
    
    await callback.message.edit_text(
        f"💳 **طريقة السحب:** {info['name']}\n\n"
        f"{info['prompt']}",
        parse_mode="Markdown"
    )
    await WithdrawalStates.waiting_for_wallet.set()
    await callback.answer()

async def process_wallet_info(message: types.Message, state: FSMContext):
    wallet_info = message.text.strip()
    data = await state.get_data()
    user = message.from_user
    
    # التحقق من المعلومات
    if data['withdraw_method'] in ['sham', 'syriatel']:
        if not wallet_info.isdigit() or len(wallet_info) != 10 or not wallet_info.startswith('09'):
            await message.answer("❌ رقم غير صحيح. يجب أن يبدأ بـ 09 ويتكون من 10 أرقام")
            return
    
    # إنشاء طلب السحب
    user_data = db.get_user(user.id)
    withdrawal_id = db.create_withdrawal(
        user_id=user_data['id'],
        amount=data['amount'],
        fee=data['fee'],
        net_amount=data['net_amount'],
        method=data['withdraw_method'],
        wallet_info=wallet_info
    )
    
    # إرسال للإدارة
    from bot import bot
    admin_text = (
        f"📤 **طلب سحب جديد #{withdrawal_id}**\n\n"
        f"👤 **المستخدم:** {user.first_name} (@{user.username or user.id})\n"
        f"💰 **المبلغ:** {data['amount']:,} {Config.CURRENCY_SYMBOL}\n"
        f"💸 **الرسوم:** {data['fee']:,} {Config.CURRENCY_SYMBOL}\n"
        f"✅ **الصافي:** {data['net_amount']:,} {Config.CURRENCY_SYMBOL}\n"
        f"💳 **الطريقة:** {data['withdraw_method_name']}\n"
        f"📝 **المحفظة:** {wallet_info}\n"
        f"📅 **الوقت:** {datetime.now().strftime('%H:%M %Y-%m-%d')}"
    )
    
    admin_keyboard = InlineKeyboardMarkup()
    admin_keyboard.add(
        InlineKeyboardButton("✅ معالجة", callback_data=f"approve_withdrawal_{withdrawal_id}_{user.id}"),
        InlineKeyboardButton("❌ رفض", callback_data=f"reject_withdrawal_{withdrawal_id}_{user.id}")
    )
    
    for admin_id in Config.ADMIN_IDS:
        try:
            await bot.send_message(admin_id, admin_text, reply_markup=admin_keyboard, parse_mode="Markdown")
        except:
            pass
    
    await message.answer(
        f"✅ **تم إرسال طلبك للإدارة**\n\n"
        f"📋 **رقم الطلب:** #{withdrawal_id}\n"
        f"💰 **المبلغ:** {data['amount']:,} {Config.CURRENCY_SYMBOL}\n"
        f"💸 **الرسوم:** {data['fee']:,} {Config.CURRENCY_SYMBOL}\n"
        f"✅ **ستحصل على:** {data['net_amount']:,} {Config.CURRENCY_SYMBOL}\n"
        f"💳 **الطريقة:** {data['withdraw_method_name']}\n\n"
        f"⏳ **جاري المعالجة...**",
        parse_mode="Markdown"
    )
    
    await state.finish()
