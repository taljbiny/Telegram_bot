# main.py
"""
Bot Telegram webhook version (Flask) - final
Usage:
  - ضع توكن البوت الخاص بك في المتغير TOKEN أدناه.
  - اضف متغير بيئة WEBHOOK_URL في إعدادات Render (أو استخدم رابط HTTPS العام)
    مثال WEBHOOK_URL = "https://your-app.onrender.com"
  - عند التشغيل، سيقوم البوت بتسجيل webhook على: <WEBHOOK_URL>/<TOKEN>
  - Install: pip install -r requirements.txt
  - requirements.txt must include: pyTelegramBotAPI, Flask, gunicorn
"""

import os
import re
from flask import Flask, request, abort
import telebot
from telebot import types

# ========== إعدادات (ضع التوكن هنا) ==========
TOKEN = "8317743306:AAFGH1Acxb6fIwZ0o0T2RvNjezQFW8KWcw8"   # <-- **ضع هنا توكن البوت** (مثال: 8317...:AA...)
ADMIN_ID = 7625893170               # <-- رقم الأدمن (عدلي إن بدك)
SERIATEL_CASH_CODE = "82492253"     # كود سيرياتيل كما طلبت
SHAM_CASH_CODE = "131efe4fbccd83a811282761222eee69"  # كود شام كاش

# اقرأ رابط الويب هوك من متغير بيئة (إلزامي على Render)
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")  # مثال: https://my-app.onrender.com
if not WEBHOOK_URL:
    # نسمح بتشغيل محلي لعمل اختبار إذا رغبت (لكن webhook يحتاج URL عام)
    print("Warning: WEBHOOK_URL not set. Webhook won't be registered. Set WEBHOOK_URL env var on Render.")
    # لا نقوم بعمل abort لأن ممكن تريد تشغيل محليًا (لكن webhook لن يعمل)

# =================================================
bot = telebot.TeleBot(TOKEN, threaded=True)
app = Flask(__name__)

# تخزين مؤقت بالذاكرة (استبدله بقاعدة بيانات في الإنتاج)
user_states = {}    # user_id -> state dict
user_accounts = {}  # user_id -> account_name

# ---------- أدوات مساعدة ----------
def set_state(uid, **kwargs):
    user_states[uid] = user_states.get(uid, {})
    user_states[uid].update(kwargs)

def get_state(uid):
    return user_states.get(uid, {})

def clear_state(uid):
    if uid in user_states:
        del user_states[uid]

def main_keyboard():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(types.KeyboardButton("إنشاء حساب"),
           types.KeyboardButton("إيداع"),
           types.KeyboardButton("سحب"),
           types.KeyboardButton("حذف الحساب"))
    return kb

# ---------- Flask route for webhook ----------
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    # Telegram will post updates here
    if request.headers.get("content-type") == "application/json":
        json_str = request.get_data().decode("utf-8")
        update = telebot.types.Update.de_json(json_str)
        bot.process_new_updates([update])
        return "", 200
    else:
        abort(403)

# ---------- Register /start ----------
@bot.message_handler(commands=["start", "home"])
def cmd_start(msg):
    clear_state(msg.from_user.id)
    bot.send_message(msg.chat.id, "أهلاً! اختار العملية:", reply_markup=main_keyboard())

# ---------- إنشاء حساب ----------
@bot.message_handler(func=lambda m: m.text == "إنشاء حساب")
def create_account_start(msg):
    if msg.from_user.id in user_accounts:
        bot.send_message(msg.chat.id, "⚠️ لديك حساب بالفعل. إن أردت حذفه استخدم 'حذف الحساب'.", reply_markup=main_keyboard())
        return
    set_state(msg.from_user.id, flow="create_account", step="ask_name")
    bot.send_message(msg.chat.id, "📝 أرسل اسم الحساب الذي تريد إنشاؤه:")

@bot.message_handler(func=lambda m: get_state(m.from_user.id).get("flow") == "create_account")
def create_account_process(msg):
    st = get_state(msg.from_user.id)
    if st.get("step") == "ask_name":
        account_name = msg.text.strip()
        user_accounts[msg.from_user.id] = account_name
        clear_state(msg.from_user.id)
        bot.send_message(msg.chat.id, f"✅ تم إنشاء الحساب باسم: {account_name}", reply_markup=main_keyboard())
        bot.send_message(ADMIN_ID,
                         f"👤 مستخدم جديد أنشأ حساباً\nUserID: {msg.from_user.id}\n"
                         f"اسم الحساب: {account_name}\n\n"
                         f"(رد على هذه الرسالة لإرسال رد للمستخدم)")
        
