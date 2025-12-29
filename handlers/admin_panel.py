from telebot import types
from config import ADMINS
from database import get_connection

def admin_handlers(bot):

    @bot.message_handler(commands=['admin'])
    def admin_panel(message):
        if message.from_user.id not in ADMINS:
            return

        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add("🔍 بحث عن مستخدم")
        kb.add("📋 كل المستخدمين")
        kb.add("❌ إغلاق")

        bot.send_message(
            message.chat.id,
            "🔐 لوحة تحكم الأدمن",
            reply_markup=kb
        )
