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
RENDER_URL = "https://telegram-bot-xsto.onrender.com"  # رابط الويب هوك الخاص بك (Render)
DATA_FILE = "data.json"
MIN_AMOUNT = 25000

# ====== المتغيرات المؤقتة ======
pending_accounts = {}      # { user_id: {"username": "...", "password": "...", "raw": "..."} }
pending_deposits = {}      # { user_id: {amount, method, file_id} }
pending_withdraws = {}     # { user_id: {amount, method, wallet} }
pending_deletes = {}       # { user_id: {account} }

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
    include_create = user_id not in data["user_accounts"]
    if user_id in data["user_accounts"]:
        markup = main_menu(message.chat.id)
        bot.send_message(message.chat.id, f"👤 لديك حساب مسجل مسبقاً.\nاختر العملية من الأزرار أدناه:", reply_markup=markup)
    else:
        markup = main_menu(message.chat.id, include_create=True)
        text = f"👋 أهلاً بك في نظام [55BETS]({SITE_LINK})!\nاختر العملية من الأزرار أدناه:"
        bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode="Markdown")

# ====== عرض القائمة الرئيسية عبر الزر ======
@bot.callback_query_handler(func=lambda call: call.data == "main_menu")
def show_main_menu(call):
    try:
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
    except:
        pass
    data = load_data()
    user_id = str(call.message.chat.id)
    include_create = user_id not in data["user_accounts"]
    bot.send_message(call.message.chat.id, "🔙 القائمة الرئيسية:", reply_markup=main_menu(call.message.chat.id, include_create=include_create))

# ====== إنشاء الحساب - بخطوتين للمستخدم ======
@bot.callback_query_handler(func=lambda call: call.data == "create_account")
def create_account(call):
    try:
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
    except:
        pass
    data = load_data()
    user_id = str(call.message.chat.id)
    if user_id in data["user_accounts"]:
        bot.answer_callback_query(call.id, "❌ لديك حساب مسبق، احذف الحساب القديم أولاً.")
        return
    # نطلب اسم المستخدم أولاً
    msg = bot.send_message(call.message.chat.id, "📝 أرسل اسم المستخدم الذي تريده:", reply_markup=back_to_menu())
    bot.register_next_step_handler(msg, collect_username_step)

def collect_username_step(message):
    if not message.text:
        msg = bot.send_message(message.chat.id, "❌ الرجاء إرسال اسم مستخدم نصي:", reply_markup=back_to_menu())
        bot.register_next_step_handler(msg, collect_username_step)
        return
    if message.text.strip().lower() == "🔙 القائمة الرئيسية":
        bot.send_message(message.chat.id, "🔙 عدت للقائمة الرئيسية.", reply_markup=main_menu(message.chat.id))
        return
    user_id = str(message.chat.id)
    username = message.text.strip()
    # خزّن الاسم مؤقتًا ثم اطلب كلمة السر
    pending_accounts[user_id] = {"username": username, "password": None, "raw_from_user": None}
    msg = bot.send_message(message.chat.id, "🔐 الآن أرسل كلمة السر التي تريدها:", reply_markup=back_to_menu())
    bot.register_next_step_handler(msg, collect_password_step)

def collect_password_step(message):
    if not message.text:
        msg = bot.send_message(message.chat.id, "❌ الرجاء إرسال كلمة سر نصية:", reply_markup=back_to_menu())
        bot.register_next_step_handler(msg, collect_password_step)
        return
    if message.text.strip().lower() == "🔙 القائمة الرئيسية":
        # إلغاء الطلب المؤقت إن رجع للقائمة
        user_id = str(message.chat.id)
        if user_id in pending_accounts:
            del pending_accounts[user_id]
        bot.send_message(message.chat.id, "🔙 عدت للقائمة الرئيسية.", reply_markup=main_menu(message.chat.id, include_create=True))
        return
    user_id = str(message.chat.id)
    password = message.text.strip()
    # خزّن كلمة السر مع الاسم، واحفظ النص الخام أيضاً
    if user_id not in pending_accounts:
        pending_accounts[user_id] = {"username": None, "password": password, "raw_from_user": None}
    else:
        pending_accounts[user_id]["password"] = password
    raw_text = f"Username: {pending_accounts[user_id].get('username', '')}\nPassword: {password}"
    pending_accounts[user_id]["raw_from_user"] = raw_text
    # أرسل للإدمن مع أزرار التحكم
    bot.send_message(
        ADMIN_ID,
        f"📩 طلب إنشاء حساب جديد:\n👤 المستخدم: {user_id}\n\n{raw_text}",
        reply_markup=admin_controls(user_id)
    )
    bot.send_message(message.chat.id, "⏳ تم إرسال طلب إنشاء الحساب للإدارة، يرجى الانتظار...", reply_markup=main_menu(message.chat.id))

