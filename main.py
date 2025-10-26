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

# ====== المتغيرات المؤقتة ======
pending_accounts = {}        # { user_id: {"user_text": "..."} } طلبات الإنشاء المرسلة من المستخدم
pending_deposits = {}        # { user_id: {account, amount, method, file_id} }
pending_withdraws = {}       # { user_id: {amount, method, wallet} }
pending_deletes = {}         # { user_id: {account} }

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

def admin_controls(user_id):
    """أزرار تظهر للإدمن مع user_id داخل callback_data"""
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("✅ قبول", callback_data=f"admin_accept_{user_id}"),
        types.InlineKeyboardButton("❌ رفض", callback_data=f"admin_reject_{user_id}"),
        types.InlineKeyboardButton("💬 رد يدوي", callback_data=f"admin_manual_{user_id}")
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
        bot.send_message(message.chat.id, f"👤 لديك حساب مسجل مسبقاً.\nاختر العملية من الأزرار أدناه:", reply_markup=markup)
    else:
        markup = main_menu(message.chat.id, include_create=True)
        text = f"👋 أهلاً بك في نظام [55BETS]({SITE_LINK})!\nاختر العملية من الأزرار أدناه:"
        bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode="Markdown")

# ====== رجوع للقائمة (callback) ======
@bot.callback_query_handler(func=lambda call: call.data == "main_menu")
def show_main_menu(call):
    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
    data = load_data()
    user_id = str(call.message.chat.id)
    include_create = user_id not in data["user_accounts"]
    bot.send_message(call.message.chat.id, "🔙 القائمة الرئيسية:", reply_markup=main_menu(call.message.chat.id, include_create=include_create))

# ====== إنشاء الحساب ======
@bot.callback_query_handler(func=lambda call: call.data == "create_account")
def create_account(call):
    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
    data = load_data()
    user_id = str(call.message.chat.id)
    if user_id in data["user_accounts"]:
        bot.answer_callback_query(call.id, "❌ لديك حساب مسبق، احذف الحساب القديم أولاً.")
        return
    # نطلب من المستخدم Username و Password
    msg = bot.send_message(
        call.message.chat.id,
        "📝 أرسل اسم الحساب وكلمة السر بصيغة (سطرين):\nUsername: اسم الحساب\nPassword: كلمة السر",
        reply_markup=back_to_menu()
    )
    bot.register_next_step_handler(msg, process_account_info)

def process_account_info(message):
    # رجوع للقائمة عبر كولباك handled separately; هنا نتحقق من نص
    if message.text and message.text.strip().lower() == "🔙 القائمة الرئيسية":
        bot.send_message(message.chat.id, "🔙 عدت للقائمة الرئيسية.", reply_markup=main_menu(message.chat.id))
        return
    user_id = str(message.chat.id)
    text = message.text or ""
    lines = text.split("\n")
    username_line = next((l for l in lines if l.strip().startswith("Username:")), None)
    password_line = next((l for l in lines if l.strip().startswith("Password:")), None)
    if not username_line or not password_line:
        msg = bot.send_message(message.chat.id, "❌ الصيغة غير صحيحة. يجب أن تكون بصيغة:\nUsername: اسم\nPassword: كلمة", reply_markup=back_to_menu())
        bot.register_next_step_handler(msg, process_account_info)
        return
    # خزّن الطلب مؤقتًا (نخزن نص المستخدم لمرجعيته)
    pending_accounts[user_id] = {"user_text": text}
    # أرسل للإدمن مع أزرار التحكم (الإدمن سيضغط قبول ثم يرسل بيانات الحساب النهائي)
    bot.send_message(
        ADMIN_ID,
        f"📩 طلب إنشاء حساب جديد:\n👤 المستخدم: {user_id}\n\n{text}",
        reply_markup=admin_controls(user_id)
    )
    bot.send_message(message.chat.id, "⏳ تم إرسال طلب إنشاء الحساب للإدارة، يرجى الانتظار...", reply_markup=main_menu(user_id))

