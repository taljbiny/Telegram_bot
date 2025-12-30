import telebot
from telebot import types
import sqlite3

# ========= CONFIG =========
TOKEN = "8167728652:AAHkmA95NJaNle90-X0o2rct8ZoJZS_T8C8"
ADMINS = [5831849688, 8219716285]

MIN_DEPOSIT = 25000
MIN_WITHDRAW = 50000
WITHDRAW_FEE = 0.05

bot = telebot.TeleBot(TOKEN)

# ========= DATABASE =========
conn = sqlite3.connect("data.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    telegram_id INTEGER PRIMARY KEY,
    account_name TEXT,
    password TEXT,
    balance INTEGER DEFAULT 0
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS deposits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER,
    amount INTEGER,
    status TEXT
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS withdrawals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER,
    amount INTEGER,
    fee INTEGER,
    net INTEGER,
    status TEXT
)
""")

conn.commit()

# ========= STATES =========
user_state = {}
user_temp = {}

# ========= KEYBOARDS =========
def main_menu(uid):
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("➕ إنشاء حساب", callback_data="create"),
        types.InlineKeyboardButton("💰 الرصيد", callback_data="balance"),
        types.InlineKeyboardButton("💰 إيداع", callback_data="deposit"),
        types.InlineKeyboardButton("💸 سحب", callback_data="withdraw"),
        types.InlineKeyboardButton("📞 الدعم", callback_data="support"),
    )
    if uid in ADMINS:
        kb.add(types.InlineKeyboardButton("🎛 لوحة الأدمن", callback_data="admin"))
    return kb

def admin_menu():
    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton("✅ قبول إيداع", callback_data="approve_deposit"),
        types.InlineKeyboardButton("✅ قبول سحب", callback_data="approve_withdraw"),
    )
    return kb

# ========= COMMANDS =========
@bot.message_handler(commands=["start"])
def start(msg):
    cur.execute("INSERT OR IGNORE INTO users (telegram_id) VALUES (?)", (msg.chat.id,))
    conn.commit()
    bot.send_message(msg.chat.id, "👋 أهلاً بك", reply_markup=main_menu(msg.chat.id))

@bot.message_handler(commands=["balance"])
def balance(msg):
    cur.execute("SELECT balance FROM users WHERE telegram_id=?", (msg.chat.id,))
    bal = cur.fetchone()[0]
    bot.send_message(msg.chat.id, f"💰 رصيدك: {bal}")

@bot.message_handler(commands=["help"])
def help_cmd(msg):
    bot.send_message(msg.chat.id, "📞 تواصل مع الدعم عبر هذا البوت")

# ========= CALLBACKS =========
@bot.callback_query_handler(func=lambda c: True)
def callbacks(c):
    uid = c.message.chat.id
    data = c.data

    if data == "create":
        user_state[uid] = "account"
        bot.send_message(uid, "✍️ اكتب اسم الحساب")

    elif data == "balance":
        cur.execute("SELECT balance FROM users WHERE telegram_id=?", (uid,))
        bot.send_message(uid, f"💰 رصيدك: {cur.fetchone()[0]}")

    elif data == "deposit":
        user_state[uid] = "deposit"
        bot.send_message(uid, f"💰 أدخل مبلغ الإيداع (≥ {MIN_DEPOSIT})")

    elif data == "withdraw":
        user_state[uid] = "withdraw"
        bot.send_message(uid, f"💸 أدخل مبلغ السحب (≥ {MIN_WITHDRAW})")

    elif data == "support":
        bot.send_message(uid, "📞 الدعم سيتواصل معك قريباً")

    elif data == "admin" and uid in ADMINS:
        bot.send_message(uid, "🎛 لوحة الأدمن", reply_markup=admin_menu())

    elif data == "approve_deposit" and uid in ADMINS:
        cur.execute("SELECT id, telegram_id, amount FROM deposits WHERE status='pending' LIMIT 1")
        row = cur.fetchone()
        if not row:
            bot.send_message(uid, "❌ لا يوجد طلبات")
            return
        did, user, amount = row
        cur.execute("UPDATE users SET balance = balance + ? WHERE telegram_id=?", (amount, user))
        cur.execute("UPDATE deposits SET status='approved' WHERE id=?", (did,))
        conn.commit()
        bot.send_message(user, f"✅ تم قبول الإيداع: {amount}")
        bot.send_message(uid, "✔️ تم")

    elif data == "approve_withdraw" and uid in ADMINS:
        cur.execute("SELECT id, telegram_id, net FROM withdrawals WHERE status='pending' LIMIT 1")
        row = cur.fetchone()
        if not row:
            bot.send_message(uid, "❌ لا يوجد طلبات")
            return
        wid, user, net = row
        cur.execute("UPDATE withdrawals SET status='approved' WHERE id=?", (wid,))
        conn.commit()
        bot.send_message(user, f"✅ تم قبول السحب: {net}")
        bot.send_message(uid, "✔️ تم")

# ========= STEPS =========
@bot.message_handler(func=lambda m: m.chat.id in user_state)
def steps(msg):
    uid = msg.chat.id
    step = user_state[uid]

    if step == "account":
        user_temp[uid] = msg.text
        user_state[uid] = "password"
        bot.send_message(uid, "🔑 اكتب كلمة السر")

    elif step == "password":
        cur.execute("UPDATE users SET account_name=?, password=? WHERE telegram_id=?",
                    (user_temp[uid], msg.text, uid))
        conn.commit()
        user_state.pop(uid)
        user_temp.pop(uid)
        bot.send_message(uid, "✅ تم إنشاء الحساب", reply_markup=main_menu(uid))

    elif step == "deposit":
        amount = int(msg.text)
        if amount < MIN_DEPOSIT:
            bot.send_message(uid, "❌ مبلغ غير صحيح")
            return
        cur.execute("INSERT INTO deposits (telegram_id, amount, status) VALUES (?,?,?)",
                    (uid, amount, "pending"))
        conn.commit()
        user_state.pop(uid)
        for a in ADMINS:
            bot.send_message(a, f"💰 طلب إيداع {amount} من {uid}")
        bot.send_message(uid, "⏳ بانتظار موافقة الأدمن")

    elif step == "withdraw":
        amount = int(msg.text)
        if amount < MIN_WITHDRAW:
            bot.send_message(uid, "❌ مبلغ غير صحيح")
            return
        fee = int(amount * WITHDRAW_FEE)
        net = amount - fee
        cur.execute("SELECT balance FROM users WHERE telegram_id=?", (uid,))
        if cur.fetchone()[0] < amount:
            bot.send_message(uid, "❌ رصيد غير كافي")
            return
        cur.execute("UPDATE users SET balance = balance - ? WHERE telegram_id=?", (amount, uid))
        cur.execute("INSERT INTO withdrawals (telegram_id, amount, fee, net, status) VALUES (?,?,?,?,?)",
                    (uid, amount, fee, net, "pending"))
        conn.commit()
        user_state.pop(uid)
        for a in ADMINS:
            bot.send_message(a, f"💸 طلب سحب {amount} من {uid}")
        bot.send_message(uid, f"⏳ بانتظار الموافقة\nالعمولة: {fee}\nالصافي: {net}")

# ========= RUN =========
print("BOT RUNNING")
bot.infinity_polling()
