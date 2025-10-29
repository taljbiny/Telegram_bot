import telebot
from telebot import types
from flask import Flask, request
import json
import os
import traceback
import asyncio

# ✅ الاستيرادات الجديدة من النظام الجديد
from config import BOT_TOKEN, ADMIN_ID, SYRIATEL_CODE, SHAM_CODE, SITE_LINK, MIN_AMOUNT
from database.user_queries import find_or_create_user, save_user_request

# ====== المتغيرات المؤقتة ======
pending_accounts = {}      # { user_id: {"username": "...", "password": "...", "raw": "..."} }
pending_deposits = {}      # { user_id: {amount, method, file_id} }
pending_withdraws = {}     # { user_id: {amount, method, wallet} }
pending_deletes = {}       # { user_id: {account} }

# ====== نظام الدعم المصحح كلياً ======
active_support_sessions = {}  # { user_id: chat_id }

# ====== إعدادات إضافية ======
DATA_FILE = "data.json"
RENDER_URL = "https://telegram-bot-xsto.onrender.com"

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# ====== نظام التذكر المدمج ======
def check_or_create_user(user_id, username):
    """نسخة معدلة تستخدم النظام الجديد"""
    try:
        # استخدم النظام الجديد مباشرة
        success = find_or_create_user(user_id, username)
        if success:
            return {"usage_count": 1, "user_id": user_id}
        return None
    except Exception as e:
        print(f"❌ خطأ في نظام التذكر: {e}")
        return None

# ====== نظام الطلبات المدمج ======
def save_user_request_legacy(user_id, request_type, amount, status="pending"):
    """نسخة معدلة من دالة حفظ الطلب - تربط النظامين"""
    try:
        # 🔥 النظام الجديد: حفظ في قاعدة البيانات
        success = save_user_request(user_id, request_type, amount, "طلب من البوت")
        print(f"✅ تم حفظ الطلب في النظام الجديد: {request_type} - {amount}")
    except Exception as e:
        print(f"⚠️ خطأ في النظام الجديد: {e}")
    
    # إرجاع بيانات وهمية للنظام القديم
    return {"id": 1, "status": status}

# ====== نظام الدعم المبسط ======
def create_support_chat(user_id):
    """نسخة مبسطة بدون supabase"""
    try:
        print(f"✅ تم إنشاء محادثة دعم للمستخدم: {user_id}")
        return {"id": 1, "status": "open"}  # إرجاع بيانات وهمية
    except Exception as e:
        print(f"❌ خطأ في إنشاء محادثة: {e}")
        return None

def add_support_message(chat_id, user_id, message, is_from_user=True):
    """نسخة مبسطة بدون supabase"""
    try:
        print(f"✅ رسالة دعم: {user_id} - {message}")
        return {"id": 1}
    except Exception as e:
        print(f"❌ خطأ في إضافة رسالة: {e}")
        return None

def close_support_chat(chat_id):
    """نسخة مبسطة بدون supabase"""
    try:
        print(f"✅ تم إغلاق محادثة الدعم: {chat_id}")
        return True
    except Exception as e:
        print(f"❌ خطأ في إغلاق المحادثة: {e}")
        return False

# ====== حفظ وقراءة البيانات المحلية ======
def load_data():
    if not os.path.exists(DATA_FILE) or os.path.getsize(DATA_FILE) == 0:
        return {"user_accounts": {}, "pending_deposits": {}, "pending_withdraws": {}, "pending_deletes": {}}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {"user_accounts": {}, "pending_deposits": {}, "pending_withdraws": {}, "pending_deletes": {}}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ====== القوائم ======
def main_menu(chat_id, include_create=False):
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("💳 شحن الحساب", callback_data="deposit"),
        types.InlineKeyboardButton("💸 سحب", callback_data="withdraw")
    )
    if include_create:
        markup.add(types.InlineKeyboardButton("🆕 إنشاء حساب", callback_data="create_account"))
    markup.add(
        types.InlineKeyboardButton("🗑️ حذف الحساب", callback_data="delete_account"),
        types.InlineKeyboardButton("📞 الدعم", callback_data="support")
    )
    return markup

def back_to_menu():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="main_menu"))
    return markup

def admin_controls(user_id):
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("✅ قبول", callback_data=f"admin_accept_{user_id}"),
        types.InlineKeyboardButton("❌ رفض", callback_data=f"admin_reject_{user_id}"),
        types.InlineKeyboardButton("💬 رد يدوي", callback_data=f"admin_manual_{user_id}")
    )
    return markup

def check_min_amount(amount):
    try:
        return int(amount) >= MIN_AMOUNT
    except:
        return False

def is_back_command(text):
    return text and "🔙 القائمة الرئيسية" in text

