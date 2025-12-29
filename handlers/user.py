from telebot import types
from database import get_connection

def user_handlers(bot):

    @bot.message_handler(commands=['start'])
    def start(message):
        conn = get_connection()
        cur = conn.cursor()
        # إضافة المستخدم الجديد
        cur.execute(
            "INSERT OR IGNORE INTO users (telegram_id, username) VALUES (?, ?)",
            (message.from_user.id, message.from_user.username)
        )
        conn.commit()
        conn.close()

        kb = types.InlineKeyboardMarkup(row_width=2)
        kb.add(
            types.InlineKeyboardButton("➕ إنشاء حساب", callback_data="create_account"),
            types.InlineKeyboardButton("💰 شحن", callback_data="deposit"),
            types.InlineKeyboardButton("➖ سحب", callback_data="withdraw")
        )
        kb.add(
            types.InlineKeyboardButton("💵 شحن البوت", callback_data="bot_deposit"),
            types.InlineKeyboardButton("💸 سحب من البوت", callback_data="bot_withdraw"),
            types.InlineKeyboardButton("🛠 الدعم", callback_data="support")
        )

        bot.send_message(message.chat.id, "أهلاً بك 👋\nاختر من الخيارات:", reply_markup=kb)

    @bot.callback_query_handler(func=lambda call: True)
    def callback_handler(call):
        if call.data == "create_account":
            bot.answer_callback_query(call.id, "ميزة إنشاء الحساب")
            bot.send_message(call.message.chat.id, "⚡ تم اختيار إنشاء حساب")
        elif call.data == "deposit":
            bot.answer_callback_query(call.id, "ميزة الشحن")
            bot.send_message(call.message.chat.id, "💰 اختر طريقة الشحن: سيرياتيل / شام")
        elif call.data == "withdraw":
            bot.answer_callback_query(call.id, "ميزة السحب")
            bot.send_message(call.message.chat.id, "➖ اختر المبلغ للسحب")
        elif call.data == "bot_deposit":
            bot.answer_callback_query(call.id, "شحن البوت")
            bot.send_message(call.message.chat.id, "💵 شحن رصيد البوت")
        elif call.data == "bot_withdraw":
            bot.answer_callback_query(call.id, "سحب من البوت")
            bot.send_message(call.message.chat.id, "💸 سحب رصيد من البوت")
        elif call.data == "support":
            bot.answer_callback_query(call.id, "الدعم")
            bot.send_message(call.message.chat.id, "🛠 للتواصل مع الدعم يرجى إرسال رسالة هنا")
