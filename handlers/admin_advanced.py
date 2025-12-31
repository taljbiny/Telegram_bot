from aiogram import types
from aiogram.dispatcher import FSMContext
from database import db
from keyboards.admin_advanced import *
from config import Config
from datetime import datetime

async def admin_panel_advanced(message: types.Message):
    """لوحة الإدارة المتقدمة"""
    if message.from_user.id not in Config.ADMIN_IDS:
        return
    
    stats = db.get_admin_stats()
    
    panel_text = f"""
👑 **لوحة التحكم المتقدمة**

📊 **الإحصائيات:**
👥 إجمالي المستخدمين: {stats['total_users']}
⏳ قيد المراجعة: {stats['pending_users']}
✅ نشطين: {stats['active_users']}
❌ مرفوضين: {stats['rejected_users']}

💰 **المالية:**
📥 طلبات إيداع معلقة: {stats['pending_deposits']}
📤 طلبات سحب معلقة: {stats['pending_withdrawals']}
💼 الرصيد الكلي: {Config.CURRENCY_SYMBOL}{stats['total_balance']:,.0f}
    """
    
    await message.answer(
        panel_text,
        reply_markup=admin_main_menu_keyboard(),
        parse_mode="Markdown"
    )

async def show_pending_registrations(callback: types.CallbackQuery):
    """عرض طلبات التسجيل المعلقة"""
    pending_users = db.get_pending_users()
    
    if not pending_users:
        await callback.message.edit_text(
            "📭 لا توجد طلبات تسجيل معلقة",
            reply_markup=back_to_admin_keyboard()
        )
        return
    
    for user in pending_users[:5]:  # عرض أول 5 طلبات
        user_info = f"""
📋 **طلب تسجيل #{user['telegram_id']}**

👤 الاسم: {user['first_name']} {user['last_name'] or ''}
🆔 @{user['username'] or 'لا يوجد'}
📱 {user['phone_number']}
📧 {user['email']}
🌍 {user['country']}
📅 {user['created_at'][:10]}
        """
        
        await callback.message.answer_photo(
            photo=user['id_card_image'],
            caption=user_info,
            reply_markup=admin_user_approval_keyboard(
                user['telegram_id'],
                user['id']
            )
        )
    
    await callback.answer()

async def approve_user_registration(callback: types.CallbackQuery):
    """الموافقة على تسجيل مستخدم"""
    user_id = int(callback.data.split('_')[3])
    db_id = int(callback.data.split('_')[4])
    
    # تفعيل المستخدم
    db.activate_user(db_id, callback.from_user.id)
    
    # إشعار المستخدم
    from bot import bot
    try:
        await bot.send_message(
            chat_id=user_id,
            text="🎉 **تمت الموافقة على حسابك!**\n\n"
                 "✅ حسابك نشط الآن ويمكنك استخدام جميع الخدمات\n"
                 "💰 استخدم /deposit لشحن الرصيد\n"
                 "💳 استخدم /withdraw لسحب الأرباح\n\n"
                 "🎊 أهلاً بك في عائلتنا!"
        )
    except:
        pass
    
    await callback.message.edit_caption(
        f"✅ تمت الموافقة على المستخدم #{user_id}",
        reply_markup=None
    )
    await callback.answer()

async def reject_user_registration(callback: types.CallbackQuery, state: FSMContext):
    """رفض تسجيل مستخدم مع إدخال السبب"""
    user_id = int(callback.data.split('_')[3])
    
    await callback.message.answer(
        f"❌ رفض طلب تسجيل #{user_id}\n\n"
        f"الرجاء إدخال سبب الرفض:",
        reply_markup=cancel_action_keyboard()
    )
    
    await state.update_data(reject_user_id=user_id)