# ====== /start مع التذكر المدمج ======
@bot.message_handler(commands=['start'])
def start(message):
    user_id = str(message.chat.id)
    username = message.from_user.username or message.from_user.first_name or "No username"
    
    # 🔥 النظام الجديد: البحث أو إنشاء مستخدم
    try:
        bot_user = check_or_create_user(user_id, username)
    except Exception as e:
        print(f"❌ خطأ في النظام الجديد: {e}")
        bot_user = None
    
    # النظام القديم: التحقق من الحسابات المحلية
    data = load_data()
    include_create = user_id not in data["user_accounts"]
    
    if user_id in data["user_accounts"]:
        # رسالة ترحيب مع التذكر من النظام الجديد
        welcome_msg = f"👤 أهلاً بعودتك! {username} 😊\n"
        if bot_user:
            welcome_msg += f"🔄 هذه الزيارة رقم {bot_user.get('usage_count', 1)} لك!\n\n"
        welcome_msg += "اختر العملية من الأزرار أدناه:"
        
        markup = main_menu(message.chat.id)
        bot.send_message(message.chat.id, welcome_msg, reply_markup=markup)
    else:
        markup = main_menu(message.chat.id, include_create=True)
        text = f"👋 أهلاً بك في نظام [55BETS]({SITE_LINK})!\nاختر العملية من الأزرار أدناه:"
        bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode="Markdown")

# ====== عرض القائمة الرئيسية ======
@bot.callback_query_handler(func=lambda call: call.data == "main_menu")
def show_main_menu(call):
    try:
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
    except:
        pass
    
    # تنظيف أي عمليات مؤقتة
    user_id = str(call.message.chat.id)
    pending_accounts.pop(user_id, None)
    pending_deposits.pop(user_id, None)
    pending_withdraws.pop(user_id, None)
    active_support_sessions.pop(user_id, None)  # ✅ تنظيف جلسات الدعم
    
    data = load_data()
    include_create = user_id not in data["user_accounts"]
    bot.send_message(call.message.chat.id, "🔙 القائمة الرئيسية:", reply_markup=main_menu(call.message.chat.id, include_create=include_create))

# ====== إنشاء الحساب ======
@bot.callback_query_handler(func=lambda call: call.data == "create_account")
def create_account(call):
    try:
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
    except:
        pass
    
    data = load_data()
    user_id = str(call.message.chat.id)
    if user_id in data["user_accounts"]:
        bot.answer_callback_query(call.id, "❌ لديك حساب مسبق، احذف الحساب القديم أولاً.")
        return
    
    msg = bot.send_message(call.message.chat.id, "📝 أرسل اسم المستخدم الذي تريده:", reply_markup=back_to_menu())
    bot.register_next_step_handler(msg, collect_username_step)

def collect_username_step(message):
    if is_back_command(message.text):
        bot.send_message(message.chat.id, "🔙 عدت للقائمة الرئيسية.", reply_markup=main_menu(message.chat.id, include_create=True))
        return
    
    if not message.text:
        msg = bot.send_message(message.chat.id, "❌ الرجاء إرسال اسم مستخدم نصي:", reply_markup=back_to_menu())
        bot.register_next_step_handler(msg, collect_username_step)
        return
    
    user_id = str(message.chat.id)
    username = message.text.strip()
    pending_accounts[user_id] = {"username": username, "password": None}
    
    msg = bot.send_message(message.chat.id, "🔐 الآن أرسل كلمة السر التي تريدها:", reply_markup=back_to_menu())
    bot.register_next_step_handler(msg, collect_password_step)

def collect_password_step(message):
    if is_back_command(message.text):
        user_id = str(message.chat.id)
        pending_accounts.pop(user_id, None)
        bot.send_message(message.chat.id, "🔙 عدت للقائمة الرئيسية.", reply_markup=main_menu(message.chat.id, include_create=True))
        return
    
    if not message.text:
        msg = bot.send_message(message.chat.id, "❌ الرجاء إرسال كلمة سر نصية:", reply_markup=back_to_menu())
        bot.register_next_step_handler(msg, collect_password_step)
        return
    
    user_id = str(message.chat.id)
    password = message.text.strip()
    
    if user_id not in pending_accounts:
        pending_accounts[user_id] = {"username": None, "password": password}
    else:
        pending_accounts[user_id]["password"] = password
    
    raw_text = f"اسم المستخدم: {pending_accounts[user_id].get('username', '')}\nكلمة السر: {password}"
    
    bot.send_message(
        ADMIN_ID,
        f"📩 طلب إنشاء حساب جديد:\n👤 المستخدم: {user_id}\n\n{raw_text}",
        reply_markup=admin_controls(user_id)
    )
    bot.send_message(message.chat.id, "⏳ تم إرسال طلب إنشاء الحساب للإدارة، يرجى الانتظار...", reply_markup=main_menu(message.chat.id))

