from telebot import types

def admin_menu():
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("➕ إضافة رصيد", callback_data="admin_add_balance"),
        types.InlineKeyboardButton("🔍 بحث مستخدم", callback_data="admin_search")
    )
    kb.add(
        types.InlineKeyboardButton("👥 جميع المستخدمين", callback_data="admin_users"),
        types.InlineKeyboardButton("✅ الموافقة على الطلبات", callback_data="admin_pending")
    )
    kb.add(types.InlineKeyboardButton("📜 سجل العمليات", callback_data="admin_logs"))
    kb.add(types.InlineKeyboardButton("⬅️ رجوع", callback_data="back"))
    return kb