# ---------- إيداع ----------
@bot.message_handler(func=lambda m: m.text == "إيداع")
def deposit_start(msg):
    if msg.from_user.id not in user_accounts:
        bot.send_message(msg.chat.id, "⚠️ لا يوجد حساب. أنشئ حساب أولاً.", reply_markup=main_keyboard())
        return
    set_state(msg.from_user.id, flow="deposit", step="ask_amount")
    bot.send_message(msg.chat.id, "💰 أرسل المبلغ الذي تريد إيداعه:")

@bot.message_handler(func=lambda m: get_state(m.from_user.id).get("flow") == "deposit" and get_state(m.from_user.id).get("step") == "ask_amount")
def deposit_amount(msg):
    try:
        amount = float(msg.text.strip())
    except:
        bot.send_message(msg.chat.id, "❗ الرجاء إدخال مبلغ رقمي صالح.")
        return
    set_state(msg.from_user.id, flow="deposit", step="ask_method", amount=amount)
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(types.KeyboardButton("سيرياتيل كاش"), types.KeyboardButton("شام كاش"))
    bot.send_message(msg.chat.id, "اختر طريقة الدفع:", reply_markup=kb)

@bot.message_handler(func=lambda m: get_state(m.from_user.id).get("flow") == "deposit" and get_state(m.from_user.id).get("step") == "ask_method")
def deposit_method(msg):
    method = msg.text.strip()
    if method not in ["سيرياتيل كاش", "شام كاش"]:
        bot.send_message(msg.chat.id, "❗ اختر أحد الأزرار المتاحة.")
        return
    set_state(msg.from_user.id, flow="deposit", step="ask_code", method=method)
    code = SERIATEL_CASH_CODE if method == "سيرياتيل كاش" else SHAM_CASH_CODE
    bot.send_message(msg.chat.id,
                     f"📲 حول المبلغ ({get_state(msg.from_user.id)['amount']}) إلى {method}\n"
                     f"كود المحفظة: {code}\n\n"
                     f"بعد التحويل أرسل رقم الشحن / كود العملية هنا:")

@bot.message_handler(func=lambda m: get_state(m.from_user.id).get("flow") == "deposit" and get_state(m.from_user.id).get("step") == "ask_code")
def deposit_code(msg):
    st = get_state(msg.from_user.id)
    account = user_accounts.get(msg.from_user.id, "—")
    code_sent = msg.text.strip()
    admin_text = (
        f"📥 طلب إيداع جديد\n"
        f"👤 المستخدم: {msg.from_user.username or msg.from_user.full_name}\n"
        f"🆔 UserID: {msg.from_user.id}\n"
        f"📛 الحساب: {account}\n"
        f"💰 المبلغ: {st.get('amount')}\n"
        f"💳 الطريقة: {st.get('method')}\n"
        f"🔢 رقم الشحن/الكود المرسل: {code_sent}\n\n"
        f"رد على هذه الرسالة لإرسال رد للمستخدم."
    )
    bot.send_message(ADMIN_ID, admin_text)
    bot.send_message(msg.chat.id, "✅ تم إرسال طلب الإيداع للإدارة للمراجعة.", reply_markup=main_keyboard())
    clear_state(msg.from_user.id)

# ---------- سحب ----------
@bot.message_handler(func=lambda m: m.text == "سحب")
def withdraw_start(msg):
    if msg.from_user.id not in user_accounts:
        bot.send_message(msg.chat.id, "⚠️ لا يوجد حساب لديك. أنشئ حساب أولاً.", reply_markup=main_keyboard())
        return
    set_state(msg.from_user.id, flow="withdraw", step="ask_amount")
    bot.send_message(msg.chat.id, "💵 أرسل المبلغ الذي تريد سحبه:")

@bot.message_handler(func=lambda m: get_state(m.from_user.id).get("flow") == "withdraw" and get_state(m.from_user.id).get("step") == "ask_amount")
def withdraw_amount(msg):
    try:
        amount = float(msg.text.strip())
    except:
        bot.send_message(msg.chat.id, "❗ الرجاء إدخال مبلغ رقمي صالح.")
        return
    set_state(msg.from_user.id, flow="withdraw", step="ask_wallet", amount=amount)
    bot.send_message(msg.chat.id, "📲 أرسل رقم/كود المحفظة التي تريد استلام المبلغ عليها:")

