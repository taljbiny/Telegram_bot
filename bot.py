# bot.py
# متطلبات: pip install pyTelegramBotAPI
import os
import json
import time
import threading
from telebot import TeleBot, types

# ============================
# ====== الإعدادات ======
# ============================
BOT_TOKEN = "8317743306:AAHAM9svd23L2mqSfHnPFEsqKY_bavW3kMg"
ADMIN_ID = 7625893170
SUPPORT_USERNAME = "@supp_mo"
SARI_CASH_CODE = "82492253"
SHAM_CASH_CODE = "131efe4fbccd83a811282761222eee69"
MIN_AMOUNT = 25000  # الحد الأدنى للعملية

# ============================
# ====== تهيئة البوت وملفات البيانات ======
# ============================
bot = TeleBot(BOT_TOKEN)

DATA_DIR = "data"
USERS_FILE = os.path.join(DATA_DIR, "users.json")
REQUESTS_FILE = os.path.join(DATA_DIR, "requests.json")
ADMIN_MAP_FILE = os.path.join(DATA_DIR, "admin_map.json")

os.makedirs(DATA_DIR, exist_ok=True)

def load_json(path, default):
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(default, f, ensure_ascii=False, indent=2)
        return default.copy()
    with open(path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except Exception:
            return default.copy()

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

users = load_json(USERS_FILE, {"users": {}})         # structure: { "users": { "<user_id>": {...} } }
requests_db = load_json(REQUESTS_FILE, {})           # structure: { "<req_id>": {...} }
admin_map = load_json(ADMIN_MAP_FILE, {})            # map: admin_message_id -> req_id

# ============================
# ====== مساعدة و Utilities ======
# ============================
def now_ts():
    return int(time.time())

def gen_request_id():
    return str(int(time.time() * 1000))

def touch_user(tg_user):
    """Ensure user exists in users and update last_active. Returns uid (str)."""
    uid = str(tg_user.id)
    changed = False
    if uid not in users["users"]:
        users["users"][uid] = {
            "user_id": tg_user.id,
            "username": tg_user.username or "",
            "name": tg_user.full_name,
            "created_at": now_ts(),
            "last_active": now_ts(),
            "account_name": None,
            "password_set": False,
            "approved": False,
            "state": "idle"  # used for flow management
        }
        changed = True
    else:
        users["users"][uid]["username"] = tg_user.username or users["users"][uid].get("username", "")
        users["users"][uid]["name"] = tg_user.full_name
        users["users"][uid]["last_active"] = now_ts()
        changed = True
    if changed:
        save_json(USERS_FILE, users)
    return uid

def set_user_state(uid, state):
    users["users"][uid]["state"] = state
    save_json(USERS_FILE, users)

def clear_user_flow(uid):
    # remove temporary flow keys but keep account info
    keys_to_keep = {"user_id","username","name","created_at","last_active","account_name","password_set","approved","state"}
    data = users["users"].get(uid, {})
    new = {k: v for k, v in data.items() if k in keys_to_keep}
    users["users"][uid] = new
    save_json(USERS_FILE, users)

# ============================
# ====== Keyboards (Inline - تظهر أعلى الرسالة) ======
# ============================
def main_keyboard():
    kb = types.InlineKeyboardMarkup()
    kb.row(
        types.InlineKeyboardButton("🆕 إنشاء حساب", callback_data="create_account"),
        types.InlineKeyboardButton("💰 شحن", callback_data="deposit_start"),
        types.InlineKeyboardButton("💸 سحب", callback_data="withdraw_start"),
    )
    kb.row(
        types.InlineKeyboardButton("🎧 الدعم الفني", callback_data="support"),
        types.InlineKeyboardButton("🗑️ طلب حذف الحساب", callback_data="request_delete_account"),
    )
    return kb

def back_inline():
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("⬅️ رجوع", callback_data="back_to_main"))
    return kb

def wallet_inline():
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("📋 نسخ كود سرياتيل كاش", callback_data="copy_sari"))
    kb.add(types.InlineKeyboardButton("📋 نسخ كود شام كاش", callback_data="copy_sham"))
    kb.add(types.InlineKeyboardButton("⬅️ رجوع", callback_data="back_to_main"))
    return kb

