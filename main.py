import telebot
from telebot import types
from flask import Flask, request

# ====== الإعدادات ======
TOKEN = "8317743306:AAFGH1Acxb6fIwZ0o0T2RvNjezQFW8KWcw8"
ADMIN_ID = 7625893170
bot = telebot.TeleBot(TOKEN)
server = Flask(__name__)

# ====== لوحة البداية ======
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("🆕 إنشاء حساب")
    markup.row("💰 إيداع", "💵 سحب")
    return markup

# ====== زر الرجوع ======
def back_button():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("🔙 رجوع للقائمة الرئيسية")
    return markup

# ====== /start ======
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(
        message.chat.id,
        "أهلاً بك 👋\nاختر من القائمة:",
        reply_markup=main_menu()
    )

# ====== الرجوع للقائمة الرئيسية ======
@bot.message_handler(func=lambda message: message.text == "🔙 رجوع للقائمة الرئيسية")
def back_to_menu(message):
    bot.send_message(
        message.chat.id,
        "رجعت للقائمة الرئيسية ✅",
        reply_markup=main_menu()
    )

# ====== إنشاء حساب ======
@bot.message_handler(func=lambda message: message.text == "🆕 إنشاء حساب")
def create_account(message):
    msg = bot.send_message(message.chat.id, "📛 أرسل اسم الحساب:", reply_markup=back_button())
    bot.register_next_step_handler(msg, process_account_name)

def process_account_name(message):
    if message.text == "🔙 رجوع للقائمة الرئيسية":
        return back_to_menu(message)

    account_name = message.text
    bot.send_message(
        ADMIN_ID,
        f"📥 طلب إنشاء حساب جديد:\nاسم الحساب: {account_name}\nمن المستخدم: {message.from_user.id}"
    )
    bot.send_message(message.chat.id, f"✅ تم استلام طلب إنشاء الحساب: {account_name}\nبانتظار رد الادمن.", reply_markup=main_menu())

# ====== إيداع ======
@bot.message_handler(func=lambda message: message.text == "💰 إيداع")
def deposit(message):
    msg = bot.send_message(message.chat.id, "📛 أرسل اسم حسابك:", reply_markup=back_button())
    bot.register_next_step_handler(msg, process_deposit_name)

def process_deposit_name(message):
    if message.text == "🔙 رجوع للقائمة الرئيسية":
        return back_to_menu(message)

    account_name = message.text
    msg = bot.send_message(message.chat.id, "💵 أدخل المبلغ (أقل عملية 25,000 ل.س):", reply_markup=back_button())
    bot.register_next_step_handler(msg, process_deposit_amount, account_name)

def process_deposit_amount(message, account_name):
    if message.text == "🔙 رجوع للقائمة الرئيسية":
        return back_to_menu(message)

    try:
        amount = int(message.text.replace(",", "").replace(".", ""))
        if amount < 25000:
            msg = bot.send_message(message.chat.id, "⚠️ المبلغ يجب أن يكون 25,000 ل.س أو أكثر.\nأدخل المبلغ من جديد:", reply_markup=back_button())
            return bot.register_next_step_handler(msg, process_deposit_amount, account_name)
    except:
        msg = bot.send_message(message.chat.id, "⚠️ رجاءً أدخل المبلغ بشكل صحيح:", reply_markup=back_button())
        return bot.register_next_step_handler(msg, process_deposit_amount, account_name)

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("📲 سيرياتيل كاش")
    markup.row("🏦 شام كاش", "💳 حوالة")
    markup.row("🔙 رجوع للقائمة الرئيسية")
    msg = bot.send_message(message.chat.id, "اختر طريقة الدفع:", reply_markup=markup)
    bot.register_next_step_handler(msg, process_payment_method, account_name, amount)

def process_payment_method(message, account_name, amount):
    if message.text == "🔙 رجوع للقائمة الرئيسية":
        return back_to_menu(message)

    method = message.text
    if method == "📲 سيرياتيل كاش":
        msg = bot.send_message(
            message.chat.id,
            "💳 أرسل المبلغ إلى الرقم التالي:\n📱 82492253\nبعد الدفع أرسل صورة التأكيد.",
            reply_markup=back_button()
        )
        bot.register_next_step_handler(msg, confirm_payment, account_name, amount, method)
    elif method in ["🏦 شام كاش", "💳 حوالة"]:
        bot.send_message(message.chat.id, "❌ هذه الطريقة غير متوفرة حالياً.", reply_markup=main_menu())
    else:
        bot.send_message(message.chat.id, "⚠️ خيار غير صحيح.", reply_markup=main_menu())

