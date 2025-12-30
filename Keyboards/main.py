from telebot import types
from config import ADMINS

def main_menu(uid):
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("➕ إنشاء حساب", callback_data="create_account"),
        types.InlineKeyboardButton("💰 الرصيد", callback_data="balance")
    )
    kb.add(
        types.InlineKeyboardButton("💰 إيداع", callback_data="deposit"),
        types.InlineKeyboardButton("💸 سحب", callback_data="withdraw")
    )
    kb.add(
        types.InlineKeyboardButton("🔑 تغيير كلمة السر", callback_data="change_pass"),
        types.InlineKeyboardButton("📞 الدعم", callback_data="support")
    )
    if uid in ADMINS:
        kb.add(types.InlineKeyboardButton("🎛 لوحة الأدمن", callback_data="admin_panel"))
    return kb
