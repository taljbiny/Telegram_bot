from aiogram import types
from aiogram.dispatcher import FSMContext
from database import db
from keyboards.deposit import *
from keyboards.main import main_menu_keyboard
from handlers.states import DepositStates
from config import Config
from utils.helpers import format_currency

async def start_deposit(message: types.Message):
    """بدء عملية الإيداع"""
    user_data = db.get_user(message.from_user.id)
    
    if not user_data:
        await message.answer("⚠️ ليس لديك حساب. استخدم /register أولاً")
        return
    
    await message.answer(
        f"💳 **شحن الرصيد**\n\n"
        f"💰 **الحد الأدنى:** {format_currency(Config.MIN_DEPOSIT)}\n"
        f"💎 **لا توجد رسوم على الإيداعات**\n\n"
        f"اختر طريقة الدفع:",
        reply_markup=deposit_methods_keyboard(),
        parse_mode="Markdown"
    )
    await DepositStates.waiting_for_method.set()

async def process_deposit_method(callback: types.CallbackQuery, state: FSMContext):
    """معالجة طريقة الدفع"""
    method = callback.data.split('_')[1]  # sham, syriatel, ethereum
    
    method_info = Config.PAYMENT_METHODS.get(method)
    if not method_info:
        await callback.answer("❌ طريقة غير متاحة")
        return
    
    await state.update_data(method=method, method_info=method_info)
    
    # عرض تفاصيل الحساب
    payment_text = f"""
✅ **طريقة الدفع: {method_info['name']}**

{'🆔 **الرمز:** ' + method_info['hash'] if 'hash' in method_info else ''}
{'📱 **الرقم:** ' + method_info['number'] if 'number' in method_info else ''}
{'🔗 **العنوان:** ' + method_info['address'] if 'address' in method_info else ''}

📋 **تعليمات الدفع:**
1. قم بالتحويل للحساب أعلاه
2. احفظ رقم العملية (Transaction ID)
3. أدخل المبلغ المراد إيداعه أدناه

💰 **أدخل المبلغ:**"""
    
    await callback.message.edit_text(
        payment_text,
        parse_mode="Markdown",
        reply_markup=cancel_keyboard()
    )
    await DepositStates.waiting_for_amount.set()
    await callback.answer()

async def process_deposit_amount(message: types.Message, state: FSMContext):
    """معالجة مبلغ الإيداع"""
    try:
        amount = float(message.text.replace(',', '').replace(' ', ''))
        
        if amount < Config.MIN_DEPOSIT:
            await message.answer(
                f"❌ الحد الأدنى للإيداع: {format_currency(Config.MIN_DEPOSIT)}"
            )
            return
        
        await state.update_data(amount=amount)
        
        data = await state.get_data()
        
        await message.answer(
            f"💰 **المبلغ:** {format_currency(amount)}\n\n"
            f"🔢 **الآن أرسل رقم العملية (Transaction ID):**\n\n"
            f"📝 **مثال:**\n"
            f"• شام كاش: SHAM123456789\n"
            f"• سيرياتيل: SYR987654321\n"
            f"• إيثيريوم: 0xabc123def456...",
            parse_mode="Markdown"
        )
        await DepositStates.waiting_for_transaction_id.set()
        
    except ValueError:
        await message.answer("❌ الرجاء إدخال رقم صحيح")

async def process_transaction_id(message: types.Message, state: FSMContext):
    """معالجة رقم العملية"""
    transaction_id = message.text.strip()
    data = await state.get_data()
    user = message.from_user
    
    # إنشاء طلب الإيداع
    deposit_id = db.create_deposit(
        user_id=db.get_user(user.id)['id'],
        amount=data['amount'],
        method=data['method'],
        transaction_id=transaction_id
    )
    
    # إرسال إشعار للإدارة
    from bot import bot
    admin_message = f"""
📥 **طلب إيداع جديد #{deposit_id}**

👤 **المستخدم:** {user.first_name} (@{user.username or user.id})
💰 **المبلغ:** {format_currency(data['amount'])}
💳 **الطريقة:** {data['method_info']['name']}
🔢 **رقم العملية:** {transaction_id}
📅 **الوقت:** {datetime.now().strftime('%Y-%m-%d %H:%M')}

{'🆔 **الحساب:** ' + data['method_info'].get('hash', '') if data['method'] == 'sham' else ''}
{'📱 **الحساب:** ' + data['method_info'].get('number', '') if data['method'] == 'syriatel' else ''}
{'🔗 **الحساب:** ' + data['method_info'].get('address', '') if data['method'] == 'ethereum' else ''}
"""
    
    for admin_id in Config.ADMIN_IDS:
        try:
            await bot.send_message(
                chat_id=admin_id,
                text=admin_message,
                reply_markup=admin_deposit_actions_keyboard(deposit_id, user.id)
            )
        except:
            pass
    
    await message.answer(
        f"✅ **تم إرسال طلب الإيداع للإدارة**\n\n"
        f"📋 **تفاصيل الطلب:**\n"
        f"💰 المبلغ: {format_currency(data['amount'])}\n"
        f"💳 الطريقة: {data['method_info']['name']}\n"
        f"🔢 رقم العملية: {transaction_id}\n\n"
        f"⏳ **جاري المراجعة...**\n"
        f"📩 سيتم إعلامك فور الموافقة",
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard()
    )
    
    await state.finish()

async def confirm_deposit_request(callback: types.CallbackQuery):
    """تأكيد طلب الإيداع (للمستخدم)"""
    deposit_id = int(callback.data.split('_')[2])
    
    # يمكن إضافة تأكيد إضافي من المستخدم هنا
    
    await callback.answer("✅ تم تأكيد إرسال الطلب")
