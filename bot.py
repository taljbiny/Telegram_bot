import telebot
from telebot import types
from flask import Flask
import threading
from config import TOKEN, ADMINS
from database import init_db, get_connection

from handlers.admin_panel import admin_handlers
from handlers.user import user_handlers
from handlers.support import support_handlers

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# Flask endpoint للبقاء مستيقظ
@app.route("/")
def home():
    return "Bot is alive"

def run_flask():
    app.run(host="0.0.0.0", port=8080)

# تهيئة قاعدة البيانات
init_db()

# إضافة Handlers
user_handlers(bot)
admin_handlers(bot)
support_handlers(bot)

# تشغيل Flask في Thread منفصل
threading.Thread(target=run_flask).start()

print("Bot is running...")
bot.infinity_polling()
