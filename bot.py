# bot.py
# متطلبات: pip install pyTelegramBotAPI
import telebot
from telebot import types
import os, json, time, threading

# ====== إعدادات (استبدل إذا حبيت لكن حالياً حسب بياناتك) ======
TOKEN = "8317743306:AAHAM9svd23L2mqSfHnPFEsqKY_bavW3kMg"
ADMIN_ID = 7625893170
SUPPORT_USERNAME = "@supp_mo"
SARI_CASH_CODE = "82492253"
SHAM_CASH_CODE = "131efe4fbccd83a811282761222eee69"
MIN_AMOUNT = 25000  # الحد الأدنى بالوحدة المتفق عليها

# ====== تهيئة ======
bot = telebot.TeleBot(TOKEN)
DATA_DIR = "data"
USERS_FILE = os.path.join(DATA_DIR, "users.json")
REQUESTS_FILE = os.path.join(DATA_DIR, "requests.json")
ADMIN_MAP_FILE = os.path.join(DATA_DIR, "admin_map.json")  # map admin_message_id -> request_id

# Ensure data dir
os.makedirs(DATA_DIR, exist_ok=True)

# JSON helpers
def load_json(path, default):
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(default, f, ensure_ascii=False, indent=2)
        return default.copy()
    with open(path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except:
            return default.copy()

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

users = load_json(USERS_FILE, {})        # key: user_id (str) -> user data
requests_db = load_json(REQUESTS_FILE, {})  # key: request_id -> request info
admin_map = load_json(ADMIN_MAP_FILE, {})   # key: admin_message_id (str) -> request_id (str)

# Utility: make main top keyboard (buttons always on top)
def top_keyboard():
    kb = types.ReplyKeyboardMarkup(row_width=3, resize_keyboard=True)
    kb.add("إنشاء حساب", "شحن الحساب", "سحب من الحساب")
    kb.add("تواصل مع الدعم", "طلب حذف الحساب")
    return kb

# Small keyboard with back button
def back_keyboard():
    kb = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    kb.add("🔙 رجوع", "إلغاء")
    return kb

# Inline keyboard for wallet codes with "copy" button
def wallet_inline_markup():
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("📋 نسخ كود سيرياتيل كاش", callback_data="copy_sari"))
    kb.add(types.InlineKeyboardButton("📋 نسخ كود شام كاش", callback_data="copy_sham"))
    kb.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="inline_back"))
    return kb

# Generate request id
def new_request_id():
    return str(int(time.time()*1000))

# Cleanup: remove users inactive > 30 days
def cleanup_inactive():
    now = int(time.time())
    cutoff = now - 30*24*3600  # 30 days
    removed = []
    for uid, u in list(users.items()):
        if u.get("last_active", u.get("created_at", 0)) < cutoff:
            removed.append(uid)
            users.pop(uid, None)
    if removed:
        save_json(USERS_FILE, users)
    # reschedule next cleanup in 24h
    threading.Timer(24*3600, cleanup_inactive).start()

# start cleanup timer
threading.Timer(5, cleanup_inactive).start()

# Update user's last_active and basic profile
def touch_user(tg_user):
    uid = str(tg_user.id)
    changed = False
    if uid not in users:
        users[uid] = {
            "user_id": tg_user.id,
            "username": tg_user.username or "",
            "name": tg_user.full_name,
            "created_at": int(time.time()),
            "last_active": int(time.time()),
            "account_name": None,
            "approved": False
        }
        changed = True
    else:
        users[uid]["username"] = tg_user.username or users[uid].get("username", "")
        users[uid]["name"] = tg_user.full_name
        users[uid]["last_active"] = int(time.time())
        changed = True
    if changed:
        save_json(USERS_FILE, users)
    return uid