# ====== شحن الحساب ======
@bot.callback_query_handler(func=lambda call: call.data == "deposit")
def deposit_start(call):
    try:
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
    except:
        pass
    
    user_id = str(call.message.chat.id)
    data = load_data()
    
    # 🔥 التحقق إذا فيه طلب شحن قيد الانتظار
    if user_id in pending_deposits:
        bot.send_message(user_id, "⏳ لديك طلب شحن قيد الانتظار. انتظر حتى يتم معالجته.", reply_markup=main_menu(user_id))
        return
        
    # 🔥 التحقق من وجود الحساب - نتحقق من البيانات المحفوظة
    if user_id not in data["user_accounts"] or not data["user_accounts"][user_id]:
        bot.send_message(user_id, "❌ ليس لديك حساب، يرجى إنشاء حساب أولاً.", reply_markup=main_menu(user_id, include_create=True))
        return
    
    msg = bot.send_message(call.message.chat.id, f"💰 أدخل المبلغ لشحن الحساب (الحد الأدنى {MIN_AMOUNT}):", reply_markup=back_to_menu())
    bot.register_next_step_handler(msg, deposit_amount_step)

def deposit_amount_step(message):
    if is_back_command(message.text):
        bot.send_message(message.chat.id, "🔙 عدت للقائمة الرئيسية.", reply_markup=main_menu(message.chat.id))
        return
    
    amount = message.text.strip()
    if not check_min_amount(amount):
        msg = bot.send_message(message.chat.id, f"❌ الحد الأدنى للشحن هو {MIN_AMOUNT}. أعد الإدخال:", reply_markup=back_to_menu())
        bot.register_next_step_handler(msg, deposit_amount_step)
        return
    
    # حفظ الطلب في النظام المدمج
    save_user_request_legacy(str(message.chat.id), "deposit", amount)
    
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("سيرياتيل كاش", callback_data=f"deposit_method_syriatel_{amount}"),
        types.InlineKeyboardButton("شام كاش", callback_data=f"deposit_method_sham_{amount}")
    )
    bot.send_message(message.chat.id, f"💳 سيتم شحن مبلغ {amount}. اختر طريقة الدفع:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("deposit_method_"))
def deposit_method_selected(call):
    try:
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
    except:
        pass
    
    parts = call.data.split("_")
    method = parts[2]
    amount = parts[3]
    user_id = str(call.message.chat.id)
    method_name = "سيرياتيل كاش" if method == "syriatel" else "شام كاش"
    code = SYRIATEL_CODE if method == "syriatel" else SHAM_CODE
    
    msg = bot.send_message(call.message.chat.id, f"📱 كود المحفظة لـ {method_name}: `{code}`\n📸 أرسل صورة تأكيد الدفع الآن.", parse_mode="Markdown", reply_markup=back_to_menu())
    bot.register_next_step_handler(msg, lambda m: handle_deposit_photo(m, amount, method_name))

def handle_deposit_photo(message, amount, method_name):
    if is_back_command(message.text):
        bot.send_message(message.chat.id, "🔙 عدت للقائمة الرئيسية.", reply_markup=main_menu(message.chat.id))
        return

    if not message.photo:
        msg = bot.send_message(message.chat.id, "❌ الرجاء إرسال صورة تأكيد الدفع فقط.", reply_markup=back_to_menu())
        bot.register_next_step_handler(msg, lambda m: handle_deposit_photo(m, amount, method_name))
        return

    file_id = message.photo[-1].file_id
    user_id = str(message.chat.id)
    pending_deposits[user_id] = {"amount": amount, "method": method_name, "file_id": file_id}

    # جلب اسم المستخدم للإشعار
    data = load_data()
    username = data["user_accounts"].get(user_id, {}).get("username", "غير معروف")

    bot.send_photo(
        ADMIN_ID,
        file_id,
        caption=f"💳 طلب شحن جديد:\n👤 المستخدم: {user_id}\n👤 اسم الحساب: {username}\n💰 المبلغ: {amount}\n💼 الطريقة: {method_name}",
        reply_markup=admin_controls(user_id)
    )
    bot.send_message(message.chat.id, "📩 تم إرسال طلب الشحن للإدارة، يرجى الانتظار.", reply_markup=main_menu(message.chat.id))

# ====== سحب الحساب ======
@bot.callback_query_handler(func=lambda call: call.data == "withdraw")
def withdraw_start(call):
    try:
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
    except:
        pass
    
    user_id = str(call.message.chat.id)
    data = load_data()
    
    # 🔥 التحقق إذا فيه طلب سحب قيد الانتظار
    if user_id in pending_withdraws:
        bot.send_message(user_id, "⏳ لديك طلب سحب قيد الانتظار. انتظر حتى يتم معالجته.", reply_markup=main_menu(user_id))
        return
    
    # 🔥 التحقق من وجود الحساب - نتحقق من البيانات المحفوظة
    if user_id not in data["user_accounts"] or not data["user_accounts"][user_id]:
        bot.send_message(user_id, "❌ ليس لديك حساب، يرجى إنشاء حساب أولاً.", reply_markup=main_menu(user_id, include_create=True))
        return
    
    msg = bot.send_message(call.message.chat.id, f"💰 أدخل المبلغ للسحب (الحد الأدنى {MIN_AMOUNT}):", reply_markup=back_to_menu())
    bot.register_next_step_handler(msg, withdraw_amount_step)

def withdraw_amount_step(message):
    if is_back_command(message.text):
        bot.send_message(message.chat.id, "🔙 عدت للقائمة الرئيسية.", reply_markup=main_menu(message.chat.id))
        return
    
    amount = message.text.strip()
    if not check_min_amount(amount):
        msg = bot.send_message(message.chat.id, f"❌ الحد الأدنى للسحب هو {MIN_AMOUNT}. أعد الإدخال:", reply_markup=back_to_menu())
        bot.register_next_step_handler(msg, withdraw_amount_step)
        return
    
    # حفظ الطلب في النظام المدمج
    save_user_request_legacy(str(message.chat.id), "withdraw", amount)
    
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("سيرياتيل كاش", callback_data=f"withdraw_method_syriatel_{amount}"),
        types.InlineKeyboardButton("شام كاش", callback_data=f"withdraw_method_sham_{amount}")
    )
    @bot.message_handler(func=lambda message: True, content_types=['text', 'photo'])
