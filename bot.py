# bot.py — النسخة النهائية الكاملة
import telebot
from telebot import types
import json
import os
import uuid
import time

# ==========================
# إعدادات البوت — عدّل القيم هنا إن لزم
# ==========================
TOKEN = "8317743306:AAHAM9svd23L2mqSfHnPFEsqKY_bavW3kMg"
ADMIN_ID = 7625893170  # ضع هنا آي دي الأدمن الأساسي
SUPPORT_USERNAME = "@supp_mo"  # اسم حساب الدعم (يظهر للمستخدم)
SYRIATEL_WALLET = "82492253"
SHAM_WALLET = "131efe4fbccd83a811282761222eee69"
DATA_FILE = "data/users.json"

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

# ==========================
# تهيئة ملفات البيانات
# ==========================
if not os.path.exists("data"):
    os.makedirs("data")

if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f)

def load_users():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_users(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ==========================
# مخازن مؤقتة لطلبات الأدمن (في الذاكرة)
# ==========================
# pending_create: opid -> {user_id, name, password, timestamp}
# pending_deposit: opid -> {user_id, amount, method, wallet, photo_file_id or text, timestamp}
# pending_withdraw: opid -> {user_id, amount, method, code_or_photo, timestamp}
# pending_delete: opid -> {user_id, timestamp}
pending_create = {}
pending_deposit = {}
pending_withdraw = {}
pending_delete = {}

# ==========================
# دوال مساعدة لإنشاء الأزرار
# ==========================
def main_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🧾 إنشاء حساب", callback_data="create_account"),
        types.InlineKeyboardButton("💰 شحن الحساب", callback_data="deposit"),
        types.InlineKeyboardButton("💸 سحب", callback_data="withdraw"),
        types.InlineKeyboardButton("🧑‍💻 دعم فني", callback_data="support"),
        types.InlineKeyboardButton("🗑️ حذف الحساب", callback_data="delete_account")
    )
    return markup

def back_button():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("⬅️ رجوع", callback_data="back"))
    return markup

def admin_approve_markup(op_type, opid):
    # op_type: 'create','deposit','withdraw','delete'
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("✅ موافقة", callback_data=f"{op_type}_ok_{opid}"),
        types.InlineKeyboardButton("❌ رفض", callback_data=f"{op_type}_no_{opid}")
    )
    return markup

# ==========================
# دالة تحقق سريعة: هل المستخدم مسجل؟ (باستعمال user_id string)
# ==========================
def user_registered(user_id_str):
    users = load_users()
    return user_id_str in users

# ==========================
# 1) START - رسالة ترحيبية
# ==========================
@bot.message_handler(commands=["start"])
def cmd_start(message):
    users = load_users()
    uid = str(message.from_user.id)
    if uid in users:
        u = users[uid]
        bot.send_message(message.chat.id,
            f"👋 أهلاً! لديك حساب مسجّل بالفعل.\n\n👤 اسم الحساب: <b>{u['name']}</b>\n🔑 كلمة السر: <code>{u['password']}</code>",
            reply_markup=main_menu())
    else:
        bot.send_message(message.chat.id,
            "👋 أهلاً بك في بوت 55BETS الرسمي.\nاختر أحد الخيارات أدناه:",
            reply_markup=main_menu())

# ==========================
# 2) إنشاء حساب — flow كامل (خطوتين) -> طلب للأدمن -> الأدمن يقدر يعدل ويوافق/يرفض
# ==========================
@bot.callback_query_handler(func=lambda call: call.data == "create_account")
def on_create_account(call):
    uid = str(call.from_user.id)
    users = load_users()
    if uid in users:
        u = users[uid]
        bot.send_message(call.message.chat.id,
            f"⚠️ لديك حساب مسجّل مسبقًا.\n\n👤 اسم الحساب: <b>{u['name']}</b>\n🔑 كلمة السر: <code>{u['password']}</code>",
            reply_markup=main_menu())
        return
    msg = bot.send_message(call.message.chat.id, "🧾 أرسل اسم الحساب الذي ترغب بإنشائه:", reply_markup=back_button())
    bot.register_next_step_handler(msg, create_get_password, name=None)

