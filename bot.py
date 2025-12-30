import telebot
from telebot import types
from config import TOKEN
from handlers.commands import register_commands
from handlers.callbacks import register_callbacks
from handlers.support import register_support
from handlers.admin import register_admin

bot = telebot.TeleBot(TOKEN)

bot.set_my_commands([
    types.BotCommand("start", "تشغيل البوت"),
    types.BotCommand("balance", "عرض الرصيد"),
    types.BotCommand("help", "الدعم")
])

register_commands(bot)
register_callbacks(bot)
register_support(bot)
register_admin(bot)

print("Bot is running...")
bot.infinity_polling()