def deposit_method_keyboard():
    kb = types.InlineKeyboardMarkup()
    kb.row(
        types.InlineKeyboardButton("💳 سرياتيل كاش", callback_data="deposit_method_sari"),
        types.InlineKeyboardButton("🏦 شام كاش", callback_data="deposit_method_sham")
    )
    kb.add(types.InlineKeyboardButton("⬅️ رجوع", callback_data="back_to_main"))
    return kb

def withdraw_method_keyboard():
    kb = types.InlineKeyboardMarkup()
    kb.row(
        types.InlineKeyboardButton("💳 سرياتيل كاش", callback_data="withdraw_method_sari"),
        types.InlineKeyboardButton("🏦 شام كاش", callback_data="withdraw_method_sham")
    )
    kb.add(types.InlineKeyboardButton("⬅️ رجوع", callback_data="back_to_main"))
    return kb

# admin action keyboard for requests
def admin_action_kb(req_id):
    kb = types.InlineKeyboardMarkup()
    kb.row(
        types.InlineKeyboardButton("✅ موافقة", callback_data=f"admin_approve|{req_id}"),
        types.InlineKeyboardButton("❌ رفض", callback_data=f"admin_reject|{req_id}")
    )
    kb.row(
        types.InlineKeyboardButton("✉️ رد للمستخدم", callback_data=f"admin_reply|{req_id}")
    )
    # For delete requests add delete_ok (same as approve but clarifies)
    return kb

# ============================
# ====== /start handler ======
# ============================
@bot.message_handler(commands=["start"])
def cmd_start(m):
    touch_user(m.from_user)
    bot.send_message(m.chat.id, f"مرحبًا {m.from_user.full_name} 👋\nاختر ما تريد من الأزرار أدناه:", reply_markup=main_keyboard())

# ============================
# ====== Create account flow (2 steps: name + password) ======
# ============================
@bot.callback_query_handler(func=lambda c: c.data == "create_account")
def cb_create_account(c):
    uid = touch_user(c.from_user)
    user = users["users"][uid]
    # if already has an account and approved, block new creation
    if user.get("account_name") and user.get("approved"):
        bot.answer_callback_query(c.id, "⚠️ لديك حساب مفعل بالفعل. إذا أردت حذفه اضغط طلب حذف الحساب.")
        return
    # if has account but not approved — still prevent creating a new one until admin handles?
    if user.get("account_name") and not user.get("approved"):
        # allow re-sending creation request? We'll prevent duplicate: tell user waiting.
        bot.answer_callback_query(c.id, "⚠️ لديك طلب إنشاء حساب قيد المراجعة بالفعل.")
        return
    # start flow
    set_user_state(uid, "creating_account_wait_name")
    bot.edit_message_text("📝 أرسل اسم الحساب الذي تريد تسجيله:", c.message.chat.id, c.message.message_id, reply_markup=back_inline())

@bot.message_handler(func=lambda m: users["users"].get(str(m.chat.id), {}).get("state") == "creating_account_wait_name", content_types=["text"])
def handle_account_name(m):
    uid = touch_user(m.from_user)
    name = m.text.strip()
    if not name:
        bot.send_message(m.chat.id, "❌ الاسم لا يمكن أن يكون فارغًا. حاول مرة أخرى.", reply_markup=back_inline())
        return
    users["users"][uid]["account_name"] = name
    set_user_state(uid, "creating_account_wait_password")
    save_json(USERS_FILE, users)
    bot.send_message(m.chat.id, "🔒 الآن أرسل كلمة المرور التي تريدها للحساب:", reply_markup=back_inline())

