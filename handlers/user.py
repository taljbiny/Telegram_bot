from telebot import types
from database import get_connection

def user_handlers(bot):

    @bot.message_handler(commands=['start'])
    def start(message):
        conn = get_connection()
        cur = conn.cursor()

        # إضافة المستخدم إذا جديد
        cur.execute(
            "INSERT OR IGNORE INTO users (telegram_id, username) VALUES (?, ?)",
            (message.from_user.id, message.from_user.username)
        )
        conn.commit()
        conn.close()

        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add("➕ إيداع", "➖ سحب")
        kb.add("💰 رصيدي")
        kb.add("📝 سجل المعاملات")

        bot.send_message(
            message.chat.id,
            "أهلاً بك 👋\nاختر من القائمة:",
            reply_markup=kb
        )

    # رصيد المستخدم
    @bot.message_handler(func=lambda m: m.text == "💰 رصيدي")
    def balance(message):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT balance FROM users WHERE telegram_id=?", (message.from_user.id,))
        result = cur.fetchone()
        conn.close()
        balance = result[0] if result else 0
        bot.send_message(message.chat.id, f"رصيدك الحالي: {balance} وحدة")

    # سجل المعاملات
    @bot.message_handler(func=lambda m: m.text == "📝 سجل المعاملات")
    def transactions(message):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT type, method, amount, status, created_at FROM transactions WHERE user_id=? ORDER BY id DESC LIMIT 10", (message.from_user.id,))
        rows = cur.fetchall()
        conn.close()
        if not rows:
            bot.send_message(message.chat.id, "لا توجد معاملات بعد.")
        else:
            text = ""
            for r in rows:
                text += f"{r[0]} {r[1]} {r[2]} | {r[3]} | {r[4]}\n"
            bot.send_message(message.chat.id, text)