# Send a request to admin with inline action buttons
def send_request_to_admin(req):
    # req is dict with: id, type, user_id, data...
    text_lines = []
    text_lines.append(f"📨 طلب جديد: {req['type']}")
    u = users.get(str(req["user_id"]), {})
    text_lines.append(f"👤 المستخدم: {u.get('name','-')} (id: {req['user_id']})")
    if req.get("account_name"):
        text_lines.append(f"🏷️ اسم الحساب: {req['account_name']}")
    if req.get("amount"):
        text_lines.append(f"💵 المبلغ: {req['amount']}")
    if req.get("method"):
        text_lines.append(f"💳 الطريقة: {req['method']}")
    if req.get("wallet_code"):
        text_lines.append(f"🪪 كود المحفظة: {req['wallet_code']}")
    text = "\n".join(text_lines)
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("✅ موافقة", callback_data=f"approve|{req['id']}"))
    kb.add(types.InlineKeyboardButton("❌ رفض", callback_data=f"reject|{req['id']}"))
    kb.add(types.InlineKeyboardButton("✉️ رد للمستخدم", callback_data=f"reply|{req['id']}"))
    # Special: if request is a delete-request allow delete approval
    if req["type"] == "delete_account":
        kb.add(types.InlineKeyboardButton("🗑️ موافقة حذف الحساب", callback_data=f"delete_ok|{req['id']}"))
    sent = bot.send_message(ADMIN_ID, text, reply_markup=kb)
    # map admin message id to request id for fallback
    admin_map[str(sent.message_id)] = req["id"]
    save_json(ADMIN_MAP_FILE, admin_map)

# ====== Handlers ======
@bot.message_handler(commands=["start"])
def cmd_start(m):
    uid = touch_user(m.from_user)
    bot.send_message(m.chat.id, f"أهلًا {m.from_user.full_name}! اختر إجراء من الأزرار الأعلى:", reply_markup=top_keyboard())

@bot.message_handler(func=lambda m: m.text == "🔙 رجوع")
def handle_back(m):
    # Just show main top keyboard
    bot.send_message(m.chat.id, "تم الرجوع.", reply_markup=top_keyboard())

@bot.message_handler(func=lambda m: m.text == "إلغاء")
def handle_cancel(m):
    bot.send_message(m.chat.id, "تم الإلغاء.", reply_markup=top_keyboard())
    # Clear any pending state (simple approach)
    if hasattr(bot, "pending"):
        bot.pending.pop(str(m.from_user.id), None)

# إنشاء حساب
@bot.message_handler(func=lambda m: m.text == "إنشاء حساب")
def start_create(m):
    touch_user(m.from_user)
    bot.send_message(m.chat.id, "أدخل اسم الحساب الذي تريد إنشاؤه:", reply_markup=back_keyboard())
    # set pending
    bot.pending = getattr(bot, "pending", {})
    bot.pending[str(m.from_user.id)] = {"action":"create_account_wait_name"}

@bot.message_handler(func=lambda m: getattr(bot, "pending", {}).get(str(m.from_user.id), {}).get("action") == "create_account_wait_name")
def recv_create_name(m):
    uid = touch_user(m.from_user)
    name = m.text.strip()
    users[uid]["account_name"] = name
    save_json(USERS_FILE, users)
    # create request
    rid = new_request_id()
    req = {"id": rid, "type": "create_account", "user_id": int(uid), "account_name": name, "status":"pending", "created_at": int(time.time())}
    requests_db[rid] = req
    save_json(REQUESTS_FILE, requests_db)
    bot.pending.pop(str(m.from_user.id), None)
    bot.send_message(m.chat.id, "تم إرسال طلب إنشاء الحساب إلى الأدمن للمراجعة.", reply_markup=top_keyboard())
    send_request_to_admin(req)

# شحن الحساب
@bot.message_handler(func=lambda m: m.text == "شحن الحساب")
def start_deposit(m):
    touch_user(m.from_user)
    bot.send_message(m.chat.id, "أدخل قيمة الشحن (لا تقل عن 25,000):", reply_markup=back_keyboard())
    bot.pending = getattr(bot, "pending", {})
    bot.pending[str(m.from_user.id)] = {"action":"deposit_wait_amount"}