def handle_all_messages(message):
    """تتعامل مع كل الرسائل"""
    user_id = str(message.chat.id)
    
    # إذا كان في محادثة دعم نشطة
    if user_id in active_support_sessions:
        chat_id = active_support_sessions[user_id]
        
        # إذا كانت رسالة إنهاء المحادثة
        if message.text and "إنهاء" في message.text:
            end_support_session(user_id)
            return
        
        # معالجة رسالة الدعم
        if message.text:
            add_support_message(chat_id, user_id, message.text, True)
            bot.send_message(ADMIN_ID, f"📩 رسالة دعم جديدة من {user_id}:\n{message.text}", reply_markup=admin_controls(user_id))
            bot.send_message(user_id, "✅ تم إرسال رسالتك للدعم. انتظر الرد.")
        elif message.photo:
            file_id = message.photo[-1].file_id
            add_support_message(chat_id, user_id, "[صورة]", True)
            bot.send_photo(ADMIN_ID, file_id, caption=f"📩 صورة دعم جديدة من {user_id}", reply_markup=admin_controls(user_id))
            bot.send_message(user_id, "✅ تم إرسال صورتك للدعم. انتظر الرد.")
        
        # إعادة عرض زر إنهاء المحادثة
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔚 إنهاء المحادثة", callback_data=f"end_chat_{chat_id}"))
        bot.send_message(user_id, "✍️ يمكنك إرسال رسالة أخرى:", reply_markup=markup)
    
    # إذا ما كان في محادثة دعم وكانت رسالة عادية
    elif message.text and not message.text.startswith('/'):
        bot.send_message(user_id, "🔍 لم أفهم طلبك. استخدم الأزرار أدناه:", reply_markup=main_menu(user_id))
    
    parts = call.data.split("_")
    method = parts[2]
    amount = parts[3]
    method_name = "سيرياتيل كاش" if method == "syriatel" else "شام كاش"
    user_id = str(call.message.chat.id)
    
    msg = bot.send_message(call.message.chat.id, f"📩 أرسل رقم/كود المحفظة لطريقة {method_name}:", reply_markup=back_to_menu())
    bot.register_next_step_handler(msg, lambda m: confirm_withdraw_wallet(m, amount, method_name))

def confirm_withdraw_wallet(message, amount, method_name):
    if is_back_command(message.text):
        bot.send_message(message.chat.id, "🔙 عدت للقائمة الرئيسية.", reply_markup=main_menu(message.chat.id))
        return

    wallet = message.text.strip()
    user_id = str(message.chat.id)
    pending_withdraws[user_id] = {"amount": amount, "method": method_name, "wallet": wallet}

    # جلب اسم المستخدم للإشعار
    data = load_data()
    username = data["user_accounts"].get(user_id, {}).get("username", "غير معروف")

    bot.send_message(
        ADMIN_ID,
        f"💸 طلب سحب جديد:\n👤 المستخدم: {user_id}\n👤 اسم الحساب: {username}\n💰 المبلغ: {amount}\n💼 الطريقة: {method_name}\n📥 المحفظة: {wallet}",
        reply_markup=admin_controls(user_id)
    )
    bot.send_message(message.chat.id, "📩 تم إرسال طلب السحب للإدارة، يرجى الانتظار.", reply_markup=main_menu(message.chat.id))

