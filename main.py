import telebot
from telebot import types
from flask import Flask, request

# ===== إعدادات البوت =====
TOKEN = "8317743306:AAFGH1Acxb6fIwZ0o0T2RvNjezQFW8KWcw8"
ADMIN_ID = 7625893170
bot = telebot.TeleBot(TOKEN)
server = Flask(__name__)

# ===== تخزين جلسات المستخدم =====
user_sessions = {}
reply_sessions = {}  # لتخزين جلسات الرد للأدمن

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

# ===== بدء البوت =====
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "👋 أهلاً بك في بوت موقع 55Bets\nاختر من الأزرار التالية:", reply_markup=main_menu_inline())

# ===== التعامل مع الأزرار =====
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    chat_id = call.message.chat.id
    data = call.data

    if data == "create_account":
        msg = bot.send_message(chat_id, "📝 أرسل اسم الحساب الذي ترغب بإنشائه:", reply_markup=back_markup())
        bot.register_next_step_handler(msg, process_account_creation)

    elif data == "deposit":
        msg = bot.send_message(chat_id, "💬 أرسل اسم حسابك للإيداع:", reply_markup=back_markup())
        bot.register_next_step_handler(msg, deposit_step_account)

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
            bot.register_next_step_handler(msg, withdraw_step_account, method)

    elif data.startswith("pay_"):
        method = data.split("_")[1]
        chat_id = call.message.chat.id
        session = user_sessions.get(chat_id)
        if not session:
            bot.send_message(chat_id, "⚠️ حدث خطأ، الرجاء إعادة العملية.", reply_markup=main_menu_inline())
            return
        session["payment_method"] = method
        if method == "syriatel":
            bot.send_message(chat_id, "💳 أرسل المبلغ إلى رقم سيرياتيل كاش 82492253\nثم أرسل صورة التأكيد:", reply_markup=back_markup())
        elif method == "sham":
            bot.send_message(chat_id, "💳 أرسل المبلغ إلى كود شام كاش 131efe4fbccd83a811282761222eee69\nثم أرسل صورة التأكيد:", reply_markup=back_markup())
        bot.register_next_step_handler_by_chat_id(chat_id, deposit_step_confirm)

    elif data == "support":
        msg = bot.send_message(chat_id, "📩 اشرح مشكلتك بالتفصيل، وسيتم الرد عليك من الإدارة:", reply_markup=back_markup())
        bot.register_next_step_handler(msg, process_support_message)

    elif data == "back_main":
        bot.send_message(chat_id, "رجعت للقائمة الرئيسية ✅", reply_markup=main_menu_inline())

    elif data.startswith("reply|"):
        handle_reply_button(call)

# ===== إنشاء حساب =====
def process_account_creation(message):
    chat_id = message.chat.id
    if message.text.strip() == "🔙 رجوع":
        bot.send_message(chat_id, "رجعت للقائمة الرئيسية ✅", reply_markup=main_menu_inline())
        return
    username = message.text.strip()
    bot.send_message(chat_id, f"✅ تم استلام طلب إنشاء الحساب: {username}\nبانتظار رد الإدارة.", reply_markup=main_menu_inline())
    send_to_admin(f"📥 طلب إنشاء حساب:\nاسم الحساب: {username}\nمن المستخدم: {chat_id}", chat_id)

# ===== الإيداع كامل الخطوات =====
def deposit_step_account(message):
    chat_id = message.chat.id
    if message.text.strip() == "🔙 رجوع":
        bot.send_message(chat_id, "رجعت للقائمة الرئيسية ✅", reply_markup=main_menu_inline())
        return
    account_name = message.text.strip()
    user_sessions[chat_id] = {"account_name": account_name}
    msg = bot.send_message(chat_id, "💵 أدخل المبلغ (أقل 25,000 ل.س):", reply_markup=back_markup())
    bot.register_next_step_handler(msg, deposit_step_amount)

def deposit_step_amount(message):
    chat_id = message.chat.id
    if message.text.strip() == "🔙 رجوع":
        user_sessions.pop(chat_id, None)
        bot.send_message(chat_id, "رجعت للقائمة الرئيسية ✅", reply_markup=main_menu_inline())
        return
    try:
        amount = int(message.text.replace(",", "").replace(".", ""))
        if amount < 25000:
            msg = bot.send_message(chat_id, "⚠️ الحد الأدنى 25,000 ل.س، أعد الإدخال:", reply_markup=back_markup())
            bot.register_next_step_handler(msg, deposit_step_amount)
            return
    except:
        msg = bot.send_message(chat_id, "⚠️ أدخل المبلغ بشكل صحيح:", reply_markup=back_markup())
        bot.register_next_step_handler(msg, deposit_step_amount)
        return
    user_sessions[chat_id]["amount"] = amount
    # خيارات الدفع
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📱 سيرياتيل كاش", callback_data="pay_syriatel"))
    markup.add(types.InlineKeyboardButton("💳 شام كاش", callback_data="pay_sham"))
    bot.send_message(chat_id, "اختر طريقة الدفع:", reply_markup=markup)