@bot.message_handler(func=lambda m: users["users"].get(str(m.chat.id), {}).get("state") == "creating_account_wait_password", content_types=["text"])
def handle_account_password(m):
    uid = touch_user(m.from_user)
    pwd = m.text.strip()
    if not pwd:
        bot.send_message(m.chat.id, "❌ كلمة المرور لا يمكن أن تكون فارغة. حاول ثانية.", reply_markup=back_inline())
        return
    users["users"][uid]["password"] = pwd
    users["users"][uid]["password_set"] = True
    users["users"][uid]["approved"] = False
    users["users"][uid]["state"] = "idle"
    save_json(USERS_FILE, users)
    # create a request record for admin to approve creation
    rid = gen_request_id()
    req = {
        "id": rid,
        "type": "create_account",
        "user_id": int(uid),
        "account_name": users["users"][uid]["account_name"],
        "password": pwd,
        "status": "pending",
        "created_at": now_ts()
    }
    requests_db[rid] = req
    save_json(REQUESTS_FILE, requests_db)
    # notify user
    bot.send_message(m.chat.id, "✅ تم إرسال طلب إنشاء الحساب للإدارة للموافقة. ستصلك رسالة عند القرار.", reply_markup=main_keyboard())
    # send to admin with admin action buttons
    text = (f"📥 طلب إنشاء حساب جديد\n\n"
            f"👤 المستخدم: @{users['users'][uid].get('username','')}\n"
            f"🆔 ID: {uid}\n"
            f"📛 اسم الحساب: {users['users'][uid].get('account_name')}\n"
            f"🔑 كلمة المرور: {pwd}\n"
            f"⏱️ الوقت: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(req['created_at']))}")
    sent = bot.send_message(ADMIN_ID, text, reply_markup=admin_action_kb(rid))
    admin_map[str(sent.message_id)] = rid
    save_json(ADMIN_MAP_FILE, admin_map)

# ============================
# ====== Request delete account (user) -> admin decides ======
# ============================
@bot.callback_query_handler(func=lambda c: c.data == "request_delete_account")
def cb_request_delete(c):
    uid = touch_user(c.from_user)
    user = users["users"][uid]
    if not user.get("account_name"):
        bot.answer_callback_query(c.id, "❌ لا يوجد لديك حساب مسجل أصلاً.")
        return
    # create delete request
    rid = gen_request_id()
    req = {
        "id": rid,
        "type": "delete_account",
        "user_id": int(uid),
        "account_name": user.get("account_name"),
        "status": "pending",
        "created_at": now_ts()
    }
    requests_db[rid] = req
    save_json(REQUESTS_FILE, requests_db)
    bot.send_message(c.message.chat.id, "🗑️ تم إرسال طلب حذف الحساب للإدارة. سيتم إبلاغك بالقرار.", reply_markup=main_keyboard())
    text = (f"🗑️ طلب حذف حساب\n\n"
            f"👤 المستخدم: @{user.get('username','')}\n"
            f"🆔 ID: {uid}\n"
            f"📛 الحساب: {user.get('account_name')}\n"
            f"⏱️ الوقت: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(req['created_at']))}")
    sent = bot.send_message(ADMIN_ID, text, reply_markup=admin_action_kb(rid))
    admin_map[str(sent.message_id)] = rid
    save_json(ADMIN_MAP_FILE, admin_map)

# ============================
# ====== Deposit flow ======
# ============================
@bot.callback_query_handler(func=lambda c: c.data == "deposit_start")
def cb_deposit_start(c):
    uid = touch_user(c.from_user)
    user = users["users"][uid]
    if not user.get("account_name") or not user.get("password_set"):
        bot.answer_callback_query(c.id, "⚠️ يجب أن يكون لديك حساب مفعل أو مُقدّم قبل الشحن.")
        return
    set_user_state(uid, "deposit_choose_method")
    bot.edit_message_text("💰 اختر طريقة الشحن:", c.message.chat.id, c.message.message_id, reply_markup=deposit_method_keyboard())

@bot.callback_query_handler(func=lambda c: c.data in ["deposit_method_sari", "deposit_method_sham"])
def cb_deposit_method(c):
    uid = touch_user(c.from_user)
    if users["users"][uid].get("state") != "deposit_choose_method":
        bot.answer_callback_query(c.id, "يرجى اتباع الخطوات.")
        return
    method = "سرياتيل كاش" if c.data.endswith("sari") else "شام كاش"
    code = SARI_CASH_CODE if c.data.endswith("sari") else SHAM_CASH_CODE
    users["users"][uid]["state"] = f"deposit_amount_{'sari' if c.data.endswith('sari') else 'sham'}"
    users["users"][uid]["deposit_method"] = method
    users["users"][uid]["deposit_code"] = code
    save_json(USERS_FILE, users)
    bot.edit_message_text(f"أرسل الآن قيمة الشحن (الحد الأدنى {MIN_AMOUNT}):", c.message.chat.id, c.message.message_id, reply_markup=wallet_inline())

