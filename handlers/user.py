from telebot import types
from database import get_connection

def user_handlers(bot):

    @bot.message_handler(commands=['start'])
    def start(message):
        conn = get_connection()
        cur = conn.cursor()

        cur.execute(
            "INSERT OR IGNORE INTO users (telegram_id, username) VALUES (?, ?)",
            (message.from_user.id, message.from_user.username)
        )

        conn.commit()
        conn.close()

        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add("➕ إيداع", "➖ سحب")
        kb.add("💰 رصيدي")

        bot.send_message(
            message.chat.id,
            "أهلاً بك 👋\nاختر من القائمة:",
            reply_markup=kb
        )
