from telebot import types
from config import ADMINS
from database import get_connection

def admin_handlers(bot):

    @bot.message_handler(commands=['admin'])
    def admin_panel(message):
        if message.from_user.id not in ADMINS:
            return

        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add("🔍 بحث عن مستخدم")
        kb.add("📋 كل المستخدمين")
        kb.add("❌ إغلاق")
        bot.send_message(message.chat.id, "🔐 لوحة تحكم الأدمن", reply_markup=kb)

    # قائمة كل المستخدمين
    @bot.message_handler(func=lambda m: m.text == "📋 كل المستخدمين")
    def all_users(message):
        if message.from_user.id not in ADMINS:
            return
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT telegram_id, username, balance, status FROM users")
        rows = cur.fetchall()
        conn.close()
        text = ""
        for r in rows:
            text += f"ID: {r[0]} | {r[1]} | رصيد: {r[2]} | حالة: {r[3]}\n"
        bot.send_message(message.chat.id, text or "لا يوجد مستخدمين.")

    # البحث عن مستخدم
    @bot.message_handler(func=lambda m: m.text == "🔍 بحث عن مستخدم")
    def search_user(message):
        if message.from_user.id not in ADMINS:
            return
        msg = bot.send_message(message.chat.id, "أرسل ID المستخدم للبحث عنه:")
        bot.register_next_step_handler(msg, process_search)

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
