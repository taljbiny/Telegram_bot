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
        msg = bot.send_message(chat_id, "📩 الرجاء شرح المشكلة بالتفصيل، وسيتم الرد عليك من الدعم بأقرب وقت ممكن:", reply_markup=back_markup())
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
    bot.send_message(chat_id, f"✅ تم استلام طلب إنشاء الحساب: {username}\nبانتظار رد الإدارة.", reply_markup=main_menu_inline())

    # إرسال رسالة للأدمن مع زر الرد
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📩 الرد على المستخدم", callback_data=f"reply|{chat_id}"))
    bot.send_message(ADMIN_ID, f"📥 طلب إنشاء حساب جديد:\nاسم الحساب: {username}\nمن المستخدم: {chat_id}", reply_markup=markup)

# ===== الإيداع =====
def process_deposit_account(message):
    chat_id = message.chat.id
    if message.text.strip() == "🔙 رجوع":
        bot.send_message(chat_id, "رجعت للقائمة الرئيسية ✅", reply_markup=main_menu_inline())
        return
    account_name = message.text.strip()
    user_sessions[chat_id] = {"account_name": account_name}
    msg = bot.send_message(chat_id, "💵 أدخل المبلغ (أقل عملية 25,000 ل.س):", reply_markup=back_markup())
    bot.register_next_step_handler(msg, process_deposit_amount)

def process_deposit_amount(message):
    chat_id = message.chat.id
    if message.text.strip() == "🔙 رجوع":
        user_sessions.pop(chat_id, None)
        bot.send_message(chat_id, "رجعت للقائمة الرئيسية ✅", reply_markup=main_menu_inline())
        return
    try:
        amount = int(message.text.replace(",", "").replace(".", ""))
        if amount < 25000:
            msg = bot.send_message(chat_id, "⚠️ الحد الأدنى 25,000 ل.س، أعد الإدخال:", reply_markup=back_markup())
            bot.register_next_step_handler(msg, process_deposit_amount)
            return
    except:
        msg = bot.send_message(chat_id, "⚠️ أدخل المبلغ بشكل صحيح:", reply_markup=back_markup())
        bot.register_next_step_handler(msg, process_deposit_amount)
        return

    user_sessions[chat_id]["amount"] = amount
    # خيارات الدفع
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📱 سيرياتيل كاش", callback_data="pay_syriatel"))
    markup.add(types.InlineKeyboardButton("💳 شام كاش", callback_data="pay_sham"))
    bot.send_message(chat_id, "اختر طريقة الدفع:", reply_markup=markup)

    # رسالة للأدمن مع زر الرد
    markup_admin = types.InlineKeyboardMarkup()
    markup_admin.add(types.InlineKeyboardButton("📩 الرد على المستخدم", callback_data=f"reply|{chat_id}"))
    bot.send_message(ADMIN_ID, f"📥 طلب إيداع:\nاسم الحساب: {user_sessions[chat_id]['account_name']}\nالمبلغ: {amount}\nمن المستخدم: {chat_id}", reply_markup=markup_admin)

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

# ===== زر الرد من الأدمن =====
@bot.callback_query_handler(func=lambda call: call.data.startswith("reply|"))
def reply_user(call):
    user_id = int(call.data.split("|")[1])
    msg = bot.send_message(call.from_user.id, f"📩 اكتب الرد الذي تريد إرساله للمستخدم {user_id}:")
    bot.register_next_step_handler(msg, send_reply_to_user, user_id)

def send_reply_to_user(message, user_id):
    bot.send_message(user_id, f"💬 رسالة من الإدارة:\n{message.text}")
    bot.send_message(message.chat.id, "✅ تم إرسال الرد بنجاح.")

if __name__ == "__main__":
    server.run(host="0.0.0.0", port=10000)