# ====== شحن الحساب ======
@bot.callback_query_handler(func=lambda call: call.data.startswith("deposit_") or call.data == "deposit")
def deposit_handler(call):
    # مسح أزرار الرسالة السابقة للمستخدم
    try:
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
    except:
        pass
    user_id = str(call.message.chat.id)
    data = load_data()
    if user_id not in data["user_accounts"]:
        bot.send_message(user_id, "❌ ليس لديك حساب، يرجى إنشاء حساب أولاً.", reply_markup=main_menu(user_id, include_create=True))
        return
    # ادخل المبلغ
    msg = bot.send_message(call.message.chat.id, f"💰 أدخل المبلغ لشحن الحساب (الحد الأدنى {MIN_AMOUNT}):", reply_markup=back_to_menu())
    bot.register_next_step_handler(msg, deposit_amount_step)

def deposit_amount_step(message):
    if message.text and message.text.strip().lower() == "🔙 القائمة الرئيسية":
        bot.send_message(message.chat.id, "🔙 عدت للقائمة الرئيسية.", reply_markup=main_menu(message.chat.id))
        return
    amount = message.text.strip()
    if not check_min_amount(amount):
        msg = bot.send_message(message.chat.id, f"❌ الحد الأدنى للشحن هو {MIN_AMOUNT}. أعد إدخال المبلغ:", reply_markup=back_to_menu())
        bot.register_next_step_handler(msg, deposit_amount_step)
        return
    user_id = str(message.chat.id)
    data = load_data()
    account = data["user_accounts"].get(user_id, user_id)
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("سيرياتيل كاش", callback_data=f"deposit_syriatel_{amount}"),
        types.InlineKeyboardButton("شام كاش", callback_data=f"deposit_sham_{amount}")
    )
    bot.send_message(message.chat.id, f"💳 سيتم شحن الحساب: {account}\nاختر طريقة الدفع:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("deposit_syriatel_") or call.data.startswith("deposit_sham_"))
def deposit_method_selected(call):
    try:
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
    except:
        pass
    parts = call.data.split("_")
    method = parts[1]   # syriatel or sham
    amount = parts[2]
    user_id = str(call.message.chat.id)
    method_name = "سيرياتيل كاش" if method == "syriatel" else "شام كاش"
    code = SYRIATEL_CODE if method == "syriatel" else SHAM_CODE
    bot.send_message(call.message.chat.id, f"📱 كود المحفظة لـ {method_name}: `{code}`\n📸 الآن أرسل صورة تأكيد الدفع.", parse_mode="Markdown")
    bot.register_next_step_handler(call.message, lambda m: confirm_deposit_image(m, amount, method_name))

def confirm_deposit_image(message, amount, method_name):
    if not message.photo:
        bot.send_message(message.chat.id, "❌ يرجى إرسال صورة تأكيد الدفع فقط.", reply_markup=main_menu(message.chat.id))
        return
    file_id = message.photo[-1].file_id
    user_id = str(message.chat.id)
    # حفظ طلب الشحن مؤقتًا
    pending_deposits[user_id] = {"amount": amount, "method": method_name, "file_id": file_id}
    # إرسال للادمن مع الصورة وأزرار التحكم
    bot.send_photo(
        ADMIN_ID,
        file_id,
        caption=f"💳 طلب شحن جديد:\n👤 المستخدم: {user_id}\n💰 المبلغ: {amount}\n💼 الطريقة: {method_name}",
        reply_markup=admin_controls(user_id)
    )
    bot.send_message(message.chat.id, "📩 تم إرسال طلب الشحن للإدارة، يرجى الانتظار.", reply_markup=main_menu(message.chat.id))

# ====== سحب الحساب ======
@bot.callback_query_handler(func=lambda call: call.data.startswith("withdraw_") or call.data == "withdraw")
def withdraw_handler(call):
    try:
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
    except:
        pass
    user_id = str(call.message.chat.id)
    data = load_data()
    if user_id not in data["user_accounts"]:
        bot.send_message(user_id, "❌ ليس لديك حساب، يرجى إنشاء حساب أولاً.", reply_markup=main_menu(user_id, include_create=True))
        return
    msg = bot.send_message(call.message.chat.id, f"💰 أدخل المبلغ للسحب (الحد الأدنى {MIN_AMOUNT}):", reply_markup=back_to_menu())
    bot.register_next_step_handler(msg, withdraw_amount_step)

def withdraw_amount_step(message):
    if message.text and message.text.strip().lower() == "🔙 القائمة الرئيسية":
        bot.send_message(message.chat.id, "🔙 عدت للقائمة الرئيسية.", reply_markup=main_menu(message.chat.id))
        return
    amount = message.text.strip()
    if not check_min_amount(amount):
        msg = bot.send_message(message.chat.id, f"❌ الحد الأدنى للسحب هو {MIN_AMOUNT}. أعد إدخال المبلغ:", reply_markup=back_to_menu())
        bot.register_next_step_handler(msg, withdraw_amount_step)
        return
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("سيرياتيل كاش", callback_data=f"withdraw_syriatel_{amount}"),
        types.InlineKeyboardButton("شام كاش", callback_data=f"withdraw_sham_{amount}")
    )
    bot.send_message(message.chat.id, "💳 اختر طريقة السحب:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("withdraw_syriatel_") or call.data.startswith("withdraw_sham_"))
def withdraw_method_selected(call):
    try:
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
    except:
        pass
    parts = call.data.split("_")
    method = parts[1]  # syriatel or sham
    amount = parts[2]
    user_id = str(call.message.chat.id)
    method_name = "سيرياتيل كاش" if method == "syriatel" else "شام كاش"
    # نطلب رقم/كود المحفظة
    msg = bot.send_message(call.message.chat.id, f"📩 أرسل رقم/كود المحفظة للطريقة {method_name}:", reply_markup=back_to_menu())
    bot.register_next_step_handler(msg, lambda m: confirm_withdraw_wallet(m, amount, method_name))

def confirm_withdraw_wallet(message, amount, method_name):
    if message.text and message.text.strip().lower() == "🔙 القائمة الرئيسية":
        bot.send_message(message.chat.id, "🔙 عدت للقائمة الرئيسية.", reply_markup=main_menu(message.chat.id))
        return
    wallet = message.text.strip()
    user_id = str(message.chat.id)
    pending_withdraws[user_id] = {"amount": amount, "method": method_name, "wallet": wallet}
    # إشعار للإدمن مع أزرار التحكم
    bot.send_message(
        ADMIN_ID,
        f"💸 طلب سحب جديد:\n👤 المستخدم: {user_id}\n💰 المبلغ: {amount}\n💼 الطريقة: {method_name}\n📥 المحفظة: {wallet}",
        reply_markup=admin_controls(user_id)
    )
    bot.send_message(message.chat.id, "📩 تم إرسال طلب السحب للإدارة، يرجى الانتظار.", reply_markup=main_menu(message.chat.id))

# ====== حذف الحساب ======
@bot.callback_query_handler(func=lambda call: call.data == "delete_account")
def delete_account(call):
    try:
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
    except:
        pass
    user_id = str(call.message.chat.id)
    data = load_data()
    if user_id not in data["user_accounts"]:
        bot.send_message(user_id, "❌ لا يوجد لديك حساب.", reply_markup=main_menu(user_id, include_create=True))
        return
    pending_deletes[user_id] = {"account": data["user_accounts"][user_id]}
    bot.send_message(ADMIN_ID, f"🗑️ طلب حذف الحساب:\n👤 المستخدم: {user_id}", reply_markup=admin_controls(user_id))
    bot.send_message(user_id, "📩 تم إرسال طلب حذف الحساب للإدارة، يرجى الانتظار.", reply_markup=main_menu(user_id))

# ====== الدعم ======
@bot.callback_query_handler(func=lambda call: call.data == "support")
def support_handler(call):
    try:
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
    except:
        pass
    msg = bot.send_message(call.message.chat.id, "📩 اكتب رسالتك للدعم:", reply_markup=back_to_menu())
    bot.register_next_step_handler(msg, send_support_message)

def send_support_message(message):
    if message.text and message.text.strip().lower() == "🔙 القائمة الرئيسية":
        bot.send_message(message.chat.id, "🔙 عدت للقائمة الرئيسية.", reply_markup=main_menu(message.chat.id))
        return
    user_id = str(message.chat.id)
    bot.send_message(ADMIN_ID, f"📩 رسالة من المستخدم {user_id}:\n{message.text}", reply_markup=admin_controls(user_id))
    bot.send_message(message.chat.id, "✅ تم إرسال رسالتك إلى الدعم. ستتلقى الرد قريبًا.", reply_markup=main_menu(message.chat.id))

# ====== لوحة تحكم الإدمن (callbacks) ======
@bot.callback_query_handler(func=lambda call: call.data.startswith("admin_"))
def admin_action(call):
    parts = call.data.split("_")
    action = parts[1]      # accept / reject / manual
    user_id = parts[2]

    # لا نحذف أزرار الإدمن - تبقى متاحة
    if action == "manual":
        msg = bot.send_message(ADMIN_ID, f"📝 اكتب الرد اليدوي الذي تريد إرساله للمستخدم {user_id}:")
        bot.register_next_step_handler(msg, lambda m: send_manual_reply(m, user_id))

    elif action == "accept":
        # عند الضغط قبول، نطلب من الادمن إرسال بيانات الحساب (Username & Password)
        msg = bot.send_message(ADMIN_ID, f"🆕 ارسل بيانات الحساب للمستخدم {user_id} بصيغة:\nUsername: اسم\nPassword: كلمة\n\n(يمكنك ترك Password فارغة وسيتم وضع ********)")
        bot.register_next_step_handler(msg, lambda m: save_new_account_from_admin(m, user_id))

    elif action == "reject":
        try:
            bot.send_message(int(user_id), "❌ تم رفض طلبك من قبل الإدارة.", reply_markup=main_menu(int(user_id)))
        except:
            pass
        if user_id in pending_accounts:
            del pending_accounts[user_id]
        if user_id in pending_deposits:
            del pending_deposits[user_id]
        if user_id in pending_withdraws:
            del pending_withdraws[user_id]
        if user_id in pending_deletes:
            del pending_deletes[user_id]
        bot.send_message(ADMIN_ID, f"✅ تم رفض الطلب للمستخدم {user_id}.")

def send_manual_reply(message, user_id):
    try:
        bot.send_message(int(user_id), f"📩 رسالة من الإدارة:\n{message.text}", reply_markup=main_menu(int(user_id)))
        bot.send_message(ADMIN_ID, "✅ تم إرسال الرد للمستخدم.")
    except Exception as e:
        bot.send_message(ADMIN_ID, f"⚠️ خطأ أثناء إرسال الرسالة للمستخدم: {e}")

def save_new_account_from_admin(message, user_id):
    """يحفظ بيانات الحساب التي أرسلها الإدمن بعد الضغط على قبول"""
    text = message.text or ""
    lines = text.split("\n")
    username_line = next((l for l in lines if l.strip().startswith("Username:")), None)
    password_line = next((l for l in lines if l.strip().startswith("Password:")), None)

    if not username_line:
        msg = bot.send_message(ADMIN_ID, "⚠️ لم أجد سطر Username:. أعد الإرسال بصيغة:\nUsername: اسم\nPassword: كلمة (اختياري)")
        bot.register_next_step_handler(msg, lambda m: save_new_account_from_admin(m, user_id))
        return

    username = username_line.split(":",1)[1].strip()
    password = password_line.split(":",1)[1].strip() if password_line else "********"

    # احفظ في data.json
    data = load_data()
    data["user_accounts"][user_id] = {"username": username, "password": password}
    save_data(data)

    # أخبر المستخدم
    try:
        bot.send_message(int(user_id), f"✅ تم إنشاء حسابك بنجاح!\nUsername: {username}\nPassword: {password}", reply_markup=main_menu(int(user_id)))
    except:
        pass

    # تأكيد للإدمن
    bot.send_message(ADMIN_ID, f"✅ تم حفظ الحساب للمستخدم {user_id}:\nUsername: {username}\nPassword: {password}")

    # تنظيف أي طلبات مؤقتة
    if user_id in pending_accounts:
        del pending_accounts[user_id]
    if user_id in pending_deposits:
        del pending_deposits[user_id]
    if user_id in pending_withdraws:
        del pending_withdraws[user_id]
    if user_id in pending_deletes:
        del pending_deletes[user_id]

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
    # set webhook when visiting root
    try:
        bot.remove_webhook()
        bot.set_webhook(url=RENDER_URL + '/' + TOKEN)
    except Exception as e:
        print("Webhook set error:", e)
    return "Webhook Set!"

if __name__ == "__main__":
    PORT = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=PORT)
