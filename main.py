from flask import Flask, request
import telebot
from telebot import types
import os

# ======= إعدادات البوت =======
TOKEN = "8317743306:AAFGH1Acxb6fIwZ0o0T2RvNjezQFW8KWcw8"
ADMIN_ID = 7625893170
MIN_AMOUNT = 25000
SERIATEL_CASH_NUMBER = "0996099355"

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# ======= قائمة رئيسية =======
def main_menu(chat_id):
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn1 = types.KeyboardButton("📝 إنشاء حساب")
    btn2 = types.KeyboardButton("💰 إيداع")
    btn3 = types.KeyboardButton("💸 سحب")
    markup.add(btn1, btn2, btn3)
    bot.send_message(chat_id, "أهلاً! اختر من القائمة:", reply_markup=markup)

# ======= Start command =======
@bot.message_handler(commands=['start'])
def send_welcome(message):
    main_menu(message.chat.id)

# ======= أمر الرد للادمن =======
@bot.message_handler(commands=['reply'])
def admin_reply(message):
    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "⚠️ أنت لست الأدمن.")
        return
    parts = message.text.split(' ', 2)
    if len(parts) < 3:
        bot.send_message(message.chat.id, "⚠️ استخدم الصيغة: /reply <user_id> <رسالتك>")
        return
    try:
        user_id = int(parts[1])
        reply_text = parts[2]
        bot.send_message(user_id, reply_text)  # 🔹 بدون كلمة "رد من الأدمن"
        bot.send_message(message.chat.id, "✅ تم إرسال الرسالة للمستخدم.")
    except ValueError:
        bot.send_message(message.chat.id, "⚠️ معرف المستخدم غير صالح.")

# ======= التعامل مع الأزرار =======
@bot.message_handler(func=lambda message: True, content_types=['text'])
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
    elif text == "🏠 القائمة الرئيسية":
        main_menu(message.chat.id)
    else:
        bot.send_message(ADMIN_ID, f"رسالة من {message.from_user.username} ({message.from_user.id}): {message.text}")

# ======= إنشاء الحساب =======
def create_account(message):
    username = message.text
    bot.send_message(message.chat.id, "✅ تم استلام طلبك، سيتم إرسال تفاصيل الحساب بأسرع وقت ممكن")
    bot.send_message(ADMIN_ID, f"📌 طلب إنشاء حساب جديد:\nUsername: {username}\nمن المستخدم: {message.from_user.username} ({message.from_user.id})")
    bot.send_message(message.chat.id, "🏠 للعودة للقائمة الرئيسية اضغط: 🏠 القائمة الرئيسية")

# ======= الإيداع =======
def deposit_get_amount(message):
    username = message.text
    bot.send_message(message.chat.id, "💰 أرسل المبلغ الذي تريد إيداعه:")
    bot.register_next_step_handler(message, deposit_enter_amount, username)

def deposit_enter_amount(message, username):
    try:
        amount = int(message.text.replace(',', '').replace(' ', ''))
        if amount < MIN_AMOUNT:
            bot.send_message(message.chat.id, f"⚠️ أدنى حد للسحب والتعبئة {MIN_AMOUNT} ل.س 🌹")
            bot.register_next_step_handler(message, deposit_enter_amount, username)
            return
    except ValueError:
        bot.send_message(message.chat.id, "⚠️ يرجى إدخال مبلغ صحيح بالأرقام فقط.")
        bot.register_next_step_handler(message, deposit_enter_amount, username)
        return

    bot.send_message(message.chat.id,
                     f"💳 رقم محفظة سيرياتيل كاش لإتمام الإيداع: {SERIATEL_CASH_NUMBER}\n📸 بعد الدفع، أرسل صورة التأكيد أو إشعار العملية:")
    bot.register_next_step_handler(message, deposit_confirm, username, amount)

def deposit_confirm(message, username, amount):
    if message.content_type == "photo":
        # إذا بعت صورة، نحولها للأدمن
        file_id = message.photo[-1].file_id
        bot.send_photo(ADMIN_ID, file_id,
                       caption=f"💰 طلب إيداع:\nUsername: {username}\nالمبلغ: {amount} ل.س\nمن المستخدم: {message.from_user.username} ({message.from_user.id})")
    else:
        bot.send_message(ADMIN_ID, f"💰 طلب إيداع:\nUsername: {username}\nالمبلغ: {amount} ل.س\nتأكيد: {message.text}\nمن المستخدم: {message.from_user.username} ({message.from_user.id})")

    bot.send_message(message.chat.id, f"✅ تم استلام الإيداع بنجاح.\nUsername: {username}\nالمبلغ: {amount} ل.س")
    bot.send_message(message.chat.id, "🏠 للعودة للقائمة الرئيسية اضغط: 🏠 القائمة الرئيسية")

# ======= السحب =======
def withdraw_get_amount(message):
    username = message.text
    bot.send_message(message.chat.id, "💸 أرسل المبلغ الذي تريد سحبه:")
    bot.register_next_step_handler(message, withdraw_enter_amount, username)

def withdraw_enter_amount(message, username):
    try:
        amount = int(message.text.replace(',', '').replace(' ', ''))
        if amount < MIN_AMOUNT:
            bot.send_message(message.chat.id, f"⚠️ أدنى حد للسحب والتعبئة {MIN_AMOUNT} ل.س 🌹")
            bot.register_next_step_handler(message, withdraw_enter_amount, username)
            return
    except ValueError:
        bot.send_message(message.chat.id, "⚠️ يرجى إدخال مبلغ صحيح بالأرقام فقط.")
        bot.register_next_step_handler(message, withdraw_enter_amount, username)
        return

    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn1 = types.KeyboardButton("سيرياتيل كاش")
    btn2 = types.KeyboardButton("شام كاش")
    markup.add(btn1, btn2)
    bot.send_message(message.chat.id, f"💳 اختر طريقة الدفع للسحب ({amount} ل.س):", reply_markup=markup)
    bot.register_next_step_handler(message, withdraw_enter_wallet, username, amount)

def withdraw_enter_wallet(message, username, amount):
    method = message.text
    bot.send_message(message.chat.id, "📌 أرسل رقم محفظتك ليتم تحويل المبلغ:")
    bot.register_next_step_handler(message, withdraw_confirm, username, amount, method)

def withdraw_confirm(message, username, amount, method):
    wallet = message.text
    bot.send_message(message.chat.id, "✅ تم استلام طلب السحب\n📌 طلبك قيد المعالجة، عند الانتهاء سنرسل لك تأكيد العملية")
    bot.send_message(ADMIN_ID, f"💸 طلب سحب:\nUsername: {username}\nالمبلغ: {amount} ل.س\nطريقة الدفع: {method}\nرقم المحفظة: {wallet}\nمن المستخدم: {message.from_user.username} ({message.from_user.id})")
    bot.send_message(message.chat.id, "🏠 للعودة للقائمة الرئيسية اضغط: 🏠 القائمة الرئيسية")

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