@bot.message_handler(func=lambda m: getattr(bot, "pending", {}).get(str(m.from_user.id), {}).get("action") == "deposit_wait_amount")
def recv_deposit_amount(m):
    uid = touch_user(m.from_user)
    try:
        val = float(m.text.strip())
    except:
        bot.send_message(m.chat.id, "الرجاء إدخال رقم صالح.", reply_markup=back_keyboard())
        return
    if val < MIN_AMOUNT:
        bot.send_message(m.chat.id, f"الحد الأدنى للشحن هو {MIN_AMOUNT}. أدخل قيمة أكبر أو تساوي الحد.", reply_markup=back_keyboard())
        return
    bot.pending[str(m.from_user.id)] = {"action":"deposit_choose_method", "amount": val}
    # show methods and wallet inline copy
    kb = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    kb.add("سرياتيل كاش", "شام كاش", "🔙 رجوع")
    bot.send_message(m.chat.id, f"المبلغ: {val}. اختر طريقة الدفع:", reply_markup=kb)

@bot.message_handler(func=lambda m: getattr(bot, "pending", {}).get(str(m.from_user.id), {}).get("action") == "deposit_choose_method")
def recv_deposit_method(m):
    uid = touch_user(m.from_user)
    choice = m.text.strip()
    p = bot.pending[str(m.from_user.id)]
    if choice not in ["سرياتيل كاش", "شام كاش", "🔙 رجوع"]:
        bot.send_message(m.chat.id, "اختر خيارًا صحيحًا.", reply_markup=back_keyboard())
        return
    if choice == "🔙 رجوع":
        bot.pending.pop(str(m.from_user.id), None)
        bot.send_message(m.chat.id, "تم الرجوع.", reply_markup=top_keyboard())
        return
    amount = p["amount"]
    # show wallet info with inline copy buttons
    if choice == "سرياتيل كاش":
        text = f"قم بتحويل {amount} إلى سرياتيل كاش عبر الكود التالي:\n`{SARI_CASH_CODE}`\nثم أرسل صورة أو رمز العملية للتأكيد."
    else:
        text = f"قم بتحويل {amount} إلى شام كاش عبر المحفظة التالية:\n`{SHAM_CASH_CODE}`\nثم أرسل صورة أو رمز العملية للتأكيد."
    bot.send_message(m.chat.id, text, parse_mode="Markdown", reply_markup=types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True).add("إرسال إيصال", "🔙 رجوع"))
    # store pending info
    bot.pending[str(m.from_user.id)].update({"action":"deposit_wait_proof", "method": choice, "amount": amount})
    # Also send inline wallet copy markup (separately)
    bot.send_message(m.chat.id, "أزرار نسخ الأكواد:", reply_markup=wallet_inline_markup())

@bot.message_handler(func=lambda m: getattr(bot, "pending", {}).get(str(m.from_user.id), {}).get("action") == "deposit_wait_proof", content_types=["photo", "document", "text"])
def recv_deposit_proof(m):
    uid = touch_user(m.from_user)
    p = bot.pending[str(m.from_user.id)]
    if m.text and m.text.strip() == "🔙 رجوع":
        bot.pending.pop(str(m.from_user.id), None)
        bot.send_message(m.chat.id, "تم الإلغاء.", reply_markup=top_keyboard())
        return
    # Accept photo/document or text code
    proof = None
    file_id = None
    if m.content_type == "photo":
        file_id = m.photo[-1].file_id
    elif m.content_type == "document":
        file_id = m.document.file_id
    elif m.content_type == "text":
        proof = m.text.strip()
    # create request
    rid = new_request_id()
    req = {"id": rid, "type": "deposit", "user_id": int(uid), "amount": p["amount"], "method": p["method"], "status":"pending", "created_at": int(time.time())}
    if proof:
        req["proof_text"] = proof
    requests_db[rid] = req
    save_json(REQUESTS_FILE, requests_db)
    bot.pending.pop(str(m.from_user.id), None)
    bot.send_message(m.chat.id, "تم إرسال طلب الشحن إلى الأدمن للمراجعة.", reply_markup=top_keyboard())
    # send to admin (with photo if exists)
    caption = f"طلب شحن:\nمن: {users[uid]['name']} (id:{uid})\nمبلغ: {req['amount']}\nالطريقة: {req['method']}"
    if file_id:
        try:
            bot.send_photo(ADMIN_ID, file_id, caption=caption)
        except:
            try:
                bot.send_document(ADMIN_ID, file_id, caption=caption)
            except:
                bot.send_message(ADMIN_ID, caption + "\n(ملف الإيصال لم يُرسل تلقائياً)")
    else:
        bot.send_message(ADMIN_ID, caption + (f"\nتفاصيل الإيصال: {proof}" if proof else ""))
    send_request_to_admin(req)

