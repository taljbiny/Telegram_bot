from telebot import types
from database import cursor, conn
from config import SYRIATEL_CASH_NUMBER, SHAM_CASH_CODE

user_steps = {}

def register(bot):

    @bot.message_handler(commands=["start"])
    def start(message):
        cursor.execute(
            "INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)",
            (message.chat.id, message.from_user.username)
        )
        conn.commit()

        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add("➕ إنشاء حساب", "💰 إيداع")
        kb.add("💸 سحب", "📞 دعم")
        bot.send_message(message.chat.id, "أهلاً بك 🤍", reply_markup=kb)

    @bot.message_handler(commands=["balance"])
    def balance(message):
        cursor.execute("SELECT balance FROM users WHERE user_id=?", (message.chat.id,))
        bal = cursor.fetchone()[0]
        bot.send_message(message.chat.id, f"💰 رصيدك: {bal}")

    @bot.message_handler(func=lambda m: m.text == "💰 إيداع")
    def deposit(message):
        bot.send_message(message.chat.id, "💰 أرسل المبلغ:")
        user_steps[message.chat.id] = "deposit_amount"

    @bot.message_handler(func=lambda m: m.text == "💸 سحب")
    def withdraw(message):
        bot.send_message(message.chat.id, "💸 أرسل المبلغ:")
        user_steps[message.chat.id] = "withdraw_amount"

    @bot.message_handler(content_types=["text"])
    def handle(message):
        step = user_steps.get(message.chat.id)

        if step == "deposit_amount":
            kb = types.InlineKeyboardMarkup()
            kb.add(
                types.InlineKeyboardButton("سيرياتيل كاش", callback_data=f"dep_sy_{message.text}"),
                types.InlineKeyboardButton("شام كاش", callback_data=f"dep_sh_{message.text}")
            )
            bot.send_message(message.chat.id, "اختر طريقة الدفع:", reply_markup=kb)
            user_steps.pop(message.chat.id)

        elif step == "withdraw_amount":
            user_steps[message.chat.id] = {"amount": message.text}
            bot.send_message(message.chat.id, "📲 أرسل محفظة سيرياتيل كاش")

        elif isinstance(step, dict):
            cursor.execute(
                "INSERT INTO withdrawals (user_id, amount, wallet, status) VALUES (?,?,?,?)",
                (message.chat.id, step["amount"], message.text, "pending")
            )
            conn.commit()
            bot.send_message(message.chat.id, "⏳ طلب السحب قيد المراجعة")
            user_steps.pop(message.chat.id)