# ====== حذف الحساب ======
@bot.callback_query_handler(func=lambda call: call.data == "delete_account")
def delete_account(call):
    try:
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
    except:
        pass
    
    user_id = str(call.message.chat.id)
    data = load_data()
    if user_id not in data["user_accounts"]:
        bot.send_message(user_id, "❌ لا يوجد لديك حساب.", reply_markup=main_menu(user_id, include_create=True))
        return
    
    pending_deletes[user_id] = {"account": data["user_accounts"][user_id]}
    
    username = data["user_accounts"][user_id].get("username", "غير معروف")
    bot.send_message(ADMIN_ID, f"🗑️ طلب حذف الحساب:\n👤 المستخدم: {user_id}\n👤 اسم الحساب: {username}", reply_markup=admin_controls(user_id))
    bot.send_message(user_id, "📩 تم إرسال طلب حذف الحساب للإدارة، يرجى الانتظار.", reply_markup=main_menu(user_id))

# ====== نظام الدعم المصحح كلياً ======
@bot.callback_query_handler(func=lambda call: call.data == "support")
def support_handler(call):
    try:
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
    except:
        pass
    
    user_id = str(call.message.chat.id)
    
    # التحقق إذا فيه محادثة نشطة
    if user_id in active_support_sessions:
        bot.send_message(user_id, "⚠️ لديك محادثة دعم نشطة مسبقاً.")
        return
    
    # إنشاء محادثة دعم جديدة
    chat = create_support_chat(user_id)
    
    if chat:
        # حفظ المحادثة النشطة
        active_support_sessions[user_id] = chat['id']
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔚 إنهاء المحادثة", callback_data=f"end_chat_{chat['id']}"))
        
        bot.send_message(
            user_id, 
            "📩 **وضع الدعم نشط**\n\nارسل رسالتك الآن...\nستصل رسالتك مباشرة للإدارة.", 
            reply_markup=markup,
            parse_mode="Markdown"
        )
    else:
        bot.send_message(user_id, "❌ حدث خطأ في فتح محادثة الدعم.", reply_markup=main_menu(user_id))