@bot.message_handler(func=lambda m: get_state(m.from_user.id).get("flow") == "withdraw" and get_state(m.from_user.id).get("step") == "ask_wallet")
def withdraw_wallet(msg):
    st = get_state(msg.from_user.id)
    account = user_accounts.get(msg.from_user.id, "—")
    admin_text = (
        f"📤 طلب سحب\n"
        f"👤 المستخدم: {msg.from_user.username or msg.from_user.full_name}\n"
        f"🆔 UserID: {msg.from_user.id}\n"
        f"📛 الحساب: {account}\n"
        f"💰 المبلغ: {st.get('amount')}\n"
        f"🔢 تفاصيل المحفظة: {msg.text.strip()}\n\n"
        f"رد على هذه الرسالة لإرسال رد للمستخدم."
    )
    bot.send_message(ADMIN_ID, admin_text)
    bot.send_message(msg.chat.id, "✅ تم إرسال طلب السحب للإدارة.", reply_markup=main_keyboard())
    clear_state(msg.from_user.id)

# ---------- حذف الحساب ----------
@bot.message_handler(func=lambda m: m.text == "حذف الحساب")
def delete_account_request(msg):
    if msg.from_user.id not in user_accounts:
        bot.send_message(msg.chat.id, "❗ لا يوجد حساب لحذفه.", reply_markup=main_keyboard())
        return
    set_state(msg.from_user.id, flow="delete", step="confirm")
    bot.send_message(msg.chat.id, "⚠️ هل أنت متأكد من حذف الحساب؟ أرسل: نعم أو لا")

@bot.message_handler(func=lambda m: get_state(m.from_user.id).get("flow") == "delete" and get_state(m.from_user.id).get("step") == "confirm")
def confirm_delete(msg):
    if msg.text.strip().lower() == "نعم":
        account = user_accounts.get(msg.from_user.id, "—")
        bot.send_message(msg.chat.id, "📨 تم إرسال طلب حذف الحساب للإدارة، بانتظار القرار.")
        bot.send_message(ADMIN_ID,
                         f"🗑️ طلب حذف حساب\n"
                         f"👤 المستخدم: {msg.from_user.username or msg.from_user.full_name}\n"
                         f"🆔 UserID: {msg.from_user.id}\n"
                         f"📛 الحساب: {account}\n\n"
                         f"رد بـ 'موافقة' أو 'رفض' على هذه الرسالة.")
        clear_state(msg.from_user.id)
    else:
        bot.send_message(msg.chat.id, "❌ تم إلغاء طلب الحذف.", reply_markup=main_keyboard())
        clear_state(msg.from_user.id)

# ---------- استقبال صور/ملفات إثبات (عمليات الإيداع لو أردت) ----------
@bot.message_handler(content_types=['photo', 'document'])
def handle_media(msg):
    # إذا المستخدم كان بمرحلة ما نريد التعامل معه كـ proof للإيداع:
    st = get_state(msg.from_user.id)
    if st.get("flow") == "deposit" and st.get("step") in ("await_proof", "ask_code"):
        # في هذه النسخة نعتبر أن المستخدم أرسل إثباتًا بدلاً من كود نصي
        account = user_accounts.get(msg.from_user.id, "—")
        amount = st.get("amount")
        method = st.get("method")
        admin_caption = (
            f"📥 إثبات إيداع وصل\n"
            f"👤 المستخدم: {msg.from_user.username or msg.from_user.full_name}\n"
            f"🆔 UserID: {msg.from_user.id}\n"
            f"📛 الحساب: {account}\n"
            f"💰 المبلغ: {amount}\n"
            f"💳 الطريقة: {method}\n\n"
            f"رد على هذه الرسالة لإرسال رد للمستخدم."
        )
        # أرسل النص ثم الملف للأدمن
        bot.send_message(ADMIN_ID, admin_caption)
        try:
            if msg.content_type == 'photo':
                file_id = msg.photo[-1].file_id
                bot.send_photo(ADMIN_ID, file_id, caption="إثبات من المستخدم")
            else:
                bot.send_document(ADMIN_ID, msg.document.file_id, caption=f"إثبات من المستخدم: {msg.document.file_name}")
            bot.send_message(msg.chat.id, "✅ تم إرسال الإثبات للإدارة للمراجعة.", reply_markup=main_keyboard())
        except Exception as e:
            bot.send_message(msg.chat.id, "⚠️ فشل إرسال الإثبات. حاول لاحقًا.")
        finally:
            clear_state(msg.from_user.id)
        return
    # غير ذلك: تجاهل أو رد عام
    bot.send_message(msg.chat.id, "استخدم الأزرار لإجراء العمليات.", reply_markup=main_keyboard())

