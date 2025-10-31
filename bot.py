import telebot
from telebot import types
import json
import os

# ==========================
# إعدادات البوت
# ==========================
TOKEN = "8317743306:AAHAM9svd23L2mqSfHnPFEsqKY_bavW3kMg"
ADMIN_ID = 7625893170
SUPPORT_USERNAME = "@supp_mo"
SYRIATEL_WALLET = "82492253"
SHAM_WALLET = "131efe4fbccd83a811282761222eee69"
DATA_FILE = "data/users.json"

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

# ==========================
# إعداد ملفات البيانات
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
# القائمة الرئيسية
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
# بدء المحادثة
# ==========================
@bot.message_handler(commands=["start"])
def start(message):
    users = load_users()
    user_id = str(message.from_user.id)
    if user_id in users:
        name = users[user_id]["name"]
        password = users[user_id]["password"]
        bot.send_message(
            message.chat.id,
            f"👋 أهلاً! لديك حساب مسجّل بالفعل.\n👤 اسم الحساب: {name}\n🔑 كلمة السر: {password}",
            reply_markup=main_menu()
        )
    else:
        bot.send_message(
            message.chat.id,
            "👋 أهلاً بك في بوت 55BETS الرسمي.\nاختر أحد الخيارات أدناه:",
            reply_markup=main_menu()
        )

# ==========================
# إنشاء الحساب
# ==========================
@bot.callback_query_handler(func=lambda call: call.data == "create_account")
def create_account(call):
    users = load_users()
    user_id = str(call.from_user.id)
    if user_id in users:
        name = users[user_id]["name"]
        password = users[user_id]["password"]
        bot.send_message(
            call.message.chat.id,
            f"⚠️ لديك حساب مسجّل مسبقًا.\n👤 اسم الحساب: {name}\n🔑 كلمة السر: {password}",
            reply_markup=main_menu()
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
    bot.send_message(ADMIN_ID, text, reply_markup=markup)
    bot.send_message(user_id, "⏳ تم إرسال طلبك إلى الإدارة، الرجاء الانتظار للمراجعة.", reply_markup=main_menu())

# ==========================
# موافقة/رفض الأدمن
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
    name = parts[2]
    password = parts[3]
    msg = bot.send_message(
        call.message.chat.id,
        f"✏️ أرسل البيانات المعدّلة (اختياري):\n<code>اسم - كلمة_السر</code>\nأو أرسل /skip للإبقاء على القيم الحالية.\n\nالقيم الحالية:\n👤 {name}\n🔑 {password}"
    )
    bot.register_next_step_handler(msg, lambda m: finalize_approval(m, user_id, name, password))

def finalize_approval(message, user_id, old_name, old_pass):
    users = load_users()
    name = old_name
    password = old_pass
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
    # عرض الكود للنسخ
    text = f"💸 الرجاء تحويل المبلغ <b>{amount}</b> إلى المحفظة:\n<code>{wallet}</code>"
    bot.send_message(call.message.chat.id, text)
    admin_text = f"""
📥 <b>طلب إيداع جديد</b>
👤 الحساب: <b>{name}</b>
💰 المبلغ: <b>{amount}</b>
💳 الطريقة: {'سيرياتيل كاش' if method == 'syriatel' else 'شام كاش'}
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
        bot.send_message(message.chat.id, "اختر طريقة الدفع للسحب:", reply_markup=markup)
    except:
        bot.send_message(message.chat.id, "❌ الرجاء إدخال رقم صالح.", reply_markup=main_menu())

@bot.callback_query_handler(func=lambda call: call.data.startswith("withdraw_"))
def withdraw_method(call):
    parts = call.data.split("_")
    method = parts[1]
    amount = parts[2]
    wallet_type = "سيرياتيل كاش" if method == "syriatel" else "شام كاش"
    user_id = str(call.from_user.id)
    msg = bot.send_message(call.message.chat.id, f"📥 أرسل كود محفظتك لـ {wallet_type}:")
    bot.register_next_step_handler(msg, lambda m: finalize_withdraw(m, amount, wallet_type))

def finalize_withdraw(message, amount, wallet_type):
    code = message.text.strip()
    user_id = str(message.from_user.id)
    users = load_users()
    name = users.get(user_id, {}).get("name", "غير مسجل")
    bot.send_message(message.chat.id, "⏳ تم إرسال طلب السحب للإدارة، الرجاء الانتظار.", reply_markup=main_menu())
    admin_text = f"""
📤 <b>طلب سحب جديد</b>
👤 الحساب: <b>{name}</b>
💰 المبلغ: <b>{amount}</b>
💳 الطريقة: {wallet_type}
🆔 المستخدم: <code>{user_id}</code>
🔑 كود المحفظة: <code>{code}</code>
"""
    bot.send_message(ADMIN_ID, admin_text)

# ==========================
# الدعم الفني
# ==========================
@bot.callback_query_handler(func=lambda call: call.data == "support")
def support(call):
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("⬅️ رجوع", callback_data="back")
    )
    bot.send_message(call.message.chat.id, f"🧑‍💻 للتواصل مع الدعم، استخدم: {SUPPORT_USERNAME}", reply_markup=markup)

# ==========================
# حذف الحساب
# ==========================
@bot.callback_query_handler(func=lambda call: call.data == "delete_account")
def delete_account(call):
    user_id = str(call.from_user.id)
    users = load_users()
    if user_id not in users:
        bot.send_message(call.message.chat.id, "⚠️ لا يوجد حساب مسجّل لديك.", reply_markup=main_menu())
        return
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("✅ موافقة الأدمن", callback_data=f"delete_approve_{user_id}"),
        types.InlineKeyboardButton("❌ رفض", callback_data=f"delete_reject_{user_id}"),
        types.InlineKeyboardButton("⬅️ رجوع", callback_data="back")
    )
    bot.send_message(call.message.chat.id, "⚠️ سيتم حذف حسابك بموافقة الأدمن:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("delete_"))
def delete_confirm(call):
    parts = call.data.split("_")
    action = parts[1]
    user_id = parts[2]
    users = load_users()
    if action == "approve":
        if user_id in users:
            del users[user_id]
            save_users(users)
        bot.send_message(user_id, "🗑️ تم حذف حسابك بنجاح.", reply_markup=main_menu())
        bot.send_message(call.message.chat.id, "✅ تم حذف الحساب.")
    else:
        bot.send_message(user_id, "❌ تم رفض حذف حسابك من قبل الأدمن.", reply_markup=main_menu())

# ==========================
# زر الرجوع
# ==========================
@bot.callback_query_handler(func=lambda call: call.data == "back")
def back_to_menu(call):
    bot.edit_message_text("🏠 عدت إلى القائمة الرئيسية:", call.message.chat.id, call.message.message_id, reply_markup=main_menu())

# ==========================
# تشغيل البوت
# ==========================
print("✅ Bot is running...")
bot.infinity_polling()
