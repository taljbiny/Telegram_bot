import telebot
from telebot import types
from flask import Flask, request
import json
import os
import traceback
import asyncio
from supabase import create_client

# ✅ الاستيرادات الجديدة من النظام الجديد
from config import BOT_TOKEN, ADMIN_ID, SYRIATEL_CODE, SHAM_CODE, SITE_LINK, MIN_AMOUNT
from database.user_queries import find_or_create_user, save_user_request

# ====== المتغيرات المؤقتة ======
pending_accounts = {}      # { user_id: {"username": "...", "password": "...", "raw": "..."} }
pending_deposits = {}      # { user_id: {amount, method, file_id} }
pending_withdraws = {}     # { user_id: {amount, method, wallet} }
pending_deletes = {}       # { user_id: {account} }

# ====== إعدادات إضافية ======
DATA_FILE = "data.json"
RENDER_URL = "https://telegram-bot-xsto.onrender.com"

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# ====== Supabase للتذكر ======
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://kocqdumkwnnajjaswtlv.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtvY3FkdW1rd25uYWpqYXN3dGx2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjE2NjEzODIsImV4cCI6MjA3NzIzNzM4Mn0.tyDnoxrwV0jzekdBbhnh8_kf1PGKr_9pF6-2T-7cy58")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ====== نظام التذكر الجديد ======
def check_or_create_user(user_id, username):
    """شيك إذا المستخدم مسجل او سجله جديد"""
    try:
        # ابحث عن المستخدم
        response = supabase.table("users").select("*").eq("user_id", str(user_id)).execute()
        
        if len(response.data) > 0:
            # المستخدم موجود
            user_data = response.data[0]
            # حدث عدد الاستخدامات
            supabase.table("users").update({
                "usage_count": user_data["usage_count"] + 1,
                "last_seen": "now()"
            }).eq("user_id", str(user_id)).execute()
            return user_data
        else:
            # سجل مستخدم جديد
            new_user = {
                "user_id": str(user_id),
                "username": username or "No username",
                "usage_count": 1,
                "last_seen": "now()"
            }
            response = supabase.table("users").insert(new_user).execute()
            return response.data[0]
    except Exception as e:
        print(f"Database Error: {e}")
        return None

# ====== نظام الطلبات المدمج ======
def save_user_request_legacy(user_id, request_type, amount, status="pending"):
    """نسخة معدلة من دالة حفظ الطلب - تربط النظامين"""
    try:
        # 🔥 النظام الجديد: حفظ في قاعدة البيانات
        asyncio.run(save_user_request(user_id, request_type, amount, "طلب من البوت"))
        print(f"✅ تم حفظ الطلب في النظام الجديد: {request_type} - {amount}")
    except Exception as e:
        print(f"⚠️ خطأ في النظام الجديد: {e}")
    
    # النظام القديم: يستمر يعمل كما هو
    try:
        request_data = {
            "user_id": str(user_id),
            "request_type": request_type,
            "amount": int(amount),
            "status": status
        }
        response = supabase.table("user_requests").insert(request_data).execute()
        print(f"✅ Saved user request: {request_data}")
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"Error saving request: {e}")
        return None

def update_request_status(request_id, status):
    """تحديث حالة الطلب"""
    try:
        supabase.table("user_requests").update({"status": status}).eq("id", request_id).execute()
        return True
    except Exception as e:
        print(f"Error updating request: {e}")
        return False

# ====== نظام الدعم المتقدم ======
def create_support_chat(user_id):
    """إنشاء محادثة دعم جديدة"""
    try:
        chat_data = {
            "user_id": str(user_id),
            "status": "open"
        }
        response = supabase.table("support_chats").insert(chat_data).execute()
        print(f"✅ Created support chat: {response.data}")
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"❌ Error creating support chat: {e}")
        traceback.print_exc()
        return None

def add_support_message(chat_id, user_id, message, is_from_user=True):
    """إضافة رسالة إلى محادثة الدعم"""
    try:
        message_data = {
            "chat_id": chat_id,
            "user_id": str(user_id),
            "message": message,
            "is_from_user": is_from_user
        }
        response = supabase.table("support_messages").insert(message_data).execute()
        print(f"✅ Added support message: {message_data}")
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"❌ Error adding support message: {e}")
        traceback.print_exc()
        return None

