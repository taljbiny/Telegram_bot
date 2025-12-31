from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def admin_menu_keyboard():
    """قائمة الإدارة"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    buttons = [
        ("📊 الإحصائيات", "admin_stats"),
        ("👥 المستخدمين", "admin_users"),
        ("📥 طلبات الإيداع", "admin_deposits"),
        ("📤 طلبات السحب", "admin_withdrawals"),
        ("🛟 تذاكر الدعم", "admin_tickets"),
        ("⚙️ الإعدادات", "admin_settings")
    ]
    
    for text, callback in buttons:
        keyboard.add(InlineKeyboardButton(text, callback_data=callback))
    
    return keyboard

def admin_deposit_actions_keyboard(deposit_id, user_id):
    """إجراءات على طلب إيداع"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("✅ قبول", callback_data=f"approve_deposit_{deposit_id}_{user_id}"),
        InlineKeyboardButton("❌ رفض", callback_data=f"reject_deposit_{deposit_id}_{user_id}")
    )
    return keyboard

def admin_withdrawal_actions_keyboard(withdrawal_id, user_id):
    """إجراءات على طلب سحب"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("✅ معالجة", callback_data=f"approve_withdrawal_{withdrawal_id}_{user_id}"),
        InlineKeyboardButton("❌ رفض", callback_data=f"reject_withdrawal_{withdrawal_id}_{user_id}")
    )
    return keyboard

def admin_ticket_actions_keyboard(ticket_id, user_id):
    """إجراءات على تذكرة دعم"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("📩 رد", callback_data=f"reply_ticket_{ticket_id}_{user_id}"),
        InlineKeyboardButton("✅ إغلاق", callback_data=f"close_ticket_{ticket_id}_{user_id}")
    )
    return keyboard