# سحب من الحساب
@bot.message_handler(func=lambda m: m.text == "سحب من الحساب")
def start_withdraw(m):
    touch_user(m.from_user)
    bot.send_message(m.chat.id, "أدخل قيمة السحب (لا تقل عن 25,000):", reply_markup=back_keyboard())
    bot.pending = getattr(bot, "pending", {})
    bot.pending[str(m.from_user.id)] = {"action":"withdraw_wait_amount"}

@bot.message_handler(func=lambda m: getattr(bot, "pending", {}).get(str(m.from_user.id), {}).get("action") == "withdraw_wait_amount")
def recv_withdraw_amount(m):
    uid = touch_user(m.from_user)
    try:
        val = float(m.text.strip())
    except:
        bot.send_message(m.chat.id, "الرجاء إدخال رقم صالح.", reply_markup=back_keyboard())
        return
    if val < MIN_AMOUNT:
        bot.send_message(m.chat.id, f"الحد الأدنى للسحب هو {MIN_AMOUNT}.", reply_markup=back_keyboard())
        return
    bot.pending[str(m.from_user.id)] = {"action":"withdraw_choose_method", "amount": val}
    kb = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    kb.add("سرياتيل كاش", "شام كاش", "🔙 رجوع")
    bot.send_message(m.chat.id, f"المبلغ: {val}. اختر طريقة السحب:", reply_markup=kb)

@bot.message_handler(func=lambda m: getattr(bot, "pending", {}).get(str(m.from_user.id), {}).get("action") == "withdraw_choose_method")
def recv_withdraw_method(m):
    uid = touch_user(m.from_user)
    choice = m.text.strip()
    p = bot.pending[str(m.from_user.id)]
    if choice not in ["سرياتيل كاش", "شام كاش", "🔙 رجوع"]:
        bot.send_message(m.chat.id, "اختر خيارًا صحيحًا.", reply_markup=back_keyboard())
        return
    if choice == "🔙 رجوع":
        bot.pending.pop(str(m.from_user.id), None)
        bot.send_message(m.chat.id, "تم الإلغاء.", reply_markup=top_keyboard())
        return
    bot.pending[str(m.from_user.id)].update({"action":"withdraw_wait_wallet", "method": choice})
    bot.send_message(m.chat.id, "أدخل كود/رقم محفظتك أو أرسل صورة QR:", reply_markup=types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True).add("🔙 رجوع"))

@bot.message_handler(func=lambda m: getattr(bot, "pending", {}).get(str(m.from_user.id), {}).get("action") == "withdraw_wait_wallet", content_types=["text","photo","document"])
def recv_withdraw_wallet(m):
    uid = touch_user(m.from_user)
    p = bot.pending[str(m.from_user.id)]
    if m.text and m.text.strip() == "🔙 رجوع":
        bot.pending.pop(str(m.from_user.id), None)
        bot.send_message(m.chat.id, "تم الإلغاء.", reply_markup=top_keyboard())
        return
    wallet = None
    file_id = None
    if m.content_type == "text":
        wallet = m.text.strip()
    elif m.content_type in ["photo","document"]:
        if m.content_type == "photo":
            file_id = m.photo[-1].file_id
        else:
            file_id = m.document.file_id
    # create request
    rid = new_request_id()
    req = {"id": rid, "type": "withdraw", "user_id": int(uid), "amount": p["amount"], "method": p["method"], "status":"pending", "created_at": int(time.time())}
    if wallet:
        req["wallet_code"] = wallet
    requests_db[rid] = req
    save_json(REQUESTS_FILE, requests_db)
    bot.pending.pop(str(m.from_user.id), None)
    bot.send_message(m.chat.id, "تم إرسال طلب السحب إلى الأدمن للمراجعة.", reply_markup=top_keyboard())
    caption = f"طلب سحب:\nمن: {users[uid]['name']} (id:{uid})\nمبلغ: {req['amount']}\nالطريقة: {req['method']}"
    if file_id:
        try:
            bot.send_photo(ADMIN_ID, file_id, caption=caption)
        except:
            try:
                bot.send_document(ADMIN_ID, file_id, caption=caption)
            except:
                bot.send_message(ADMIN_ID, caption + "\n(ملف المرفق لم يُرسل تلقائياً)")
    else:
        bot.send_message(ADMIN_ID, caption + (f"\nمحفظة: {wallet}" if wallet else ""))
    send_request_to_admin(req)

