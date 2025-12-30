import telebot
from config import TOKEN
from handlers import user, support, admin_panel

bot = telebot.TeleBot(TOKEN)

user.register(bot)
support.register(bot)
admin_panel.register(bot)

bot.infinity_polling()