@bot.message_handler(func=lambda m: users["users"].get(str(m.chat.id), {}).get("state", "").startswith("deposit_amount_"), content_types=["text"])
def handle_deposit_amount(m):
    uid = touch_user(m.from_user)
    st = users["users"][uid].get("state", "")
    try:
        amount = int(m.text.strip())
    except:
        bot.send_message(m.chat.id, "❌ الرجاء إرسال مبلغ رقمي صحيح.", reply_markup=wallet_inline())
        return
    if amount < MIN_AMOUNT:
        bot.send_message(m.chat.id, f"❌ الحد الأدنى للشحن هو {MIN_AMOUNT}.", reply_markup=wallet_inline())
        return
    users["users"][uid]["deposit_amount"] = amount
    users["users"][uid]["state"] = "deposit_wait_proof"
    save_json(USERS_FILE, users)
    bot.send_message(m.chat.id, ("📸 الآن أرسل صورة الإيصال أو اكتب رمز/تفاصيل العملية للتأكيد.\n"
                                 "يمكنك أيضاً استخدام زر نسخ الكود لإرسال الكود إلى محفظتك ثم تحويل المبلغ."), reply_markup=back_inline())

@bot.message_handler(content_types=["photo","document","text"], func=lambda m: users["users"].get(str(m.chat.id), {}).get("state") == "deposit_wait_proof")
def handle_deposit_proof(m):
    uid = touch_user(m.from_user)
    user = users["users"][uid]
    # build request
    rid = gen_request_id()
    req = {
        "id": rid,
        "type": "deposit",
        "user_id": int(uid),
        "account_name": user.get("account_name"),
        "amount": user.get("deposit_amount"),
        "method": user.get("deposit_method"),
        "status": "pending",
        "created_at": now_ts()
    }
    # attach proof (text or file_id)
    if m.content_type == "photo":
        file_id = m.photo[-1].file_id
        req["proof_type"] = "photo"
        req["proof_file_id"] = file_id
    elif m.content_type == "document":
        file_id = m.document.file_id
        req["proof_type"] = "document"
        req["proof_file_id"] = file_id
    else:
        req["proof_type"] = "text"
        req["proof_text"] = m.text.strip()
    # save request
    requests_db[rid] = req
    save_json(REQUESTS_FILE, requests_db)
    # clear user flow state
    clear_user_flow(uid)
    bot.send_message(m.chat.id, "✅ تم إرسال طلب الشحن إلى الأدمن للمراجعة.", reply_markup=main_keyboard())
    # prepare admin message
    caption = (f"📥 طلب شحن جديد\n\n👤 @{user.get('username','')}\n🆔 ID: {uid}\n📛 الحساب: {user.get('account_name')}\n"
               f"💵 المبلغ: {req['amount']}\n🏦 الطريقة: {req['method']}\n⏱️ {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(req['created_at']))}")
    # send proof to admin with action buttons
    if req.get("proof_type") in ("photo","document"):
        try:
            if req["proof_type"] == "photo":
                sent = bot.send_photo(ADMIN_ID, req["proof_file_id"], caption)
            else:
                sent = bot.send_document(ADMIN_ID, req["proof_file_id"], caption)
            admin_map[str(sent.message_id)] = rid
        except Exception:
            sent = bot.send_message(ADMIN_ID, caption + "\n(المرفق لم يُرسل تلقائياً)")
            admin_map[str(sent.message_id)] = rid
    else:
        sent = bot.send_message(ADMIN_ID, caption + f"\n🧾 تفاصيل الإيصال: {req.get('proof_text','')}")
        admin_map[str(sent.message_id)] = rid
    # add admin action buttons below the admin message
    try:
        bot.edit_message_reply_markup(ADMIN_ID, sent.message_id, reply_markup=admin_action_kb(rid))
    except Exception:
        # some send methods may not allow edit; instead, send a new message with buttons
        sent2 = bot.send_message(ADMIN_ID, f"إجراءات للطلب: {rid}", reply_markup=admin_action_kb(rid))
        admin_map[str(sent2.message_id)] = rid
    save_json(ADMIN_MAP_FILE, admin_map)

# ============================
# ====== Withdraw flow ======
# ============================
@bot.callback_query_handler(func=lambda c: c.data == "withdraw_start")
def cb_withdraw_start(c):
    uid = touch_user(c.from_user)
    user = users["users"][uid]
    if not user.get("account_name") or not user.get("password_set"):
        bot.answer_callback_query(c.id, "⚠️ يجب أن يكون لديك حساب مُسجل قبل طلب سحب.")
        return
    set_user_state(uid, "withdraw_choose_method")
    bot.edit_message_text("💸 اختر طريقة السحب:", c.message.chat.id, c.message.message_id, reply_markup=withdraw_method_keyboard())