@bot.message_handler(func=lambda message: True, content_types=['text', 'photo'])
def handle_all_messages(message):
    """تتعامل مع كل الرسائل"""
    user_id = str(message.chat.id)
    
    # إذا كان في محادثة دعم نشطة
    if user_id in active_support_sessions:
        chat_id = active_support_sessions[user_id        chat_id = active_support_sessions[user_id]
        
        # إذا]
        
        # إذا كانت رسالة إنه كانت رسالة إنهاءاء المحادثة
        if المحادثة
        if message.text and "إن message.text and "إنهاء" in messageهاء" in message.text:
            end.text:
            end_s_support_session(user_id)
upport_session(user_id)
            return
            
        # مع            return
            
        # معالالجة رسالة الدعم
       جة رسالة الدعم
        if message if message.text:
            add.text:
            add_s_support_message(chat_idupport_message(chat_id, user_id,, user_id, message message.text, True)
           .text, True)
            bot.send bot.send_message(ADMIN_message(ADMIN_ID, f"📩_ID, f"📩 رسالة دعم جديدة من رسالة دعم جديدة من {user_id}:\ {user_id}:\n{message.text}",n{message.text}", reply_markup= reply_markup=admin_controls(user_id))
           admin_controls(user_id))
            bot.send_message(user bot.send_message(user_id, "✅_id, "✅ تم إ تم إرسالرسال رسالتك لل رسالتك للدعم. انتدعم. انتظر الرد.")
       ظر الرد.")
        elif message.photo elif message.photo:
            file_id =:
            file_id = message.photo[-1 message.photo[-1].file_id
            add_support].file_id
            add_support_message(chat_message(chat_id, user_id,_id, user_id, "[صورة "[صورة]", True)
            bot.send]", True)
            bot.send_photo_photo(ADMIN_ID(ADMIN_ID, file, file_id,_id, caption=f caption=f"📩 ص"📩 صورة دورة دعم جديدة من {عم جديدة من {user_iduser_id}", reply_markup=admin_controls(user_id))
            bot}", reply_markup=admin_controls(user_id))
            bot.send_message(user_id, "✅ تم إرسال صورتك لل.send_message(user_id, "✅ تم إرسال صورتك للدعم. انتدعم. انتظر الظر الرد.")
        
رد.")
        
        # إ        # إعادة عرضعادة عرض زر إنه زر إنهاء المحاء المحادثةادثة
       
        markup = types.In markup = types.InlineKeyboardMarkup()
       lineKeyboardMarkup()
        markup.add markup.add(types.Inline(types.InlineKeyboardButtonKeyboardButton("("🔚 إنه🔚 إنهاء المحاداء المحادثة",ثة", callback_data=f" callback_data=f"end_chend_chat_{chatat_{chat_id}_id}"))
        bot"))
        bot.send_message(user.send_message(user_id_id, "✍, "✍️ يمكنك إ️ يمكنك إرسال رسالة أخرىرسال رسالة أخرى:", reply_markup:", reply_markup=markup)
    
   =markup)
    
    # إذا # إذا ما ما كان في مح كان في محادثةادثة دعم وكان دعم وكانت رست رسالة عالة عادية
    elifادية message.text and not
    elif message.text and not message.text.startswith message.text.startswith('/'):
('/'):
        bot.send_message        bot.send_message(user_id(user_id, ", "🔍 لم أف🔍 لم أفهمهم طلبك طلبك. استخدم الأ. استخدم الأزرار أدناه:", reply_mزرار أدناه:", reply_markup=mainarkup=main_menu_menu(user_id))

@bot(user_id))

@bot.call.callback_query_handler(funcback_query_handler(func=lambda=lambda call: call.data call: call.data.startswith.startswith("end_chat("end_chat_"))
_"))
def end_supportdef end_support_chat(call_chat(call):
    user_id = str(c):
    user_id = str(call.message.chall.message.chat.id)
    end_support_session(user_id)
   at.id)
    end_support_session(user_id)
    bot.send_message(user bot.send_message(user_id, "🔚 تم_id, "🔚 تم إنه إنهاء محادثة الدعم.", reply_markاء محادثة الدعم.", reply_markup=main_menu(user_id))

defup=main_menu(user_id))

def end_support_session(user_id):
    end_support_session(user_id):
    """إنهاء ج """إنهاء جلسة الدعم"""
لسة الدعم"""
    if user_id in    if user_id in active active_support_sessions:
       _support_sessions:
        chat_id = active chat_id = active_support_sessions[user_id]
        close_support_chat(chat_id)
        active_support_support_sessions[user_id]
        close_support_chat(chat_id)
        active_support_sessions.pop(user_sessions.pop(user_id,_id, None)

 None)

# ======# ====== لوحة لوحة تحكم الإ تحكم الإدمن =دمن ======
=====
@bot.callback@bot.callback_query_handler_query_handler(func=lambda(func=lambda call: call.data call: call.data.startswith.startswith("admin_"))
("admin_"))
def admindef admin_action(c_action(callall):
):
    data = call.data.split("    data = call.data.split("_")
   _")
    action = data[1]
    user action = data[1]
    user_id = data[_id = data[2]

2    if action == "accept]

    if action == "accept":
        #":
        # 🟢 🟢 حالة 1: حالة 1: إن إنشاء حساب جديد
       شاء حساب جديد
        if user_id in pending if user_id in pending_account_accounts:
            msgs:
            msg = bot = bot.send_message(
               .send_message(
                ADMIN ADMIN_ID,
                f"_ID,
                f"🆕 ار🆕 ارسل بيانات الحسل بيانات الحساب النهائية للمستخدمساب النهائية للمستخدم {user_id} {user_id}:\n(يمكنك إ:\n(يمكنك إرسال أي نص -رسال أي نص - لن يتم التح لن يتم التحقق منقق من الصيغة)"
 الصيغة)"
            )
            )
            bot.register            bot.register_next_step_handler_next_step_handler(msg,(msg, lambda m: lambda m: admin_confirm admin_confirm_account_data(m, user_id))
           _account_data(m, user_id return

        # 🟢 حالة 2: حذف حساب
))
            return

        # 🟢 حالة 2: حذف حساب
        elif        elif user_id in pending user_id in pending_de_deletes:
            data_fileletes:
            data_file = load_data()
            = load_data()
            if if user_id in data user_id in data_file["_file["user_accounts"]user_accounts"]:
:
                del data_file["                del data_file["user_accountuser_accounts"][s"][user_id]
user_id]
                save                save_data(data_file)
            pending_deletes.pop(user_id, None)
           _data(data_file)
            pending_deletes.pop(user_id, None)
            try try:
                bot.send_message:
                bot.send_message(int(int(user_id), "(user_id), "✅✅ تم حذف حساب تم حذف حسابك بنجاح، يمكنك بنجاح، يمكنك الآن إنشاء حسابك الآن إنشاء حساب جديد جديد.", reply_mark.", reply_markupup=main_menu(int(user=main_menu(int(user_id), include_create=True))
_id), include_create=True))
            except:
                pass
            except:
                pass
            bot.send_message(AD            bot.send_message(MIN_ID, f"ADMIN_ID, f🗑️ تم ح"🗑️ تم حذف حساب المستخدم {ذف حساب المستخدمuser_id} بنجاح.")
            return

        {user_id} بنجاح.")
            return

        # 🟢 حالة # 🟢 حالة 3: شحن حساب 3: شحن حساب
       
        elif user_id in pending_deposits elif user_id in pending_deposits:
            dep = pending:
            dep = pending_deposits.pop(user_deposits.pop(user_id)
            try:
                bot.send_message(int_id)
            try:
                bot.send_message(int(user_id), f"✅(user_id), f"✅ تم قب تم قبول طلب الشول طلب الشحن.\n💰 سيتم إضافة الرصحن.\n💰 سيتم إضافة الرصيد إلى حسابك خلاليد إلى حسابك خلال 5 دقائق 5 دقائق ك كحد أقصى.",حد أقصى.", reply_markup=main reply_markup=main_menu(int_menu(int(user_id)))
            except:
                pass(user_id)))
            except:
                pass
            bot.send
            bot.send_message(ADMIN_ID, f"💰_message(ADMIN_ID, f"💰 تم تم قبول شحن المستخدم {user قبول شحن المستخدم {user_id}_id} ({dep['amount']} عبر {dep[' ({dep['amount']} عبر {dep['method']}).")
            returnmethod']}).")
            return

        #

        # 🟢 🟢 حالة 4: حالة 4: سحب رص سحب رصيد
        elif user_idيد
        elif user_id in pending in pending_withdraws:
            wd = pending_with_withdraws:
            wd = pending_withdraws.pop(user_id)
draws.pop(user_id)
            try:
                           try:
                bot.send_message(int(user_id bot.send_message(int(user_id), f"✅ تم قب), f"✅ تم قبول طلب السحبول طلب السحب.\n💵 سي.\n💵 سيتم تحويل المبلغ إلىتم تحويل المبلغ إلى محفظتك في أقرب محفظتك في أقرب وقت ممكن.", reply_markup=main_menu(int(user_id)))
            except وقت ممكن.", reply_markup=main_menu(int(user_id)))
            except:
                pass
            bot:
                pass
            bot.send_message(.send_message(ADMIN_ID, f"💸 تم قبول سحب المستخدم {userADMIN_ID, f"💸 تم قبول سحب المستخدم {user_id_id} ({wd['amount']} إلى {} ({wd['amount']} إلى {wd['wd['wallet']}).")
           wallet']}).")
            return

        else:
            return

        else:
            bot.send_message(ADMIN bot.send_message(ADMIN_ID, "⚠_ID, "⚠️ لم يتم التعرف على️ لم يتم التعرف على نوع الطلب لقبوله نوع الطلب لقب.")
            return

    elifوله.")
            return

    elif action == "reject action == "reject":
        pending_accounts":
        pending_accounts.pop(user_id, None)
.pop(user_id, None)
        pending_deletes.pop(user        pending_deletes.pop(user_id, None)
       _id, None)
        pending_deposits pending_deposits.pop(user_id, None.pop(user_id, None)
)
        pending_withdraw        pending_withdraws.pops.pop(user_id, None(user_id, None)
        
        try:
           )
        
        try:
            bot.send_message(int(user bot.send_message(int(user_id_id), "❌), "❌ تم ر تم رفض طلبكفض طلبك من قبل الإدارة.", reply من قبل الإدارة.", reply_markup=_markup=main_menumain_menu(int(user_id)))
(int(user_id)))
        except        except:
            pass
:
            pass
        bot        bot.send_message(.send_message(ADADMIN_ID, fMIN_ID, f""🚫 تم رفض🚫 تم رفض طلب المستخدم {user_id طلب المستخدم {user_id}}.")
        return

.")
        return

    elif action == "manual":
        msg = bot.send_message(ADMIN    elif action == "manual":
        msg = bot.send_message(ADMIN_ID, f"📝 اكتب ال_ID, f"📝 اكتب الرد اليدوي الذي تريد إرسرد اليدوي الذي تريد إرساله للمستخدم {user_idاله للمستخدم {user_id}:")
        bot.register_next}:")
        bot.register_next_step_handler(msg, lambda_step_handler(msg, lambda m m: send_manual_re: send_manualply(m, user_id_reply(m, user_id))
        return

def admin))
        return

def admin_confirm_account_data(message, user_id):
   _confirm_account_data(message, user_id):
    text = (message.text or "" text = (message.text).strip()
    
    if not or "").strip()
    
    if not text:
        text:
        bot.send_message bot.send_message(AD(ADMINMIN_ID,_ID, "❌ لم يتم إرسال أي "❌ لم يتم إرسال أي بيانات. بيانات. أعد المحاول أعد المحاولة.")
ة.")
        return
    
        return
    
    # استخدام    # استخدام النص النص كما هو كما هو بدون تحقق من بدون تحقق من الصي الصيغة
    dataغة
    data = load = load_data()
    data["user_accounts_data()
    data["user_accounts"][user_id] = {"username"][user_id] =": text, "password": {"username": text, " "سيتم إرسpassword": "سيتم إرسالها للمستخدم"}
    save_data(dataالها للمستخدم"}
    save_data(data)

    try:
)

    try:
        bot        bot.send_message(int(user.send_message(int(user_id), f"_id), f"✅ تم✅ تم إنشاء حسابك إنشاء حسابك بنج بنجاح!\اح!\n{text}",n{text}", reply_markup reply_markup=main=main_menu(int_menu(int(user_id)))
    except:
        pass

    bot.send_message(ADMIN_ID,(user_id)))
    except:
        pass

    bot.send_message(ADMIN_ID, f"✅ تم حفظ الحس f"✅ تم حفظ الحساب للمستخدماب {user_id}:\n للمستخدم {user_id}{text}")

    #:\n{text}")

    # تنظيف تنظيف الط الطلبات المؤقتلبات المؤقتة
ة
    pending_account    pending_accounts.pop(user_ids.pop(user_id, None)
   , None)
    pending_d pending_deposits.popeposits.pop(user_id(user_id, None, None)
    pending)
    pending_withdraws.pop(user_withdraws.pop(user_id, None)
    pending_id, None)
    pending_deletes.pop(user_id,_deletes.pop(user_id, None)

def send_manual None)

def send_manual_reply(message,_reply(message, user_id user_id):
    try:
):
    try:
        bot.send_message(int(user        bot.send_message(int(user_id), f"📩_id), f"📩 رسالة من الإدارة:\ رسالة من الإدارةn{message.text}", reply:\n{message.text_markup=}", reply_markup=main_menu(int(user_id)))
main_menu(int(user_id)))
        bot.send_message(AD        bot.send_message(ADMIN_ID, "MIN_ID, "✅ تم✅ تم إرسال ال إرسال الردرد للم للمستخدم.")
    except Exception as e:
        bot.send_message(ADMIN_ID, f"⚠️ خطأ أثناء إرسستخدم.")
    except Exception as e:
        bot.send_message(ADMIN_ID, f"⚠️ خطأ أثناء إرسال الرسالة للمستخدم:ال الرسالة للمستخدم: {e}")

# = {e}")

#===== رسالة جم ====== رسالة جماعية ======
@اعية ======
@bot.message_handler(commands=['broadcastbot.message_handler(commands=['broadcast'])
def broadcast_message(message):
    if message.ch'])
def broadcast_message(message):
    ifat.id != ADMIN_ID:
        return
    msg = message.chat.id != ADMIN_ID:
        return
    msg = bot.send_message(message.ch bot.send_message(message.chat.idat.id, "📝, "📝 أ أرسل الرسالةرسل الرسالة الجماعية الجماعية التي تريد التي تريد إرس إرسالها لجميعالها لجميع المستخدمين:")
    bot المستخدمين:")
    bot.register_next_step_handler(msg.register_next_step_handler(msg, send_broadcast)

def, send_broadcast send_broadcast(message)

def send_broadcast(message):
    data = load):
    data = load_data()
_data()
    user_ids = list(data    user_ids = list(data["user_accounts"].keys())
["user_accounts"].keys())
    count = 0
       count = 0
    for user_id in user_ids for user_id in user_ids:
        try:
            bot:
        try:
           .send_message(int(user_id), bot.send_message(int(user_id), f"📢 f"📢 رسالة جماعية:\n رسالة جماعية:\n{message.text}")
            count{message.text}")
            count += 1
        += 1
        except:
            except:
            continue
    bot.send_message continue
    bot.send_message(ADMIN_ID, f(ADMIN_ID, f"✅ تم إ"✅ تم إرسال الرسالةرسال الرسالة إلى {count إلى {count} مستخدم} مستخدمين.")

ين.")

# ====== Webhook Flask ======
@app.route('/'# ====== Webhook Flask ======
@app.route('/' + BOT + BOT_TOKEN, methods_TOKEN, methods=['POST=['POST'])
def'])
def webhook():
    webhook():
    try:
 try:
        json_str =        json_str = request.stream request.stream.read().decode.read().decode('utf-8')
        update('utf-8')
        update = = telebot.types telebot.types.Update.de_json(json.Update.de_json(json_str)
        bot.process_new_updates_str)
        bot.process_new_updates([update])
([update])
    except Exception as e:
        print    except Exception as e:
        print("Webhook error:", e("Webhook error:", e)
    return '',)
    return '', 200 200

@app.route('/')
def index():


@app.route('/')
def index():
    try:
    try:
        bot.remove        bot.remove_webhook()
    except:
        pass
    try_webhook()
    except:
        pass
    try:
       :
        bot.set_webhook(url=RENDER_URL + '/' + BOT_TOKEN)
    except Exception as bot.set_webhook(url=RENDER_URL + '/' + BOT_TOKEN)
    except Exception as e:
        print("Web e:
        print("Webhook set error:",hook set error:", e)
 e)
    return "Web    return "Webhook Set!"

if __name__hook Set!"

if __name == "__main__":
   __ == "__main__":
    PORT = int(os.environ PORT = int(os.environ.get("PORT",.get("PORT", 100 10000))
    app00))
    app.run(host="0..run(host="0.0.0.0",0.0.0", port=PORT)
