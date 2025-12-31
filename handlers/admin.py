from aiogram import types
from aiogram.dispatcher import FSMContext
from database import db
from keyboards.admin import *
from config import Config
from utils.helpers import format_currency
from datetime import datetime

async def admin_panel(message: types.Message):
    """لوحة تحكم الإدارة"""
    if message.from_user.id not in Config.ADMIN_IDS:
        await message.answer("⛔ غير مصرح لك بالدخول")
        return
    
    stats = db.get_stats()
    
    panel_text = f"""
👑 **لوحة تحكم الإدارة**

📊 **الإحصائيات العامة:**
👥 إجمالي المستخدمين: {stats['total_users']}
🆕 جدد اليوم: {stats['new_today']}
💰 إجمالي الأرصدة: {format_currency(stats['total_balance'])}
⏸️ مجمدة: {format_currency(stats['frozen_balance'])}

📥 **طلبات الإيداع المعلقة:** {stats['pending_deposits']}
📤 **طلبات السحب المعلقة:** {stats['pending_withdrawals']}

💰 **المعاملات اليوم:**
📥 الإيداعات: {format_currency(stats['deposits_today'])}
📤 السحوبات: {format_currency(stats['withdrawals_today'])}

🕐 **آخر تحديث:** {datetime.now().strftime('%H:%M')}
"""
    
    await message.answer(
        panel_text,
        reply_markup=admin_menu_keyboard(),
        parse_mode="Markdown"
    )

async def admin_stats(callback: types.CallbackQuery):
    """عرض إحصائيات مفصلة"""
    stats = db.get_stats()
    
    detailed_stats = f"""
📊 **إحصائيات مفصلة**

👥 **المستخدمين:**
• إجمالي المسجلين: {stats['total_users']}
• جدد اليوم: {stats['new_today']}

💰 **المالية:**
• إجمالي الأرصدة: {format_currency(stats['total_balance'])}
• الأرصدة المجمدة: {format_currency(stats['frozen_balance'])}
• المتاحة: {format_currency(stats['total_balance'] - stats['frozen_balance'])}

📊 **المعاملات اليوم:**
• الإيداعات: {format_currency(stats['deposits_today'])}
• السحوبات: {format_currency(stats['withdrawals_today'])}
• الصافي: {format_currency(stats['deposits_today'] - stats['withdrawals_today'])}

⏳ **المعلقة:**
• طلبات إيداع: {stats['pending_deposits']}
• طلبات سحب: {stats['pending_withdrawals']}
"""
    
    await callback.message.edit_text(
        detailed_stats,
        parse_mode="Markdown",
        reply_markup=admin_menu_keyboard()
    )
    await callback.answer()

async def admin_deposits(callback: types.CallbackQuery):
    """عرض طلبات الإيداع المعلقة"""
    pending_deposits = db.get_pending_deposits()
    
    if not pending_deposits:
        await callback.message.edit_text(
            "📭 لا توجد طلبات إيداع معلقة",
            reply_markup=admin_menu_keyboard()
        )
        await callback.answer()
        return
    
    for deposit in pending_deposits[:3]:  # عرض أول 3 طلبات فقط
        deposit_text = f"""
📥 **طلب إيداع #{deposit['id']}**

👤 **المستخدم:** @{deposit['username']}
🆔 **ID:** {deposit['telegram_id']}
💰 **المبلغ:** {format_currency(deposit['amount'])}
💳 **الطريقة:** {deposit['method']}
🔢 **رقم العملية:** {deposit['transaction_id']}
📅 **الوقت:** {deposit['created_at'][:16]}
"""
        
        await callback.message.answer(
            deposit_text,
            reply_markup=admin_deposit_actions_keyboard(deposit['id'], deposit['telegram_id']),
            parse_mode="Markdown"
        )
    
    await callback.answer("📥 عرض طلبات الإيداع")

