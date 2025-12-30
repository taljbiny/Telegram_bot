from aiogram import types
from aiogram.dispatcher import FSMContext
from config import Config
from database import db
from keyboards.admin import *
from utils.formatters import format_user_info

async def admin_panel(message: types.Message):
    """لوحة تحكم الإدارة"""
    if message.from_user.id not in Config.ADMIN_IDS:
        await message.answer("⛔ غير مصرح لك بالدخول")
        return
    
    stats = db.get_admin_stats()
    
    admin_text = f"""
👑 **لوحة الإدارة**

📊 **الإحصائيات:**
👥 المستخدمين: {stats['total_users']}
💰 إجمالي الإيداعات: {Config.CURRENCY_SYMBOL}{stats['total_deposits']:,.0f}
💳 إجمالي السحوبات: {Config.CURRENCY_SYMBOL}{stats['total_withdrawals']:,.0f}
📥 طلبات إيداع معلقة: {stats['pending_deposits']}
📤 طلبات سحب معلقة: {stats['pending_withdrawals']}

اختر من القائمة أدناه:"""
    
    await message.answer(
        admin_text,
        reply_markup=admin_menu_keyboard(),
        parse_mode="Markdown"
    )

async def process_admin_callback(callback: types.CallbackQuery):
    """معالجة أزرار الإدارة"""
    if callback.from_user.id not in Config.ADMIN_IDS:
        await callback.answer("⛔ غير مصرح لك", show_alert=True)
        return
    
    action = callback.data
    
    if action == "admin_pending_deposits":
        await show_pending_deposits(callback)
    elif action == "admin_pending_withdrawals":
        await show_pending_withdrawals(callback)
    elif action.startswith("approve_deposit_"):
        await approve_deposit(callback)
    elif action.startswith("reject_deposit_"):
        await reject_deposit(callback)
    
    await callback.answer()

async def approve_deposit(callback: types.CallbackQuery):
    """الموافقة على إيداع"""
    request_id = int(callback.data.split('_')[2])
    deposit = db.get_deposit_request(request_id)
    
    if not deposit:
        await callback.answer("❌ الطلب غير موجود")
        return
    
    # تحديث رصيد المستخدم
    db.update_user_balance(deposit['user_id'], deposit['amount'])
    db.approve_deposit_request(request_id)
    
    # إشعار المستخدم
    from bot import bot
    try:
        await bot.send_message(
            chat_id=deposit['user_id'],
            text=f"✅ **تمت الموافقة على إيداعك**\n\n"
                 f"💰 المبلغ: {Config.CURRENCY_SYMBOL}{deposit['amount']:,.0f}\n"
                 f"📅 التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
                 f"💳 الطريقة: {deposit['payment_method']}\n\n"
                 f"🎉 تم إضافة المبلغ إلى رصيدك بنجاح!"
        )
    except:
        pass
    
    await callback.message.edit_text(
        f"✅ تمت الموافقة على طلب الإيداع #{request_id}",
        reply_markup=back_to_admin_keyboard()
    )