# ---------- رد الأدمن (Reply على رسالة الطلب في محادثة البوت مع الأدمن) ----------
@bot.message_handler(func=lambda m: m.chat.id == ADMIN_ID and m.reply_to_message is not None)
def admin_reply_handler(msg):
    original = msg.reply_to_message.text or ""
    match = re.search(r"UserID:\s*(\d+)", original)
    if not match:
        bot.send_message(ADMIN_ID, "⚠️ لم أتمكن من إيجاد UserID في الرسالة الأصلية. تأكد أنك ترد على رسالة الطلب الصحيحة.")
        return
    user_id = int(match.group(1))

    # عمليات خاصة بطلب حذف الحساب
    if "طلب حذف حساب" in original or "طلب حذف الحساب" in original or "🗑️ طلب حذف" in original:
        txt = msg.text.strip() if msg.text else ""
        if txt == "موافقة":
            if user_id in user_accounts:
                del user_accounts[user_id]
            bot.send_message(user_id, "✅ تمت الموافقة على حذف حسابك. يمكنك الآن إنشاء حساب جديد.", reply_markup=main_keyboard())
            bot.send_message(ADMIN_ID, "✅ تم حذف الحساب.")
            return
        elif txt == "رفض":
            bot.send_message(user_id, "❌ تم رفض طلب حذف حسابك من قبل الإدارة.", reply_markup=main_keyboard())
            bot.send_message(ADMIN_ID, "❌ تم رفض طلب الحذف.")
            return

    # إرسال الرد العام للمستخدم (نص/صورة/ملف)
    try:
        if msg.content_type == "text":
            bot.send_message(user_id, f"💬 رد من الإدارة:\n{msg.text}")
        elif msg.content_type == "photo":
            bot.send_photo(user_id, msg.photo[-1].file_id, caption=f"رد من الإدارة:\n{msg.caption or ''}")
        elif msg.content_type == "document":
            bot.send_document(user_id, msg.document.file_id, caption=f"رد من الإدارة:\n{msg.caption or ''}")
        else:
            bot.send_message(user_id, "📌 لديك رد جديد من الإدارة. افتح البوت لعرض التفاصيل.")
        bot.send_message(ADMIN_ID, "✅ تم إرسال ردّك إلى المستخدم.")
    except Exception as e:
        bot.send_message(ADMIN_ID, f"⚠️ فشل إرسال الرد للمستخدم. قد يكون المستخدم حظر البوت. خطأ: {e}")

# ---------- Fallback for text messages (show menu) ----------
@bot.message_handler(func=lambda m: True)
def fallback(msg):
    if msg.content_type == "text":
        text = msg.text.strip()
        # تجاهل الأزرار المعروفة (تمت معالجتها)
        known = {"إنشاء حساب", "إيداع", "سحب", "حذف الحساب", "/start", "/home"}
        if text not in known:
            bot.send_message(msg.chat.id, "اختر عملية من الأزرار أدناه:", reply_markup=main_keyboard())

# ========== Run & webhook setup ==========
if __name__ == "__main__":
    # Register webhook if WEBHOOK_URL provided
    if WEBHOOK_URL and TOKEN and "PUT_YOUR_BOT_TOKEN_HERE" not in TOKEN:
        full_url = WEBHOOK_URL.rstrip("/") + "/" + TOKEN
        # remove previous webhook and set new
        try:
            bot.remove_webhook()
            bot.set_webhook(url=full_url)
            print(f"Webhook set to: {full_url}")
        except Exception as e:
            print("Failed to set webhook:", e)
    else:
        print("Webhook NOT set. Make sure WEBHOOK_URL env var is defined and TOKEN replaced with real token.")

    # Run Flask app (on Render use gunicorn to run)
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