async def admin_withdrawals(callback: types.CallbackQuery):
    """عرض طلبات السحب المعلقة"""
    pending_withdrawals = db.get_pending_withdrawals()
    
    if not pending_withdrawals:
        await callback.message.edit_text(
            "📭 لا توجد طلبات سحب معلقة",
            reply_markup=admin_menu_keyboard()
        )
        await callback.answer()
        return
    
    for withdrawal in pending_withdrawals[:3]:
        withdrawal_text = f"""
📤 **طلب سحب #{withdrawal['id']}**

👤 **المستخدم:** @{withdrawal['username']}
🆔 **ID:** {withdrawal['telegram_id']}
💰 **المبلغ المطلوب:** {format_currency(withdrawal['amount'])}
💸 **الرسوم:** {format_currency(withdrawal['fee'])}
✅ **المبلغ الصافي:** {format_currency(withdrawal['net_amount'])}
💳 **الطريقة:** {withdrawal['method']}
📝 **المحفظة:** {withdrawal['wallet_info'][:30]}...
📅 **الوقت:** {withdrawal['created_at'][:16]}
"""
        
        await callback.message.answer(
            withdrawal_text,
            reply_markup=admin_withdrawal_actions_keyboard(withdrawal['id'], withdrawal['telegram_id']),
            parse_mode="Markdown"
        )
    
    await callback.answer("📤 عرض طلبات السحب")

async def admin_approve_deposit(callback: types.CallbackQuery):
    """الموافقة على طلب إيداع"""
    data = callback.data.split('_')
    deposit_id = int(data[2])
    user_id = int(data[3])
    
    # الموافقة على الإيداع
    success = db.approve_deposit(deposit_id, callback.from_user.id)
    
    if success:
        deposit = db.get_deposit(deposit_id)
        
        # إشعار المستخدم
        from bot import bot
        try:
            await bot.send_message(
                chat_id=user_id,
                text=f"✅ **تمت الموافقة على إيداعك!**\n\n"
                     f"💰 **المبلغ:** {format_currency(deposit['amount'])}\n"
                     f"💳 **الطريقة:** {deposit['method']}\n"
                     f"🔢 **رقم العملية:** {deposit['transaction_id']}\n"
                     f"📅 **التاريخ:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
                     f"🎉 تم إضافة المبلغ إلى رصيدك بنجاح!"
            )
        except:
            pass
        
        await callback.message.edit_text(
            f"✅ تمت الموافقة على الإيداع #{deposit_id}\n"
            f"💰 {format_currency(deposit['amount'])} أضيفت لرصيد المستخدم",
            reply_markup=admin_menu_keyboard()
        )
    else:
        await callback.message.edit_text(
            f"❌ فشل الموافقة على الإيداع #{deposit_id}",
            reply_markup=admin_menu_keyboard()
        )
    
    await callback.answer()

async def admin_reject_deposit(callback: types.CallbackQuery, state: FSMContext):
    """رفض طلب إيداع"""
    data = callback.data.split('_')
    deposit_id = int(data[2])
    user_id = int(data[3])
    
    # حفظ بيانات الرفض في الحالة
    await state.update_data(
        deposit_id=deposit_id,
        user_id=user_id,
        action='reject_deposit'
    )
    
    await callback.message.answer(
        f"❌ رفض طلب الإيداع #{deposit_id}\n\n"
        f"الرجاء إدخال سبب الرفض:",
        reply_markup=cancel_keyboard()
    )
    
    await callback.answer()

