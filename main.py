import telebot
from telebot import types
from flask import Flask, request

# ===== إعدادات البوت =====
TOKEN = "ضع_توكن_البوت_هنا"
ADMIN_ID = 7625893170
bot = telebot.TeleBot(TOKEN)
server = Flask(__name__)

# ===== تخزين الجلسات =====
user_sessions = {}

# ===== القوائم الرئيسية =====
def main_menu_inline():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🆕 إنشاء حساب", callback_data="create_account"))
    markup.add(types.InlineKeyboardButton("💰 إيداع", callback_data="deposit"))
    markup.add(types.InlineKeyboardButton("💵 سحب", callback_data="withdraw"))
    markup.add(types.InlineKeyboardButton("☎️ الاتصال بالدعم", callback_data="support"))
    return markup

def back_markup():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🔙 رجوع")
    return markup

# ===== أوامر البداية =====
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "👋 أهلاً بك في بوت موقع 55Bets\nاختر من الأزرار التالية:", reply_markup=main_menu_inline())

# ===== التعامل مع الأزرار =====
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    data = call.data
    chat_id = call.message.chat.id

    if data == "create_account":
        msg = bot.send_message(chat_id, "📝 أرسل اسم الحساب الذي ترغب بإنشائه:", reply_markup=back_markup())
        bot.register_next_step_handler(msg, process_account_creation)
    elif data == "deposit":
        msg = bot.send_message(chat_id, "💬 أرسل اسم حسابك:", reply_markup=back_markup())
        bot.register_next_step_handler(msg, process_deposit_account)
    elif data == "withdraw":
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📱 سيرياتيل كاش", callback_data="withdraw_syriatel"))
        markup.add(types.InlineKeyboardButton("💳 شام كاش", callback_data="withdraw_sham"))
        markup.add(types.InlineKeyboardButton("🏦 حوالة (متوقف)", callback_data="withdraw_off"))
        markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="back_main"))
        bot.send_message(chat_id, "اختر طريقة السحب:", reply_markup=markup)
    elif data.startswith("withdraw_"):
        method = data.split("_")[1]
        if method == "off":
            bot.send_message(chat_id, "❌ هذه الطريقة متوقفة حالياً.", reply_markup=main_menu_inline())
        else:
            msg = bot.send_message(chat_id, f"💬 أرسل اسم الحساب للسحب عبر {method.capitalize()} كاش:", reply_markup=back_markup())
            bot.register_next_step_handler(msg, process_withdraw_account, method)
    elif data == "support":
        msg = bot.send_message(chat_id, "📩 الرجاء شرح المشكلة بالتفصيل وسنقوم بالرد عليك في أقرب وقت ممكن:", reply_markup=back_markup())
        bot.register_next_step_handler(msg, process_support_message)
    elif data == "back_main":
        bot.send_message(chat_id, "رجعت للقائمة الرئيسية ✅", reply_markup=main_menu_inline())

# ===== إنشاء حساب =====
def process_account_creation(message):
    chat_id = message.chat.id
    if message.text.strip() == "🔙 رجوع":
        bot.send_message(chat_id, "رجعت للقائمة الرئيسية ✅", reply_markup=main_menu_inline())
        return

    username = message.text.strip()
    bot.send_message(chat_id, f"✅ تم إنشاء حسابك:\nUsername: {username}", reply_markup=main_menu_inline())
    bot.send_message(ADMIN_ID, f"📩 طلب إنشاء حساب جديد:\nاسم الحساب: {username}\nمن المستخدم: {message.from_user.id}",
                     reply_markup=reply_user_button(message.from_user.id))

# ===== الإيداع =====
def process_deposit_account(message):
    chat_id = message.chat.id
    if message.text.strip() == "🔙 رجوع":
        bot.send_message(chat_id, "رجعت للقائمة الرئيسية ✅", reply_markup=main_menu_inline())
        return

    account_name = message.text.strip()
    user_sessions[chat_id] = {"account_name": account_name}
    msg = bot.send_message(chat_id, "💵 أرسل المبلغ الذي ترغب بإيداعه (أقل عملية 25,000 ل.س):", reply_markup=back_markup())
    bot.register_next_step_handler(msg, process_deposit_amount)