def close_support_chat(chat_id):
    """إغلاق محادثة الدعم"""
    try:
        supabase.table("support_chats").update({"status": "closed"}).eq("id", chat_id).execute()
        print(f"✅ Closed support chat: {chat_id}")
        return True
    except Exception as e:
        print(f"❌ Error closing chat: {e}")
        traceback.print_exc()
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
        bot_user = asyncio.run(find_or_create_user(user_id, username))
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
            welcome_msg += f"🔄 هذه الزيارة رقم {bot_user.get('id', 1)} لك!\n\n"
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

روف")

    bot    bot.send_photo(
.send_photo(
        ADMIN        ADMIN_ID,
        file_ID,
        file_id,
_id,
        caption=f"        caption=f"💳 طلب💳 طلب شحن شحن جديد:\n جديد:\n👤👤 المستخدم: {user المستخدم: {user_id}\n👤 اسم الحساب: {username}\n💰 المبلغ: {amount}\n💼 الطريقة: {method_name}",
        reply_markup=admin_controls(user_id)
    )
    bot.send_message(message.chat.id_id}\n👤 اسم الحساب: {username}\n💰 المبلغ: {amount}\n💼 الطريقة: {method_name}",
        reply_markup=admin_controls(user_id)
    )
    bot.send_message, "📩 تم إ(message.chat.id, "📩 تم إرسالرسال طلب طلب الشحن للإدارة، ي الشحن للإدارة، يرجى الانتظاررجى الانتظار.", reply_markup=main_menu(message.chat.id))

.", reply_markup=main_menu(message.chat.id))

# =====# ====== سحب الحساب ======
@bot.callback_query_handler= سحب الحساب ======
@bot.callback_query_handler(func=lambda call: call.data == "withdraw")
def withdraw_start(call):
(func=lambda call: call.data == "withdraw")
def withdraw_start(call):
    try:
        bot.edit_message    try:
        bot.edit_message_reply_mark_reply_markup(call.message.chatup(call.message.chat.id, call.message.id, call.message.message_id, reply.message_id, reply_mark_markup=None)
up=None)
    except:
    except:
        pass
    
        pass
    
    user    user_id = str_id = str(call(call.message.chat.id.message.chat.id)
)
    data =    data = load_data load_data()
    
    #()
    
    # 🔥 التح 🔥 التحقق إذا فيهقق إذا فيه طلب سحب طلب سحب ق قيد الانتظار
يد الانتظار
    if user_id    if user_id in pending_withdraws:
 in pending_withdraws:
        bot.send_message(user        bot.send_message(user_id_id, ", "⏳⏳ لديك طلب س لديك طلب سحب قيد الانتحب قيد الانتظارظار. انتظر حتى. انتظر حتى يتم معالجته.", يتم معالجته.", reply reply_markup=_markup=mainmain_menu(user_id))
       _menu(user_id))
        return
    
    # 🔥 return
    
    # 🔥 التحقق من وجود التحقق من وجود الحس الحساباب - نتحقق من البيانات المح - نتحقق من البيانات المحفوظة
    if userفوظة
    if user_id not in data["user_id not in data["user_accounts"] or not_accounts"] or not data[" data["user_accountuser_accounts"][user_id]:
       s"][user_id]:
        bot.send_message(user_id, "❌ ليس لديك حساب، يرجى إنشاء bot.send_message(user_id, "❌ ليس لديك حساب، يرجى إنشاء حساب أولاً.", reply_mark حساب أولاً.", reply_markup=main_menu(user_idup=main_menu(user_id, include_create=True, include_create=True))
       ))
        return
    
    return
    
    msg = bot msg = bot.send_message.send_message(call(call.message.chat.id.message.chat.id, f, f"💰 أد"💰 أدخل المبلغخل المبلغ للسحب للسحب (ال (الحد الأدنى {حد الأدنى {MIN_AMOMIN_AMOUNT}):UNT}):", reply_m", reply_markuparkup=back_to_menu=back_to_menu())
   ())
    bot.register_next bot.register_next_step_handler(msg, withdraw_amount_step)

def withdraw_amount_step_handler(msg, withdraw_amount_step)

def withdraw_amount_step(message):
    if is_step(message):
    if is_back_command(message.text):
       _back_command(message.text):
        bot.send_message(message bot.send_message(message.chat.id,.chat.id, " "🔙 عدت للقائمة🔙 عدت لل الرئيسية.", reply_markقائمة الرئيسية.", reply_markup=mainup=main_menu_menu(message.chat.id))
(message.chat.id))
        return
    
    amount = message.text.strip()
    if not check_min_amount(        return
    
    amount = message.text.strip()
    if not check_min_amount(amount):
amount):
        msg = bot        msg = bot.send_message.send_message(message.ch(message.chat.idat.id, f", f"❌ الحد الأدنى للسحب❌ الحد الأدنى للسحب هو هو {MIN_ {MIN_AMOAMOUNT}. أعدUNT}. أعد الإدخال:", الإدخال:", reply reply_markup=_markup=back_toback_to_menu())
        bot_menu())
        bot.register_next.register_next_step_handler(msg_step_handler(msg,, withdraw_amount_step)
 withdraw_amount_step)
        return
    
    # حفظ        return
    
    # حفظ الطلب في النظام الم الطلب في النظام المدمدمج
    saveج
    save_user_request_user_request_legacy_legacy(str(str(message.chat.id(message.chat.id), "), "withdraw", amountwithdraw", amount)
    
    markup)
    
    markup = types = types.In.InlinelineKeyboardMarkup()
    markup.add(
       KeyboardMarkup()
    markup.add(
        types.Inline types.InlineKeyboardButton("سيرياتيل كاش",KeyboardButton("سيرياتيل كاش", callback callback_data=f"withdraw_data=f"withdraw_method_s_method_syriatel_{yriatel_{amount}"),
       amount}"),
        types.In types.InlineKeyboardButton("lineKeyboardButton("شامشام كاش", callback_data=f"with كاش", callback_data=f"withdraw_methoddraw_method_sham_{amount_sham_{amount}")
    )
    bot}")
    )
    bot.send.send_message(message.chat_message(message.chat.id, "💳 اخ.id, "💳 اختر طريقة السحب:", replyتر طريقة السحب:", reply_markup=_markup=markmarkup)

@up)

@bot.callbot.callback_query_handler(funcback_query_handler(func=lambda call=lambda call: call.data.start: call.data.startswith("withdraw_method_swith("withdraw_method_"))
def withdraw_method"))
def withdraw_method_selected_selected(call):
   (call):
    try:
        bot.edit_message try:
        bot.edit_message_reply_mark_reply_markup(cup(call.message.chatall.message.chat.id, call.message.message_id.id, call.message.message, reply_markup_id, reply_markup=None)
    except:
=None)
    except:
        pass
    
    parts        pass
    
    parts = call.data.split("_")
    method = parts[2]
    amount = = call.data.split("_")
    method = parts[2]
    amount = parts[3]
 parts[3]
    method_name = "س    method_name = "سيرياتيل كاش"يرياتيل كاش" if method == " if method == "sysyriatel" else "riatel" else "شام كاششام كاش"
    user_id = str"
    user_id = str(call.message.chat.id(call.message.chat.id)
    
    msg)
    
    msg = bot.send_message(call = bot.send_message(call.message.chat.id, f.message.chat.id, f"📩 أ"📩 أرسل رقم/كودرسل رقم/كود المحفظة ل المحفظة لطريقة {method_name}:طريقة {method_name}:", reply", reply_markup=_markup=back_to_menu())
back_to_menu())
    bot    bot.register_next_step_handler.register_next_step_handler(msg(msg, lambda m, lambda m:: confirm_withdraw confirm_withdraw_wallet(m_wallet(m, amount, method_name))

def confirm_with, amount, method_name))

def confirm_withdraw_walletdraw_wallet(message, amount, method(message, amount, method_name):
   _name):
    if is_back_command(message if is_back_command(message.text):
.text):
        bot.send_message        bot.send_message(message.chat.id, "(message.chat.id,🔙 عدت للق "🔙 عدتائمة الرئيسية.", للقائمة الرئيسية.", reply_markup=main reply_markup_menu(message.chat.id))
        return

   =main_menu(message.chat.id))
        return

    wallet = wallet = message.text.strip()
 message.text.strip()
    user    user_id = str_id = str(message.chat(message.chat.id)
.id)
    pending    pending_withdraws_withdraws[[user_id] =user_id] = {"amount": amount, "method": method_name, " {"amount": amount, "method": method_name, "wallet": wallet}

    # جلب اسم المستخدم للإشعارwallet": wallet}

    # جلب اسم المستخدم للإشعار
    data = load_data()
    username = data
    data = load_data()
    username = data["user_accounts["user_accounts"].get(user_id"].get(user_id, {}).get("username",, {}).get("username", " "غير معروف")

غير معروف")

    bot.send_message(
           bot.send_message(
        ADMIN_ID,
        f ADMIN_ID,
        f""💸 طلب💸 طلب سحب جديد سحب جديد:\n:\n👤 المستخدم: {user_id}\n👤 اسم الحساب: {username}\n💰 المبلغ: {amount}\n💼 الطريقة: {method_name}\n📥 المحفظة: {wallet}",
        reply_markup=admin_controls(user_id👤 المستخدم: {user_id}\n👤 اسم الحساب: {username}\n💰 المبلغ: {amount}\n💼 الطريقة: {method_name}\n📥 المحفظة: {wallet}",
        reply_markup=admin_controls(user_id)
   )
    )
    bot.send )
    bot.send_message(message.chat.id, "_message(message.chat.id, "📩 تم إرس📩 تم إرسال طلب السحب للإال طلب السحب للإدارة، يرجدارة، يرجى الانتظار.",ى الانتظار.", reply reply_m_markarkupup=main_menu(message.chat.id))

# =======main_menu(message.chat.id))

# ====== ح حذف الحسذف الحساب =اب ======
@bot=====
@bot.callback_query_handler.callback_query_handler(func=lambda(func=lambda call: call.data call: call.data == "delete_account")
def == "delete_account")
def delete_account(call):
    try:
        bot.edit_message_reply_markup(call.message delete_account(call):
    try:
        bot.edit_message_reply_markup(call.message.ch.chat.id, call.messageat.id, call.message.message_id, reply.message_id, reply_mark_markup=None)
   up=None)
    except:
        pass
    
    except:
        pass
    
    user_id = str user_id = str(call(call.message.chat.id.message.chat.id)
)
    data = load_data()
    if user    data = load_data()
    if user_id not in data["user_accounts"]:
        bot.send_message(user_id, "❌ لا يوجد لديك حساب_id not in data["user_accounts"]:
        bot.send_message(user_id, "❌ لا يوجد لديك حساب.", reply_markup=main_menu.", reply_markup=main_menu(user_id, include_create(user_id, include_create=True))
        return
    
   =True))
        return
    
    pending_deletes[user_id pending_deletes[user_id] = {"account] = {"account": data["user": data["user_account_accountss"][user_id"][user_id]}
    
    username =]}
    
    username = data data["user_accounts["user_accounts""][user_id].get][user_id].get("("username", "غير معusername", "غير معروف")
    botروف")
    bot.send_message.send_message(ADMIN_ID(ADMIN_ID, f"🗑, f"🗑️️ طلب حذ طلب حذف الحف الحسابساب:\n:\n👤 المستخدم👤 المستخدم: {: {user_id}\nuser_id}\n👤👤 اسم الحس اسم الحساباب: {: {usernameusername}", reply_markup=admin}", reply_markup=admin_controls(user_id_controls(user_id))
    bot.send_message(user))
    bot.send_message(user_id, "_id, "📩 تم إرسال ط📩 تم إرسال طلب حلب حذفذف الحساب للإدارة، يرجى الانتظ الحساب للإدارة، يار.", reply_markup=main_menu(user_id))

#رجى الانتظار.", reply_markup=main_menu(user_id ====== الد))

# ====== الدعم المتقدم - النسعم المتقدم -خة المصححة ===== النسخة المصححة ==
@bot.callback=====
@bot.callback_query_handler(func=lambda call: call.data == "_query_handler(func=lambda call: call.data == "supportsupport")
def support_handler(call):
    try")
def support_handler(call):
    try:
       :
        bot.edit_message_re bot.edit_message_reply_mply_markuparkup(call(call.message.chat.id, call.message.chat.id, call.message.message.message.message_id, reply_m_id, reply_markuparkup=None)
    except=None)
    except:
:
        pass
    
        pass
    
    user    user_id = str(c_id = str(call.messageall.message.chat.id)
    
    # إن.chat.id)
    
    # إنشاء محادثةشاء محادثة دعم دعم جديدة
    chat جديدة
    chat = = create_support create_support_chat_chat(user_id)
    
(user_id)
    
    if    if chat:
        chat:
        msg = msg = bot.send_message bot.send_message(call(call.message.chat.id.message.chat.id, ", "📩 ا📩 اكتب رسالتكتب رسالتك للدعم (يمكنك إك للدعم (يمكنك إرسال نص أورسال نص أو صورة):", reply_m صورة):", reply_markup=back_toarkup=back_to_menu_menu())
        bot.register())
        bot.register_next_step_handler(msg, lambda_next_step_handler(msg, lambda m: handle_s m: handle_supportupport_message(m, chat['_message(m, chat['id']))
    else:
id']))
    else:
        bot.send_message        bot.send_message(c(call.message.chat.idall.message.chat.id, "❌ حدث خط, "❌ حدث خطأ في فتحأ في فتح محاد محادثة الدعم.",ثة الدعم.", reply_m reply_markup=mainarkup=main_menu(c_menu(call.message.chat.id))

def handle_sall.message.chat.id))

def handle_support_message(message, chatupport_message(message, chat_id):
    if_id):
    if is_back is_back_command(message.text):
_command(message.text):
        close_support_chat        close_support_chat(chat_id)
        bot(chat_id)
        bot.send_message(message.send_message(message.chat.id, "🔙.chat.id, "🔙 عدت للق عدت للقائمة الرئيسائمة الرئيسية.", reply_markup=mainية.", reply_markup=main_menu(message_menu(message.chat.id))
.chat.id))
               return
    
    user return
    
    user_id_id = str(message.ch = str(message.chat.idat.id)
    
    #)
    
    # حفظ الرسالة في قاعدة حفظ الرسالة في قاعدة البيانات البيانات
    if message
    if message.text:
.text:
        add_support        add_support_message(chat_id_message(chat_id, user, user_id,_id, message.text, True)
 message.text, True)
        # إرسال للإد        # إرسال للإدمن
من
        bot.send_message        bot.send_message(AD(ADMIN_IDMIN_ID, f"📩 رسالة د, f"📩 رسالة دعم جديدة من {عم جديدة من {user_iduser_id}:\n{}:\n{message.text}", reply_markmessage.text}", reply_markup=admin_up=admin_controls(usercontrols(user_id))
        bot_id))
        bot.send_message(message.chat.send_message(message.chat.id.id, "✅ تم, "✅ تم إرسال رسالتك إرسال رسالتك للد للدعم. انتظرعم. انتظر الرد الرد.")
    elif message.")
    elif message.photo.photo:
       :
        file_id = file_id = message.photo message.photo[-1[-1].file_id].file_id
        add
        add_support_support_message(chat_id, user_message(chat_id, user_id,_id, "[ص "[صورة]", True)
ورة]", True)
        #        # إرس إرسال الصال الصورة للإدمنورة للإدمن
       
        bot.send_photo bot.send_photo(AD(ADMIN_ID,MIN_ID, file_id file_id, caption=f"📩 صورة دعم جديدة من {user_id}", reply_mark, caption=f"📩 صورة دعم جديدة من {user_id}", reply_markup=up=admin_admin_controls(user_id))
        botcontrols(user_id))
        bot.send_message.send_message(message.chat.id(message.chat.id, ", "✅ تم إرس✅ تم إرسالال صورتك لل صورتك للددعمعم. انتظر الرد. انتظر الرد.")
    
    # ن.")
    
    # نعيد فتح المحعيد فتح المحادثة للردود التالية
    markup = typesادثة للردود التالية
    markup = types.InlineKeyboardMarkup.InlineKeyboardMarkup()
()
    markup.add(    markup.add(types.Intypes.InlineKeyboardButton("lineKeyboardButton("🔚 إنهاء🔚 إنهاء المح المحادثة", callbackادثة", callback_data=f"end_chat_data=f"end_chat_{chat_id}_{chat_id}"))
    
"))
    
    msg = bot    msg = bot.send_message(message.chat.id.send_message(message.chat.id, "✍, "✍️ يمكنك إرسال️ يمكنك إرسال رسالة أخرى أو إنه رسالة أخرى أو إنهاء المحادثةاء المحادثة:", reply_markup=markup)
    bot.register_next_step_handler(msg, lambda m: handle_support_message(m, chat_id))

@bot.callback_query_handler(func=lambda call: call.data.startswith("end_chat_"))
def end_support_chat(call):
    try:
       :", reply_markup=markup)
    bot.register_next_step_handler(msg, lambda m: handle_support_message(m, chat_id))

@bot.callback_query_handler(func=lambda call: call.data.startswith("end_chat_"))
def end_support_chat(call):
    try:
        chat_id = int(c chat_id = int(callall.data.split("_.data.split("_")[2])  #")[2])  # تحويل لـ integer
        close_support تحويل لـ integer
        close_support_ch_chat(chat_id)
at(chat_id)
        bot.send_message(call.message.chat.id        bot.send_message(call.message.chat.id, "🔚 تم إنهاء محادثة الدعم.", reply_m, "🔚 تم إنهاء محادثة الدعم.", reply_markup=main_menu(call.message.chat.id))
    except Exception as e:
        print(f"❌ Error endingarkup=main_menu(call.message.chat.id))
    except Exception as e:
        print(f"❌ Error ending chat: {e}")
        chat: {e}")
        traceback.print_exc()
 traceback.print_exc()
        bot.send_message        bot.send_message(call.message.chat.id, "(call.message.chat.id, "❌❌ حدث خطأ في إنهاء المحاد حدث خطأ في إنهاء المحادثة.", reply_markupثة.", reply_markup=main_menu(call.message.ch=main_menu(call.message.chat.idat.id))

#))

# ===== ====== لوحة تح= لوحة تحكم الإكم الإدمندمن ======
@ ======
@bot.callbot.callback_query_handlerback_query_handler(func=lambda call(func=lambda call: call: call.data.start.data.startswith("swith("admin_"))
def admin_action(cadmin_"))
def admin_action(call):
   all):
    data = data = call.data call.data.split("_")
.split("_")
    action    action = data = data[1]
   [1]
    user_id user_id = data[2 = data[2]

   ]

    if action if action == " == "accept":
        #accept":
        # 🟢 حالة 1 🟢 حالة 1: إن: إنشاء حسابشاء حساب جديد
 جديد
        if user_id in pending_accounts:
            msg = bot.send        if user_id in pending_accounts:
            msg = bot.send_message(
_message(
                ADMIN_ID,
                ADMIN_ID,
                               f"🆕 f"🆕 ارسل بيانات الحساب النهائية للم ارسل بيانات الحساب النهائية للمستخدم {user_idستخدم {user_id}:\n(يمكنك إرس}:\n(يمكنكال أي نص - لن إرسال أي نص - يتم التحقق من الص لن يتم التحقق من الصيغة)"
            )
           يغة)"
            bot.register_next_step )
            bot.register_next_step_handler(msg_handler(msg, lambda m: admin_confirm_account, lambda m: admin_confirm_account_data(m_data(m, user_id))
, user_id))
            return

                   return

        # # 🟢 حالة  🟢 حالة 2:2: حذف حذف حساب
 حساب
        elif user        elif user_id in_id in pending_deletes:
 pending_deletes:
            data            data_file = load_data()
            if user_file = load_data()
            if user_id in_id in data_file["user data_file["user_accounts_accounts"]:
"]:
                del data                del data_file["user_file["user_accounts_accounts"]["][user_id]
               user_id]
                save_data save_data(data_file(data_file)
            pending_de)
            pending_deletes.popletes.pop(user_id(user_id, None)
            try:
, None)
            try:
                               bot.send_message(int(user_id bot.send_message(int(user_id), "✅ تم ح), "✅ تم حذف حسابكذف حسابك بنج بنجاح، يمكناح، يمكنك الآن إنك الآن إنشاء حسابشاء حساب جديد.", reply جديد.", reply_markup_markup=main=main_menu(int_menu(int(user_id), include(user_id), include_create=True_create=True))
))
            except:
                pass            except:
                pass
           
            bot.send bot.send_message(_message(ADMIN_ID,ADMIN_ID, f" f"🗑️🗑️ تم حذ تم حذف حسابف حساب المستخدم المستخدم {user_id} {user_id} بنج بنجاح.")
           اح.")
            return

 return

        #        # 🟢 🟢 حالة  حالة 3:3: شحن حساب
        elif user_id in شحن حساب
        elif user_id in pending_dep pending_deposits:
osits:
            dep = pending_depos            dep = pending_deposits.pop(user_idits.pop(user_id)
            try:
                bot.send_message)
            try:
                bot(int(user_id),.send_message(int(user_id), f"✅ تم قبول f"✅ تم قب طلب الشحن.\ول طلب الشحن.\n💰 سيn💰 سيتم إضافة الرصيد إلى حسابك خلالتم إضافة الرصيد إلى حساب 5 دك خلال 5قائق كحد أقصى دقائق كحد أ.", reply_markup=main_menu(int(userقصى.", reply_markup=main_menu(int(user_id)))
            except_id)))
            except:
                pass
            bot:
                pass
            bot.send_message(ADMIN_ID.send_message(ADMIN_ID, f"💰, f"💰 تم قبول شحن المست تم قبول شحن المستخدم {user_id} ({خدم {user_id} ({dep['amount']dep['amount']} عبر {dep['method} عبر {dep['method']}).")
            return']}).")
            return



        # 🟢 حالة 4: سحب رصيد        # 🟢 حالة 4: سحب رصيد
        elif user_id in
        elif user_id in pending_withdraws:
            pending_withdraws:
            wd = pending wd = pending_withdraws.pop(user_id)
            try:
                bot.send_message(int(user_id), f"✅ تم قبول طلب_withdraws.pop(user_id)
            try:
                bot.send_message(int(user_id), f"✅ تم قبول طلب الس السحب.\n💵حب.\n💵 سيتم تحويل المبلغ إلى محفظتك في سيتم تحويل المبلغ إلى محفظتك أقرب وقت ممكن.", في أقرب وقت ممكن.", reply_markup=main reply_markup=_menu(int(user_idmain_menu(int(user_id)))
            except:
                pass)))
            except:
                pass
            bot.send_message
            bot.send_message((ADMIN_ID,ADMIN_ID, f"💸 تم قب f"💸 تم قبول سحب المستول سحب المستخدم {خدم {user_id} ({user_id} ({wd['amount']}wd['amount']} إلى {wd['wal إلى {wd['wallet']let']}).")
            return}).")
            return

       

        else:
            bot.send_message(ADMIN else:
            bot.send_message(AD_ID, "⚠️MIN_ID, " لم يتم التعرف على نوع الطلب لقب⚠️ لم يتم التعرف على نوع الطلب لقبولهوله.")
            return

   .")
            return

    elif action elif action == " == "reject":
       reject":
        pending_account pending_accounts.pop(user_id, None)
       s.pop(user_id, None pending_deletes.pop(user)
        pending_deletes.pop_id, None)
       (user_id, None)
        pending_d pending_deposits.popeposits.pop(user_id, None)
       (user_id, None)
        pending_withdraws pending_withdraws.pop(user.pop(user_id, None)
_id, None)
        
        try:
            bot        
        try:
            bot.send_message(int(user_id), "❌ تم رفض طلبك من قبل الإدارة.", reply_markup.send_message(int(user_id), "❌ تم رفض طلبك من قبل الإدارة.", reply_markup=main=main_menu(int(user_id)))
        except:
_menu(int(user_id)))
        except:
            pass            pass
        bot.send
        bot.send_message(ADMIN_ID,_message(ADMIN_ID f"🚫 تم ر, f"🚫 تم رفض طلب المستفض طلب المستخدم {user_idخدم {user_id}.")
}.")
        return

           return

    elif action elif action == "manual":
 == "manual":
        msg = bot.send_message        msg = bot(ADMIN_ID, f.send_message(ADMIN_ID, f""📝 اكتب الرد اليدوي الذي تريد إرساله📝 اكتب الرد اليدوي الذي للمستخدم {user_id}:")
        bot.register تريد إرساله للمستخدم {user_id}:")
        bot.register_next_step_handler(msg_next_step_handler(msg, lambda m:, lambda m: send_ send_manual_reply(mmanual_reply(m, user, user_id))
        return_id))
        return

def admin_

def admin_confirm_accountconfirm_account_data(message, user_id):
    text =_data(message, user_id):
    text = ( (message.text or "").strip()
    
    if not text:
        bot.send_message(ADMINmessage.text or "").strip()
    
    if not text:
        bot.send_message(ADMIN_ID, "_ID, "❌ لم❌ لم يتم إرسال يتم إرسال أي بيانات. أ أي بيانات. أعد المحعد المحاولة.")
       اولة.")
        return
    
    # استخدام الن return
    
    # استخدام النص كما هو بدون تحققص كما هو بدون تحقق من الصيغة
 من الصيغة
    data =    data = load_data load_data()
    data["()
    data["user_accountuser_accounts"s"][user_id] = {"username":][user_id] = {"username": text, " text, "password": "password": "سيتمسيتم إرسالها إرسالها للمستخدم للمستخدم"}
    save"}
    save_data_data(data)

    try(data)

    try:
        bot.send_message(int(user_id:
        bot.send_message(int(user_id), f), f"✅"✅ تم إنشاء حساب تم إنشاء حسابك بنك بنجاح!\جاح!\nn{text}", reply{text}", reply_markup=main_menu(int(user_markup=main_menu_id)))
    except:
(int(user_id)))
    except:
        pass

        pass

    bot    bot.send_message(AD.send_message(ADMIN_IDMIN_ID, f", f"✅✅ تم حفظ الحس تم حفظ الحساب للمستخدم {user_id}اب للمستخدم {user_id:\n{text}")

    # تنظيف الطلبات المؤقت}:\n{text}")

    # تنظيف الطلبات المؤقتة
    pending_accountsة
    pending_accounts.pop(user_id, None.pop(user_id, None)
    pending_dep)
    pending_deposits.pop(user_id,osits.pop(user_id, None)
 None)
    pending_withdraws.pop(user    pending_withdraws.pop(user_id_id, None)
    pending_deletes.pop(user_id, None)
    pending_deletes.pop(user_id, None)

def send_, None)

def send_manual_reply(messagemanual_reply(message, user_id):
, user_id):
    try:
        bot.send    try:
        bot.send_message(int(user_id), f_message(int(user_id), f"📩 رسالة من الإدارة:\n{message.text}", reply_markup=main"📩 رسالة من الإدارة:\n{message.text}", reply_markup=main_menu(int_menu(int(user_id)))
       (user_id)))
        bot.send_message(ADMIN bot.send_message(ADMIN_ID, "✅_ID, "✅ تم إ تم إرسالرسال الرد الرد للمستخدم.")
    للمستخدم.")
    except Exception as e:
        except Exception as e:
        bot.send_message(ADMIN_ID, f"⚠️ خطأ أثناء إرسال الرسالة للم bot.send_message(ADMIN_ID, f"⚠️ خطأ أثناء إرسال الرسالة للمستخدم: {ستخدم: {e}e}")

# =====")

# ====== رس= رسالة جمالة جماعية ======
اعية ======
@bot@bot.message_handler(commands=['broadcast'])
def broadcast.message_handler(commands=['broadcast'])
def broadcast_message(message):
    if message_message(message):
    if message.chat.id !=.chat.id != ADMIN_ID:
        return
 ADMIN_ID:
        return
    msg =    msg = bot.send_message(message.chat.id, "📝 أرسل الرسالة الجماعية التي تريد إرسالها لجميع المست bot.send_message(message.chat.id, "📝 أرسل الرسالة الجماعية التي تريد إرسالها لجميع المستخدمين:")
    botخدمين:")
    bot.register_next_step_handler(msg.register_next_step_handler(msg, send_broadcast)

, send_broadcast)

def send_broadcast(message):
   def send_broadcast(message):
    data = load_data()
    user_ids data = load_data()
    = list(data[" user_ids = list(data["user_accounts"].keysuser_accounts"].keys())
())
    count =     count = 0
    for user_id0
    for user_id in user_ids:
        in user_ids:
        try try:
            bot.send:
            bot.send_message(int(user_id), f_message(int(user_id), f"📢 رسالة جماعية:\n{message.text"📢 رسالة جماعية:\n{message.text}")
            count +=}")
            count += 1
        except:
 1
        except:
            continue
    bot.send            continue
    bot.send_message(AD_message(ADMIN_ID,MIN_ID, f"✅ تم f"✅ تم إرسال الرسالة إلى إرسال الرس {count} مستخدمالة إلى {count} مستخدمين.")

#ين.")

# ===== ====== Webhook Flask= Webhook Flask ======
@app.route('/ ======
@app.route('/' + BOT_TOKEN' + BOT_TOKEN,, methods=['POST'])
 methods=['POST'])
def webhook():
    trydef webhook():
    try:
        json_str = request:
        json_str = request.stream.read().decode.stream.read().decode('('utf-8')
       utf-8')
        update = telebot update = telebot.types.Update.de_json(json_str.types.Update.de_json(json)
        bot.process_new_str)
        bot.process_updates([update])
   _new_updates([update])
    except Exception as e:
        except Exception as e:
        print("Webhook print("Webhook error:", error:", e)
    return e)
    return '', 200

@app.route '', 200

@app.route('/')
('/')
def index():
   def index():
    try:
        bot.remove_web try:
        bot.remove_webhook()
   hook()
    except:
 except:
        pass
           pass
    try:
        bot.set_ try:
        bot.set_webhook(url=RENDER_URLwebhook(url=R + '/' + BOT_TOKENENDER_URL + '/' + BOT_TOKEN)
    except)
    except Exception as e:
        print(" Exception as e:
       Webhook set error:", e print("Webhook set error:", e)
   )
    return " return "Webhook Set!"

Webhook Set!"

if __name__ == "__mainif __name__ == "__main__":
    PORT__":
    PORT = int = int(os.environ.get(os.environ.get("PORT("PORT", 100", 10000))
00))
    app.run    app.run(host(host="0.0.0.0",="0.0.0.0", port port=PORT)