@bot.callback_query_handler(func=lambda c: c.data in ["withdraw_method_sari", "withdraw_method_sham"])
def cb_withdraw_method(c):
    uid = touch_user(c.from_user)
    if users["users"][uid].get("state") != "withdraw_choose_method":
        bot.answer_callback_query(c.id, "يرجى اتباع الخطوات.")
        return
    method = "سرياتيل كاش" if c.data.endswith("sari") else "شام كاش"
    users["users"][uid]["state"] = f"withdraw_amount_{'sari' if c.data.endswith('sari') else 'sham'}"
    users["users"][uid]["withdraw_method"] = method
    save_json(USERS_FILE, users)
    bot.edit_message_text("أدخل مبلغ السحب (الحد الأدنى {MIN_AMOUNT}):".format(MIN_AMOUNT=MIN_AMOUNT),
                          c.message.chat.id, c.message.message_id, reply_markup=back_inline())

@bot.message_handler(func=lambda m: users["users"].get(str(m.chat.id), {}).get("state", "").startswith("withdraw_amount_"), content_types=["text"])
def handle_withdraw_amount(m):
    uid = touch_user(m.from_user)
    try:
        amount = int(m.text.strip())
    except:
        bot.send_message(m.chat.id, "❌ الرجاء إرسال مبلغ رقمي صحيح.", reply_markup=back_inline())
        return
    if amount < MIN_AMOUNT:
        bot.send_message(m.chat.id, f"❌ الحد الأدنى للسحب هو {MIN_AMOUNT}.", reply_markup=back_inline())
        return
    users["users"][uid]["withdraw_amount"] = amount
    users["users"][uid]["state"] = "withdraw_wait_wallet"
    save_json(USERS_FILE, users)
    bot.send_message(m.chat.id, "الآن أرسل رقم/كود محفظتك (أو أرسل صورة QR):", reply_markup=back_inline())

@bot.message_handler(content_types=["photo","document","text"], func=lambda m: users["users"].get(str(m.chat.id), {}).get("state") == "withdraw_wait_wallet")
def handle_withdraw_wallet(m):
    uid = touch_user(m.from_user)
    user = users["users"][uid]
    rid = gen_request_id()
    req = {
        "id": rid,
        "type": "withdraw",
        "user_id": int(uid),
        "account_name": user.get("account_name"),
        "amount": user.get("withdraw_amount"),
        "method": user.get("withdraw_method"),
        "status": "pending",
        "created_at": now_ts()
    }
    if m.content_type == "photo":
        req["proof_type"] = "photo"
        req["proof_file_id"] = m.photo[-1].file_id
    elif m.content_type == "document":
        req["proof_type"] = "document"
        req["proof_file_id"] = m.document.file_id
    else:
        req["proof_type"] = "text"
        req["wallet_code"] = m.text.strip()
    requests_db[rid] = req
    save_json(REQUESTS_FILE, requests_db)
    clear_user_flow(uid)
    bot.send_message(m.chat.id, "✅ تم إرسال طلب السحب إلى الأدمن للمراجعة.", reply_markup=main_keyboard())
    caption = (f"💸 طلب سحب جديد\n\n👤 @{user.get('username','')}\n🆔 ID: {uid}\n📛 الحساب: {user.get('account_name')}\n"
               f"💵 المبلغ: {req['amount']}\n🏦 الطريقة: {req['method']}\n⏱️ {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(req['created_at']))}")
    if req.get("proof_type") in ("photo","document"):
        try:
            if req["proof_type"] == "photo":
                sent = bot.send_photo(ADMIN_ID, req["proof_file_id"], caption)
            else:
                sent = bot.send_document(ADMIN_ID, req["proof_file_id"], caption)
            admin_map[str(sent.message_id)] = rid
        except Exception:
            sent = bot.send_message(ADMIN_ID, caption + "\n(المرفق لم يُرسل تلقائياً)")
            admin_map[str(sent.message_id)] = rid
    else:
        sent = bot.send_message(ADMIN_ID, caption + (f"\n🪪 محفظة المستخدم: {req.get('wallet_code','')}"))
        admin_map[str(sent.message_id)] = rid
    try:
        bot.edit_message_reply_markup(ADMIN_ID, sent.message_id, reply_markup=admin_action_kb(rid))
    except Exception:
        sent2 = bot.send_message(ADMIN_ID, f"إجراءات للطلب: {rid}", reply_markup=admin_action_kb(rid))
        admin_map[str(sent2.message_id)] = rid
    save_json(ADMIN_MAP_FILE, admin_map)