# ====== شحن الحساب ======
@bot.callback_query_handler(func=lambda call: call.data == "deposit")
def deposit_start(call):
    try:
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
    except:
        pass
    user_id = str(call.message.chat.id)
    data = load_data()
    if user_id not in data["user_accounts"]:
        bot.send_message(user_id, "❌ ليس لديك حساب، يرجى إنشاء حساب أولاً.", reply_markup=main_menu(user_id, include_create=True))
        return
    msg = bot.send_message(call.message.chat.id, f"💰 أدخل المبلغ لشحن الحساب (الحد الأدنى {MIN_AMOUNT}):", reply_markup=back_to_menu())
    bot.register_next_step_handler(msg, deposit_amount_step)

def deposit_amount_step(message):
    if message.text and message.text.strip().lower() == "🔙 القائمة الرئيسية":
        bot.send_message(message.chat.id, "🔙 عدت للقائمة الرئيسية.", reply_markup=main_menu(message.chat.id))
        return
    amount = message.text.strip()
    if not check_min_amount(amount):
        msg = bot.send_message(message.chat.id, f"❌ الحد الأدنى للشحن هو {MIN_AMOUNT}. أعد الإدخال:", reply_markup=back_to_menu())
        bot.register_next_step_handler(msg, deposit_amount_step)
        return
    # اختر طريقة الدفع
    msg = bot.send_message(message.chat.id, "💳 اختر طريقة الدفع:", reply_markup=None)
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("سيرياتيل كاش", callback_data=f"deposit_method_syriatel_{amount}"),
        types.InlineKeyboardButton("شام كاش", callback_data=f"deposit_method_sham_{amount}")
    )
    bot.edit_message_text(chat_id=message.chat.id, message_id=msg.message_id, text=f"💳 سيتم شحن مبلغ {amount}. اختر طريقة الدفع:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("deposit_method_"))
def deposit_method_selected(call):
    try:
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
    except:
        pass
    parts = call.data.split("_")
    # format: deposit_method_syriatel_AMOUNT
    method = parts[2]  # syriatel or sham
    amount = parts[3]
    user_id = str(call.message.chat.id)
    method_name = "سيرياتيل كاش" if method == "syriatel" else "شام كاش"
    code = SYRIATEL_CODE if method == "syriatel" else SHAM_CODE
    # نطلب صورة التأكيد
    msg = bot.send_message(call.message.chat.id, f"📱 كود المحفظة لـ {method_name}: `{code}`\n📸 أرسل صورة تأكيد الدفع الآن.", parse_mode="Markdown", reply_markup=back_to_menu())
    bot.register_next_step_handler(msg, lambda m: handle_deposit_photo(m, amount, method_name))

def handle_deposit_photo(message, amount, method_name):
    if message.text and message.text.strip().lower() == "🔙 القائمة الرئيسية":
        bot.send_message(message.chat.id, "🔙 عدت للقائمة الرئيسية.", reply_markup=main_menu(message.chat.id))
        return
    if not message.photo:
        bot.send_message(message.chat.id, "❌ الرجاء إرسال صورة تأكيد الدفع فقط.", reply_markup=main_menu(message.chat.id))
        return
    file_id = message.photo[-1].file_id
    user_id = str(message.chat.id)
    pending_deposits[user_id] = {"amount": amount, "method": method_name, "file_id": file_id}
    # ارسال للصورة مع الازرار للادمن
    bot.send_photo(
        ADMIN_ID,
        file_id,
        caption=f"💳 طلب شحن جديد:\n👤 المستخدم: {user_id}\n💰 المبلغ: {amount}\n💼 الطريقة: {method_name}",
        reply_markup=admin_controls(user_id)
    )
    bot.send_message(message.chat.id, "📩 تم إرسال طلب الشحن للإدارة، يرجى الانتظار.", reply_markup=main_menu(message.chat.id))

# ====== سحب الحساب ======
@bot.callback_query_handler(func=lambda call: call.data == "withdraw")
def withdraw_start(call):
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
        msg = bot.send_message(message.chat.id, f"❌ الحد الأدنى للسحب هو {MIN_AMOUNT}. أعد الإدخال:", reply_markup=back_to_menu())
        bot.register_next_step_handler(msg, withdraw_amount_step)
        return
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("سيرياتيل كاش", callback_data=f"withdraw_method_syriatel_{amount}"),
        types.InlineKeyboardButton("شام كاش", callback_data=f"withdraw_method_sham_{amount}")
    )
    bot.send_message(message.chat.id, "💳 اختر طريقة السحب:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("withdraw_method_"))
def withdraw_method_selected(call):
    try:
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
    except:
        pass
    parts = call.data.split("_")
    method = parts[2]
    amount = parts[3]
    method_name = "سيرياتيل كاش" if method == "syriatel" else "شام كاش"
    user_id = str(call.message.chat.id)
    msg = bot.send_message(call.message.chat.id, f"📩 أرسل رقم/كود المحفظة لطريقة {method_name}:", reply_markup=back_to_menu())
    bot.register_next_step_handler(msg, lambda m: confirm_withdraw_wallet(m, amount, method_name))

def confirm_withdraw_wallet(message, amount, method_name):
    if message.text and message.text.strip().lower() == "🔙 القائمة الرئيسية":
        bot.send_message(message.chat.id, "🔙 عدت للقائمة الرئيسية.", reply_markup=main_menu(message.chat.id))
        return
    wallet = message.text.strip()
    user_id = str(message.chat.id)
    pending_withdraws[user_id] = {"amount": amount, "method": method_name, "wallet": wallet}
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

    # زر الرد اليدوي: الإدارة تكتب رسالة تُرسل للمستخدم
    if action == "manual":
        msg = bot.send_message(ADMIN_ID, f"📝 اكتب الرد اليدوي الذي تريد إرساله للمستخدم {user_id}:")
        bot.register_next_step_handler(msg, lambda m: send_manual_reply(m, user_id))
        return

    # زر القبول: نطلب من الادمن ارسال بيانات الحساب النهائية أو "ASIS" لاستخدام بيانات المستخدم
    if action == "accept":
        # تحقق إن هناك طلب إنشاء (إن لم يكن، نقبل أي طلب آخر كالـ deposit/withdraw/delete حسب الحالة)
        # الاهم: نطلب من الادمن ارسال Username/Password أو كتابة ASIS
        msg = bot.send_message(ADMIN_ID,
            f"🆕 ارسل بيانات الحساب للمستخدم {user_id} بصيغة:\nUsername: اسم\nPassword: كلمة\n\nأو اكتب ASIS لاستخدام بيانات المستخدم المرسلة مسبقاً.")
        bot.register_next_step_handler(msg, lambda m: admin_confirm_account_data(m, user_id))
        return

    # زر الرفض: نرسل رفض للمستخدم وننظف أي طلب مؤقت
    if action == "reject":
        try:
            bot.send_message(int(user_id), "❌ تم رفض طلبك من قبل الإدارة.", reply_markup=main_menu(int(user_id)))
        except:
            pass
        # نظف الطلبات المرتبطة
        pending_accounts.pop(user_id, None)
        pending_deposits.pop(user_id, None)
        pending_withdraws.pop(user_id, None)
        pending_deletes.pop(user_id, None)
        bot.send_message(ADMIN_ID, f"✅ تم رفض الطلب للمستخدم {user_id}.")
        return

def admin_confirm_account_data(message, user_id):
    text = (message.text or "").strip()
    # إذا كتب الادمن ASIS نستخدم القيم التي أرسلها المستخدم سابقاً
    if text.upper() == "ASIS":
        if user_id not in pending_accounts:
            bot.send_message(ADMIN_ID, "⚠️ لا يوجد بيانات مستخدم محفوظة لاستخدامها (لم يقم المستخدم بإرسال اسم/كلمة سر).")
            return
        info = pending_accounts[user_id]
        username = info.get("username")
        password = info.get("password")
    else:
        # نحاول استخراج Username و Password من نص الادمن
        lines = text.split("\n")
        username_line = next((l for l in lines if l.strip().startswith("Username:")), None)
        password_line = next((l for l in lines if l.strip().startswith("Password:")), None)
        if not username_line:
            bot.send_message(ADMIN_ID, "⚠️ لم أجد سطر Username:. أعد الإرسال بصيغة:\nUsername: اسم\nPassword: كلمة (أو اكتب ASIS).")
            bot.register_next_step_handler(bot.send_message(ADMIN_ID, "أعد إرسال بيانات الحساب:"), lambda m: admin_confirm_account_data(m, user_id))
            return
        username = username_line.split(":",1)[1].strip()
        password = password_line.split(":",1)[1].strip() if password_line else "********"

    # حفظ الحساب
    data = load_data()
    data["user_accounts"][user_id] = {"username": username, "password": password}
    save_data(data)

    # إعلام المستخدم
    try:
        bot.send_message(int(user_id), f"✅ تم إنشاء حسابك بنجاح!\nUsername: {username}\nPassword: {password}", reply_markup=main_menu(int(user_id)))
    except:
        pass

    # إشعار للإدمن
    bot.send_message(ADMIN_ID, f"✅ تم حفظ الحساب للمستخدم {user_id}:\nUsername: {username}\nPassword: {password}")

    # تنظيف الطلبات المؤقتة المرتبطة
    pending_accounts.pop(user_id, None)
    pending_deposits.pop(user_id, None)
    pending_withdraws.pop(user_id, None)
    pending_deletes.pop(user_id, None)

# ====== إرسال رد يدوي للإدمن ======
def send_manual_reply(message, user_id):
    try:
        bot.send_message(int(user_id), f"📩 رسالة من الإدارة:\n{message.text}", reply_markup=main_menu(int(user_id)))
        bot.send_message(ADMIN_ID, "✅ تم إرسال الرد للمستخدم.")
    except Exception as e:
        bot.send_message(ADMIN_ID, f"⚠️ خطأ أثناء إرسال الرسالة للمستخدم: {e}")

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
    try:
        bot.remove_webhook()
    except:
        pass
    try:
        bot.set_webhook(url=RENDER_URL + '/' + TOKEN)
    except Exception as e:
        print("Webhook set error:", e)
    return "Webhook Set!"

if __name__ == "__main__":
    PORT = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=PORT)
