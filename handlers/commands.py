from telebot import types
from keyboards.main import main_menu
from database import init_db

conn, cur = init_db()

def register_commands(bot):

    @bot.message_handler(commands=["start"])
    def start(message):
        cur.execute(
            "INSERT OR IGNORE INTO users (telegram_id, username) VALUES (?,?)",
            (message.chat.id, message.from_user.username)
        )
        conn.commit()
        bot.send_message(message.chat.id, "👋 أهلاً بك في محفظة البوت", reply_markup=main_menu(message.chat.id))

    @bot.message_handler(commands=["balance"])
    def balance(message):
        cur.execute("SELECT balance FROM users WHERE telegram_id=?", (message.chat.id,))
        bal = cur.fetchone()[0]
        bot.send_message(message.chat.id, f"💰 رصيدك: {bal}")

    @bot.message_handler(commands=["help"])
    def help_cmd(message):
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        kb.add(types.KeyboardButton("📱 مشاركة جهة الاتصال", request_contact=True))
        bot.send_message(message.chat.id, "📞 للتواصل مع الدعم شارك جهة الاتصال", reply_markup=kb)
