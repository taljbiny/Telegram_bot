import telebot
from telebot import types
from flask import Flask, request

# ====== الإعدادات ======
TOKEN = "8317743306:AAFGH1Acxb6fIwZ0o0T2RvNjezQFW8KWcw8"  # غيّر إذا لزم
ADMIN_ID = 7625893170  # غيّر إلى آي دي الأدمن لو مختلف
bot = telebot.TeleBot(TOKEN)
server = Flask(__name__)

# ====== جلسات المستخدم المؤقتة ======
# يخزن بيانات مؤقتة مثل account_name و amount لكل محادثة
user_sessions = {}

# ====== تواقيع الأزرار ======
def main_menu_inline():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🆕 إنشاء حساب", callback_data="create_account"),
        types.InlineKeyboardButton("💰 إيداع", callback_data="deposit"),
        types.InlineKeyboardButton("💵 سحب", callback_data="withdraw"),
        types.InlineKeyboardButton("📞 الاتصال بالدعم", callback_data="contact_support"),
    )
    return markup

def back_markup():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="back"))
    return markup

# ====== /start ======
@bot.message_handler(commands=['start'])
def send_welcome(message):
    text = (
        "أهلاً بك 👋\n"
        "اختر من الأزرار أدناه:\n\n"
        "🌐 موقعنا: https://www.55bets.net/ar/ألعاب/slots/247\n"
        "📘 صفحتنا على فيسبوك (للتواصل أو الدعم): https://www.facebook.com/share/16Atgg9Agk/"
    )
    bot.send_message(message.chat.id, text, reply_markup=main_menu_inline())

# ====== معالجة نقرات الأزرار (Callbacks) ======
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    chat_id = call.message.chat.id
    data = call.data

    # أزل انتظار التحميل
    bot.answer_callback_query(call.id)

    if data == "back":
        # احذف أي جلسة مفتوحة للمستخدم
        user_sessions.pop(chat_id, None)
        try:
            bot.edit_message_text(
                "رجعت للقائمة الرئيسية ✅",
                chat_id,
                call.message.message_id,
                reply_markup=main_menu_inline()
            )
        except:
            bot.send_message(chat_id, "رجعت للقائمة الرئيسية ✅", reply_markup=main_menu_inline())

    elif data == "create_account":
        msg = bot.send_message(chat_id, "📛 أرسل اسم الحساب:", reply_markup=back_markup())
        bot.register_next_step_handler(msg, process_account_name)

    elif data == "deposit":
        msg = bot.send_message(chat_id, "📛 أرسل اسم حسابك:", reply_markup=back_markup())
        bot.register_next_step_handler(msg, process_deposit_name)

    elif data == "withdraw":
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("📲 سيرياتيل كاش", callback_data="withdraw_sy"),
            types.InlineKeyboardButton("🏦 شام كاش (مغلق)", callback_data="withdraw_closed"),
        )
        markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="back"))
        bot.send_message(chat_id, "اختر طريقة السحب:", reply_markup=markup)

    elif data == "withdraw_closed":
        bot.answer_callback_query(call.id, "❌ هذه الطريقة غير متاحة حالياً.", show_alert=True)

    elif data == "withdraw_sy":
        msg = bot.send_message(chat_id, "📛 أرسل اسم حسابك للسحب:", reply_markup=back_markup())
        bot.register_next_step_handler(msg, process_withdraw_name, "📲 سيرياتيل كاش")

    elif data == "contact_support":
        # رد تلقائي للمستخدم
        auto_text = (
            "الرجاء شرح المشكلة بلتفصيل وسوف يتم الرد عليك بأقرب وقت ممكن\n\n"
            "شكراً لانتظارنا"
        )
        bot.send_message(chat_id, auto_text, reply_markup=main_menu_inline())

        # إخطار الأدمن مع تعليمات للرد عبر الأمر /reply
        username = call.from_user.username or "—"
        bot.send_message(
            ADMIN_ID,
            f"📞 طلب دعم جديد:\n"
            f"المستخدم: {call.from_user.id} (username: @{username})\n\n"
            f"لمعالجة الطلب استخدم:\n/reply {call.from_user.id} رسالتك"
        )

    elif data == "pay_closed":
        bot.answer_callback_query(call.id, "❌ هذه الطريقة غير متاحة حالياً.", show_alert=True)

    elif data == "pay_sy":
        # احصل على بيانات الجلسة
        sess = user_sessions.get(chat_id)
        if not sess or "account_name" not in sess or "amount" not in sess:
            bot.send_message(chat_id, "⚠️ انتهت الجلسة أو لم تحدد الاسم/المبلغ. ابدأ مرة أخرى.", reply_markup=main_menu_inline())
            user_sessions.pop(chat_id, None)
            return

        account_name = sess["account_name"]
        amount = sess["amount"]

        msg = bot.send_message(
            chat_id,
            "💳 أرسل المبلغ إلى الرقم التالي:\n📱 82492253\n\nبعد الدفع أرسل صورة تأكيد الدفع.\n(يُفضّل أن تظهر في الصورة: المبلغ، رقم المحفظة، و/أو رقم العملية أو إيصال التحويل).",
            reply_markup=back_markup()
        )
        bot.register_next_step_handler(msg, confirm_payment, account_name, amount, "📲 سيرياتيل كاش")

