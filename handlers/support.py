def support_handlers(bot):

    @bot.message_handler(func=lambda m: m.text or "")
    def support_message(message):
        # هنا يمكنك توجيه الرسائل للدعم أو الأدمن
        pass
