from flask import Flask, request
import telebot
import os

TOKEN = "8317743306:AAFGH1Acxb6fIwZ0o0T2RvNjezQFW8KWcw8"
ADMIN_ID = 7625893170

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# Start command
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id, "أهلاً! اختر من القائمة: \n1. إنشاء حساب \n2. إيداع \n3. سحب")

# Echo any message to admin
@bot.message_handler(func=lambda m: True)
def forward_to_admin(message):
    bot.send_message(ADMIN_ID, f"رسالة من {message.from_user.username} ({message.from_user.id}): {message.text}")

# Flask route for Render Webhook
@app.route(f"/{TOKEN}", methods=['POST'])
def webhook():
    json_str = request.get_data().decode('UTF-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "!", 200

# Root route to test server
@app.route("/")
def index():
    return "بوت Telegram شغال على Render!", 200

if __name__ == "__main__":
    # Set webhook automatically if running on Render
    WEBHOOK_URL = os.environ.get("RENDER_EXTERNAL_URL") + f"/{TOKEN}"
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