async def admin_approve_withdrawal(callback: types.CallbackQuery):
    """الموافقة على طلب سحب"""
    data = callback.data.split('_')
    withdrawal_id = int(data[2])
    user_id = int(data[3])
    
    # الموافقة على السحب
    success = db.approve_withdrawal(withdrawal_id, callback.from_user.id)
    
    if success:
        withdrawal = db.get_withdrawal(withdrawal_id)
        
        # إشعار المستخدم
        from bot import bot
        try:
            await bot.send_message(
                chat_id=user_id,
                text=f"✅ **تمت معالجة طلب السحب!**\n\n"
                     f"💰 **المبلغ المطلوب:** {format_currency(withdrawal['amount'])}\n"
                     f"💸 **الرسوم:** {format_currency(withdrawal['fee'])}\n"
                     f"✅ **المبلغ المرسل:** {format_currency(withdrawal['net_amount'])}\n"
                     f"💳 **الطريقة:** {withdrawal['method']}\n"
                     f"📝 **المحفظة:** {withdrawal['wallet_info']}\n"
                     f"📅 **التاريخ:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
                     f"💰 **تم إرسال المبلغ بنجاح**"
            )
        except:
            pass
        
        await callback.message.edit_text(
            f"✅ تمت معالجة السحب #{withdrawal_id}\n"
            f"💰 {format_currency(withdrawal['net_amount'])} تم إرسالها للمستخدم",
            reply_markup=admin_menu_keyboard()
        )
    else:
        await callback.message.edit_text(
            f"❌ فشل معالجة السحب #{withdrawal_id}",
            reply_markup=admin_menu_keyboard()
        )
    
    await callback.answer()

async def admin_reject_withdrawal(callback: types.CallbackQuery, state: FSMContext):
    """رفض طلب سحب"""
    data = callback.data.split('_')
    withdrawal_id = int(data[2])
    user_id = int(data[3])
    
    await state.update_data(
        withdrawal_id=withdrawal_id,
        user_id=user_id,
        action='reject_withdrawal'
    )
    
    await callback.message.answer(
        f"❌ رفض طلب السحب #{withdrawal_id}\n\n"
        f"الرجاء إدخال سبب الرفض:",
        reply_markup=cancel_keyboard()
    )
    
    await callback.answer()

async def admin_tickets(callback: types.CallbackQuery):
    """عرض تذاكر الدعم المفتوحة"""
    open_tickets = db.get_open_tickets()
    
    if not open_tickets:
        await callback.message.edit_text(
            "📭 لا توجد تذاكر دعم مفتوحة",
            reply_markup=admin_menu_keyboard()
        )
        await callback.answer()
        return
    
    for ticket in open_tickets[:3]:
        ticket_text = f"""
🛟 **تذكرة دعم #{ticket['id']}**

👤 **المستخدم:** @{ticket['username']}
🆔 **ID:** {ticket['telegram_id']}
📝 **الرسالة:**
{ticket['message'][:200]}...
📅 **الوقت:** {ticket['created_at'][:16]}
"""
        
        await callback.message.answer(
            ticket_text,
            reply_markup=admin_ticket_actions_keyboard(ticket['id'], ticket['telegram_id']),
            parse_mode="Markdown"
        )
    
    await callback.answer("🛟 عرض تذاكر الدعم")

async def admin_reply_ticket(callback: types.CallbackQuery, state: FSMContext):
    """الرد على تذكرة دعم"""
    data = callback.data.split('_')
    ticket_id = int(data[2])
    user_id = int(data[3])
    
    await state.update_data(
        ticket_id=ticket_id,
        user_id=user_id
    )
    
    await callback.message.answer(
        f"📩 الرد على التذكرة #{ticket_id}\n\n"
        f"أدخل ردك:",
        reply_markup=cancel_keyboard()
    )
    
    await callback.answer()

async def process_admin_reply(message: types.Message, state: FSMContext):
    """معالجة رد الإدارة"""
    data = await state.get_data()
    reply = message.text
    
    # الرد على التذكرة
    success = db.reply_to_ticket(data['ticket_id'], reply)
    
    if success:
        # إرسال الرد للمستخدم
        from bot import bot
        try:
            await bot.send_message(
                chat_id=data['user_id'],
                text=f"📩 **رد من الدعم الفني**\n\n"
                     f"{reply}\n\n"
                     f"💬 تم إغلاق التذكرة"
            )
        except:
            pass
        
        await message.answer(
            f"✅ تم إرسال الرد للمستخدم",
            reply_markup=admin_menu_keyboard()
        )
    else:
        await message.answer(
            "❌ فشل إرسال الرد",
            reply_markup=admin_menu_keyboard()
        )
    
    await state.finish()
