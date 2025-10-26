import telebot
from telebot import types
from flask import Flask, request
import json
import os

# ====== الإعدادات ======
TOKEN = "8317743306:AAFGH1Acxb6fIwZ0o0T2RvNjezQFW8KWcw8"
ADMIN_ID = 7625893170
SYRIATEL_CODE = "82492253"
SHAM_CODE = "131efe4fbccd83a811282761222eee69"
RENDER_URL = "https://telegram-bot-xsto.onrender.com"
DATA_FILE = "data.json"
MIN_AMOUNT = 25000

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# ====== دوال حفظ وقراءة البيانات ======
def load_data():
    if not os.path.exists(DATA_FILE) or os.path.getsize(DATA_FILE) == 0:
        return {"user_accounts": {}, "pending_deposits": {}, "pending_withdraws": {}, "pending_deletes": {}}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {"user_accounts": {}, "pending_deposits": {}, "pending_withdraws": {}, "pending_deletes": {}}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def main_menu(chat_id):
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("💳 شحن الحساب", callback_data="deposit"),
        types.InlineKeyboardButton("💸 سحب", callback_data="withdraw")
    )
    markup.add(
        types.InlineKeyboardButton("🗑️ حذف الحساب", callback_data="delete_account"),
        types.InlineKeyboardButton("📞 الدعم", url="tel:+123456789")  # ضع رقم الدعم هنا
    )
    return markup

def check_min_amount(amount):
    try:
        return int(amount) >= MIN_AMOUNT
    except:
        return False

# ====== Start + ترحيب + رابط الموقع ======
@bot.message_handler(commands=['start'])
def start(message):
    data = load_data()
    user_id = str(message.chat.id)
    markup = main_menu(message.chat.id)
    if user_id in data["user_accounts"]:
        bot.send_message(message.chat.id, f"👤 لديك حساب مسجل مسبقاً باسم: {data['user_accounts'][user_id]}\nاختر العملية من الأزرار أدناه:", reply_markup=markup)
    else:
        text = f"👋 أهلاً بك في نظام 55BETS!\n📌 الموقع الرسمي: [55BETS](https://www.55bets.net/#/casino/)\nاختر العملية من الأزرار أدناه:"
        bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode="Markdown")

# ====== إنشاء حساب تلقائي إذا مستخدم قديم ======
def ask_account_name(message):
    bot.send_message(message.chat.id, "📝 أرسل اسم الحساب الذي تريد تسجيله:")
    bot.register_next_step_handler(message, process_account_name)

def process_account_name(message):
    data = load_data()
    user_id = str(message.chat.id)
    data["user_accounts"][user_id] = message.text
    save_data(data)
    bot.send_message(message.chat.id, f"✅ تم تسجيل الحساب باسم: {message.text}", reply_markup=main_menu(message.chat.id))
    bot.send_message(ADMIN_ID, f"📩 طلب إنشاء حساب جديد:\n👤 المستخدم: {user_id}\n📛 الاسم: {message.text}")

# ====== شحن الحساب ======
@bot.callback_query_handler(func=lambda call: call.data == "deposit")
def deposit(call):
    data = load_data()
    user_id = str(call.message.chat.id)
    if user_id not in data["user_accounts"]:
        ask_account_name(call.message)
        return
    bot.send_message(call.message.chat.id, f"💰 أدخل المبلغ لشحن الحساب (الحد الأدنى {MIN_AMOUNT}):")
    bot.register_next_step_handler(call.message, deposit_amount_step)

def deposit_amount_step(message):
    amount = message.text
    if not check_min_amount(amount):
        bot.send_message(message.chat.id, f"❌ الحد الأدنى للشحن هو {MIN_AMOUNT}.\n💰 يرجى إدخال مبلغ صحيح:")
        bot.register_next_step_handler(message, deposit_amount_step)
        return
    user_id = str(message.chat.id)
    data = load_data()
    account = data["user_accounts"][user_id]
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("سيرياتيل كاش", callback_data=f"deposit_syriatel_{amount}"),
        types.InlineKeyboardButton("شام كاش", callback_data=f"deposit_sham_{amount}")
    )
    bot.send_message(message.chat.id, f"💳 سيتم شحن الحساب: {account}\nاختر طريقة الدفع:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("deposit_"))
def deposit_method(call):
    parts = call.data.split("_")
    method = parts[1]
    amount = parts[2]
    user_id = str(call.message.chat.id)
    data = load_data()
    account = data["user_accounts"][user_id]
    method_name = "سيرياتيل كاش" if method == "syriatel" else "شام كاش"
    code = SYRIATEL_CODE if method == "syriatel" else SHAM_CODE
    bot.send_message(call.message.chat.id, f"📱 كود محفظة {method_name}: `{code}`\n📸 أرسل صورة تأكيد الدفع.", parse_mode="Markdown")
    bot.register_next_step_handler(call.message, lambda m: confirm_deposit_image(m, account, amount, method_name))

def confirm_deposit_image(message, account, amount, method_name):
    if not message.photo:
        bot.send_message(message.chat.id, "❌ يرجى إرسال صورة تأكيد الدفع فقط.")
        bot.register_next_step_handler(message, lambda m: confirm_deposit_image(m, account, amount, method_name))
        return
    file_id = message.photo[-1].file_id
    data = load_data()
    data["pending_deposits"][str(message.chat.id)] = {"account": account, "amount": amount, "method": method_name, "file_id": file_id}
    save_data(data)
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("✅ تأكيد الشحن", callback_data=f"approve_deposit_{message.chat.id}"),
        types.InlineKeyboardButton("❌ رفض الشحن", callback_data=f"reject_deposit_{message.chat.id}")
    )
    bot.send_photo(ADMIN_ID, file_id, caption=f"💳 طلب شحن جديد:\n👤 المستخدم: {message.chat.id}\n📛 الحساب: {account}\n💰 المبلغ: {amount}\n💼 الطريقة: {method_name}", reply_markup=markup)
    bot.send_message(message.chat.id, "📩 تم إرسال طلب الشحن للإدارة، يرجى الانتظار ريثما يتم التحقق.", reply_markup=main_menu(message.chat.id))