def deposit_step_confirm(message):
    chat_id = message.chat.id
    session = user_sessions.get(chat_id)
    if not session:
        bot.send_message(chat_id, "⚠️ حدث خطأ، الرجاء إعادة العملية.", reply_markup=main_menu_inline())
        return
    if message.text == "🔙 رجوع":
        user_sessions.pop(chat_id, None)
        bot.send_message(chat_id, "رجعت للقائمة الرئيسية ✅", reply_markup=main_menu_inline())
        return
    if message.content_type != "photo":
        msg = bot.send_message(chat_id, "⚠️ الرجاء إرسال صورة تأكيد الدفع:", reply_markup=back_markup())
        bot.register_next_step_handler(msg, deposit_step_confirm)
        return
    # إرسال التفاصيل للأدمن بعد إكمال جميع الخطوات
    send_to_admin(f"📥 عملية إيداع:\nاسم الحساب: {session['account_name']}\nالمبلغ: {session['amount']}\nالطريقة: {session['payment_method']}\nمن المستخدم: {chat_id}", chat_id)
    bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption="📸 صورة تأكيد الدفع")
    bot.send_message(chat_id, "✅ تم استلام عملية الإيداع، طلبك قيد المعالجة.", reply_markup=main_menu_inline())
    user_sessions.pop(chat_id, None)

# ===== السحب كامل الخطوات =====
def withdraw_step_account(message, method):
    chat_id = message.chat.id
    if message.text.strip() == "🔙 رجوع":
        bot.send_message(chat_id, "رجعت للقائمة الرئيسية ✅", reply_markup=main_menu_inline())
        return
    account_name = message.text.strip()
    user_sessions[chat_id] = {"account_name": account_name, "method": method}
    msg = bot.send_message(chat_id, "💵 أدخل المبلغ المطلوب (أقل 25,000 ل.س):", reply_markup=back_markup())
    bot.register_next_step_handler(msg, withdraw_step_amount)

def withdraw_step_amount(message):
    chat_id = message.chat.id
    if message.text.strip() == "🔙 رجوع":
        user_sessions.pop(chat_id, None)
        bot.send_message(chat_id, "رجعت للقائمة الرئيسية ✅", reply_markup=main_menu_inline())
        return
    try:
        amount = int(message.text.replace(",", "").replace(".", ""))
        if amount < 25000:
            msg = bot.send_message(chat_id, "⚠️ الحد الأدنى 25,000 ل.س، أعد الإدخال:", reply_markup=back_markup())
            bot.register_next_step_handler(msg, withdraw_step_amount)
            return
    except:
        msg = bot.send_message(chat_id, "⚠️ أدخل المبلغ بشكل صحيح:", reply_markup=back_markup())
        bot.register_next_step_handler(msg, withdraw_step_amount)
        return
    session = user_sessions.get(chat_id)
    if not session:
        bot.send_message(chat_id, "⚠️ حدث خطأ، الرجاء إعادة العملية.", reply_markup=main_menu_inline())
        return
    session["amount"] = amount
    send_to_admin(f"📥 طلب سحب:\nطريقة: {session['method']}\nاسم الحساب: {session['account_name']}\nالمبلغ: {amount}\nمن المستخدم: {chat_id}", chat_id)
    bot.send_message(chat_id, "✅ تم استلام طلب السحب، طلبك قيد المعالجة.", reply_markup=main_menu_inline())
    user_sessions.pop(chat_id, None)

# ===== دعم المستخدم =====
def process_support_message(message):
    chat_id = message.chat.id
    if message.text.strip() == "🔙 رجوع":
        bot.send_message(chat_id, "رجعت للقائمة الرئيسية ✅", reply_markup=main_menu_inline())
        return
    text = message.text.strip()
    bot.send_message(chat_id, "✅ تم استلام رسالتك، سنقوم بالرد عليك قريباً.", reply_markup=main_menu_inline())
    send_to_admin(f"📩 رسالة دعم من المستخدم {chat_id}:\n{text}", chat_id)

# ===== زر الرد للأدمن =====
def handle_reply_button(call):
    user_id = int(call.data.split("|")[1])
    reply_sessions[call.from_user.id] = user_id
    msg = bot.send_message(call.from_user.id, f"📩 اكتب الرد للمستخدم {user_id}:")
    bot.register_next_step_handler(msg, process_admin_reply)

def process_admin_reply(message):
    admin_id = message.chat.id
    if admin_id not in reply_sessions:
        bot.send_message(admin_id, "⚠️ لم يتم تحديد مستخدم للرد.")
        return
    user_id = reply_sessions.pop(admin_id)
    bot.send_message(user_id, f"💬 رسالة من الإدارة:\n{message.text}")
    bot.send_message(admin_id, "✅ تم إرسال الرد بنجاح.")

# ===== إرسال الرسائل للأدمن مع زر الرد =====
def send_to_admin(text, user_id):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📩 الرد على المستخدم", callback_data=f"reply|{user_id}"))
    bot.send_message(ADMIN_ID, text, reply_markup=markup)

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
