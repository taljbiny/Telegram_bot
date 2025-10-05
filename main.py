import telebot
from telebot import types
from flask import Flask, request

TOKEN = "8317743306:AAFGH1Acxb6fIwZ0o0T2RvNjezQFW8KWcw8"  # غيّر إذا لزم
ADMIN_ID = 7625893170  # آي دي الأدمن
bot = telebot.TeleBot(TOKEN)
server = Flask(__name__)

# تخزين الجلسات لكل مستخدم
user_sessions = {}

# ====== الأزرار الرئيسية ======
def main_menu_inline():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🆕 إنشاء حساب", callback_data="create_account"),
        types.InlineKeyboardButton("💰 إيداع", callback_data="deposit"),
        types.InlineKeyboardButton("💵 سحب", callback_data="withdraw"),
    )
    markup.add(types.InlineKeyboardButton("📞 الاتصال بالدعم", callback_data="contact_support"))
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

# ====== التعامل مع الضغط على الأزرار ======
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    chat_id = call.message.chat.id
    data = call.data
    bot.answer_callback_query(call.id)

    # الرجوع
    if data == "back":
        user_sessions.pop(chat_id, None)
        try:
            bot.edit_message_text("رجعت للقائمة الرئيسية ✅", chat_id, call.message.message_id, reply_markup=main_menu_inline())
        except:
            bot.send_message(chat_id, "رجعت للقائمة الرئيسية ✅", reply_markup=main_menu_inline())

    # إنشاء حساب
    elif data == "create_account":
        msg = bot.send_message(chat_id, "📛 أرسل اسم الحساب:", reply_markup=back_markup())
        bot.register_next_step_handler(msg, process_account_name)

    # إيداع
    elif data == "deposit":
        msg = bot.send_message(chat_id, "📛 أرسل اسم حسابك:", reply_markup=back_markup())
        bot.register_next_step_handler(msg, process_deposit_name)

    # سحب
    elif data == "withdraw":
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("📲 سيرياتيل كاش", callback_data="withdraw_sy"),
            types.InlineKeyboardButton("🏦 شام كاش", callback_data="withdraw_sham"),
        )
        markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="back"))
        bot.send_message(chat_id, "اختر طريقة السحب:", reply_markup=markup)

    elif data in ["withdraw_sy", "withdraw_sham"]:
        method = "📲 سيرياتيل كاش" if data=="withdraw_sy" else "🏦 شام كاش"
        msg = bot.send_message(chat_id, "📛 أرسل اسم حسابك للسحب:", reply_markup=back_markup())
        bot.register_next_step_handler(msg, process_withdraw_name, method)

    # الاتصال بالدعم
    elif data == "contact_support":
        msg = bot.send_message(chat_id,
            "الرجاء شرح المشكلة بالتفصيل وسوف يتم الرد عليك بأقرب وقت ممكن 🙏", 
            reply_markup=back_markup())
        bot.register_next_step_handler(msg, process_support_message)

# ====== إنشاء حساب ======
def process_account_name(message):
    chat_id = message.chat.id
    if message.text.strip() == "🔙 رجوع":
        bot.send_message(chat_id, "رجعت للقائمة الرئيسية ✅", reply_markup=main_menu_inline())
        return
    account_name = message.text.strip()
    bot.send_message(ADMIN_ID, f"📥 طلب إنشاء حساب جديد:\nاسم الحساب: {account_name}\nمن المستخدم: {message.from_user.id}", 
                     reply_markup=reply_user_button(message.from_user.id))
    bot.send_message(chat_id, f"✅ تم استلام طلب إنشاء الحساب: {account_name}\nبانتظار رد الادمن.", reply_markup=main_menu_inline())

# ====== إيداع ======
def process_deposit_name(message):
    chat_id = message.chat.id
    if message.text.strip() == "🔙 رجوع":
        bot.send_message(chat_id, "رجعت للقائمة الرئيسية ✅", reply_markup=main_menu_inline())
        return
    account_name = message.text.strip()
    user_sessions[chat_id] = {"account_name": account_name}
    msg = bot.send_message(chat_id, "💵 أدخل المبلغ (أقل عملية 25,000 ل.س):", reply_markup=back_markup())
    bot.register_next_step_handler(msg, process_deposit_amount)