# ====== سحب الحساب ======
@bot.callback_query_handler(func=lambda call: call.data == "withdraw")
def withdraw(call):
    data = load_data()
    user_id = str(call.message.chat.id)
    if user_id not in data["user_accounts"]:
        ask_account_name(call.message)
        return
    bot.send_message(call.message.chat.id, f"💰 أدخل المبلغ للسحب (الحد الأدنى {MIN_AMOUNT}):")
    bot.register_next_step_handler(call.message, withdraw_amount_step)

def withdraw_amount_step(message):
    amount = message.text
    if not check_min_amount(amount):
        bot.send_message(message.chat.id, f"❌ الحد الأدنى للسحب هو {MIN_AMOUNT}.\n💰 يرجى إدخال مبلغ صحيح:")
        bot.register_next_step_handler(message, withdraw_amount_step)
        return
    bot.send_message(message.chat.id, "💳 اختر طريقة السحب:")
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("سيرياتيل كاش", callback_data=f"withdraw_syriatel_{amount}"),
        types.InlineKeyboardButton("شام كاش", callback_data=f"withdraw_sham_{amount}")
    )
    bot.send_message(message.chat.id, "اختر الطريقة:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("withdraw_"))
def withdraw_method(call):
    parts = call.data.split("_")
    method = parts[1]
    amount = parts[2]
    user_id = str(call.message.chat.id)
    data = load_data()
    account = data["user_accounts"][user_id]
    bot.send_message(call.message.chat.id, f"📱 أرسل رقم محفظتك ({'سيرياتيل كاش' if method=='syriatel' else 'شام كاش'}) للحساب: {account}")
    bot.register_next_step_handler(call.message, lambda m: confirm_withdraw(m, amount, method, account))

def confirm_withdraw(message, amount, method, account):
    wallet = message.text
    data = load_data()
    data["pending_withdraws"][str(message.chat.id)] = {"amount": amount, "wallet": wallet, "account": account, "method": method}
    save_data(data)
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("✅ تأكيد السحب", callback_data=f"approve_withdraw_{message.chat.id}"),
        types.InlineKeyboardButton("❌ رفض السحب", callback_data=f"reject_withdraw_{message.chat.id}")
    )
    bot.send_message(ADMIN_ID, f"💸 طلب سحب جديد:\n👤 المستخدم: {message.chat.id}\n📛 الحساب: {account}\n💰 المبلغ: {amount}\n📱 المحفظة: {wallet}", reply_markup=markup)
    bot.send_message(message.chat.id, "📩 تم إرسال طلب السحب للإدارة.\n⏳ طلبك قيد المراجعة.", reply_markup=main_menu(message.chat.id))

# ====== حذف الحساب ======
@bot.callback_query_handler(func=lambda call: call.data == "delete_account")
def delete_account(call):
    bot.send_message(call.message.chat.id, "⚠️ هل أنت متأكد من رغبتك بحذف حسابك؟ سيتم إرسال طلب للإدارة للموافقة.")
    data = load_data()
    data["pending_deletes"][str(call.message.chat.id)] = True
    save_data(data)
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("✅ تأكيد الحذف", callback_data=f"request_delete_{call.message.chat.id}"),
        types.InlineKeyboardButton("❌ إلغاء", callback_data="cancel_delete")
    )
    bot.send_message(call.message.chat.id, "اختر:", reply_markup=markup)

# ====== متابعة موافقات الأدمن ======
@bot.callback_query_handler(func=lambda call: call.data.startswith(("approve_", "reject_", "request_delete_")))
def handle_admin_actions(call):
    data_file = load_data()
    parts = call.data.split("_")
    action = parts[0]
    action_type = parts[1]
    user_id = int(parts[2])
    if action_type == "deposit":
        if action == "approve":
            bot.send_message(user_id, "✅ تمت الموافقة على شحن حسابك.")
            if str(user_id) in data_file["pending_deposits"]:
                del data_file["pending_deposits"][str(user_id)]
        else:
            bot.send_message(user_id, "❌ تم رفض شحن حسابك.")
            if str(user_id) in data_file["pending_deposits"]:
                del data_file["pending_deposits"][str(user_id)]
    elif action_type == "withdraw":
        if action == "approve":
            bot.send_message(user_id, "✅ تمت الموافقة على السحب الخاص بك.")
            if str(user_id) in data_file["pending_withdraws"]:
                del data_file["pending_withdraws"][str(user_id)]
        else:
            bot.send_message(user_id, "❌ تم رفض السحب الخاص بك.")
            if str(user_id) in data_file["pending_withdraws"]:
                del data_file["pending_withdraws"][str(user_id)]
    elif action_type == "delete":
        if action == "approve":
            if str(user_id) in data_file["user_accounts"]:
                del data_file["user_accounts"][str(user_id)]
            bot.send_message(user_id, "🗑️ تمت الموافقة على حذف حسابك.\nيمكنك الآن إنشاء حساب جديد من خلال /start.")
        else:
            bot.send_message(user_id, "❌ تم رفض طلب حذف الحساب من قبل الإدارة.")
        if str(user_id) in data_file["pending_deletes"]:
            del data_file["pending_deletes"][str(user_id)]
    save_data(data_file)
    bot.answer_callback_query(call.id, "تم تنفيذ الإجراء ✅")

# ====== رد الأدمن ======
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
    PORT = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=PORT)
