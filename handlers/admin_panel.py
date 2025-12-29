from telebot import types
from config import ADMINS
from database import get_connection

def admin_handlers(bot):

    @bot.message_handler(commands=['admin'])
    def admin_panel(message):
        if message.from_user.id not in ADMINS:
            bot.send_message(message.chat.id, "❌ أنت لست الأدمن.")
            return
        kb = types.InlineKeyboardMarkup(row_width=2)
        kb.add(
            types.InlineKeyboardButton("🔍 بحث عن مستخدم", callback_data="search_user"),
            types.InlineKeyboardButton("💰 شحن/سحب رصيد", callback_data="manage_balance"),
            types.InlineKeyboardButton("📄 مراجعة العمليات", callback_data="review_transactions"),
            types.InlineKeyboardButton("🛠 الرد على الدعم", callback_data="support_admin")
        )
        bot.send_message(message.chat.id, "لوحة تحكم الأدمن:", reply_markup=kb)