def process_deposit_amount(message):
    chat_id = message.chat.id
    if message.text.strip() == "🔙 رجوع":
        bot.send_message(chat_id, "رجعت للقائمة الرئيسية ✅", reply_markup=main_menu_inline())
        user_sessions.pop(chat_id, None)
        return
    try:
        amount = int(message.text.replace(",", "").replace(".", "").strip())
        if amount < 25000:
            msg = bot.send_message(chat_id, "⚠️ المبلغ يجب أن يكون 25,000 ل.س أو أكثر.\nأعد إدخاله:", reply_markup=back_markup())
            bot.register_next_step_handler(msg, process_deposit_amount)
            return
    except:
        msg = bot.send_message(chat_id, "⚠️ أدخل المبلغ بشكل صحيح:", reply_markup=back_markup())
        bot.register_next_step_handler(msg, process_deposit_amount)
        return

    user_sessions[chat_id]["amount"] = amount
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("📲 سيرياتيل كاش", callback_data="pay_sy"),
        types.InlineKeyboardButton("🏦 شام كاش", callback_data="pay_sham"),
        types.InlineKeyboardButton("💳 حوالة ❌", callback_data="pay_closed"),
        types.InlineKeyboardButton("🔙 رجوع", callback_data="back")
    )
    bot.send_message(chat_id, "اختر طريقة الدفع:", reply_markup=markup)

# ====== معالجة الدفع ======
@bot.callback_query_handler(func=lambda call: call.data in ["pay_sy","pay_sham","pay_closed"])
def handle_payment(call):
    chat_id = call.message.chat.id
    method = "📲 سيرياتيل كاش" if call.data=="pay_sy" else "🏦 شام كاش" if call.data=="pay_sham" else None
    if method is None:
        bot.answer_callback_query(call.id, "❌ هذه الطريقة غير متاحة حالياً.", show_alert=True)
        return
    sess = user_sessions.get(chat_id)
    if not sess:
        bot.send_message(chat_id, "⚠️ انتهت الجلسة. ابدأ من جديد.", reply_markup=main_menu_inline())
        return
    account_name = sess["account_name"]
    amount = sess["amount"]
    prompt = f"💳 أرسل المبلغ إلى:\n{'82492253' if method=='📲 سيرياتيل كاش' else '131efe4fbccd83a811282761222eee69'}\n\nبعد الدفع أرسل صورة تأكيد الدفع."
    msg = bot.send_message(chat_id, prompt, reply_markup=back_markup())
    bot.register_next_step_handler(msg, confirm_payment, account_name, amount, method)

def confirm_payment(message, account_name, amount, method):
    chat_id = message.chat.id
    if message.text.strip() == "🔙 رجوع":
        bot.send_message(chat_id, "رجعت للقائمة الرئيسية ✅", reply_markup=main_menu_inline())
        user_sessions.pop(chat_id, None)
        return
    if message.content_type == "photo":
        bot.send_message(ADMIN_ID, f"📥 عملية إيداع:\nاسم الحساب: {account_name}\nالمبلغ: {amount}\nالطريقة: {method}\nمن المستخدم: {message.from_user.id}", 
                         reply_markup=reply_user_button(message.from_user.id))
        bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption="📸 صورة تأكيد الدفع")
        bot.send_message(chat_id, "✅ تم استلام عملية الإيداع.\nطلبك قيد المعالجة.", reply_markup=main_menu_inline())
        user_sessions.pop(chat_id, None)
    else:
        msg = bot.send_message(chat_id, "⚠️ رجاءً أرسل صورة تأكيد الدفع.", reply_markup=back_markup())
        bot.register_next_step_handler(msg, confirm_payment, account_name, amount, method)

# ====== سحب ======
def process_withdraw_name(message, method):
    chat_id = message.chat.id
    if message.text.strip() == "🔙 رجوع":
        bot.send_message(chat_id, "رجعت للقائمة الرئيسية ✅", reply_markup=main_menu_inline())
        return
    account_name = message.text.strip()
    user_sessions[chat_id] = {"account_name": account_name, "method": method}
    msg = bot.send_message(chat_id, "💵 أرسل المبلغ المطلوب (أقل عملية 25,000 ل.س):", reply_markup=back_markup())
    bot.register_next_step_handler(msg, process_withdraw_amount)

