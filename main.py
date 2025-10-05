import telebot
from telebot import types
from flask import Flask, request

# ===== إعدادات البوت =====
TOKEN = "8317743306:AAFGH1Acxb6fIwZ0o0T2RvNjezQFW8KWcw8"
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

# ===== بداية البوت =====
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

# ===== بقية العمليات والسحب والدعم كما في النسخة النهائية =====
# ... (يمكن إضافة باقي الدوال هنا بنفس الصياغة)

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
