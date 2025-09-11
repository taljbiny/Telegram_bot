from flask import Flask, request
import telebot
from telebot import types
import os

# ======= إعدادات البوت =======
TOKEN = "8317743306:AAFGH1Acxb6fIwZ0o0T2RvNjezQFW8KWcw8"
ADMIN_ID = 7625893170
MIN_AMOUNT = 25000  # الحد الأدنى للسحب

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# ======= Start command مع الأزرار والإيموجي =======
@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn1 = types.KeyboardButton("📝 إنشاء حساب")
    btn2 = types.KeyboardButton("💰 إيداع")
    btn3 = types.KeyboardButton("💸 سحب")
    markup.add(btn1, btn2, btn3)
    bot.send_message(message.chat.id, "أهلاً! اختر من القائمة:", reply_markup=markup)

# ======= الردود على الأزرار =======
@bot.message_handler(func=lambda message: True)
def handle_buttons(message):
    text = message.text
    if text == "📝 إنشاء حساب":
        bot.send_message(message.chat.id, "📌 أرسل اسم الحساب الذي تريد إنشاءه:")
        bot.register_next_step_handler(message, create_account)
    elif text == "💰 إيداع":
        bot.send_message(message.chat.id, "🔑 أرسل اسم الحساب/Username الذي أخذته من البوت:")
        bot.register_next_step_handler(message, deposit_get_amount)
    elif text == "💸 سحب":
        bot.send_message(message.chat.id, "🔑 أرسل اسم الحساب/Username الذي أخذته من البوت:")
        bot.register_next_step_handler(message, withdraw_get_amount)
    else:
        # أي رسالة أخرى تصل للادمن
        bot.send_message(ADMIN_ID, f"رسالة من {message.from_user.username} ({message.from_user.id}): {message.text}")

# ======= إنشاء الحساب =======
def create_account(message):
    username = message.text
    bot.send_message(message.chat.id, "✅ تم استلام طلبك، سيتم إرسال تفاصيل الحساب بأسرع وقت ممكن")
    bot.send_message(ADMIN_ID, f"📌 طلب إنشاء حساب جديد:\nUsername: {username}\nمن المستخدم: {message.from_user.username} ({message.from_user.id})")

# ======= الإيداع =======
def deposit_get_amount(message):
    username = message.text
    bot.send_message(message.chat.id, "💰 أرسل المبلغ الذي تريد إيداعه:")
    bot.register_next_step_handler(message, deposit_choose_method, username)

def deposit_choose_method(message, username):
    try:
        amount = int(message.text.replace(',', '').replace(' ', ''))
        if amount < MIN_AMOUNT:
            bot.send_message(message.chat.id, f"⚠️ المبلغ أقل من الحد الأدنى {MIN_AMOUNT} ل.س، أرسل مبلغ أكبر أو يساوي الحد الأدنى.")
            bot.register_next_step_handler(message, deposit_choose_method, username)
            return
    except ValueError:
        bot.send_message(message.chat.id, "⚠️ يرجى إدخال مبلغ صحيح بالأرقام فقط.")
        bot.register_next_step_handler(message, deposit_choose_method, username)
        return

    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn1 = types.KeyboardButton("سيرياتيل كاش")
    btn2 = types.KeyboardButton("شام كاش")
    markup.add(btn1, btn2)
    bot.send_message(message.chat.id, f"💳 اختر طريقة الدفع للإيداع ({amount} ل.س):", reply_markup=markup)
    bot.register_next_step_handler(message, deposit_confirm, username, amount)

def deposit_confirm(message, username, amount):
    method = message.text
    bot.send_message(message.chat.id, f"✅ تم استلام طلب الإيداع.\nUsername: {username}\nالمبلغ: {amount} ل.س\nطريقة الدفع: {method}\nسيتم التواصل معك لتأكيد العملية")
    bot.send_message(ADMIN_ID, f"💰 طلب إيداع:\nUsername: {username}\nالمبلغ: {amount} ل.س\nطريقة الدفع: {method}\nمن المستخدم: {message.from_user.username} ({message.from_user.id})")

# ======= السحب =======
def withdraw_get_amount(message):
    username = message.text
    bot.send_message(message.chat.id, "💸 أرسل المبلغ الذي تريد سحبه:")
    bot.register_next_step_handler(message, withdraw_choose_method, username)

def withdraw_choose_method(message, username):
    try:
        amount = int(message.text.replace(',', '').replace(' ', ''))
        if amount < MIN_AMOUNT:
            bot.send_message(message.chat.id, f"⚠️ المبلغ أقل من الحد الأدنى {MIN_AMOUNT} ل.س، أرسل مبلغ أكبر أو يساوي الحد الأدنى.")
            bot.register_next_step_handler(message, withdraw_choose_method, username)
            return
    except ValueError:
        bot.send_message(message.chat.id, "⚠️ يرجى إدخال مبلغ صحيح بالأرقام فقط.")
        bot.register_next_step_handler(message, withdraw_choose_method, username)
        return

    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn1 = types.KeyboardButton("سيرياتيل كاش")
    btn2 = types.KeyboardButton("شام كاش")
    markup.add(btn1, btn2)
    bot.send_message(message.chat.id, f"💳 اختر طريقة الدفع للسحب ({amount} ل.س):", reply_markup=markup)
    bot.register_next_step_handler(message, withdraw_confirm, username, amount)

def withdraw_confirm(message, username, amount):
    method = message.text
    bot.send_message(message.chat.id, f"✅ تم استلام طلب السحب.\nUsername: {username}\nالمبلغ: {amount} ل.س\nطريقة الدفع: {method}\nسيتم التواصل معك لتأكيد العملية")
    bot.send_message(ADMIN_ID, f"💸 طلب سحب:\nUsername: {username}\nالمبلغ: {amount} ل.س\nطريقة الدفع: {method}\nمن المستخدم: {message.from_user.username} ({message.from_user.id})")

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