def create_get_password(message, name):
    # If called with name None, then previous step passed name in message.text? We designed register_next_step_handler with lambda in other flows.
    # To be safe: if name is None and message came from previous handler, treat message as name
    if name is None:
        name = message.text.strip()
        msg = bot.send_message(message.chat.id, "🔒 أرسل كلمة السر التي ترغب بها:", reply_markup=back_button())
        bot.register_next_step_handler(msg, confirm_create, name)
    else:
        # fallback (not used)
        bot.send_message(message.chat.id, "خطأ في سير الإنشاء. أعد الضغط على 'إنشاء حساب' من القائمة.", reply_markup=main_menu())

def confirm_create(message, name):
    password = message.text.strip()
    user_id = str(message.from_user.id)
    opid = str(uuid.uuid4())
    pending_create[opid] = {"user_id": user_id, "name": name, "password": password, "ts": int(time.time())}
    admin_text = (f"🆕 طلب إنشاء حساب جديد:\n\n"
                  f"👤 الاسم المقترح: <b>{name}</b>\n"
                  f"🔑 كلمة السر المقترحة: <code>{password}</code>\n"
                  f"🆔 معرف المستخدم: <code>{user_id}</code>\n\n"
                  "يمكنك تعديل القيم أو الموافقة/الرفض.")
    # ارسال للادمن مع ازرار للموافقة/الرفض — عند الضغط على موافق يسمح بتعديل القيم قبل الحفظ
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✏️ تعديل قبل الموافقة", callback_data=f"create_edit_{opid}"))
    markup.add(types.InlineKeyboardButton("✅ اعتماد كما هي", callback_data=f"create_ok_{opid}"))
    markup.add(types.InlineKeyboardButton("❌ رفض", callback_data=f"create_no_{opid}"))
    bot.send_message(ADMIN_ID, admin_text, reply_markup=markup)
    bot.send_message(user_id, "⏳ تم إرسال طلب إنشاء الحساب إلى الإدارة، سيتم إعلامك بعد المراجعة.", reply_markup=main_menu())

# Admin edits or approves create
@bot.callback_query_handler(func=lambda call: call.data.startswith("create_edit_") or call.data.startswith("create_ok_") or call.data.startswith("create_no_"))
def handle_admin_create_action(call):
    data = call.data
    if not (call.from_user.id == ADMIN_ID):
        bot.answer_callback_query(call.id, "غير مصرح.")
        return

    parts = data.split("_")
    action = parts[1]  # edit / ok / no
    opid = parts[2]

    if opid not in pending_create:
        bot.answer_callback_query(call.id, "الطلب غير موجود أو تم معالجته.")
        return

    entry = pending_create[opid]
    user_id = entry["user_id"]
    if action == "no":
        # رفض
        bot.send_message(user_id, "❌ تم رفض طلب إنشاء الحساب من قبل الإدارة.", reply_markup=main_menu())
        bot.send_message(ADMIN_ID, f"✅ تم رفض طلب إنشاء الحساب للمستخدم {user_id}.")
        del pending_create[opid]
        return
    elif action == "ok":
        # اعتماد كما هي
        users = load_users()
        users[user_id] = {"name": entry["name"], "password": entry["password"]}
        save_users(users)
        bot.send_message(user_id, f"✅ تم إنشاء الحساب بنجاح!\n👤 اسم الحساب: <b>{entry['name']}</b>\n🔑 كلمة السر: <code>{entry['password']}</code>", reply_markup=main_menu())
        bot.send_message(ADMIN_ID, f"✅ تم اعتماد وإنشاء الحساب للمستخدم {user_id}.")
        del pending_create[opid]
        return
    else:
        # تعديل: نطلب من الأدمن إرسال "الاسم - كلمةالسر" أو /skip
        msg = bot.send_message(ADMIN_ID, "✏️ أرسل القيم المعدّلة بالصيغة:\nاسم - كلمة_السر\nأو أرسل /skip للاحتفاظ بالقيم الحالية.")
        bot.register_next_step_handler(msg, admin_edit_create, opid)

