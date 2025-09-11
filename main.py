from flask import Flask, request
import telebot
from telebot import types
import os

# ======= إعدادات البوت =======
TOKEN = "8317743306:AAFGH1Acxb6fIwZ0o0T2RvNjezQFW8KWcw8"
ADMIN_ID = 7625893170

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# ======= Start command مع الأزرار =======
@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn1 = types.KeyboardButton("إنشاء حساب")
    btn2 = types.KeyboardButton("إيداع")
    btn3 = types.KeyboardButton("سحب")
    markup.add(btn1, btn2, btn3)
    
    bot.send_message(message.chat.id, "أهلاً! اختر من القائمة:", reply_markup=markup)

# ======= الردود على الأزرار =======
@bot.message_handler(func=lambda message: True)
def handle_buttons(message):
    text = message.text
    if text == "إنشاء حساب":
        bot.send_message(message.chat.id, "📌 أرسل اسم الحساب الذي تريد إنشاءه:")
        bot.register_next_step_handler(message, create_account)
    elif text == "إيداع":
        bot.send_message(message.chat.id, "💰 أرسل اسم الحساب ثم المبلغ للإيداع:")
        bot.register_next_step_handler(message, deposit)
    elif text == "سحب":
        bot.send_message(message.chat.id, "💸 أرسل المبلغ ثم تفاصيل محفظتك للسحب:")
        bot.register_next_step_handler(message, withdraw)
    else:
        # أي رسالة أخرى تصل للادمن
        bot.send_message(ADMIN_ID, f"رسالة من {message.from_user.username} ({message.from_user.id}): {message.text}")

# ======= دوال العمليات =======
def create_account(message):
    username = message.text
    bot.send_message(message.chat.id, f"تم إنشاء حسابك ✅\nUsername: {username}")
    bot.send_message(ADMIN_ID, f"طلب إنشاء حساب جديد:\nUsername: {username}\nمن المستخدم: {message.from_user.username} ({message.from_user.id})")

def deposit(message):
    data = message.text
    bot.send_message(message.chat.id, f"تم استلام طلب الإيداع ✅\nتفاصيل: {data}")
    bot.send_message(ADMIN_ID, f"طلب إيداع:\n{data}\nمن المستخدم: {message.from_user.username} ({message.from_user.id})")

def withdraw(message):
    data = message.text
    bot.send_message(message.chat.id, f"تم استلام طلب السحب ✅\nتفاصيل: {data}")
    bot.send_message(ADMIN_ID, f"طلب سحب:\n{data}\nمن المستخدم: {message.from_user.username} ({message.from_user.id})")

# ======= Flask route للـ Webhook =======
@app.route(f"/{TOKEN}", methods=['POST'])
def webhook():
    json_str = request.get_data().decode('UTF-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "!", 200

# ======= صفحة اختبار السيرفر =======
@app.route("/")
def index():
    return "بوت Telegram شغال على Render!", 200

# ======= تشغيل البوت على Render =======
if __name__ == "__main__":
    if os.environ.get("RENDER_EXTERNAL_URL"):
        WEBHOOK_URL = os.environ.get("RENDER_EXTERNAL_URL") + f"/{TOKEN}"
        bot.remove_webhook()
        bot.set_webhook(url=WEBHOOK_URL)
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
