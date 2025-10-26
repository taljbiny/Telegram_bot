import telebot
from telebot import types
from flask import Flask, request

# ====== الإعدادات ======
TOKEN = "8317743306:AAFGH1Acxb6fIwZ0o0T2RvNjezQFW8KWcw8"
ADMIN_ID = 7625893170
SYRIATEL_CODE = "82492253"
SHAM_CODE = "131efe4fbccd83a811282761222eee69"
RENDER_URL = "https://www.55bets.net/#/casino/"

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# ====== تخزين بيانات المستخدم مؤقت ======
user_accounts = {}
pending_deletes = {}
pending_deposits = {}
pending_withdraws = {}

# ====== واجهة البداية + ترحيب + رابط الموقع ======
@bot.message_handler(commands=['start'])
def start(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("🆕 إنشاء حساب", callback_data="create_account"),
        types.InlineKeyboardButton("💰 إيداع", callback_data="deposit"),
        types.InlineKeyboardButton("💸 سحب", callback_data="withdraw"),
        types.InlineKeyboardButton("🗑️ حذف الحساب", callback_data="delete_account")
    )
    welcome_text = (
        "👋 أهلاً بك في نظام 55BETS!\n\n"
        f"📌 الموقع الرسمي: [55BETS]({RENDER_URL})\n"
        "اختر إحدى الخيارات التالية للبدء:"
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=markup, parse_mode="Markdown")

# ====== إنشاء حساب ======
@bot.callback_query_handler(func=lambda call: call.data == "create_account")
def create_account(call):
    bot.send_message(call.message.chat.id, "📝 أرسل اسم الحساب الذي تريد تسجيله:")
    bot.register_next_step_handler(call.message, process_account_name)

def process_account_name(message):
    user_accounts[message.chat.id] = message.text
    bot.send_message(message.chat.id, f"✅ تم إرسال طلب إنشاء الحساب.\nفي انتظار موافقة الأدمن.")
    bot.send_message(ADMIN_ID, f"📩 طلب إنشاء حساب جديد:\n👤 المستخدم: {message.chat.id}\n📛 الاسم: {message.text}")

# ====== إيداع ======
@bot.callback_query_handler(func=lambda call: call.data == "deposit")
def deposit(call):
    bot.send_message(call.message.chat.id, "💳 أرسل اسم الحساب الذي تريد الإيداع له:")
    bot.register_next_step_handler(call.message, process_deposit_account)

def process_deposit_account(message):
    account = message.text
    bot.send_message(message.chat.id, "💰 أرسل المبلغ الذي تريد إيداعه:")
    bot.register_next_step_handler(message, lambda m: process_deposit_amount(m, account))

def process_deposit_amount(message, account):
    amount = message.text
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("سيرياتيل كاش", callback_data=f"deposit_syriatel_{account}_{amount}"),
        types.InlineKeyboardButton("شام كاش", callback_data=f"deposit_sham_{account}_{amount}")
    )
    bot.send_message(message.chat.id, "اختر طريقة الدفع:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("deposit_syriatel_") or call.data.startswith("deposit_sham_"))
def deposit_method(call):
    parts = call.data.split("_")
    method = parts[1]
    account = parts[2]
    amount = parts[3]

    if method == "syriatel":
        code = SYRIATEL_CODE
        method_name = "سيرياتيل كاش"
    else:
        code = SHAM_CODE
        method_name = "شام كاش"

    bot.send_message(call.message.chat.id, f"📱 كود محفظة {method_name}:\n`{code}`", parse_mode="Markdown")
    bot.send_message(call.message.chat.id, "📸 أرسل صورة تأكيد الدفع.")
    bot.register_next_step_handler(call.message, lambda m: confirm_deposit_image(m, account, amount, method_name))

def confirm_deposit_image(message, account, amount, method_name):
    if not message.photo:
        bot.send_message(message.chat.id, "❌ يرجى إرسال صورة تأكيد الدفع فقط.")
        return
    file_id = message.photo[-1].file_id
    pending_deposits[message.chat.id] = {"account": account, "amount": amount, "method": method_name, "file_id": file_id}
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("✅ تأكيد الإيداع", callback_data=f"approve_deposit_{message.chat.id}"),
        types.InlineKeyboardButton("❌ رفض الإيداع", callback_data=f"reject_deposit_{message.chat.id}")
    )
    bot.send_photo(ADMIN_ID, file_id, caption=f"💳 طلب إيداع جديد:\n👤 المستخدم: {message.chat.id}\n📛 الحساب: {account}\n💰 المبلغ: {amount}\n💼 الطريقة: {method_name}", reply_markup=markup)
    bot.send_message(message.chat.id, "📩 تم إرسال طلب الإيداع للإدارة، يرجى الانتظار ريثما يتم التحقق.")