# ====== إنشاء حساب ======
def process_account_name(message):
    chat_id = message.chat.id
    # دعم زر الرجوع كتابة يدوياً (لو كتب المستخدم)
    if message.text and message.text.strip() == "🔙 رجوع":
        bot.send_message(chat_id, "رجعت للقائمة الرئيسية ✅", reply_markup=main_menu_inline())
        user_sessions.pop(chat_id, None)
        return

    account_name = message.text.strip()
    bot.send_message(
        ADMIN_ID,
        f"📥 طلب إنشاء حساب جديد:\nاسم الحساب: {account_name}\nمن المستخدم: {message.from_user.id}"
    )
    bot.send_message(message.chat.id, f"✅ تم استلام طلب إنشاء الحساب: {account_name}\nبانتظار رد الادمن.", reply_markup=main_menu_inline())

# ====== إيداع ======
def process_deposit_name(message):
    chat_id = message.chat.id
    if message.text and message.text.strip() == "🔙 رجوع":
        bot.send_message(chat_id, "رجعت للقائمة الرئيسية ✅", reply_markup=main_menu_inline())
        user_sessions.pop(chat_id, None)
        return

    account_name = message.text.strip()
    # خزّن الاسم في الجلسة
    user_sessions[chat_id] = {"account_name": account_name}
    msg = bot.send_message(chat_id, "💵 أدخل المبلغ (أقل عملية 25,000 ل.س):", reply_markup=back_markup())
    bot.register_next_step_handler(msg, process_deposit_amount)

def process_deposit_amount(message):
    chat_id = message.chat.id
    if message.text and message.text.strip() == "🔙 رجوع":
        bot.send_message(chat_id, "رجعت للقائمة الرئيسية ✅", reply_markup=main_menu_inline())
        user_sessions.pop(chat_id, None)
        return

    try:
        amount = int(message.text.replace(",", "").replace(".", "").strip())
        if amount < 25000:
            msg = bot.send_message(chat_id, "⚠️ المبلغ يجب أن يكون 25,000 ل.س أو أكثر.\nأدخل المبلغ من جديد:", reply_markup=back_markup())
            return bot.register_next_step_handler(msg, process_deposit_amount)
    except:
        msg = bot.send_message(chat_id, "⚠️ رجاءً أدخل المبلغ بشكل صحيح:", reply_markup=back_markup())
        return bot.register_next_step_handler(msg, process_deposit_amount)

    # خزّن المبلغ أيضاً في الجلسة
    if chat_id not in user_sessions:
        user_sessions[chat_id] = {}
    user_sessions[chat_id]["amount"] = amount

    # أظهر طرق الدفع (نستخدم callback pay_sy)
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📲 سيرياتيل كاش", callback_data="pay_sy"))
    markup.add(types.InlineKeyboardButton("🏦 شام كاش ❌", callback_data="pay_closed"))
    markup.add(types.InlineKeyboardButton("💳 حوالة ❌", callback_data="pay_closed"))
    markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="back"))

    bot.send_message(chat_id, "اختر طريقة الدفع:", reply_markup=markup)

def confirm_payment(message, account_name, amount, method):
    chat_id = message.chat.id
    # السماح للرجوع كتابياً
    if message.text and message.text.strip() == "🔙 رجوع":
        bot.send_message(chat_id, "رجعت للقائمة الرئيسية ✅", reply_markup=main_menu_inline())
        user_sessions.pop(chat_id, None)
        return

    if message.content_type == "photo":
        bot.send_message(
            ADMIN_ID,
            f"📥 عملية إيداع:\nاسم الحساب: {account_name}\nالمبلغ: {amount}\nالطريقة: {method}\nمن المستخدم: {message.from_user.id}"
        )
        bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption="📸 صورة تأكيد الدفع")
        bot.send_message(chat_id, "✅ تم استلام عملية الإيداع.\nطلبك قيد المعالجة.", reply_markup=main_menu_inline())
        user_sessions.pop(chat_id, None)
    else:
        msg = bot.send_message(chat_id, "⚠️ رجاءً أرسل **صورة** تأكيد الدفع (يجب أن تظهر فيها المبلغ ورقم المحفظة/الكود).", reply_markup=back_markup())
        bot.register_next_step_handler(msg, confirm_payment, account_name, amount, method)