# تواصل مع الدعم
@bot.message_handler(func=lambda m: m.text == "تواصل مع الدعم")
def contact_support(m):
    touch_user(m.from_user)
    # provide a button to open support username
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("فتح محادثة الدعم", url=f"https://t.me/{SUPPORT_USERNAME.lstrip('@')}"))
    bot.send_message(m.chat.id, "اضغط لفتح محادثة مع الدعم:", reply_markup=kb)

# طلب حذف حساب من المستخدم
@bot.message_handler(func=lambda m: m.text == "طلب حذف الحساب")
def request_delete_account(m):
    uid = touch_user(m.from_user)
    rid = new_request_id()
    req = {"id": rid, "type": "delete_account", "user_id": int(uid), "status":"pending", "created_at": int(time.time())}
    requests_db[rid] = req
    save_json(REQUESTS_FILE, requests_db)
    bot.send_message(m.chat.id, "تم إرسال طلب حذف الحساب للأدمن. سيتم إعلامك بعد القرار.", reply_markup=top_keyboard())
    send_request_to_admin(req)

# Inline callbacks (copy code, approve/reject/delete actions)
@bot.callback_query_handler(func=lambda call: True)
def inline_cb(call):
    data = call.data
    if data == "copy_sari":
        # send the code as message and answer callback
        bot.answer_callback_query(call.id, text="الكود جاهز للنسخ (أُرسل إليك).", show_alert=False)
        bot.send_message(call.from_user.id, f"كود سرياتيل كاش:\n`{SARI_CASH_CODE}`", parse_mode="Markdown")
    elif data == "copy_sham":
        bot.answer_callback_query(call.id, text="الكود جاهز للنسخ (أُرسل إليك).", show_alert=False)
        bot.send_message(call.from_user.id, f"كود شام كاش:\n`{SHAM_CASH_CODE}`", parse_mode="Markdown")
    elif data == "inline_back":
        bot.answer_callback_query(call.id, text="عودة", show_alert=False)
        bot.send_message(call.from_user.id, "تم الرجوع.", reply_markup=top_keyboard())
    else:
        # callbacks formatted like "approve|<rid>" or "reject|<rid>" or "reply|<rid>" or "delete_ok|<rid>"
        parts = data.split("|")
        if len(parts) == 2:
            action, rid = parts[0], parts[1]
            # only allow admin to press these
            if call.from_user.id != ADMIN_ID:
                bot.answer_callback_query(call.id, "غير مسموح - فقط الأدمن.", show_alert=True)
                return
            req = requests_db.get(rid)
            if not req:
                bot.answer_callback_query(call.id, "الطلب غير موجود أو منتهي.", show_alert=True)
                return
            if action == "approve":
                req["status"] = "approved"
                requests_db[rid] = req
                save_json(REQUESTS_FILE, requests_db)
                # special handling for create_account approval: mark user approved
                if req["type"] == "create_account":
                    uid = str(req["user_id"])
                    if uid in users:
                        users[uid]["approved"] = True
                        save_json(USERS_FILE, users)
                        bot.send_message(req["user_id"], f"✅ تم الموافقة على طلب إنشاء الحساب '{req.get('account_name')}'. يمكنك الآن المتابعة.", reply_markup=top_keyboard())
                bot.edit_message_text(f"تمت الموافقة على الطلب ({req['type']}).", chat_id=call.message.chat.id, message_id=call.message.message_id)
                bot.answer_callback_query(call.id, "تمت الموافقة.")
            elif action == "reject":
                req["status"] = "rejected"
                requests_db[rid] = req
                save_json(REQUESTS_FILE, requests_db)
                # notify user about rejection
                bot.send_message(req["user_id"], f"❌ تم رفض طلبك من النوع: {req['type']}. يمكنك التواصل مع الدعم إذا أردت توضيحًا.", reply_markup=top_keyboard())
                bot.edit_message_text(f"تم رفض الطلب ({req['type']}).", chat_id=call.message.chat.id, message_id=call.message.message_id)
                bot.answer_callback_query(call.id, "تم الرفض.")
            elif action == "reply":
                # Ask admin to reply by sending a message that replies to the bot's message.
                bot.answer_callback_query(call.id, "أرسل رسالة بالرد على هذه الرسالة لأُرسلها للمستخدم.", show_alert=True)
            elif action == "delete_ok" and req["type"] == "delete_account":
                # admin confirmed deletion: remove user from users and update request status
                uid = str(req["user_id"])
                if uid in users:
                    users.pop(uid, None)
                    save_json(USERS_FILE, users)
                req["status"] = "deleted_by_admin"
                requests_db[rid] = req
                save_json(REQUESTS_FILE, requests_db)
                bot.send_message(req["user_id"], "🗑️ تم حذف معلومات حسابك من البوت بناءً على موافقة الأدمن. يمكنك إنشاء حساب جديد عند الحاجة.", reply_markup=top_keyboard())
                bot.edit_message_text("تم حذف الحساب ومعلوماته من النظام.", chat_id=call.message.chat.id, message_id=call.message.message_id)
                bot.answer_callback_query(call.id, "تم حذف الحساب.")
        else:
            bot.answer_callback_query(call.id, "بيانات غير مفهومة.", show_alert=True)

