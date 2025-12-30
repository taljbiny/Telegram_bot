import telebot
from telebot import types
import sqlite3

# ================== CONFIG ==================
TOKEN = "8167728652:AAHkmA95NJaNle90-X0o2rct8ZoJZS_T8C8"
ADMINS = [5831849688, 8219716285]

MIN_DEPOSIT = 25000
MIN_WITHDRAW = 50000
WITHDRAW_FEE = 0.05

bot = telebot.TeleBot(TOKEN)

# ================== DATABASE ==================
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
conn.commit()

# ================== STATES ==================
state = {}
temp = {}

# ================== KEYBOARDS ==================
def main_menu():
    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton("➕ إنشاء حساب", callback_data="create"),
        types.InlineKeyboardButton("💰 الرصيد", callback_data="balance")
    )
    kb.add(
        types.InlineKeyboardButton("📥 إيداع", callback_data="deposit"),
        types.InlineKeyboardButton("📤 سحب", callback_data="withdraw")
    )
    kb.add(types.InlineKeyboardButton("📞 الدعم", callback_data="support"))
    return kb

def admin_menu():
    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton("👤 كل المستخدمين", callback_data="all_users"),
        types.InlineKeyboardButton("➕ إضافة رصيد", callback_data="add_balance")
    )
    return kb

# ================== COMMANDS ==================
@bot.message_handler(commands=["start"])
def start(msg):
    uid = msg.chat.id
    cur.execute("INSERT OR IGNORE INTO users (telegram_id) VALUES (?)", (uid,))
    conn.commit()

    bot.send_message(
        uid,
        "👋 أهلاً بك في محفظة البوت",
        reply_markup=main_menu()
    )

@bot.message_handler(commands=["balance"])
def balance_cmd(msg):
    uid = msg.chat.id
    cur.execute("SELECT balance FROM users WHERE telegram_id=?", (uid,))
    bal = cur.fetchone()[0]
    bot.send_message(uid, f"💰 رصيدك: {bal}")

@bot.message_handler(commands=["help"])
def help_cmd(msg):
    state[msg.chat.id] = "support"
    bot.send_message(msg.chat.id, "📞 اكتب رسالتك للدعم")

# ================== CALLBACKS ==================
@bot.callback_query_handler(func=lambda c: True)
def callbacks(call):
    uid = call.message.chat.id
    data = call.data

    if data == "create":
        state[uid] = "account_name"
        bot.send_message(uid, "✍️ أرسل اسم الحساب")

    elif data == "balance":
        cur.execute("SELECT balance FROM users WHERE telegram_id=?", (uid,))
        bal = cur.fetchone()[0]
        bot.send_message(uid, f"💰 رصيدك: {bal}")

    elif data == "deposit":
        state[uid] = "deposit"
        bot.send_message(uid, f"💰 أدخل مبلغ الإيداع (الحد الأدنى {MIN_DEPOSIT})")

    elif data == "withdraw":
        state[uid] = "withdraw"
        bot.send_message(uid, f"📤 أدخل مبلغ السحب (الحد الأدنى {MIN_WITHDRAW})")

    elif data == "support":
        state[uid] = "support"
        bot.send_message(uid, "📞 اكتب رسالتك للدعم")

    elif data == "admin" and uid in ADMINS:
        bot.send_message(uid, "🎛 لوحة تحكم الأدمن", reply_markup=admin_menu())

    elif data == "all_users" and uid in ADMINS:
        cur.execute("SELECT telegram_id, balance FROM users")
        users = cur.fetchall()
        txt = "👥 المستخدمين:\n"
        for u in users:
            txt += f"ID:{u[0]} | 💰 {u[1]}\n"
        bot.send_message(uid, txt)

# ================== STATES HANDLER ==================
@bot.message_handler(func=lambda m: m.chat.id in state)
def steps(msg):
    uid = msg.chat.id
    step = state[uid]

    if step == "account_name":
        temp[uid] = {"name": msg.text}
        state[uid] = "password"
        bot.send_message(uid, "🔑 أرسل كلمة السر")

    elif step == "password":
        cur.execute(
            "UPDATE users SET account_name=?, password=? WHERE telegram_id=?",
            (temp[uid]["name"], msg.text, uid)
        )
        conn.commit()

        for a in ADMINS:
            bot.send_message(
                a,
                f"🆕 حساب جديد\nID:{uid}\nاسم:{temp[uid]['name']}"
            )

        state.pop(uid)
        temp.pop(uid)
        bot.send_message(uid, "✅ تم إنشاء الحساب", reply_markup=main_menu())

    elif step == "deposit":
        amount = int(msg.text)
        if amount < MIN_DEPOSIT:
            bot.send_message(uid, "❌ المبلغ أقل من الحد الأدنى")
            return

        for a in ADMINS:
            bot.send_message(a, f"📥 طلب إيداع\nID:{uid}\n💰 {amount}")

        state.pop(uid)
        bot.send_message(uid, "⏳ تم إرسال الطلب للإدارة")

    elif step == "withdraw":
        amount = int(msg.text)
        if amount < MIN_WITHDRAW:
            bot.send_message(uid, "❌ المبلغ أقل من الحد الأدنى")
            return

        fee = int(amount * WITHDRAW_FEE)
        net = amount - fee

        for a in ADMINS:
            bot.send_message(
                a,
                f"📤 طلب سحب\nID:{uid}\nالمبلغ:{amount}\nالعمولة:{fee}\nالصافي:{net}"
            )

        state.pop(uid)
        bot.send_message(uid, "⏳ تم إرسال طلب السحب")

    elif step == "support":
        for a in ADMINS:
            bot.send_message(a, f"📞 دعم\nID:{uid}\n{msg.text}")

        state.pop(uid)
        bot.send_message(uid, "✅ تم إرسال رسالتك")

# ================== ADMIN SHORTCUT ==================
@bot.message_handler(commands=["admin"])
def admin_cmd(msg):
    if msg.chat.id in ADMINS:
        bot.send_message(msg.chat.id, "🎛 لوحة تحكم الأدمن", reply_markup=admin_menu())

# ================== RUN ==================
print("BOT IS RUNNING")
bot.infinity_polling()
