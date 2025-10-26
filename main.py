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

# ====== حفظ وقراءة البيانات ======
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

# ====== القائمة الرئيسية مع زر إنشاء حساب ======
def main_menu(chat_id, include_create=False):
    markup = types.InlineKeyboardMarkup()
    # أزرار الإيداع والسحب
    markup.add(
        types.InlineKeyboardButton("💳 شحن الحساب", callback_data="deposit"),
        types.InlineKeyboardButton("💸 سحب", callback_data="withdraw")
    )
    # زر إنشاء حساب إذا اخترنا تضمينه
    if include_create:
        markup.add(types.InlineKeyboardButton("🆕 إنشاء حساب", callback_data="create_account"))
    # أزرار الحذف والدعم
    markup.add(
        types.InlineKeyboardButton("🗑️ حذف الحساب", callback_data="delete_account"),
        types.InlineKeyboardButton("📞 الدعم", callback_data="support")
    )
    return markup

def check_min_amount(amount):
    try:
        return int(amount) >= MIN_AMOUNT
    except:
        return False

# ====== /start ======
@bot.message_handler(commands=['start'])
def start(message):
    data = load_data()
    user_id = str(message.chat.id)
    if user_id in data["user_accounts"]:
        markup = main_menu(message.chat.id)
        bot.send_message(message.chat.id, f"👤 لديك حساب مسجل مسبقاً باسم: {data['user_accounts'][user_id]}\nاختر العملية من الأزرار أدناه:", reply_markup=markup)
    else:
        markup = main_menu(message.chat.id, include_create=True)
        text = f"👋 أهلاً بك في نظام [55BETS]({RENDER_URL})!\nاختر العملية من الأزرار أدناه:"
        bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode="Markdown")

# ====== تسجيل حساب جديد ======
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

# ====== زر إنشاء حساب ======
@bot.callback_query_handler(func=lambda call: call.data == "create_account")
def create_account(call):
    ask_account_name(call.message)

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
    bot.send_photo(ADMIN_ID, file_id, caption=f"💳 طلب شحن جديد:\n👤 المستخدم: {message.chat.id}\n📛 الحساب: {account}\n💰 المبلغ: {amount}\n💼 الطريقة: {method_name}\n\nيمكنك الرد على هذه الرسالة مباشرة لإرسال الرد التلقائي أو أي نص آخر للمستخدم.")
    bot.send_message(message.chat.id, "📩 تم إرسال طلب الشحن للإدارة، يرجى الانتظار ريثما يتم التحقق.", reply_markup=main_menu(message.chat.id))

# ====== سحب الحساب ======
@bot.callback_query_handler(func=lambda call: call.data.startswith("withdraw"))
def withdraw_method(call):
    data = load_data()
    user_id = str(call.message.chat.id)
    if user_id not in data["user_accounts"]:
        ask_account_name(call.message)
        return
    parts = call.data.split("_")
    if len(parts) == 1:
        bot.send_message(call.message.chat.id, f"💰 أدخل المبلغ للسحب (الحد الأدنى {MIN_AMOUNT}):")
        bot.register_next_step_handler(call.message, withdraw_amount_step)
    elif len(parts) == 3:
        method = parts[1]
        amount = parts[2]
        method_name = "سيرياتيل كاش" if method == "syriatel" else "شام كاش"
        bot.send_message(call.message.chat.id, f"📩 تم إرسال طلب السحب للإدارة.\n💰 المبلغ: {amount}\n💼 الطريقة: {method_name}")
        data["pending_withdraws"][user_id] = {"amount": amount, "method": method_name, "account": data["user_accounts"][user_id]}
        save_data(data)
        bot.send_message(ADMIN_ID, f"💸 طلب سحب جديد:\n👤 المستخدم: {user_id}\n📛 الحساب: {data['user_accounts'][user_id]}\n💰 المبلغ: {amount}\n💼 الطريقة: {method_name}\n\nيمكنك الرد على هذه الرسالة مباشرة لإرسال الرد التلقائي أو أي نص آخر للمستخدم.")

def withdraw_amount_step(message):
    amount = message.text
    if not check_min_amount(amount):
        bot.send_message(message.chat.id, f"❌ الحد الأدنى للسحب هو {MIN_AMOUNT}.\n💰 يرجى إدخال مبلغ صحيح:")
        bot.register_next_step_handler(message, withdraw_amount_step)
        return
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("سيرياتيل كاش", callback_data=f"withdraw_syriatel_{amount}"),
        types.InlineKeyboardButton("شام كاش", callback_data=f"withdraw_sham_{amount}")
    )
    bot.send_message(message.chat.id, "💳 اختر طريقة السحب:", reply_markup=markup)

