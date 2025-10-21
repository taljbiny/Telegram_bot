import telebot
from telebot import types
from flask import Flask, request

# ====== الإعدادات ======
TOKEN = "8317743306:AAFGH1Acxb6fIwZ0o0T2RvNjezQFW8KWcw8"
ADMIN_IDS = [7625893170, 1337514542]  # إدمنين معاً
bot = telebot.TeleBot(TOKEN)
server = Flask(__name__)

# ====== لوحة البداية ======
def main_menu():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🆕 إنشاء حساب", callback_data="create"))
    markup.add(types.InlineKeyboardButton("💰 إيداع", callback_data="deposit"))
    markup.add(types.InlineKeyboardButton("💵 سحب", callback_data="withdraw"))
    markup.add(types.InlineKeyboardButton("🧑‍💼 الاتصال بالدعم", callback_data="support"))
    return markup

def back_button_inline():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("⬅️ رجوع", callback_data="back_main"))
    return markup

# ====== /start ======
@bot.message_handler(commands=['start'])
def send_welcome(message):
    text = (
        "🎰 أهلاً وسهلاً بك في بوت **55BETS** الرسمي 💎\n\n"
        "من خلال هذا البوت يمكنك:\n"
        "- 🆕 إنشاء حساب جديد\n"
        "- 💰 إجراء عمليات الإيداع والسحب\n"
        "- 🧑‍💼 التواصل مع الدعم الفني مباشرة\n\n"
        "🌐 موقعنا الرسمي:\n"
        "https://www.55bets.net/casino/slots/240"
    )
    bot.send_message(message.chat.id, text, reply_markup=main_menu(), parse_mode="Markdown")

# ====== المتغيرات المؤقتة ======
user_states = {}

# ====== العودة للقائمة ======
@bot.callback_query_handler(func=lambda call: call.data == "back_main")
def back_main(call):
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text="✅ رجعت إلى القائمة الرئيسية.",
        reply_markup=main_menu()
    )
    user_states.pop(call.message.chat.id, None)

# ====== إنشاء حساب ======
@bot.callback_query_handler(func=lambda call: call.data == "create")
def create_account(call):
    msg = bot.send_message(call.message.chat.id, "📛 أرسل اسم الحساب الذي تريد إنشاءه:")
    bot.register_next_step_handler(msg, process_create)

def process_create(message):
    account_name = message.text
    text = f"🆕 طلب إنشاء حساب جديد:\n👤 الاسم: {account_name}\n🆔 المستخدم: {message.from_user.id}"
    send_to_admins(text, message.from_user.id)
    bot.send_message(message.chat.id, f"✅ تم استلام طلب إنشاء الحساب: **{account_name}**\nبانتظار تأكيد العملية.", parse_mode="Markdown", reply_markup=main_menu())

# ====== إيداع ======
@bot.callback_query_handler(func=lambda call: call.data == "deposit")
def deposit(call):
    msg = bot.send_message(call.message.chat.id, "📛 أرسل اسم حسابك على موقع 55BETS:")
    bot.register_next_step_handler(msg, process_deposit_name)

def process_deposit_name(message):
    account = message.text
    msg = bot.send_message(message.chat.id, "💵 أرسل المبلغ الذي تريد إيداعه (الحد الأدنى 25,000 ل.س):")
    bot.register_next_step_handler(msg, process_deposit_amount, account)

