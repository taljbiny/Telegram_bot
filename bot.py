import telebot
from flask import Flask
import threading
from config import TOKEN, ADMINS
from database import init_db, get_connection

# استيراد handlers
from handlers.user import user_handlers
from handlers.admin_panel import admin_handlers

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

# إضافة جميع Handlers
user_handlers(bot)
admin_handlers(bot)

# تشغيل Flask في Thread منفصل
threading.Thread(target=run_flask).start()

print("Bot is running...")
bot.infinity_polling()
