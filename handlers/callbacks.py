from .main import main_menu  # صححت المسار
from .admin import admin_state
from database import init_db
from config import ADMINS

conn, cur = init_db()
user_state = {}
user_temp = {}
pending_requests = {"deposit": [], "withdraw": []}

def register_callbacks(bot):

    @bot.callback_query_handler(func=lambda call: True)
    def callbacks(call):
        uid = call.message.chat.id
        data = call.data

        if data == "back":
            bot.edit_message_text("⬅️ رجوع", uid, call.message.id, reply_markup=main_menu(uid))

        elif data == "balance":
            cur.execute("SELECT balance FROM users WHERE telegram_id=?", (uid,))
            bal = cur.fetchone()[0]
            bot.send_message(uid, f"💰 رصيدك: {bal}")

        elif data == "support":
            bot.send_message(uid, "📞 استخدم /help للتواصل مع الدعم")

        elif data == "create_account":
            user_state[uid] = "account_name"
            bot.send_message(uid, "✍️ أرسل اسم الحساب")

        elif data == "deposit":
            user_state[uid] = "deposit_amount"
            bot.send_message(uid, f"💰 أدخل مبلغ الإيداع (الحد الأدنى 25000)")

        elif data == "withdraw":
            user_state[uid] = "withdraw_amount"
            bot.send_message(uid, f"💸 أدخل مبلغ السحب (الحد الأدنى 50000)")

        elif data == "admin_panel" and uid in ADMINS:
            from .admin import admin_menu  # import هنا عشان يكون متوافق
            bot.send_message(uid, "🎛 لوحة تحكم الأدمن", reply_markup=admin_menu())