# ====== سحب ======
def process_withdraw_name(message, method):
    chat_id = message.chat.id
    if message.text and message.text.strip() == "🔙 رجوع":
        bot.send_message(chat_id, "رجعت للقائمة الرئيسية ✅", reply_markup=main_menu_inline())
        user_sessions.pop(chat_id, None)
        return

    account_name = message.text.strip()
    # خزّن الاسم والطريقة
    user_sessions[chat_id] = {"account_name": account_name, "method": method}
    msg = bot.send_message(chat_id, "💵 أرسل المبلغ المطلوب (أقل عملية 25,000 ل.س):", reply_markup=back_markup())
    bot.register_next_step_handler(msg, process_withdraw_amount)

def process_withdraw_amount(message):
    chat_id = message.chat.id
    if message.text and message.text.strip() == "🔙 رجوع":
        bot.send_message(chat_id, "رجعت للقائمة الرئيسية ✅", reply_markup=main_menu_inline())
        user_sessions.pop(chat_id, None)
        return

    try:
        amount = int(message.text.replace(",", "").replace(".", "").strip())
        if amount < 25000:
            msg = bot.send_message(chat_id, "⚠️ المبلغ يجب أن يكون 25,000 ل.س أو أكثر.\nأدخل المبلغ من جديد:", reply_markup=back_markup())
            return bot.register_next_step_handler(msg, process_withdraw_amount)
    except:
        msg = bot.send_message(chat_id, "⚠️ رجاءً أدخل المبلغ بشكل صحيح:", reply_markup=back_markup())
        return bot.register_next_step_handler(msg, process_withdraw_amount)

    sess = user_sessions.get(chat_id, {})
    account_name = sess.get("account_name", "غير معروف")
    method = sess.get("method", "غير محدد")

    user_sessions[chat_id]["amount"] = amount

    # نص توجيهي حسب الطريقة
    if method == "📲 سيرياتيل كاش":
        prompt = (
            "📲 الآن أرسل **رقم/كود محفظة سيرياتيل كاش** الذي تريد استلام المبلغ عليه.\n\n"
            "مثال: 82492253\n"
            "▪️ اكتب فقط الأرقام (بدون كلمات إضافية أو رموز).\n"
            "▪️ تأكد من أن الرقم صحيح لتصلك الحوالة."
        )
    else:
        prompt = (
            "🏦 الآن أرسل **كود محفظة شام كاش** الذي تريد استلام المبلغ عليه.\n\n"
            "مثال: 131efe4fbccd83a811282761222eee69\n"
            "▪️ انسخ الكود تماماً كما هو (حساس للحروف والأرقام).\n"
            "▪️ اكتب فقط الكود بدون نص إضافي."
        )

    msg = bot.send_message(chat_id, prompt, reply_markup=back_markup())
    bot.register_next_step_handler(msg, confirm_withdraw)

def confirm_withdraw(message):
    chat_id = message.chat.id
    if message.text and message.text.strip() == "🔙 رجوع":
        bot.send_message(chat_id, "رجعت للقائمة الرئيسية ✅", reply_markup=main_menu_inline())
        user_sessions.pop(chat_id, None)
        return

    wallet = message.text.strip()
    sess = user_sessions.get(chat_id, {})
    account_name = sess.get("account_name", "غير معروف")
    amount = sess.get("amount", 0)
    method = sess.get("method", "غير محدد")

    bot.send_message(
        ADMIN_ID,
        f"📥 طلب سحب:\nطريقة السحب: {method}\n"
        f"اسم الحساب: {account_name}\nالمبلغ: {amount}\n"
        f"رقم/كود المحفظة: {wallet}\nمن المستخدم: {message.from_user.id}"
    )
    bot.send_message(chat_id, "✅ تم استلام طلب السحب.\nطلبك قيد المعالجة، عند الانتهاء سنرسل لك تأكيد العملية.", reply_markup=main_menu_inline())
    user_sessions.pop(chat_id, None)

# ====== رد الأدمن عبر الأمر /reply ======
@bot.message_handler(commands=['reply'])
def reply_user(message):
    try:
        parts = message.text.split(" ", 2)
        user_id = int(parts[1])
        reply_text = parts[2]
        bot.send_message(user_id, f"{reply_text}")
        bot.send_message(message.chat.id, "✅ تم إرسال الرد.")
    except:
        bot.send_message(message.chat.id, "⚠️ الصيغة غير صحيحة.\nاكتب: /reply user_id الرسالة")

# ====== Webhook مع Render ======
@server.route('/' + TOKEN, methods=['POST'])
def getMessage():
    json_str = request.get_data().decode('UTF-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "!", 200

@server.route("/")
def webhook():
    bot.remove_webhook()
    # غيّر الرابط هنا إلى رابط مشروعك على Render (مثال)
    bot.set_webhook(url="https://telegram-bot-xsto.onrender.com/" + TOKEN)
    return "!", 200

if __name__ == "__main__":
    server.run(host="0.0.0.0", port=10000)