def admin_edit_create(message, opid):
    if opid not in pending_create:
        bot.send_message(ADMIN_ID, "الطلب غير موجود أو تم معالجته.")
        return
    if message.text == "/skip":
        entry = pending_create[opid]
        users = load_users()
        users[entry["user_id"]] = {"name": entry["name"], "password": entry["password"]}
        save_users(users)
        bot.send_message(entry["user_id"], f"✅ تم إنشاء الحساب بنجاح!\n👤 اسم الحساب: <b>{entry['name']}</b>\n🔑 كلمة السر: <code>{entry['password']}</code>", reply_markup=main_menu())
        bot.send_message(ADMIN_ID, f"✅ تم اعتماد الحساب كما هو للمستخدم {entry['user_id']}.")
        del pending_create[opid]
        return
    if "-" not in message.text:
        bot.send_message(ADMIN_ID, "خطأ في الصيغة — أرسل بالصيغة: اسم - كلمة_السر أو أرسل /skip")
        return
    parts = message.text.split("-")
    name = parts[0].strip()
    password = parts[1].strip()
    entry = pending_create[opid]
    users = load_users()
    users[entry["user_id"]] = {"name": name, "password": password}
    save_users(users)
    bot.send_message(entry["user_id"], f"✅ تم إنشاء الحساب بنجاح!\n👤 اسم الحساب: <b>{name}</b>\n🔑 كلمة السر: <code>{password}</code>", reply_markup=main_menu())
    bot.send_message(ADMIN_ID, f"✅ تم إنشاء الحساب (بعد تعديلك) للمستخدم {entry['user_id']}.")
    del pending_create[opid]

# ==========================
# 3) شحن الحساب (Deposit) — flow كامل مع رفع صورة/نص، وصول للأدمن كصورة أو نص، وموافقة/رفض الأدمن
# ==========================
@bot.callback_query_handler(func=lambda call: call.data == "deposit")
def on_deposit(call):
    uid = str(call.from_user.id)
    if not user_registered(uid):
        bot.send_message(call.message.chat.id, "⚠️ ليس لديك حساب مسجل. الرجاء إنشاء حساب أولاً.", reply_markup=main_menu())
        return
    msg = bot.send_message(call.message.chat.id, "💰 أرسل المبلغ الذي تريد شحنه (الحد الأدنى 25000):", reply_markup=back_button())
    bot.register_next_step_handler(msg, deposit_get_amount)

