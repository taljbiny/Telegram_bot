import telebot
from telebot import types
import sqlite3
from config import TOKEN, ADMINS

bot = telebot.TeleBot(TOKEN)

# ================= DATABASE =================
conn = sqlite3.connect("database.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    telegram_id INTEGER PRIMARY KEY,
    username TEXT,
    account_name TEXT,
    password TEXT,
    balance REAL DEFAULT 0,
    status TEXT
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS deposits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER,
    amount REAL,
    method TEXT,
    proof TEXT,
    status TEXT
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS withdrawals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER,
    amount REAL,
    fee REAL,
    net REAL,
    wallet_type TEXT,
    wallet_number TEXT,
    status TEXT
)
""")
conn.commit()

# ================= STATES =================
user_state = {}
temp = {}
support_sessions = {}

# ================= KEYBOARDS =================
def main_menu(uid):
    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton("➕ إنشاء حساب", callback_data="create_account"),
        types.InlineKeyboardButton("💰 إيداع", callback_data="deposit")
    )
    kb.add(
        types.InlineKeyboardButton("💸 سحب", callback_data="withdraw"),
        types.InlineKeyboardButton("🔑 تغيير كلمة السر", callback_data="change_password")
    )
    kb.add(types.InlineKeyboardButton("📞 الاتصال بالدعم", callback_data="support"))
    if uid in ADMINS:
        kb.add(types.InlineKeyboardButton("🎛️ لوحة الأدمن", callback_data="admin_panel"))
    return kb

def admin_menu():
    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton("🔍 بحث مستخدم", callback_data="admin_search"),
        types.InlineKeyboardButton("💰 تعديل رصيد", callback_data="admin_balance")
    )
    kb.add(
        types.InlineKeyboardButton("👥 جميع المستخدمين", callback_data="admin_users"),
        types.InlineKeyboardButton("🔑 تغيير كلمة السر", callback_data="admin_password")
    )
    kb.add(types.InlineKeyboardButton("⬅️ رجوع", callback_data="back"))
    return kb

# ================= COMMANDS =================
@bot.message_handler(commands=["start"])
def start(message):
    cur.execute(
        "INSERT OR IGNORE INTO users (telegram_id, username, status) VALUES (?,?,?)",
        (message.chat.id, message.from_user.username, "none")
    )
    conn.commit()
    bot.send_message(message.chat.id, "أهلاً بك 🤍", reply_markup=main_menu(message.chat.id))
    user_state[message.chat.id] = "menu"

@bot.message_handler(commands=["balance"])
def balance(message):
    cur.execute("SELECT balance FROM users WHERE telegram_id=?", (message.chat.id,))
    bal = cur.fetchone()[0]
    bot.send_message(message.chat.id, f"💰 رصيدك: {bal}")

@bot.message_handler(commands=["reply"])
def admin_reply(message):
    if message.chat.id not in ADMINS:
        return
    try:
        _, uid, text = message.text.split(" ", 2)
        uid = int(uid)
        bot.send_message(uid, f"📩 الدعم:\n{text}")
        bot.send_message(message.chat.id, "✅ تم الإرسال")
    except:
        bot.send_message(message.chat.id, "❌ الصيغة:\n/reply USER_ID الرسالة")

# ================= CALLBACKS =================
@bot.callback_query_handler(func=lambda c: True)
def callbacks(call):
    uid = call.message.chat.id

    if call.data == "support":
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        kb.add(types.KeyboardButton("📱 مشاركة جهة الاتصال", request_contact=True))
        bot.send_message(uid, "📞 شارك جهة الاتصال للتواصل مع الدعم", reply_markup=kb)

    elif call.data == "admin_panel" and uid in ADMINS:
        bot.send_message(uid, "🎛️ لوحة تحكم الأدمن", reply_markup=admin_menu())
        user_state[uid] = "admin"

    elif call.data == "admin_users" and uid in ADMINS:
        cur.execute("SELECT telegram_id, account_name, balance FROM users")
        rows = cur.fetchall()
        text = "👥 المستخدمون:\n\n"
        for r in rows:
            text += f"ID:{r[0]} | حساب:{r[1]} | رصيد:{r[2]}\n"
        bot.send_message(uid, text)

    elif call.data == "back":
        bot.send_message(uid, "⬅️ رجوع", reply_markup=main_menu(uid))
        user_state[uid] = "menu"

# ================= SUPPORT =================
@bot.message_handler(content_types=["contact"])
def support_contact(message):
    uid = message.chat.id
    support_sessions[uid] = True
    bot.send_message(uid, "✅ تم فتح تذكرة دعم، اكتب مشكلتك الآن")

    for admin in ADMINS:
        bot.send_message(
            admin,
            f"📞 طلب دعم جديد\n"
            f"ID: {uid}\n"
            f"الاسم: {message.from_user.first_name}\n"
            f"الرقم: {message.contact.phone_number}"
        )

@bot.message_handler(func=lambda m: m.chat.id in support_sessions)
def support_chat(message):
    for admin in ADMINS:
        bot.send_message(
            admin,
            f"💬 رسالة دعم\nID:{message.chat.id}\n{message.text}"
        )

# ================= RUN =================
bot.infinity_polling()