def confirm_payment(message, account_name, amount, method):
    if message.text == "🔙 رجوع للقائمة الرئيسية":
        return back_to_menu(message)

    if message.content_type == "photo":
        bot.send_message(
            ADMIN_ID,
            f"📥 عملية إيداع:\nاسم الحساب: {account_name}\nالمبلغ: {amount}\nالطريقة: {method}\nمن المستخدم: {message.from_user.id}"
        )
        bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption="📸 صورة تأكيد الدفع")
        bot.send_message(message.chat.id, "✅ تم استلام عملية الإيداع.\nطلبك قيد المعالجة.", reply_markup=main_menu())
    else:
        bot.send_message(message.chat.id, "⚠️ رجاءً أرسل صورة تأكيد الدفع.", reply_markup=back_button())
        bot.register_next_step_handler(message, confirm_payment, account_name, amount, method)

# ====== سحب ======
@bot.message_handler(func=lambda message: message.text == "💵 سحب")
def withdraw_options(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("📲 سيرياتيل كاش")
    markup.row("🏦 شام كاش", "💳 حوالة")
    markup.row("🔙 رجوع للقائمة الرئيسية")
    bot.send_message(message.chat.id, "اختر طريقة السحب:", reply_markup=markup)
    bot.register_next_step_handler(message, withdraw_method)

def withdraw_method(message):
    if message.text == "🔙 رجوع للقائمة الرئيسية":
        return back_to_menu(message)

    method = message.text
    if method == "📲 سيرياتيل كاش":
        msg = bot.send_message(message.chat.id, "📛 أرسل اسم حسابك للسحب:", reply_markup=back_button())
        bot.register_next_step_handler(msg, process_withdraw_name, method)
    elif method in ["🏦 شام كاش", "💳 حوالة"]:
        bot.send_message(message.chat.id, "❌ هذه الطريقة غير متوفرة حالياً.", reply_markup=main_menu())
    else:
        bot.send_message(message.chat.id, "⚠️ خيار غير صحيح.", reply_markup=main_menu())

def process_withdraw_name(message, method):
    if message.text == "🔙 رجوع للقائمة الرئيسية":
        return back_to_menu(message)

    account_name = message.text
    msg = bot.send_message(message.chat.id, "💵 أرسل المبلغ المطلوب (أقل عملية 25,000 ل.س):", reply_markup=back_button())
    bot.register_next_step_handler(msg, process_withdraw_amount, account_name, method)

def process_withdraw_amount(message, account_name, method):
    if message.text == "🔙 رجوع للقائمة الرئيسية":
        return back_to_menu(message)

    try:
        amount = int(message.text.replace(",", "").replace(".", ""))
        if amount < 25000:
            msg = bot.send_message(message.chat.id, "⚠️ المبلغ يجب أن يكون 25,000 ل.س أو أكثر.\nأدخل المبلغ من جديد:", reply_markup=back_button())
            return bot.register_next_step_handler(msg, process_withdraw_amount, account_name, method)
    except:
        msg = bot.send_message(message.chat.id, "⚠️ رجاءً أدخل المبلغ بشكل صحيح:", reply_markup=back_button())
        return bot.register_next_step_handler(msg, process_withdraw_amount, account_name, method)

    msg = bot.send_message(message.chat.id, "📲 أرسل رقم/كود محفظتك:", reply_markup=back_button())
    bot.register_next_step_handler(msg, confirm_withdraw, account_name, amount, method)

def confirm_withdraw(message, account_name, amount, method):
    if message.text == "🔙 رجوع للقائمة الرئيسية":
        return back_to_menu(message)

    wallet = message.text
    bot.send_message(
        ADMIN_ID,
        f"📥 طلب سحب:\nطريقة السحب: {method}\nاسم الحساب: {account_name}\nالمبلغ: {amount}\nرقم/كود المحفظة: {wallet}\nمن المستخدم: {message.from_user.id}"
    )
    bot.send_message(message.chat.id, "✅ تم استلام طلب السحب.\nطلبك قيد المعالجة، عند الانتهاء سنرسل لك تأكيد العملية.", reply_markup=main_menu())

# ====== رد الادمن ======
@bot.message_handler(commands=['reply'])
def reply_user(message):
    try:
        parts = message.text.split(" ", 2)
        user_id = int(parts[1])
        reply_text = parts[2]
        bot.send_message(user_id, f"{reply_text}")
        bot.send_message(message.chat.id, "✅ تم إرسال الرد.")
    except:
        bot.send_message(message.chat.id, "⚠️ الصيغة غير صحيحة.\nاكتب: /reply user_id الرسالة")

# ====== Webhook مع Render ======
@server.route('/' + TOKEN, methods=['POST'])
def getMessage():
    json_str = request.get_data().decode('UTF-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "!", 200

@server.route("/")
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url="https://telegram-bot-xsto.onrender.com/" + TOKEN)
    return "!", 200

if __name__ == "__main__":
    server.run(host="0.0.0.0", port=10000)