def process_deposit_amount(message):
    chat_id = message.chat.id
    if message.text.strip() == "🔙 رجوع":
        bot.send_message(chat_id, "رجعت للقائمة الرئيسية ✅", reply_markup=main_menu_inline())
        user_sessions.pop(chat_id, None)
        return

    try:
        amount = int(message.text.replace(",", "").replace(".", "").strip())
        if amount < 25000:
            msg = bot.send_message(chat_id, "⚠️ الحد الأدنى 25,000 ل.س، أعد الإدخال:", reply_markup=back_markup())
            bot.register_next_step_handler(msg, process_deposit_amount)
            return
    except:
        msg = bot.send_message(chat_id, "⚠️ أدخل المبلغ بشكل صحيح:", reply_markup=back_markup())
        bot.register_next_step_handler(msg, process_deposit_amount)
        return

    user_sessions[chat_id]["amount"] = amount
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📱 سيرياتيل كاش", callback_data="pay_syriatel"))
    markup.add(types.InlineKeyboardButton("💳 شام كاش", callback_data="pay_sham"))
    bot.send_message(chat_id, "اختر طريقة الدفع:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("pay_"))
def process_payment(call):
    chat_id = call.message.chat.id
    method = call.data.split("_")[1]
    sess = user_sessions.get(chat_id)
    if not sess:
        bot.send_message(chat_id, "⚠️ انتهت الجلسة. ابدأ من جديد.", reply_markup=main_menu_inline())
        return

    if method == "sham":
        code = "131efe4fbccd83a811282761222eee69"
        bot.send_message(chat_id, f"💳 كود شام كاش للدفع:\n`{code}`", parse_mode="Markdown")
    elif method == "syriatel":
        bot.send_message(chat_id, "💳 كود سيرياتيل كاش للدفع:\n`سيتم تزويده لاحقاً`", parse_mode="Markdown")

    msg = bot.send_message(chat_id, "📷 أرسل صورة تأكيد عملية الدفع:", reply_markup=back_markup())
    bot.register_next_step_handler(msg, process_payment_proof, method)

def process_payment_proof(message, method):
    chat_id = message.chat.id
    sess = user_sessions.pop(chat_id, None)
    if not sess:
        bot.send_message(chat_id, "⚠️ انتهت الجلسة. ابدأ من جديد.", reply_markup=main_menu_inline())
        return
    if message.text and message.text.strip() == "🔙 رجوع":
        bot.send_message(chat_id, "رجعت للقائمة الرئيسية ✅", reply_markup=main_menu_inline())
        return

    if message.content_type == "photo":
        bot.send_photo(ADMIN_ID, message.photo[-1].file_id,
            caption=f"💰 طلب إيداع:\nاسم الحساب: {sess['account_name']}\nالمبلغ: {sess['amount']}\nطريقة الدفع: {method}\nمن المستخدم: {message.from_user.id}",
            reply_markup=reply_user_button(message.from_user.id))
        bot.send_message(chat_id, "✅ تم استلام عملية الإيداع.\nطلبك قيد المعالجة.", reply_markup=main_menu_inline())
    else:
        bot.send_message(chat_id, "⚠️ يجب إرسال صورة تأكيد الدفع.", reply_markup=main_menu_inline())

# ===== السحب =====
def process_withdraw_account(message, method):
    chat_id = message.chat.id
    if message.text.strip() == "🔙 رجوع":
        bot.send_message(chat_id, "رجعت للقائمة الرئيسية ✅", reply_markup=main_menu_inline())
        return
    account_name = message.text.strip()
    user_sessions[chat_id] = {"account_name": account_name, "method": method}
    msg = bot.send_message(chat_id, "💵 أرسل المبلغ المطلوب (أقل عملية 25,000 ل.س):", reply_markup=back_markup())
    bot.register_next_step_handler(msg, process_withdraw_amount)

def process_withdraw_amount(message):
    chat_id = message.chat.id
    sess = user_sessions.get(chat_id)
    if not sess:
        bot.send_message(chat_id, "⚠️ انتهت الجلسة. ابدأ من جديد.", reply_markup=main_menu_inline())
        return
    if message.text.strip() == "🔙 رجوع":
        bot.send_message(chat_id, "رجعت للقائمة الرئيسية ✅", reply_markup=main_menu_inline())
        user_sessions.pop(chat_id, None)
        return

    try:
        amount = int(message.text.replace(",", "").replace(".", "").strip())
        if amount < 25000:
            msg = bot.send_message(chat_id, "⚠️ المبلغ يجب أن يكون 25,000 ل.س أو أكثر.\nأعد إدخاله:", reply_markup=back_markup())
            bot.register_next_step_handler(msg, process_withdraw_amount)
            return
    except:
        msg = bot.send_message(chat_id, "⚠️ أدخل المبلغ بشكل صحيح:", reply_markup=back_markup())
        bot.register_next_step_handler(msg, process_withdraw_amount)
        return

    sess["amount"] = amount
    msg = bot.send_message(chat_id, "📲 أرسل رقم/كود المحفظة المراد استلام المبلغ عليها:", reply_markup=back_markup())
    bot.register_next_step_handler(msg, confirm_withdraw)

def confirm_withdraw(message):
    chat_id = message.chat.id
    sess = user_sessions.pop(chat_id, None)
    if not sess:
        bot.send_message(chat_id, "⚠️ انتهت الجلسة. ابدأ من جديد.", reply_markup=main_menu_inline())
        return
    if message.text.strip() == "🔙 رجوع":
        bot.send_message(chat_id, "رجعت للقائمة الرئيسية ✅", reply_markup=main_menu_inline())
        return

    wallet = message.text.strip()
    bot.send_message(ADMIN_ID,
        f"📥 طلب سحب:\nطريقة السحب: {sess['method']}\nاسم الحساب: {sess['account_name']}\nالمبلغ: {sess['amount']}\nكود المحفظة: {wallet}\nمن المستخدم: {message.from_user.id}",
        reply_markup=reply_user_button(message.from_user.id))
    bot.send_message(chat_id, "✅ تم استلام طلب السحب.\nطلبك قيد المعالجة، سنرسل تأكيداً عند الانتهاء.", reply_markup=main_menu_inline())

# ===== الدعم =====
def process_support_message(message):
    chat_id = message.chat.id
    if message.text.strip() == "🔙 رجوع":
        bot.send_message(chat_id, "رجعت للقائمة الرئيسية ✅", reply_markup=main_menu_inline())
        return

    if message.content_type == "photo":
        bot.send_photo(ADMIN_ID, message.photo[-1].file_id,
            caption=f"📥 رسالة دعم من المستخدم {message.from_user.id}",
            reply_markup=reply_user_button(message.from_user.id, support=True))
    else:
        bot.send_message(ADMIN_ID, f"📥 رسالة دعم من المستخدم {message.from_user.id}:\n{message.text}",
                         reply_markup=reply_user_button(message.from_user.id, support=True))
    bot.send_message(chat_id, "✅ تم إرسال رسالتك للدعم، سيتم الرد عليك قريباً.", reply_markup=main_menu_inline())

# ===== زر الرد على المستخدم =====
def reply_user_button(user_id, support=False):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📩 الرد على المستخدم", callback_data=f"reply|{user_id}|{'support' if support else 'other'}"))
    return markup

@bot.callback_query_handler(func=lambda call: call.data.startswith("reply|"))
def handle_admin_reply(call):
    _, user_id, mode = call.data.split("|")
    user_id = int(user_id)
    is_support = (mode == "support")

    bot.answer_callback_query(call.id)
    msg = bot.send_message(call.message.chat.id, f"✍️ أرسل الرد ليتم إرساله للمستخدم {user_id}:")
    bot.register_next_step_handler(msg, lambda m: send_admin_reply(m, user_id, is_support))

def send_admin_reply(message, user_id, is_support):
    try:
        text = message.text
        if is_support:
            text = f"💬 **رد من الدعم الفني:**\n{text}"
        else:
            text = f"📩 **رد من الإدارة:**\n{text}"

        bot.send_message(user_id, text, parse_mode="Markdown")
        bot.send_message(message.chat.id, "✅ تم إرسال الرد للمستخدم بنجاح.")
    except Exception as e:
        bot.send_message(message.chat.id, f"⚠️ خطأ أثناء الإرسال:\n{e}")

# ===== Webhook =====
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
