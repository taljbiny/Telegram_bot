from config import ADMINS

def register_support(bot):
    @bot.message_handler(content_types=["contact"])
    def contact_handler(message):
        for admin in ADMINS:
            bot.send_message(admin,
                             f"📞 طلب دعم جديد\n"
                             f"ID: {message.chat.id}\n"
                             f"الاسم: {message.from_user.first_name}\n"
                             f"رقم الهاتف: {message.contact.phone_number}")
        bot.send_message(message.chat.id, "✅ تم إرسال طلبك للدعم")
