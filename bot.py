import telebot
from telebot import types
import json
import os

# ==========================
# إعدادات البوت الأساسية
# ==========================
TOKEN = "8317743306:AAHAM9svd23L2mqSfHnPFEsqKY_bavW3kMg"
ADMIN_ID = 7625893170
SUPPORT_USERNAME = "@supp_mo"

# أكواد المحافظ
SYRIATEL_WALLET = "82492253"
SHAM_WALLET = "131efe4fbccd83a811282761222eee69"

# ملف تخزين المستخدمين
DATA_FILE = "data/users.json"

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

# ==========================
# تحميل وحفظ بيانات المستخدمين
# ==========================
if not os.path.exists("data"):
    os.makedirs("data")

if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f)

def load_users():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_users(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ==========================
# لوحة الأزرار الرئيسية
# ==========================
def main_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🧾 إنشاء حساب", callback_data="create_account"),
        types.InlineKeyboardButton("💰 إيداع", callback_data="deposit"),
        types.InlineKeyboardButton("💸 سحب", callback_data="withdraw"),
        types.InlineKeyboardButton("🧑‍💻 دعم فني", callback_data="support"),
        types.InlineKeyboardButton("🗑️ حذف الحساب", callback_data="delete_account")
    )
    return markup

# ==========================
# عند بدء المحادثة
# ==========================
@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(
        message.chat.id,
        "👋 أهلاً بك في بوت 55BETS الرسمي.\nاختر أحد الخيارات أدناه:",
        reply_markup=main_menu(),
    )

# ==========================
# إنشاء الحساب (بخطوتين)
# ==========================
@bot.callback_query_handler(func=lambda call: call.data == "create_account")
def create_account(call):
    users = load_users()
    user_id = str(call.from_user.id)

    # التحقق إن كان لديه حساب سابق
    if user_id in users:
        bot.send_message(
            call.message.chat.id,
            "⚠️ لديك حساب مُسجل بالفعل.\nلحذف الحساب القديم، استخدم زر حذف الحساب.",
            reply_markup=main_menu(),
        )
        return

    msg = bot.send_message(call.message.chat.id, "🧾 أرسل اسم الحساب الذي ترغب بإنشائه:")
    bot.register_next_step_handler(msg, get_account_name)

def get_account_name(message):
    name = message.text.strip()
    msg = bot.send_message(message.chat.id, "🔒 أرسل كلمة السر التي ترغب بها:")
    bot.register_next_step_handler(msg, lambda msg2: confirm_account(message, msg2, name))

def confirm_account(name_msg, pass_msg, name):
    password = pass_msg.text.strip()
    user_id = str(name_msg.from_user.id)

    text = f"""
🆕 <b>طلب إنشاء حساب جديد</b>
👤 الاسم: <code>{name}</code>
🔑 كلمة السر: <code>{password}</code>
🆔 المستخدم: <code>{user_id}</code>
"""
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("✅ موافقة", callback_data=f"approve_{user_id}_{name}_{password}"),
        types.InlineKeyboardButton("❌ رفض", callback_data=f"reject_{user_id}")
    )

    # إرسال الطلب إلى الأدمن
    bot.send_message(ADMIN_ID, text, reply_markup=markup)
    bot.send_message(user_id, "⏳ تم إرسال طلبك إلى الإدارة، الرجاء الانتظار للمراجعة.", reply_markup=main_menu())

# ==========================
# معالجة قرار الأدمن (موافقة / رفض)
# ==========================
@bot.callback_query_handler(func=lambda call: call.data.startswith("approve_") or call.data.startswith("reject_"))
def handle_admin_decision(call):
    parts = call.data.split("_")
    action = parts[0]
    user_id = parts[1]

    if action == "reject":
        bot.send_message(int(user_id), "❌ تم رفض إنشاء حسابك من قبل الإدارة.", reply_markup=main_menu())
        bot.send_message(call.message.chat.id, "🚫 تم رفض الطلب بنجاح.")
        return

    # في حال الموافقة:
    name = parts[2]
    password = parts[3]

    msg = bot.send_message(
        call.message.chat.id,
        f"✏️ أرسل البيانات المعدّلة (اختياري):\n<code>اسم - كلمة_السر</code>\nأو أرسل /skip للإبقاء على القيم الحالية.\n\nالقيم الحالية:\n👤 {name}\n🔑 {password}"
    )
    bot.register_next_step_handler(msg, lambda m: finalize_approval(m, user_id, name, password))

def finalize_approval(message, user_id, name, password):
    users = load_users()

    # تعديل القيم في حال أرسل بيانات جديدة
    if message.text != "/skip" and "-" in message.text:
        parts = message.text.split("-")
        name = parts[0].strip()
        password = parts[1].strip()

    users[user_id] = {"name": name, "password": password}
    save_users(users)

    bot.send_message(int(user_id), f"✅ تم إنشاء الحساب بنجاح!\n👤 الاسم: <b>{name}</b>\n🔑 كلمة السر: <b>{password}</b>", reply_markup=main_menu())
    bot.send_message(message.chat.id, f"✅ تم إنشاء الحساب للمستخدم {user_id} بنجاح.")

# ==========================
# الإيداع
# ==========================
@bot.callback_query_handler(func=lambda call: call.data == "deposit")
def deposit(call):
    msg = bot.send_message(call.message.chat.id, "💰 أرسل المبلغ الذي ترغب بإيداعه (الحد الأدنى 25,000):")
    bot.register_next_step_handler(msg, get_deposit_amount)