def deposit_get_amount(message):
    try:
        amount = int(message.text.strip())
    except:
        bot.send_message(message.chat.id, "❌ الرجاء إدخال رقم صالح للمبلغ.", reply_markup=main_menu())
        return
    if amount < 25000:
        bot.send_message(message.chat.id, "⚠️ الحد الأدنى للشحن هو 25,000.", reply_markup=main_menu())
        return
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("📱 سيرياتيل كاش", callback_data=f"deposit_method_syriatel_{amount}"),
        types.InlineKeyboardButton("💳 شام كاش", callback_data=f"deposit_method_sham_{amount}"),
        types.InlineKeyboardButton("⬅️ رجوع", callback_data="back")
    )
    bot.send_message(message.chat.id, "اختر طريقة الدفع:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("deposit_method_"))
def deposit_method_selected(call):
    parts = call.data.split("_")
    # format: deposit_method_{method}_{amount}
    method = parts[2]  # syriatel or sham
    amount = parts[3]
    uid = str(call.from_user.id)
    users = load_users()
    name = users.get(uid, {}).get("name", "غير مسجل")
    wallet = SYRIATEL_WALLET if method == "syriatel" else SHAM_WALLET
    # طلب إرسال صورة أو نص العملية
    msg = bot.send_message(call.message.chat.id,
                           f"💸 الرجاء تحويل <b>{amount}</b> إلى المحفظة:\n<code>{wallet}</code>\n\nبعد التحويل أرسل صورة الإيصال أو اكتب رمز/تفاصيل العملية:",
                           reply_markup=back_button())
    # ننتظر رسالة تحتوي نص أو صورة
    bot.register_next_step_handler(msg, deposit_receive_proof, uid, amount, method, wallet, name)

def deposit_receive_proof(message, uid, amount, method, wallet, name):
    # uid is string
    opid = str(uuid.uuid4())
    entry = {
        "user_id": uid,
        "amount": amount,
        "method": method,
        "wallet": wallet,
        "name": name,
        "ts": int(time.time())
    }
    # Save proof: either photo file_id or text
    if message.content_type == "photo":
        file_id = message.photo[-1].file_id
        entry["photo_file_id"] = file_id
    else:
        entry["text"] = message.text or ""
    pending_deposit[opid] = entry

    # notify admin with photo or text, plus approve/reject buttons
    admin_caption = (f"📥 طلب شحن حساب\n\n"
                     f"👤 الحساب: <b>{name}</b>\n"
                     f"💰 المبلغ: <b>{amount}</b>\n"
                     f"💳 الطريقة: {'سيرياتيل كاش' if method=='syriatel' else 'شام كاش'}\n"
                     f"🆔 المستخدم: <code>{uid}</code>")

    if "photo_file_id" in entry:
        # send photo to admin with caption
        try:
            bot.send_photo(ADMIN_ID, entry["photo_file_id"], caption=admin_caption)
        except Exception as e:
            # fallback: send text and file_id
            bot.send_message(ADMIN_ID, admin_caption + f"\n\n(مشكلة في إرسال الصورة — file_id: {entry['photo_file_id']})")
    else:
        bot.send_message(ADMIN_ID, admin_caption + f"\n\n🖼️ تفاصيل العملية: {entry.get('text','')}")

    # add approve/reject inline buttons (with opid)
    bot.send_message(ADMIN_ID, "اختر الموافقة أو الرفض:", reply_markup=admin_approve_markup("deposit", opid))
    bot.send_message(message.chat.id, "⏳ تم إرسال طلب الشحن للإدارة للمراجعة.", reply_markup=main_menu())

@bot.callback_query_handler(func=lambda call: call.data.startswith("deposit_ok_") or call.data.startswith("deposit_no_"))
def handle_admin_deposit_decision(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "غير مصرح.")
        return
    parts = call.data.split("_")
    action = parts[1]  # ok or no
    opid = parts[2]
    if opid not in pending_deposit:
        bot.answer_callback_query(call.id, "الطلب غير موجود أو تم معالجته.")
        return
    entry = pending_deposit[opid]
    uid = entry["user_id"]
    if action == "no":
        bot.send_message(uid, "❌ تم رفض طلب الشحن من قبل الإدارة. تواصل مع الدعم لمزيد من التفاصيل.", reply_markup=main_menu())
        bot.send_message(ADMIN_ID, f"✅ تم رفض طلب الشحن للمستخدم {uid}.")
        del pending_deposit[opid]
        return
    # action == ok
    bot.send_message(uid, f"✅ تمت الموافقة على شحن مبلغ {entry['amount']}. سيتم تحديث الحساب يدوياً من قبل الإدارة.", reply_markup=main_menu())
    bot.send_message(ADMIN_ID, f"✅ تمت الموافقة على طلب الشحن للمستخدم {uid}.")
    # هنا ممكن إضافة منطق تحديث رصيد داخلي لو أردت — حالياً نكتفي بالإخطار لأن إدارة الرصيد تتم يدوياً عبر الأدمن
    del pending_deposit[opid]

# ==========================
# 4) السحب (Withdraw) — نفس فكرة الشحن لكن الأدمن يوافق/يرفض
# ==========================
@bot.callback_query_handler(func=lambda call: call.data == "withdraw")
def on_withdraw(call):
    uid = str(call.from_user.id)
    if not user_registered(uid):
        bot.send_message(call.message.chat.id, "⚠️ ليس لديك حساب مسجل. الرجاء إنشاء حساب أولاً.", reply_markup=main_menu())
        return
    msg = bot.send_message(call.message.chat.id, "💸 أرسل المبلغ الذي ترغب بسحبه (الحد الأدنى 25000):", reply_markup=back_button())
    bot.register_next_step_handler(msg, withdraw_get_amount)

def withdraw_get_amount(message):
    try:
        amount = int(message.text.strip())
    except:
        bot.send_message(message.chat.id, "❌ الرجاء إدخال رقم صالح.", reply_markup=main_menu())
        return
    if amount < 25000:
        bot.send_message(message.chat.id, "⚠️ الحد الأدنى للسحب هو 25,000.", reply_markup=main_menu())
        return
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("📱 سيرياتيل كاش", callback_data=f"withdraw_method_syriatel_{amount}"),
        types.InlineKeyboardButton("💳 شام كاش", callback_data=f"withdraw_method_sham_{amount}"),
        types.InlineKeyboardButton("⬅️ رجوع", callback_data="back")
    )
    bot.send_message(message.chat.id, "اختر طريقة استلام المبلغ:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("withdraw_method_"))
def withdraw_method_selected(call):
    parts = call.data.split("_")
    method = parts[2]
    amount = parts[3]
    uid = str(call.from_user.id)
    users = load_users()
    name = users.get(uid, {}).get("name", "غير مسجل")
    wallet = SYRIATEL_WALLET if method == "syriatel" else SHAM_WALLET
    msg = bot.send_message(call.message.chat.id,
                           f"📥 ستحال المبلغ <b>{amount}</b> عبر { 'سيرياتيل' if method=='syriatel' else 'شام' }.\nأرسل الآن كود محفظتك أو صورة QR لاستلام المبلغ:",
                           reply_markup=back_button())
    bot.register_next_step_handler(msg, withdraw_receive_proof, uid, amount, method, wallet, name)

def withdraw_receive_proof(message, uid, amount, method, wallet, name):
    opid = str(uuid.uuid4())
    entry = {
        "user_id": uid,
        "amount": amount,
        "method": method,
        "wallet": wallet,
        "name": name,
        "ts": int(time.time())
    }
    if message.content_type == "photo":
        entry["photo_file_id"] = message.photo[-1].file_id
    else:
        entry["code"] = message.text or ""

    pending_withdraw[opid] = entry

    admin_caption = (f"📤 طلب سحب\n\n"
                     f"👤 الحساب: <b>{name}</b>\n"
                     f"💰 المبلغ: <b>{amount}</b>\n"
                     f"💳 الطريقة: {'سيرياتيل كاش' if method=='syriatel' else 'شام كاش'}\n"
                     f"🆔 المستخدم: <code>{uid}</code>")

    if "photo_file_id" in entry:
        try:
            bot.send_photo(ADMIN_ID, entry["photo_file_id"], caption=admin_caption)
        except:
            bot.send_message(ADMIN_ID, admin_caption + f"\n\n(ملف الصورة: {entry['photo_file_id']})")
    else:
        bot.send_message(ADMIN_ID, admin_caption + f"\n\n🔑 كود المحفظة: {entry.get('code','')}")

    bot.send_message(ADMIN_ID, "اختر الموافقة أو الرفض:", reply_markup=admin_approve_markup("withdraw", opid))
    bot.send_message(uid, "⏳ تم إرسال طلب السحب للإدارة للمراجعة.", reply_markup=main_menu())

@bot.callback_query_handler(func=lambda call: call.data.startswith("withdraw_ok_") or call.data.startswith("withdraw_no_"))
def handle_admin_withdraw_decision(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "غير مصرح.")
        return
    parts = call.data.split("_")
    action = parts[1]
    opid = parts[2]
    if opid not in pending_withdraw:
        bot.answer_callback_query(call.id, "الطلب غير موجود أو تم معالجته.")
        return
    entry = pending_withdraw[opid]
    uid = entry["user_id"]
    if action == "no":
        bot.send_message(uid, "❌ تم رفض طلب السحب من قبل الإدارة. تواصل مع الدعم للمزيد.", reply_markup=main_menu())
        bot.send_message(ADMIN_ID, f"✅ تم رفض طلب السحب للمستخدم {uid}.")
        del pending_withdraw[opid]
        return
    # ok
    bot.send_message(uid, f"✅ تمت الموافقة على طلب السحب بمبلغ {entry['amount']}. سيتم تنفيذ السحب يدويًا من قبل الإدارة.", reply_markup=main_menu())
    bot.send_message(ADMIN_ID, f"✅ تمت الموافقة على طلب السحب للمستخدم {uid}.")
    del pending_withdraw[opid]

# ==========================
# 5) حذف الحساب — يرسل طلب للأدمن، ثم إخطار المستخدم بناء على قرار الأدمن
# ==========================
@bot.callback_query_handler(func=lambda call: call.data == "delete_account")
def on_delete_request(call):
    uid = str(call.from_user.id)
    if not user_registered(uid):
        bot.send_message(call.message.chat.id, "⚠️ ليس لديك حساب مسجل.", reply_markup=main_menu())
        return
    opid = str(uuid.uuid4())
    pending_delete[opid] = {"user_id": uid, "ts": int(time.time())}
    # إرسال طلب للأدمن فقط
    admin_text = f"⚠️ طلب حذف حساب\n\n🆔 المستخدم: <code>{uid}</code>\nهل تريد حذف حسابه؟"
    bot.send_message(ADMIN_ID, admin_text, reply_markup=admin_approve_markup("delete", opid))
    bot.send_message(uid, "⏳ تم إرسال طلب حذف الحساب للإدارة للمراجعة.", reply_markup=main_menu())

@bot.callback_query_handler(func=lambda call: call.data.startswith("delete_ok_") or call.data.startswith("delete_no_"))
def handle_admin_delete(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "غير مصرح.")
        return
    parts = call.data.split("_")
    action = parts[1]
    opid = parts[2]
    if opid not in pending_delete:
        bot.answer_callback_query(call.id, "الطلب غير موجود أو تم معالجته.")
        return
    uid = pending_delete[opid]["user_id"]
    if action == "no":
        bot.send_message(uid, "❌ تم رفض طلب حذف حسابك من قبل الإدارة.", reply_markup=main_menu())
        bot.send_message(ADMIN_ID, f"✅ تم رفض حذف حساب المستخدم {uid}.")
        del pending_delete[opid]
        return
    # ok -> حذف الحساب
    users = load_users()
    if uid in users:
        del users[uid]
        save_users(users)
    bot.send_message(uid, "✅ تم حذف حسابك بنجاح. يمكنك الآن إنشاء حساب جديد.", reply_markup=main_menu())
    bot.send_message(ADMIN_ID, f"✅ تم حذف حساب المستخدم {uid}.")
    del pending_delete[opid]

# ==========================
# 6) دعم فني — عرض رابط الدعم وإمكانية الرجوع
# ==========================
@bot.callback_query_handler(func=lambda call: call.data == "support")
def on_support(call):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("💬 افتح المحادثة مع الدعم", url=f"https://t.me/{SUPPORT_USERNAME.replace('@','')}"))
    markup.add(types.InlineKeyboardButton("⬅️ رجوع", callback_data="back"))
    bot.send_message(call.message.chat.id, "🧑‍💻 للتواصل مع الدعم، اضغط الزر أدناه:", reply_markup=markup)

