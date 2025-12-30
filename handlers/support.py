from config import ADMINS
from database import cursor, conn

support_wait = set()

def register(bot):

    @bot.message_handler(commands=["help"])
    def help_cmd(message):
        bot.send_message(message.chat.id, "📞 اكتب رسالتك:")
        support_wait.add(message.chat.id)

    @bot.message_handler(func=lambda m: m.chat.id in support_wait)
    def support_msg(message):
        for admin in ADMINS:
            bot.send_message(admin, f"📩 دعم من {message.chat.id}:\n{message.text}")
        bot.send_message(message.chat.id, "✅ تم إرسال رسالتك")
        support_wait.remove(message.chat.id)