def process_withdraw_amount(message):
    chat_id = message.chat.id
    sess = user_sessions.get(chat_id)
    if not sess:
        bot.send_message(chat_id, "⚠️ انتهت الجلسة. ابدأ من جديد.", reply_markup=main_menu_inline())
        return
    if message.text.strip() == "🔙 رجوع":
        bot.send_message(chat_id, "رجعت للقائمة الرئيسية ✅", reply_markup=main_menu_inline())
        user_sessions.pop(chat_id, None)
        return
    try:
        amount = int(message.text.replace(",", "").replace(".", "").strip())
        if amount < 25000:
            msg = bot.send_message(chat_id, "⚠️ المبلغ يجب أن يكون 25,000 ل.س أو أكثر.\nأعد إدخاله:", reply_markup=back_markup())
            bot.register_next_step_handler(msg, process_withdraw_amount)
            return
    except:
        msg = bot.send_message(chat_id, "⚠️ أدخل المبلغ بشكل صحيح:", reply_markup=back_markup())
        bot.register_next_step_handler(msg, process_withdraw_amount)
        return

    sess["amount"] = amount
    prompt = "📲 أرسل رقم/كود المحفظة المراد استلام المبلغ عليها:"
    msg = bot.send_message(chat_id, prompt, reply_markup=back_markup())
    bot.register_next_step_handler(msg, confirm_withdraw)

def confirm_withdraw(message):
    chat_id = message.chat.id
    sess = user_sessions.get(chat_id)
    if not sess:
        bot.send_message(chat_id, "⚠️ انتهت الجلسة. ابدأ من جديد.", reply_markup=main_menu_inline())
        return
    if message.text.strip() == "🔙 رجوع":
        bot.send_message(chat_id, "رجعت للقائمة الرئيسية ✅", reply_markup=main_menu_inline())
        user_sessions.pop(chat_id, None)
        return
    wallet = message.text.strip()
    bot.send_message(ADMIN_ID,
        f"📥 طلب سحب:\nطريقة السحب: {sess['method']}\nاسم الحساب: {sess['account_name']}\nالمبلغ: {sess['amount']}\nرقم/كود المحفظة: {wallet}\nمن المستخدم: {message.from_user.id}",
        reply_markup=reply_user_button(message.from_user.id))
    bot.send_message(chat_id, "✅ تم استلام طلب السحب.\nطلبك قيد المعالجة، عند الانتهاء سنرسل لك تأكيد العملية.", reply_markup=main_menu_inline())
    user_sessions.pop(chat_id, None)

# ====== دعم العملاء ======
def process_support_message(message):
    chat_id = message.chat.id
    if message.text.strip() == "🔙 رجوع":
        bot.send_message(chat_id, "رجعت للقائمة الرئيسية ✅", reply_markup=main_menu_inline())
        return
    # تحويل الرسالة للأدمن
    if message.content_type == "photo":
        bot.send_photo(ADMIN_ID, message.photo[-1].file_id,
            caption=f"📥 رسالة دعم من {message.from_user.id}", 
            reply_markup=reply_user_button(message.from_user.id, support=True))
    else:
        bot.send_message(ADMIN_ID, f"📥 رسالة دعم من {message.from_user.id}:\n{message.text}", 
                         reply_markup=reply_user_button(message.from_user.id, support=True))
    bot.send_message(chat_id, "✅ تم إرسال رسالتك للدعم، سيتم الرد عليك قريباً.", reply_markup=main_menu_inline())

# ====== زر الرد على المستخدم للأدمن ======
def reply_user_button(user_id, support=False):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📩 الرد على المستخدم", callback_data=f"reply_{user_id}_{'support' if support else 'other'}"))
    return markup

@bot.callback_query_handler(func=lambda call: call.data.startswith("reply_"))
def handle_admin_reply(call):
    data = call.data.split("_")
    user_id = int(data[1])
    is_support = data[2]=="support"
    chat_id = call.message.chat.id
    bot.answer_callback_query(call.id)
    msg = bot.send_message(chat_id, "✍️ أرسل الرد ليتم إرساله للمستخدم:")
    bot.register_next_step_handler(msg, send_admin_reply, user_id, is_support)

def send_admin_reply(message, user_id, is_support):
    text = message.text
    if is_support:
        text = f"💬 **رد من الدعم الفني:**\n{text}"
    bot.send_message(user_id, text)
    bot.send_message(message.chat.id, "✅ تم إرسال ردك للمستخدم بنجاح.")

# ====== Webhook مع Render ======
from flask import Flask, request
@server.route('/' + TOKEN, methods=['POST'])
def getMessage():
    json_str = request.get_data().decode('UTF-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "!", 200

@server.route("/")
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url="https://telegram-bot-xsto.onrender.com/" + TOKEN)
    return "!", 200

if __name__ == "__main__":
    server.run(host="0.0.0.0", port=10000)
