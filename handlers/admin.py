from config import ADMINS, SYRIATEL_CASH_NUMBER, SHAM_CASH_CODE
from database import cursor, conn

def register(bot):

    @bot.callback_query_handler(func=lambda c: c.data.startswith("dep_"))
    def deposit(call):
        _, method, amount = call.data.split("_")
        method_name = "سيرياتيل كاش" if method == "sy" else "شام كاش"

        cursor.execute(
            "INSERT INTO deposits (user_id, amount, method, status) VALUES (?,?,?,?)",
            (call.message.chat.id, amount, method_name, "pending")
        )
        conn.commit()

        info = SYRIATEL_CASH_NUMBER if method == "sy" else SHAM_CASH_CODE
        bot.send_message(call.message.chat.id, f"📲 حوّل على:\n{info}\nثم أرسل صورة التأكيد")

        for admin in ADMINS:
            bot.send_message(admin, f"💰 طلب إيداع\nالمبلغ: {amount}\nالطريقة: {method_name}")