def get_deposit_amount(message):
    try:
        amount = int(message.text)
        if amount < 25000:
            bot.send_message(message.chat.id, "⚠️ الحد الأدنى للإيداع هو 25,000.", reply_markup=main_menu())
            return
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("📱 سيرياتيل كاش", callback_data=f"deposit_syriatel_{amount}"),
            types.InlineKeyboardButton("💳 شام كاش", callback_data=f"deposit_sham_{amount}"),
            types.InlineKeyboardButton("⬅️ رجوع", callback_data="back")
        )
        bot.send_message(message.chat.id, "اختر طريقة الدفع:", reply_markup=markup)
    except:
        bot.send_message(message.chat.id, "❌ الرجاء إدخال رقم صالح.", reply_markup=main_menu())

@bot.callback_query_handler(func=lambda call: call.data.startswith("deposit_"))
def deposit_method(call):
    parts = call.data.split("_")
    method = parts[1]
    amount = parts[2]
    wallet = SYRIATEL_WALLET if method == "syriatel" else SHAM_WALLET
    user_id = str(call.from_user.id)
    users = load_users()
    name = users.get(user_id, {}).get("name", "غير مسجل")

    text = f"💸 الرجاء تحويل <b>{amount}</b> إلى المحفظة:\n<code>{wallet}</code>\nثم أرسل صورة أو رمز العملية للتأكيد."
    bot.send_message(call.message.chat.id, text)

    admin_text = f"""
📥 <b>طلب إيداع جديد</b>
👤 الحساب: <b>{name}</b>
💰 المبلغ: <b>{amount}</b>
💳 الطريقة: { 'سيرياتيل كاش' if method == 'syriatel' else 'شام كاش' }
🆔 المستخدم: <code>{user_id}</code>
"""
    bot.send_message(ADMIN_ID, admin_text)

# ==========================
# السحب
# ==========================
@bot.callback_query_handler(func=lambda call: call.data == "withdraw")
def withdraw(call):
    msg = bot.send_message(call.message.chat.id, "💸 أرسل المبلغ الذي ترغب بسحبه (الحد الأدنى 25,000):")
    bot.register_next_step_handler(msg, get_withdraw_amount)

def get_withdraw_amount(message):
    try:
        amount = int(message.text)
        if amount < 25000:
            bot.send_message(message.chat.id, "⚠️ الحد الأدنى للسحب هو 25,000.", reply_markup=main_menu())
            return
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("📱 سيرياتيل كاش", callback_data=f"withdraw_syriatel_{amount}"),
            types.InlineKeyboardButton("💳 شام كاش", callback_data=f"withdraw_sham_{amount}"),
            types.InlineKeyboardButton("⬅️ رجوع", callback_data="back")
        )
        bot.send_message(message.chat.id, "اختر طريقة الدفع:", reply_markup=markup)
    except:
        bot.send_message(message.chat.id, "❌ الرجاء إدخال رقم صالح.", reply_markup=main_menu())

@bot.callback_query_handler(func=lambda call: call.data.startswith("withdraw_"))
def withdraw_method(call):
    parts = call.data.split("_")
    method = parts[1]
    amount = parts[2]
    user_id = str(call.from_user.id)
    users = load_users()
    name = users.get(user_id, {}).get("name", "غير مسجل")

    msg = bot.send_message(call.message.chat.id, "📱 أرسل رقم أو كود محفظتك لاستلام المبلغ:")
    bot.register_next_step_handler(msg, lambda m: confirm_withdrawal(m, method, amount, name))

def confirm_withdrawal(message, method, amount, name):
    wallet_code = message.text.strip()
    user_id = str(message.from_user.id)
    text = f"✅ تم إرسال طلب السحب للإدارة، الرجاء الانتظار للمراجعة."
    bot.send_message(message.chat.id, text, reply_markup=main_menu())

    admin_text = f"""
📤 <b>طلب سحب جديد</b>
👤 الحساب: <b>{name}</b>
💰 المبلغ: <b>{amount}</b>
💳 الطريقة: { 'سيرياتيل كاش' if method == 'syriatel' else 'شام كاش' }
🏧 كود المحفظة: <code>{wallet_code}</code>
🆔 المستخدم: <code>{user_id}</code>
"""
    bot.send_message(ADMIN_ID, admin_text)

# ==========================
# الدعم الفني
# ==========================
@bot.callback_query_handler(func=lambda call: call.data == "support")
def support(call):
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("💬 تواصل مع الدعم", url=f"https://t.me/{SUPPORT_USERNAME.replace('@', '')}"),
        types.InlineKeyboardButton("⬅️ رجوع", callback_data="back")
    )
    bot.send_message(call.message.chat.id, "🧑‍💻 تواصل مع الدعم الفني:", reply_markup=markup)

# ==========================
# الرجوع للقائمة
# ==========================
@bot.callback_query_handler(func=lambda call: call.data == "back")
def back_to_menu(call):
    bot.edit_message_text("🏠 عدت إلى القائمة الرئيسية:", call.message.chat.id, call.message.message_id, reply_markup=main_menu())

# ==========================
# تشغيل البوت
# ==========================
print("✅ Bot is running...")
bot.infinity_polling()