# ============================
# ====== Support (open link) ======
# ============================
@bot.callback_query_handler(func=lambda c: c.data == "support")
def cb_support(c):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("فتح محادثة الدعم", url=f"https://t.me/{SUPPORT_USERNAME.lstrip('@')}"))
    kb.add(types.InlineKeyboardButton("⬅️ رجوع", callback_data="back_to_main"))
    bot.edit_message_text("💬 تواصل مع الدعم عبر الزر أدناه:", c.message.chat.id, c.message.message_id, reply_markup=kb)

# ============================
# ====== Inline callbacks: copy codes & back & admin actions ======
# ============================
@bot.callback_query_handler(func=lambda call: True)
def inline_cb(call):
    data = call.data
    uid = touch_user(call.from_user)
    # copy code handlers
    if data == "copy_sari":
        bot.answer_callback_query(call.id, "الكود أُرسل لك في رسالة مستقلة للنسخ.", show_alert=False)
        bot.send_message(call.from_user.id, f"كود سرياتيل كاش:\n`{SARI_CASH_CODE}`", parse_mode="Markdown")
        return
    if data == "copy_sham":
        bot.answer_callback_query(call.id, "الكود أُرسل لك في رسالة مستقلة للنسخ.", show_alert=False)
        bot.send_message(call.from_user.id, f"كود شام كاش:\n`{SHAM_CASH_CODE}`", parse_mode="Markdown")
        return
    if data == "back_to_main":
        # edit message back to main menu
        try:
            bot.edit_message_text("🏠 القائمة الرئيسية:", call.message.chat.id, call.message.message_id, reply_markup=main_keyboard())
        except Exception:
            bot.send_message(call.message.chat.id, "🏠 القائمة الرئيسية:", reply_markup=main_keyboard())
        set_user_state(uid, "idle")
        return

    # admin actions like approve/reject/reply |<rid>
    if data.startswith("admin_"):
        parts = data.split("|")
        if len(parts) != 2:
            bot.answer_callback_query(call.id, "خطأ في بيانات الزر.")
            return
        action, rid = parts[0], parts[1]
        # only admin allowed
        if call.from_user.id != ADMIN_ID:
            bot.answer_callback_query(call.id, "غير مسموح - فقط الأدمن.", show_alert=True)
            return
        req = requests_db.get(rid)
        if not req:
            bot.answer_callback_query(call.id, "الطلب غير موجود أو منتهي.", show_alert=True)
            return
        # APPROVE
        if action == "admin_approve":
            req["status"] = "approved"
            req["handled_at"] = now_ts()
            requests_db[rid] = req
            save_json(REQUESTS_FILE, requests_db)
            # specific actions per request type
            if req["type"] == "create_account":
                uid = str(req["user_id"])
                if uid in users["users"]:
                    users["users"][uid]["approved"] = True
                    save_json(USERS_FILE, users)
                    bot.send_message(int(uid), f"✅ تمت الموافقة على إنشاء الحساب '{req.get('account_name')}'. يمكنك الآن استخدام الشحن والسحب.", reply_markup=main_keyboard())
            elif req["type"] == "delete_account":
                uid = str(req["user_id"])
                # delete user data entirely (remove from users)
                if uid in users["users"]:
                    users["users"].pop(uid, None)
                    save_json(USERS_FILE, users)
                    bot.send_message(int(uid), "🗑️ تم حذف معلومات حسابك بناءً على موافقة الأدمن. يمكنك إنشاء حساب جديد إذا رغبت.", reply_markup=main_keyboard())
            elif req["type"] == "deposit":
                bot.send_message(int(req["user_id"]), f"✅ تمت الموافقة على طلب الشحن بمبلغ {req.get('amount')} ({req.get('method')}).", reply_markup=main_keyboard())
            elif req["type"] == "withdraw":
                bot.send_message(int(req["user_id"]), f"✅ تمت الموافقة على طلب السحب بمبلغ {req.get('amount')} ({req.get('method')}).", reply_markup=main_keyboard())
            # confirm to admin
            bot.edit_message_text(f"✅ تمت الموافقة على الطلب ({req['type']}).", call.message.chat.id, call.message.message_id)
            bot.answer_callback_query(call.id, "تمت الموافقة.")
            return
        # REJECT
        if action == "admin_reject":
            req["status"] = "rejected"
            req["handled_at"] = now_ts()
            requests_db[rid] = req
            save_json(REQUESTS_FILE, requests_db)
            # notify user
            bot.send_message(int(req["user_id"]), f"❌ تم رفض طلبك من النوع: {req['type']}. إذا أردت توضيحًا راسل الدعم.", reply_markup=main_keyboard())
            bot.edit_message_text(f"❌ تم رفض الطلب ({req['type']}).", call.message.chat.id, call.message.message_id)
            bot.answer_callback_query(call.id, "تم الرفض.")
            return
        # REPLY action triggers admin to type a reply message (we will map by instructing admin)
        if action == "admin_reply":
            bot.answer_callback_query(call.id, "أرسل ردك بالرد على هذه الرسالة (Reply) لأرسله للمستخدم.", show_alert=True)
            return

    # Catch all other inline cases
    bot.answer_callback_query(call.id, "تم.", show_alert=False)

