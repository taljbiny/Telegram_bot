import telebot
from flask import Flask
import threading

from config import TOKEN
from database import init_db
from handlers.user import user_handlers
from handlers.admin_panel import admin_handlers

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is alive"

def run_flask():
    app.run(host="0.0.0.0", port=8080)

init_db()
user_handlers(bot)
admin_handlers(bot)

threading.Thread(target=run_flask).start()

print("Bot is running...")
bot.infinity_polling()
