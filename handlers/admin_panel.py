from telebot import types
from config import ADMINS
from database import get_connection

def admin_handlers(bot):

    @bot.message_handler(commands=['admin'])
    def admin_panel(message):
        if message.from_user.id not in ADMINS:
            return

        kb = types.InlineKeyboardMarkup(row_width=2)
        kb.add(
            types.InlineKeyboardButton("📋 كل المستخدمين", callback_data="all_users"),
            types.InlineKeyboardButton("🔍 بحث عن مستخدم", callback_data="search_user")
        )
        kb.add(
            types.InlineKeyboardButton("💵 شحن البوت", callback_data="bot_deposit"),
            types.InlineKeyboardButton("💸 سحب من البوت", callback_data="bot_withdraw")
        )

        bot.send_message(message.chat.id, "🔐 لوحة تحكم الأدمن", reply_markup=kb)

    @bot.callback_query_handler(func=lambda call: True)
    def admin_callback(call):
        if call.data == "all_users":
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("SELECT telegram_id, username, balance, status FROM users")
            rows = cur.fetchall()
            conn.close()
            text = ""
            for r in rows:
                text += f"ID: {r[0]} | {r[1]} | رصيد: {r[2]} | حالة: {r[3]}\n"
            bot.send_message(call.message.chat.id, text or "لا يوجد مستخدمين.")
        elif call.data == "search_user":
            msg = bot.send_message(call.message.chat.id, "أرسل ID المستخدم للبحث عنه:")
            bot.register_next_step_handler(msg, process_search)
        elif call.data == "bot_deposit":
            bot.send_message(call.message.chat.id, "💵 شحن رصيد البوت")
        elif call.data == "bot_withdraw":
            bot.send_message(call.message.chat.id, "💸 سحب رصيد من البوت")

    def process_search(message):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT telegram_id, username, balance, status FROM users WHERE telegram_id=?", (message.text,))
        row = cur.fetchone()
        conn.close()
        if row:
            bot.send_message(message.chat.id, f"ID: {row[0]} | {row[1]} | رصيد: {row[2]} | حالة: {row[3]}")
        else:
            bot.send_message(message.chat.id, "المستخدم غير موجود.")