# ============================
# ====== Admin replies handling: when admin REPLIES to the admin message, forward to user ======
# ============================
@bot.message_handler(func=lambda m: m.reply_to_message is not None and m.from_user.id == ADMIN_ID, content_types=['text','photo','document'])
def admin_reply_handler(m):
    # try to find request id by reply_to_message.message_id
    replied_mid = str(m.reply_to_message.message_id)
    rid = admin_map.get(replied_mid)
    if not rid:
        # Could be other admin message; try scanning for request id in original text
        bot.send_message(ADMIN_ID, "لم أتمكن من ربط هذا الرد بطلب. الرجاء الرد مباشرة على رسالة الطلب المرسلة من البوت.")
        return
    req = requests_db.get(rid)
    if not req:
        bot.send_message(ADMIN_ID, "الطلب غير موجود أو تم حذفه.")
        return
    target_uid = int(req["user_id"])
    # forward admin content to user
    if m.content_type == "text":
        bot.send_message(target_uid, f"رسالة من الأدمن:\n\n{m.text}", reply_markup=main_keyboard())
    elif m.content_type == "photo":
        file_id = m.photo[-1].file_id
        bot.send_photo(target_uid, file_id, caption=(m.caption or "صورة من الأدمن"))
    elif m.content_type == "document":
        file_id = m.document.file_id
        bot.send_document(target_uid, file_id, caption=(m.caption or "ملف من الأدمن"))
    bot.send_message(ADMIN_ID, "✅ تم إرسال ردك للمستخدم.")

# ============================
# ====== Catch-all to keep last_active and basic flow safety ======
# ============================
@bot.message_handler(func=lambda m: True, content_types=['text','photo','document'])
def catch_all(m):
    touch_user(m.from_user)
    # If user presses "⬅️ رجوع" as plain text or sends "إلغاء"
    if m.content_type == "text":
        txt = m.text.strip()
        if txt in ["⬅️ رجوع", "رجوع", "إلغاء"]:
            uid = str(m.from_user.id)
            set_user_state(uid, "idle")
            bot.send_message(m.chat.id, "تم الرجوع إلى القائمة الرئيسية.", reply_markup=main_keyboard())
            return
    # otherwise do nothing here; specific handlers above will process flows

# ============================
# ====== Background cleanup: remove inactive users after 30 days ======
# ============================
def cleanup_inactive():
    try:
        now = now_ts()
        cutoff = now - 30*24*3600
        removed = []
        for uid, u in list(users["users"].items()):
            last = u.get("last_active", u.get("created_at", 0))
            if last < cutoff:
                removed.append(uid)
                users["users"].pop(uid, None)
        if removed:
            save_json(USERS_FILE, users)
        # schedule next cleanup in 24h
        threading.Timer(24*3600, cleanup_inactive).start()
    except Exception as e:
        print("cleanup error:", e)
        threading.Timer(24*3600, cleanup_inactive).start()

# start cleanup after short delay
threading.Timer(5, cleanup_inactive).start()

# ============================
# ====== Start polling ======
# ============================
if __name__ == "__main__":
    print("Bot is running...")
    bot.infinity_polling()