# Admin reply via replying to admin's own message: forward reply to user
@bot.message_handler(func=lambda m: m.reply_to_message is not None and m.from_user.id == ADMIN_ID, content_types=["text","photo","document"])
def admin_reply_handler(m):
    # find which request this admin message was mapped to (by reply_to_message.message_id)
    replied_id = str(m.reply_to_message.message_id)
    rid = admin_map.get(replied_id)
    if not rid:
        # fallback: if admin just replies to a user's forwarded message, we try to parse user id from text
        bot.send_message(ADMIN_ID, "لم أتمكن من تحديد الطلب المرتبط بهذا الرد. تأكد من الرد على رسالة الطلب التي أرسلها البوت.")
        return
    req = requests_db.get(rid)
    if not req:
        bot.send_message(ADMIN_ID, "الطلب غير موجود أو منتهي.")
        return
    target_user_id = req["user_id"]
    # forward admin's reply content to the user
    if m.content_type == "text":
        bot.send_message(target_user_id, f"رسالة من الأدمن:\n\n{m.text}", reply_markup=top_keyboard())
    elif m.content_type == "photo":
        file_id = m.photo[-1].file_id
        bot.send_photo(target_user_id, file_id, caption=f"صورة من الأدمن:\n\n{m.caption or ''}")
    elif m.content_type == "document":
        file_id = m.document.file_id
        bot.send_document(target_user_id, file_id, caption=f"ملف من الأدمن:\n\n{m.caption or ''}")
    bot.send_message(ADMIN_ID, "تم إرسال ردك للمستخدم.")

# Catch-all to update last_active
@bot.message_handler(func=lambda m: True, content_types=['text','photo','document'])
def catch_all(m):
    touch_user(m.from_user)
    # do nothing else (allows flows to continue)

# Start polling
if __name__ == "__main__":
    print("Bot started...")
    bot.infinity_polling()
