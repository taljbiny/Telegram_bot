from telebot import types
from database import get_connection
from config import ADMINS, MIN_DEPOSIT, MIN_WITHDRAW, WITHDRAW_COMMISSION

active_process = {}  # لتتبع خطوات العملية لكل مستخدم

def user_handlers(bot):

    @bot.message_handler(commands=['start'])
    def start(message):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("INSERT OR IGNORE INTO users (telegram_id, username) VALUES (?, ?)",
                    (message.from_user.id, message.from_user.username))
        conn.commit()
        conn.close()

        # أزرار رئيسية للمستخدم
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

        # أزرار سفلية ثابتة
        reply_kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        reply_kb.add("تشغيل البوت", "عرض الرصيد", "المساعدة / الاتصال بالدعم")

        bot.send_message(message.chat.id, "أهلاً بك 👋\nاختر من الخيارات:", reply_markup=kb)

    @bot.callback_query_handler(func=lambda call: True)
    def callback_handler(call):
        user_id = call.from_user.id
        if call.data == "create_account":
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("SELECT account_name FROM users WHERE telegram_id=?", (user_id,))
            result = cur.fetchone()
            conn.close()
            if result and result[0]:
                bot.answer_callback_query(call.id, "لقد أنشأت حساب مسبقاً.")
                bot.send_message(call.message.chat.id, "⚠️ لديك حساب بالفعل ولا يمكنك إنشاء آخر.")
                return
            bot.answer_callback_query(call.id)
            msg = bot.send_message(call.message.chat.id, "📌 أدخل اسم الحساب:")
            bot.register_next_step_handler(msg, process_account_name)

        elif call.data in ["deposit", "withdraw", "bot_deposit", "bot_withdraw"]:
            start_transaction(bot, call.message.chat.id, user_id, call.data)

        elif call.data == "support":
            msg = bot.send_message(call.message.chat.id,
                                   "يرجى مشاركة جهة اتصالك لتسهيل التواصل مع الدعم:",
                                   reply_markup=contact_button())
            bot.register_next_step_handler(msg, receive_contact)

    # إنشاء الحساب
    def process_account_name(message):
        user_id = message.from_user.id
        active_process[user_id] = {"step": "account_name", "account_name": message.text}
        msg = bot.send_message(message.chat.id, "📌 أدخل كلمة السر:")
        bot.register_next_step_handler(msg, process_password)

    def process_password(message):
        user_id = message.from_user.id
        active_process[user_id]["password"] = message.text
        # إرسال للأدمن
        account_name = active_process[user_id]["account_name"]
        password = active_process[user_id]["password"]
        bot.send_message(ADMINS[0], f"🔔 طلب إنشاء حساب جديد\nUser: {message.from_user.username}\nاسم الحساب: {account_name}\nكلمة السر: {password}\nيمكنك الرد على المستخدم عند الضرورة.")
        # حفظ البيانات
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("UPDATE users SET account_name=?, password=? WHERE telegram_id=?",
                    (account_name, password, user_id))
        conn.commit()
        conn.close()
        bot.send_message(message.chat.id, "✅ تم إنشاء الحساب بنجاح.")
        del active_process[user_id]

    # زر مشاركة جهة الاتصال
    def contact_button():
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        kb.add(types.KeyboardButton("مشاركة جهة الاتصال", request_contact=True))
        return kb

    def receive_contact(message):
        user_id = message.from_user.id
        if message.contact:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("INSERT INTO support_requests(user_id, contact_shared, message) VALUES (?, ?, ?)",
                        (user_id, 1, "طلب دعم"))
            conn.commit()
            conn.close()
            bot.send_message(message.chat.id, "✅ تم إرسال جهة الاتصال إلى الدعم، سيتم الرد عليك قريباً.")
        else:
            bot.send_message(message.chat.id, "❌ يجب مشاركة جهة الاتصال لتواصل الدعم.")

    # بدء أي معاملة
    def start_transaction(bot, chat_id, user_id, trans_type):
        active_process[user_id] = {"step": "choose_wallet", "type": trans_type}
        kb = types.InlineKeyboardMarkup(row_width=2)
        kb.add(
            types.InlineKeyboardButton("سيرياتيل", callback_data="wallet_syriatel"),
            types.InlineKeyboardButton("شام", callback_data="wallet_sham"),
            types.InlineKeyboardButton("إلغاء العملية", callback_data="cancel_process")
        )
        bot.send_message(chat_id, "اختر المحفظة:", reply_markup=kb)
