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
SITE_LINK = "https://www.55bets.net/#/casino/"
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

# ====== القوائم ======
def main_menu(chat_id, include_create=False):
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("💳 شحن الحساب", callback_data="deposit"),
        types.InlineKeyboardButton("💸 سحب", callback_data="withdraw")
    )
    if include_create:
        markup.add(types.InlineKeyboardButton("🆕 إنشاء حساب", callback_data="create_account"))
    markup.add(
        types.InlineKeyboardButton("🗑️ حذف الحساب", callback_data="delete_account"),
        types.InlineKeyboardButton("📞 الدعم", callback_data="support")
    )
    return markup

def back_to_menu():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="main_menu"))
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
        bot.send_message(message.chat.id, f"👤 لديك حساب مسجل مسبقاً.\nاختر العملية من الأزرار أدناه:", reply_markup=markup)
    else:
        markup = main_menu(message.chat.id, include_create=True)
        text = f"👋 أهلاً بك في نظام [55BETS]({SITE_LINK})!\nاختر العملية من الأزرار أدناه:"
        bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode="Markdown")

# ====== إنشاء حساب ======
def ask_account_info(message):
    msg = bot.send_message(message.chat.id, "📝 أرسل اسم الحساب وكلمة السر بصيغة:\nUsername: اسم الحساب\nPassword: كلمة السر", reply_markup=back_to_menu())
    bot.register_next_step_handler(msg, process_account_info)

def process_account_info(message):
    if message.text.lower() == "🔙 القائمة الرئيسية":
        bot.send_message(message.chat.id, "🔙 عدت للقائمة الرئيسية.", reply_markup=main_menu(message.chat.id))
        return
    data = load_data()
    user_id = str(message.chat.id)
    if user_id in data["user_accounts"]:
        bot.send_message(message.chat.id, "❌ لديك حساب مسبق، احذف الحساب القديم أولاً.", reply_markup=main_menu(message.chat.id))
        return
    # إرسال طلب للإدمن
    bot.send_message(ADMIN_ID, f"📩 طلب إنشاء حساب جديد:\n👤 المستخدم: {user_id}\n{message.text}", reply_markup=admin_controls(user_id))

@bot.callback_query_handler(func=lambda call: call.data == "create_account")
def create_account(call):
    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
    data = load_data()
    user_id = str(call.message.chat.id)
    if user_id in data["user_accounts"]:
        bot.answer_callback_query(call.id, "❌ لديك حساب مسبق، احذف الحساب القديم أولاً.")
        return
    ask_account_info(call.message)

# ====== شحن / سحب / حذف / دعم ======
# سيتم التعامل معهم بنفس طريقة إنشاء الحساب مع ارسال طلب للإدمن وزر التحكم الثلاثي
# على سبيل المثال، شحن الحساب:
@bot.callback_query_handler(func=lambda call: call.data.startswith("deposit"))
def deposit_handler(call):
    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
    data = load_data()
    user_id = str(call.message.chat.id)
    if user_id not in data["user_accounts"]:
        ask_account_info(call.message)
        return
    msg = bot.send_message(call.message.chat.id, f"💰 أدخل المبلغ لشحن الحساب (الحد الأدنى {MIN_AMOUNT}):", reply_markup=back_to_menu())
    bot.register_next_step_handler(msg, deposit_amount_step)

def deposit_amount_step(message):
    if message.text.lower() == "🔙 القائمة الرئيسية":
        bot.send_message(message.chat.id, "🔙 عدت للقائمة الرئيسية.", reply_markup=main_menu(message.chat.id))
        return
    amount = message.text
    if not check_min_amount(amount):
        msg = bot.send_message(message.chat.id, f"❌ الحد الأدنى للشحن هو {MIN_AMOUNT}.\n💰 أدخل مبلغ صحيح:", reply_markup=back_to_menu())
        bot.register_next_step_handler(msg, deposit_amount_step)
        return
    user_id = str(message.chat.id)
    data = load_data()
    account = data["user_accounts"][user_id]
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("سيرياتيل كاش", callback_data=f"deposit_syriatel_{amount}"),
        types.InlineKeyboardButton("شام كاش", callback_data=f"deposit_sham_{amount}")
    )
    bot.send_message(message.chat.id, "💳 اختر طريقة الدفع:", reply_markup=markup)

# ====== لوحة تحكم الإدمن ======
def admin_controls(user_id):
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("✅ قبول", callback_data=f"admin_accept_{user_id}"),
        types.InlineKeyboardButton("❌ رفض", callback_data=f"admin_reject_{user_id}"),
        types.InlineKeyboardButton("💬 رد يدوي", callback_data=f"admin_manual_{user_id}")
    )
    return markup

@bot.callback_query_handler(func=lambda call: call.data.startswith("admin_"))
def admin_action(call):
    parts = call.data.split("_")
    action = parts[1]
    user_id = parts[2]
    bot.edit_message_reply_markup(ADMIN_ID, call.message.message_id, reply_markup=None)
    if action == "manual":
        msg = bot.send_message(ADMIN_ID, f"📝 اكتب الرد للمستخدم {user_id}:")
        bot.register_next_step_handler(msg, lambda m: send_manual_reply(m, user_id))
    elif action == "accept":
        # حفظ الحساب إذا كان إنشاء
        msg_text = call.message.text
        if "Username:" in msg_text and "Password:" in msg_text:
            lines = msg_text.split("\n")
            username = lines[1].replace("Username:","").strip() if "Username:" in lines[1] else lines[1].strip()
            password = lines[2].replace("Password:","").strip() if "Password:" in lines[2] else lines[2].strip()
            data = load_data()
            data["user_accounts"][user_id] = {"username": username, "password": password}
            save_data(data)
            bot.send_message(int(user_id), f"✅ تم إنشاء حسابك بنجاح!\nUsername: {username}\nPassword: {password}", reply_markup=main_menu(user_id))
        else:
            bot.send_message(int(user_id), "✅ تم قبول طلبك.", reply_markup=main_menu(user_id))
    elif action == "reject":
        bot.send_message(int(user_id), "❌ تم رفض طلبك.", reply_markup=main_menu(user_id))

def send_manual_reply(message, user_id):
    bot.send_message(int(user_id), f"📩 رسالة من الإدارة:\n{message.text}", reply_markup=main_menu(user_id))
    bot.send_message(ADMIN_ID, "✅ تم إرسال الرد للمستخدم.")

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
