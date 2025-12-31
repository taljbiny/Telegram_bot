from aiogram import types
from aiogram.dispatcher import FSMContext
from database import db
from handlers.states import DepositStates
from config import Config
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime

def deposit_methods_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("💳 شام كاش", callback_data="deposit_sham"),
        InlineKeyboardButton("📱 سيرياتيل", callback_data="deposit_syriatel"),
        InlineKeyboardButton("₿ Ethereum", callback_data="deposit_ethereum")
    )
    return keyboard

def cancel_keyboard():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("❌ إلغاء", callback_data="cancel_deposit"))
    return keyboard

async def start_deposit(message: types.Message):
    user_data = db.get_user(message.from_user.id)
    
    if not user_data:
        await message.answer("⚠️ ليس لديك حساب. استخدم /register")
        return
    
    await message.answer(
        "💳 **شحن الرصيد**\n\n"
        f"💰 **الحد الأدنى:** {Config.MIN_DEPOSIT:,} {Config.CURRENCY_SYMBOL}\n"
        "💎 **لا رسوم على الإيداع**\n\n"
        "اختر طريقة الدفع:",
        reply_markup=deposit_methods_keyboard(),
        parse_mode="Markdown"
    )
    await DepositStates.waiting_for_method.set()

async def process_deposit_method(callback: types.CallbackQuery, state: FSMContext):
    method = callback.data.split('_')[1]
    
    methods_info = {
        'sham': {
            'name': 'شام كاش',
            'account': '🆔 **الرمز:** 19f013ef640f4ab20aace84b8a617bd6',
            'instructions': 'أرسل المبلغ لهذا الرمز'
        },
        'syriatel': {
            'name': 'سيرياتيل كاش', 
            'account': '📱 **الرقم:** 0996099355',
            'instructions': 'أرسل المبلغ لهذا الرقم'
        },
        'ethereum': {
            'name': 'Ethereum',
            'account': '🔗 **العنوان:** 0x2abf01f2d131b83f7a9b2b9642638ebcaab67c43',
            'instructions': 'أرسل المبلغ لهذا العنوان'
        }
    }
    
    if method not in methods_info:
        await callback.answer("❌ طريقة غير متاحة")
        return
    
    info = methods_info[method]
    await state.update_data(
        method=method,
        method_name=info['name'],
        method_account=info['account']
    )
    
    await callback.message.edit_text(
        f"✅ **طريقة الدفع:** {info['name']}\n\n"
        f"{info['account']}\n\n"
        f"📋 **{info['instructions']}**\n\n"
        f"💰 **أدخل المبلغ:**",
        parse_mode="Markdown",
        reply_markup=cancel_keyboard()
    )
    await DepositStates.waiting_for_amount.set()
    await callback.answer()

async def process_deposit_amount(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text.replace(',', '').replace(' ', ''))
        
        if amount < Config.MIN_DEPOSIT:
            await message.answer(f"❌ الحد الأدنى: {Config.MIN_DEPOSIT:,} {Config.CURRENCY_SYMBOL}")
            return
        
        await state.update_data(amount=amount)
        data = await state.get_data()
        
        await message.answer(
            f"💰 **المبلغ:** {amount:,} {Config.CURRENCY_SYMBOL}\n"
            f"💳 **الطريقة:** {data['method_name']}\n\n"
            f"📝 **بعد التحويل، أرسل رقم العملية:**\n\n"
            f"🔢 **مثال:**\n"
            f"• شام كاش: SHAM123456789\n"
            f"• سيرياتيل: SYR987654321\n"
            f"• إيثيريوم: 0xabc123...",
            parse_mode="Markdown"
        )
        await DepositStates.waiting_for_transaction_id.set()
        
    except ValueError:
        await message.answer("❌ أدخل رقم صحيح")

async def process_transaction_id(message: types.Message, state: FSMContext):
    transaction_id = message.text.strip()
    data = await state.get_data()
    user = message.from_user
    
    if len(transaction_id) < 5:
        await message.answer("❌ رقم العملية قصير جداً")
        return
    
    # إنشاء طلب الإيداع
    user_data = db.get_user(user.id)
    deposit_id = db.create_deposit(
        user_id=user_data['id'],
        amount=data['amount'],
        method=data['method'],
        transaction_id=transaction_id
    )
    
    # إرسال للإدارة
    from bot import bot
    admin_text = (
        f"📥 **طلب إيداع جديد #{deposit_id}**\n\n"
        f"👤 **المستخدم:** {user.first_name} (@{user.username or user.id})\n"
        f"💰 **المبلغ:** {data['amount']:,} {Config.CURRENCY_SYMBOL}\n"
        f"💳 **الطريقة:** {data['method_name']}\n"
        f"🔢 **رقم العملية:** {transaction_id}\n"
        f"📅 **الوقت:** {datetime.now().strftime('%H:%M %Y-%m-%d')}"
    )
    
    admin_keyboard = InlineKeyboardMarkup()
    admin_keyboard.add(
        InlineKeyboardButton("✅ قبول", callback_data=f"approve_deposit_{deposit_id}_{user.id}"),
        InlineKeyboardButton("❌ رفض", callback_data=f"reject_deposit_{deposit_id}_{user.id}")
    )
    
    for admin_id in Config.ADMIN_IDS:
        try:
            await bot.send_message(admin_id, admin_text, reply_markup=admin_keyboard, parse_mode="Markdown")
        except:
            pass
    
    await message.answer(
        f"✅ **تم إرسال طلبك للإدارة**\n\n"
        f"📋 **رقم الطلب:** #{deposit_id}\n"
        f"💰 **المبلغ:** {data['amount']:,} {Config.CURRENCY_SYMBOL}\n"
        f"💳 **الطريقة:** {data['method_name']}\n\n"
        f"⏳ **جاري المراجعة...**\n"
        f"📩 سيتم إعلامك فور الموافقة",
        parse_mode="Markdown"
    )
    
    await state.finish()

async def cancel_deposit(callback: types.CallbackQuery, state: FSMContext):
    await state.finish()
    await callback.message.edit_text("✅ تم إلغاء عملية الإيداع")
    await callback.answer()