# ====== سحب ======
@bot.callback_query_handler(func=lambda call: call.data == "withdraw")
def withdraw(call):
    bot.send_message(call.message.chat.id, "💸 أرسل المبلغ الذي تريد سحبه:")
    bot.register_next_step_handler(call.message, process_withdraw_amount)

def process_withdraw_amount(message):
    amount = message.text
    bot.send_message(message.chat.id, "📱 أرسل رقم محفظتك (سيرياتيل كاش):")
    bot.register_next_step_handler(message, lambda m: process_withdraw_wallet(m, amount))

def process_withdraw_wallet(message, amount):
    wallet = message.text
    pending_withdraws[message.chat.id] = {"amount": amount, "wallet": wallet}
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("✅ تأكيد السحب", callback_data=f"approve_withdraw_{message.chat.id}"),
        types.InlineKeyboardButton("❌ رفض السحب", callback_data=f"reject_withdraw_{message.chat.id}")
    )
    bot.send_message(ADMIN_ID, f"💸 طلب سحب جديد:\n👤 المستخدم: {message.chat.id}\n💰 المبلغ: {amount}\n📱 المحفظة: {wallet}", reply_markup=markup)
    bot.send_message(message.chat.id, "📩 تم إرسال طلب السحب للإدارة.\n⏳ طلبك قيد المراجعة.")

# ====== حذف الحساب ======
@bot.callback_query_handler(func=lambda call: call.data == "delete_account")
def delete_account(call):
    bot.send_message(call.message.chat.id, "⚠️ هل أنت متأكد من رغبتك بحذف حسابك؟ سيتم إرسال طلب للإدارة للموافقة.")
    pending_deletes[call.message.chat.id] = True
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("✅ تأكيد الحذف", callback_data=f"request_delete_{call.message.chat.id}"),
        types.InlineKeyboardButton("❌ إلغاء", callback_data="cancel_delete")
    )
    bot.send_message(call.message.chat.id, "اختر:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("request_delete_"))
def request_delete(call):
    user_id = int(call.data.split("_")[2])
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("✅ قبول الحذف", callback_data=f"approve_delete_{user_id}"),
        types.InlineKeyboardButton("❌ رفض الحذف", callback_data=f"reject_delete_{user_id}")
    )
    bot.send_message(ADMIN_ID, f"🗑️ طلب حذف حساب من المستخدم {user_id}", reply_markup=markup)
    bot.send_message(user_id, "📩 تم إرسال طلب حذف حسابك للإدارة، يرجى الانتظار.")

@bot.callback_query_handler(func=lambda call: call.data == "cancel_delete")
def cancel_delete(call):
    bot.send_message(call.message.chat.id, "❎ تم إلغاء عملية الحذف.")

# ====== موافقات ورفض من الأدمن ======
@bot.callback_query_handler(func=lambda call: call.data.startswith(("approve_", "reject_")))
def handle_admin_actions(call):
    data = call.data.split("_")
    action = data[0]
    action_type = data[1]
    user_id = int(data[2])

    if action_type == "deposit":
        if action == "approve":
            bot.send_message(user_id, "✅ تمت الموافقة على عملية الإيداع الخاصة بك، وتم إضافة الرصيد.")
        else:
            bot.send_message(user_id, "❌ تم رفض عملية الإيداع الخاصة بك.")
    elif action_type == "withdraw":
        if action == "approve":
            bot.send_message(user_id, "✅ تمت الموافقة على عملية السحب الخاصة بك.")
        else:
            bot.send_message(user_id, "❌ تم رفض عملية السحب الخاصة بك.")
    elif action_type == "delete":
        if action == "approve":
            user_accounts.pop(user_id, None)
            bot.send_message(user_id, "🗑️ تمت الموافقة على حذف حسابك.\nيمكنك الآن إنشاء حساب جديد من خلال /start.")
        else:
            bot.send_message(user_id, "❌ تم رفض طلب حذف الحساب من قبل الإدارة.")

    bot.answer_callback_query(call.id, "تم تنفيذ الإجراء ✅")

# ====== رد الأدمن على المستخدم ======
@bot.message_handler(func=lambda message: str(message.chat.id) == str(ADMIN_ID) and message.reply_to_message)
def admin_reply(message):
    try:
        target_text = message.reply_to_message.text
        user_id = int(target_text.split("المستخدم: ")[1].split("\n")[0])
        bot.send_message(user_id, f"📩 رسالة من الإدارة:\n{message.text}")
    except Exception:
        bot.send_message(ADMIN_ID, "⚠️ لم أتمكن من تحديد المستخدم بشكل صحيح.")

# ====== Flask Webhook ======
@app.route('/' + TOKEN, methods=['POST'])
def webhook():
    json_str = request.stream.read().decode('utf-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return '', 200

@app.route('/')
def index():
    bot.remove_webhook()
    bot.set_webhook(url=RENDER_URL + '/' + TOKEN)
    return "Webhook Set!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