def process_deposit_amount(message, account):
    try:
        amount = int(message.text.replace(",", "").replace(".", ""))
        if amount < 25000:
            msg = bot.send_message(message.chat.id, "⚠️ الحد الأدنى هو 25,000 ل.س. أرسل المبلغ مجدداً:")
            return bot.register_next_step_handler(msg, process_deposit_amount, account)
    except:
        msg = bot.send_message(message.chat.id, "⚠️ أدخل المبلغ بشكل صحيح:")
        return bot.register_next_step_handler(msg, process_deposit_amount, account)

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📲 سيرياتيل كاش", callback_data=f"deposit_syriatel|{account}|{amount}"))
    markup.add(types.InlineKeyboardButton("🏦 شام كاش", callback_data=f"deposit_sham|{account}|{amount}"))
    markup.add(types.InlineKeyboardButton("⬅️ رجوع", callback_data="back_main"))
    bot.send_message(message.chat.id, "💳 اختر طريقة الدفع:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("deposit_"))
def deposit_method(call):
    method, account, amount = call.data.split("|")

    if method == "deposit_syriatel":
        text = (
            "💳 أرسل المبلغ إلى رقم المحفظة التالية:\n"
            "📱 **82492253** (سيرياتيل كاش)\n\n"
            "بعد الدفع، أرسل **صورة تأكيد الدفع** تحتوي على المبلغ ورقم العملية 📸"
        )
    elif method == "deposit_sham":
        text = (
            "💳 أرسل المبلغ إلى محفظة شام كاش التالية:\n"
            "🏦 **131efe4fbccd83a811282761222eee69**\n\n"
            "بعد الدفع، أرسل **صورة تأكيد الدفع** تحتوي على المبلغ ورقم العملية 📸"
        )
    else:
        return

    msg = bot.send_message(call.message.chat.id, text, parse_mode="Markdown")
    bot.register_next_step_handler(msg, process_deposit_photo, account, amount, method)

def process_deposit_photo(message, account, amount, method):
    if not message.photo:
        msg = bot.send_message(message.chat.id, "⚠️ أرسل صورة تأكيد الدفع:")
        return bot.register_next_step_handler(msg, process_deposit_photo, account, amount, method)

    caption = (
        f"💰 طلب إيداع جديد:\n"
        f"👤 الحساب: {account}\n"
        f"💵 المبلغ: {amount} ل.س\n"
        f"💳 الطريقة: {'سيرياتيل كاش' if 'syriatel' in method else 'شام كاش'}\n"
        f"🆔 المستخدم: {message.from_user.id}"
    )
    send_to_admins(caption, message.from_user.id, message.photo[-1].file_id)
    bot.send_message(message.chat.id, "✅ تم استلام طلب الإيداع.\nسيتم تأكيد العملية قريباً.", reply_markup=main_menu())

# ====== سحب ======
@bot.callback_query_handler(func=lambda call: call.data == "withdraw")
def withdraw(call):
    msg = bot.send_message(call.message.chat.id, "📛 أرسل اسم حسابك على موقع 55BETS:")
    bot.register_next_step_handler(msg, process_withdraw_name)

def process_withdraw_name(message):
    account = message.text
    msg = bot.send_message(message.chat.id, "💵 أرسل المبلغ الذي تريد سحبه (الحد الأدنى 25,000 ل.س):")
    bot.register_next_step_handler(msg, process_withdraw_amount, account)

def process_withdraw_amount(message, account):
    try:
        amount = int(message.text.replace(",", "").replace(".", ""))
        if amount < 25000:
            msg = bot.send_message(message.chat.id, "⚠️ المبلغ يجب أن يكون 25,000 ل.س أو أكثر. أعد الإرسال:")
            return bot.register_next_step_handler(msg, process_withdraw_amount, account)
    except:
        msg = bot.send_message(message.chat.id, "⚠️ أدخل المبلغ بشكل صحيح:")
        return bot.register_next_step_handler(msg, process_withdraw_amount, account)

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📲 سيرياتيل كاش", callback_data=f"withdraw_syriatel|{account}|{amount}"))
    markup.add(types.InlineKeyboardButton("🏦 شام كاش", callback_data=f"withdraw_sham|{account}|{amount}"))
    markup.add(types.InlineKeyboardButton("⬅️ رجوع", callback_data="back_main"))
    bot.send_message(message.chat.id, "💳 اختر طريقة السحب:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("withdraw_"))
def withdraw_method(call):
    method, account, amount = call.data.split("|")
    msg = bot.send_message(call.message.chat.id, "📲 أرسل رقم أو كود محفظتك:")
    bot.register_next_step_handler(msg, process_withdraw_wallet, account, amount, method)

def process_withdraw_wallet(message, account, amount, method):
    wallet = message.text
    caption = (
        f"📤 طلب سحب جديد:\n"
        f"👤 الحساب: {account}\n"
        f"💵 المبلغ: {amount} ل.س\n"
        f"💳 الطريقة: {'سيرياتيل كاش' if 'syriatel' in method else 'شام كاش'}\n"
        f"📲 محفظة المستخدم: {wallet}\n"
        f"🆔 المستخدم: {message.from_user.id}"
    )
    send_to_admins(caption, message.from_user.id)
    bot.send_message(message.chat.id, "✅ تم استلام طلب السحب.\nطلبك قيد المعالجة، سيتم تأكيد العملية قريباً.", reply_markup=main_menu())

# ====== الدعم ======
@bot.callback_query_handler(func=lambda call: call.data == "support")
def support(call):
    msg = bot.send_message(call.message.chat.id, "💬 الرجاء شرح مشكلتك بالتفصيل ليتم الرد عليك بأقرب وقت:")
    bot.register_next_step_handler(msg, process_support)

def process_support(message):
    text = f"🆘 طلب دعم فني من المستخدم {message.from_user.id}:\n\n{message.text}"
    send_to_admins(text, message.from_user.id)
    bot.send_message(message.chat.id, "✅ تم إرسال رسالتك للدعم، الرجاء الانتظار.", reply_markup=main_menu())

# ====== إرسال الرسائل للأدمن مع زر الرد ======
def send_to_admins(text, user_id, photo_id=None):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📩 الرد على المستخدم", callback_data=f"reply|{user_id}"))
    for admin_id in ADMIN_IDS:
        if photo_id:
            bot.send_photo(admin_id, photo_id, caption=text, reply_markup=markup)
        else:
            bot.send_message(admin_id, text, reply_markup=markup)

# ====== رد الأدمن ======
@bot.callback_query_handler(func=lambda call: call.data.startswith("reply|"))
def reply_to_user(call):
    user_id = int(call.data.split("|")[1])
    msg = bot.send_message(call.message.chat.id, "✍️ أرسل الآن الرد ليصل للمستخدم:")
    bot.register_next_step_handler(msg, send_admin_reply, user_id, call.from_user.id)

def send_admin_reply(message, user_id, admin_id):
    bot.send_message(user_id, f"💬 رد من الدعم:\n{message.text}")
    bot.send_message(admin_id, "✅ تم إرسال الرد بنجاح.")
    for other_admin in ADMIN_IDS:
        if other_admin != admin_id:
            bot.send_message(other_admin, f"ℹ️ قام الإدمن الآخر بالرد على المستخدم ({user_id}):\n💬 {message.text}")

# ====== Webhook مع Render ======
@server.route('/' + TOKEN, methods=['POST'])
def getMessage():
    update = telebot.types.Update.de_json(request.data.decode('UTF-8'))
    bot.process_new_updates([update])
    return "!", 200

@server.route('/')
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url="https://telegram-bot-xsto.onrender.com/" + TOKEN)
    return "!", 200

if __name__ == "__main__":
    server.run(host="0.0.0.0", port=10000)