# ====== حذف الحساب ======
@bot.callback_query_handler(func=lambda call: call.data == "delete_account")
def delete_account(call):
    user_id = str(call.message.chat.id)
    data = load_data()
    if user_id not in data["user_accounts"]:
        bot.send_message(call.message.chat.id, "❌ لا يوجد لديك حساب مسجل.", reply_markup=main_menu(call.message.chat.id))
        return
    data["pending_deletes"][user_id] = {"account": data["user_accounts"][user_id]}
    save_data(data)
    bot.send_message(ADMIN_ID, f"🗑️ طلب حذف الحساب:\n👤 المستخدم: {user_id}\n📛 الحساب: {data['user_accounts'][user_id]}\n\nيمكنك الرد على هذه الرسالة مباشرة لإرسال الرد التلقائي أو أي نص آخر للمستخدم.")
    bot.send_message(call.message.chat.id, "📩 تم إرسال طلب حذف الحساب للإدارة، يرجى الانتظار.", reply_markup=main_menu(call.message.chat.id))

# ====== الدعم ======
@bot.callback_query_handler(func=lambda call: call.data == "support")
def support(call):
    bot.send_message(call.message.chat.id, "📩 اكتب رسالتك للدعم، وسيتم إرسالها مباشرة للإدمن:")
    bot.register_next_step_handler(call.message, send_support_message)

def send_support_message(message):
    bot.send_message(ADMIN_ID, f"📩 رسالة من المستخدم {message.chat.id}:\n{message.text}")
    bot.send_message(message.chat.id, "✅ تم إرسال رسالتك إلى الدعم. ستتلقى الرد قريبًا.", reply_markup=main_menu(message.chat.id))

# ====== رد الإدمن يصل للمستخدم مع تنبيهات تلقائية ======
@bot.message_handler(func=lambda message: str(message.chat.id) == str(ADMIN_ID) and message.reply_to_message)
def admin_reply(message):
    try:
        lines = message.reply_to_message.text.split("\n")
        user_line = next((l for l in lines if "المستخدم:" in l), None)
        if user_line:
            user_id = int(user_line.split("المستخدم:")[1].strip())
            response_text = message.text.strip().lower()
            # تنبيهات تلقائية
            auto_response = None
            if "قبول" in response_text:
                if "شحن" in message.reply_to_message.text or "deposit" in message.reply_to_message.text:
                    auto_response = "✅ تم شحن حسابك بنجاح."
                elif "سحب" in message.reply_to_message.text or "withdraw" in message.reply_to_message.text:
                    auto_response = "✅ تم تنفيذ طلب السحب الخاص بك."
                elif "حذف" in message.reply_to_message.text or "delete" in message.reply_to_message.text:
                    auto_response = "✅ تم حذف حسابك بنجاح."
            elif "رفض" in response_text:
                if "شحن" in message.reply_to_message.text or "deposit" in message.reply_to_message.text:
                    auto_response = "❌ لم يتم شحن حسابك، يرجى التواصل مع الدعم."
                elif "سحب" in message.reply_to_message.text or "withdraw" in message.reply_to_message.text:
                    auto_response = "❌ لم يتم تنفيذ طلب السحب، يرجى التواصل مع الدعم."
                elif "حذف" in message.reply_to_message.text or "delete" in message.reply_to_message.text:
                    auto_response = "❌ لم يتم حذف حسابك."
            # إذا موجود تنبيه تلقائي، أضفه مع نص الإدمن إذا كتب أي شيء
            if auto_response:
                final_text = f"{auto_response}\n\n📩 رسالة من الإدارة:\n{message.text}"
            else:
                final_text = f"📩 رسالة من الإدارة:\n{message.text}"
            bot.send_message(user_id, final_text, reply_markup=main_menu(user_id))
    except Exception as e:
        bot.send_message(ADMIN_ID, f"⚠️ لم أتمكن من إرسال الرد للمستخدم: {e}")

# ====== Webhook Flask ======
@app.route('/' + TOKEN, methods=['POST'])
def webhook():
    try:
        json_str = request.stream.read().decode('utf-8')
        update = telebot.types.Update.de_json(json_str)
        bot.process_new_updates([update])
    except Exception as e:
        print("Webhook error:", e)
    return '', 200

@app.route('/')
def index():
    bot.remove_webhook()
    bot.set_webhook(url=RENDER_URL + '/' + TOKEN)
    return "Webhook Set!"

if __name__ == "__main__":
    PORT = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=PORT)
