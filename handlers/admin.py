from database import init_db
from .admin import admin_menu  # صححت المسار
from .commands import main_menu  # صححت المسار
from config import ADMINS

conn, cur = init_db()
admin_state = {}
temp = {}

def register_admin(bot):

    @bot.message_handler(func=lambda m: m.chat.id in admin_state)
    def admin_steps(message):
        uid = message.chat.id
        step = admin_state[uid]

        if step == "add_id":
            temp[uid] = int(message.text)
            admin_state[uid] = "add_amount"
            bot.send_message(uid, "💰 أرسل المبلغ")

        elif step == "add_amount":
            cur.execute("UPDATE users SET balance = balance + ? WHERE telegram_id=?",
                        (int(message.text), temp[uid]))
            conn.commit()
            bot.send_message(uid, "✅ تم إضافة الرصيد")
            bot.send_message(temp[uid], f"💰 تم شحن رصيدك: {message.text}")
            cur.execute("INSERT INTO logs (telegram_id, action, details) VALUES (?,?,?)",
                        (temp[uid], "إضافة رصيد يدوي", f"المبلغ: {message.text}"))
            conn.commit()
            admin_state.pop(uid)
