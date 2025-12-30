from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from config import Config
from database import db
from keyboards.payment import *
from utils.validators import validate_amount

class DepositStates(StatesGroup):
    waiting_for_amount = State()
    waiting_for_method = State()
    waiting_for_receipt = State()

async def start_deposit(message: types.Message):
    """بدء عملية الإيداع"""
    await message.answer(
        f"💰 **الإيداع**\n\n"
        f"الحد الأدنى للإيداع: {Config.CURRENCY_SYMBOL}{Config.MIN_DEPOSIT:,.0f}\n"
        f"الرجاء إدخال المبلغ المراد إيداعه:",
        parse_mode="Markdown"
    )
    await DepositStates.waiting_for_amount.set()

async def process_deposit_amount(message: types.Message, state: FSMContext):
    """معالجة مبلغ الإيداع"""
    amount = message.text.replace(',', '').strip()
    
    # التحقق من المبلغ
    try:
        amount = float(amount)
        if amount < Config.MIN_DEPOSIT:
            await message.answer(
                f"❌ المبلغ أقل من الحد الأدنى\n"
                f"الحد الأدنى: {Config.CURRENCY_SYMBOL}{Config.MIN_DEPOSIT:,.0f}"
            )
            return
    except ValueError:
        await message.answer("❌ الرجاء إدخال رقم صحيح")
        return
    
    # حفظ المبلغ في الحالة
    await state.update_data(amount=amount)
    
    # عرض طرق الدفع
    await message.answer(
        "💳 **اختر طريقة الدفع:**",
        reply_markup=deposit_methods_keyboard(),
        parse_mode="Markdown"
    )
    await DepositStates.waiting_for_method.set()

async def process_deposit_method(callback: types.CallbackQuery, state: FSMContext):
    """معالجة طريقة الدفع"""
    method = callback.data.split('_')[1]  # deposit_sham, deposit_syriatel, etc.
    method_info = Config.PAYMENT_METHODS.get(method)
    
    if not method_info:
        await callback.answer("❌ طريقة دفع غير متاحة")
        return
    
    # حفظ الطريقة
    await state.update_data(method=method, method_info=method_info)
    data = await state.get_data()
    
    # عرض معلومات الحساب
    payment_text = f"""
✅ **تم اختيار: {method_info['name']}**

📋 **تعليمات الدفع:**
{method_info['instructions']}

{'🆔 **الرمز:** ' + method_info['hash'] if 'hash' in method_info else ''}
{'📱 **الرقم:** ' + method_info['number'] if 'number' in method_info else ''}
{'🔗 **العنوان:** ' + method_info['address'] if 'address' in method_info else ''}

💰 **المبلغ:** {Config.CURRENCY_SYMBOBL}{data['amount']:,.0f}

📸 **بعد التحويل، أرسل صورة الإيصال**"""
    
    await callback.message.edit_text(
        payment_text,
        parse_mode="Markdown",
        reply_markup=cancel_keyboard()
    )
    await DepositStates.waiting_for_receipt.set()
    await callback.answer()

async def process_deposit_receipt(message: types.Message, state: FSMContext):
    """معالجة إيصال الدفع"""
    if not message.photo:
        await message.answer("❌ الرجاء إرسال صورة الإيصال")
        return
    
    data = await state.get_data()
    user_id = message.from_user.id
    
    # حفظ طلب الإيداع
    db.create_deposit_request(
        user_id=user_id,
        amount=data['amount'],
        payment_method=data['method'],
        receipt_image=message.photo[-1].file_id
    )
    
    # إرسال إشعار للإدارة
    from bot import bot
    for admin_id in Config.ADMIN_IDS:
        try:
            await bot.send_photo(
                chat_id=admin_id,
                photo=message.photo[-1].file_id,
                caption=f"📥 طلب إيداع جديد\n"
                       f"👤 المستخدم: @{message.from_user.username}\n"
                       f"💰 المبلغ: {Config.CURRENCY_SYMBOL}{data['amount']:,.0f}\n"
                       f"💳 الطريقة: {data['method_info']['name']}",
                reply_markup=admin_approval_keyboard(user_id, data['amount'])
            )
        except:
            pass
    
    await message.answer(
        "✅ **تم استلام طلبك!**\n\n"
        "📋 تم إرسال طلب الإيداع للإدارة للمراجعة.\n"
        "⏳ سيتم إعلامك فور الموافقة على الطلب.\n"
        "🕐 الوقت المتوقع: 1-24 ساعة",
        parse_mode="Markdown"
    )
    
    await state.finish()