# ==========================
# 7) زر الرجوع — يعيد المستخدم إلى القائمة الرئيسية
# ==========================
@bot.callback_query_handler(func=lambda call: call.data == "back")
def on_back(call):
    try:
        bot.edit_message_text("🏠 القائمة الرئيسية:", call.message.chat.id, call.message.message_id, reply_markup=main_menu())
    except:
        # إذا تعذر التعديل (مثلاً بعض الرسائل لا يمكن تحريرها)، نرسل رسالة جديدة
        bot.send_message(call.message.chat.id, "🏠 القائمة الرئيسية:", reply_markup=main_menu())

# ==========================
# 8) رسالة جماعية — الأمر /broadcast فقط للأدمن
#    الأدمن يرسل /broadcast، يطلب نص الرسالة، ثم يرسل لكل مستخدم مسجّل
# ==========================
@bot.message_handler(commands=["broadcast"])
def cmd_broadcast(message):
    if message.from_user.id != ADMIN_ID:
        return
    msg = bot.send_message(message.chat.id, "📢 أرسل الرسالة التي تريد إرسالها لجميع المستخدمين:")
    bot.register_next_step_handler(msg, do_broadcast)

def do_broadcast(message):
    if message.from_user.id != ADMIN_ID:
        return
    text = message.text or ""
    users = load_users()
    count = 0
    for uid in users:
        try:
            bot.send_message(int(uid), f"📢 رسالة من الإدارة:\n\n{text}")
            count += 1
        except:
            continue
    bot.send_message(ADMIN_ID, f"✅ تم إرسال الرسالة إلى {count} مستخدم(ـين).")

# ==========================
# 9) مساعدة صغيرة — أمر /users لعرض عدد المستخدمين (للأدمن فقط)
# ==========================
@bot.message_handler(commands=["users"])
def cmd_users(message):
    if message.from_user.id != ADMIN_ID:
        return
    users = load_users()
    bot.send_message(ADMIN_ID, f"👥 عدد المستخدمين المسجلين حالياً: {len(users)}")

# ==========================
# 10) معالجة رسائل أخرى (صور/نصوص) عند الحاجة
#     — لتجنّب فقدان next_step_handler، نحتفظ بالمنطق أعلاه
# ==========================

# ==========================
# 11) بدء التشغيل
# ==========================
print("✅ Bot is running...")
bot.infinity_polling()
