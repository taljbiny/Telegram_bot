from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from database import db
from keyboards.deposit_advanced import *
from config import Config

class AdvancedDepositStates(StatesGroup):
    waiting_for_method = State()
    waiting_for_amount = State()
    waiting_for_transaction_id = State()

async def start_advanced_deposit(message: types.Message):
    """بدء إيداع متقدم"""
    user = db.get_user(message.from_user.id)
    
    if not user:
        await message.answer("⚠️ الرجاء إنشاء حساب أولاً باستخدام /start")
        return
    
    await message.answer(
        "💳 **اختر طريقة الدفع:**",
        reply_markup=deposit_methods_advanced_keyboard(),
        parse_mode="Markdown"
    )
    await AdvancedDepositStates.waiting_for_method.set()

async def process_deposit_method_advanced(callback: types.CallbackQuery, state: FSMContext):
    """معالجة طريقة الدفع"""
    method = callback.data.split('_')[1]  # deposit_sham, deposit_syriatel, etc.
    method_info = Config.PAYMENT_METHODS.get(method)
    
    if not method_info:
        await callback.answer("❌ طريقة غير متاحة")
        return
    
    # حفظ الطريقة
    await state.update_data(method=method, method_info=method_info)
    
    # عرض تفاصيل الحساب أولاً
    payment_details = f"""
✅ **طريقة الدفع: {method_info['name']}**

{'🆔 **الرمز:** ' + method_info['hash'] if 'hash' in method_info else ''}
{'📱 **الرقم:** ' + method_info['number'] if 'number' in method_info else ''}
{'🔗 **العنوان:** ' + method_info['address'] if 'address' in method_info else ''}

📋 **تعليمات:**
1. قم بالتحويل للحساب أعلاه
2. احفظ رقم العملية
3. أدخل المبلغ المراد إيداعه
4. أدخل رقم العملية للتأكيد

💰 **الآن أدخل المبلغ:**"""
    
    await callback.message.edit_text(
        payment_details,
        parse_mode="Markdown",
        reply_markup=cancel_deposit_keyboard()
    )
    await AdvancedDepositStates.waiting_for_amount.set()
    await callback.answer()

async def process_deposit_amount_advanced(message: types.Message, state: FSMContext):
    """معالجة مبلغ الإيداع"""
    try:
        amount = float(message.text.replace(',', '').strip())
        
        if amount < Config.MIN_DEPOSIT:
            await message.answer(
                f"❌ الحد الأدنى للإيداع: {Config.CURRENCY_SYMBOL}{Config.MIN_DEPOSIT:,.0f}"
            )
            return
    except ValueError:
        await message.answer("❌ الرجاء إدخال رقم صحيح")
        return
    
    await state.update_data(amount=amount)
    
    data = await state.get_data()
    
    await message.answer(
        f"💰 **المبلغ:** {Config.CURRENCY_SYMBOL}{amount:,.0f}\n\n"
        f"🔢 **الخطوة الأخيرة:** أرسل رقم العملية (Transaction ID)\n\n"
        f"📝 مثال لرقم العملية:\n"
        f"• شام كاش: SHAM123456789\n"
        f"• سيرياتيل: SYR987654321\n"
        f"• إيثيريوم: 0xabc123...",
        parse_mode="Markdown"
    )
    await AdvancedDepositStates.waiting_for_transaction_id.set()

async def process_transaction_id(message: types.Message, state: FSMContext):
    """معالجة رقم العملية"""
    transaction_id = message.text.strip()
    data = await state.get_data()
    user = message.from_user
    
    # حفظ طلب الإيداع
    deposit_id = db.create_deposit_request_advanced(
        user_id=user.id,
        amount=data['amount'],
        payment_method=data['method'],
        transaction_id=transaction_id,
        details=f"المستخدم: @{user.username or user.id}"
    )
    
    # إرسال إشعار للإدارة
    from bot import bot
    admin_message = f"""
📥 **طلب إيداع جديد #{deposit_id}**

👤 **المستخدم:** {user.first_name} (@{user.username or user.id})
💰 **المبلغ:** {Config.CURRENCY_SYMBOL}{data['amount']:,.0f}
💳 **الطريقة:** {data['method_info']['name']}
🔢 **رقم العملية:** {transaction_id}
📅 **الوقت:** {datetime.now().strftime('%Y-%m-%d %H:%M')}

{'🆔 **الحساب:** ' + data['method_info'].get('hash', '') if data['method'] == 'sham_cash' else ''}
{'📱 **الحساب:** ' + data['method_info'].get('number', '') if data['method'] == 'syriatel_cash' else ''}
{'🔗 **الحساب:** ' + data['method_info'].get('address', '') if data['method'] == 'ethereum' else ''}
    """
    
    for admin_id in Config.ADMIN_IDS:
        try:
            await bot.send_message(
                chat_id=admin_id,
                text=admin_message,
                reply_markup=admin_deposit_approval_keyboard(deposit_id, user.id),
                parse_mode="Markdown"
            )
        except:
            pass
    
    await message.answer(
        f"✅ **تم إرسال طلب الإيداع للإدارة**\n\n"
        f"📋 **تفاصيل الطلب:**\n"
        f"💰 المبلغ: {Config.CURRENCY_SYMBOL}{data['amount']:,.0f}\n"
        f"💳 الطريقة: {data['method_info']['name']}\n"
        f"🔢 رقم العملية: {transaction_id}\n\n"
        f"⏳ جاري المراجعة...\n"
        f"📩 سيتم إعلامك فور الموافقة",
        parse_mode="Markdown"
    )
    
    await state.finish()
