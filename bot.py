import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
import os

# إعداد البوت
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = "8317743306:AAHAM9svd23L2mqSfHnPFEsqKY_bavW3kMg"
ADMIN_ID = 7625893170  # آيدي الإدمن
PORT = int(os.environ.get('PORT', 8443))

# متغيرات مؤقتة لتخزين بيانات المستخدمين
user_data = {}

# أمر /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    welcome_text = f"""
🎯 مرحباً {user.first_name}!

أهلاً بك في 55Bets ⚡
🌐 الموقع: 55bets.net

📋 الخدمات المتاحة:
/register - إنشاء حساب جديد
/deposit - شحن الرصيد  
/withdraw - سحب الرصيد
/support - التواصل مع الدعم
/delete_account - حذف الحساب

نتمنى لك ربحاً وفيراً! 🎰
    """
    await update.message.reply_text(welcome_text)

# أمر /register - بدء عملية التسجيل
async def register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data[user_id] = {'step': 'awaiting_name'}
    
    await update.message.reply_text(
        "📝 إنشاء حساب جديد\n\n"
        "أرسل لي الاسم الكامل الذي تريد استخدامه للحساب:"
    )

# معالجة الرسائل (لجمع البيانات)
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_text = update.message.text
    
    if user_id in user_data:
        current_step = user_data[user_id].get('step')
        
        if current_step == 'awaiting_name':
            # حفظ الاسم والانتظار لكلمة السر
            user_data[user_id]['name'] = user_text
            user_data[user_id]['step'] = 'awaiting_password'
            
            await update.message.reply_text(
                "🔐 حسناً!\n"
                "الآن أرسل كلمة السر التي تريد استخدامها:"
            )
            
        elif current_step == 'awaiting_password':
            # حفظ كلمة السر وإرسال الطلب للإدمن
            user_data[user_id]['password'] = user_text
            user_data[user_id]['step'] = 'completed'
            
            # إرسال الطلب للإدمن
            request_text = f"""
📋 طلب إنشاء حساب جديد

👤 المستخدم: {update.effective_user.first_name} (@{update.effective_user.username})
🆔 آيدي: {user_id}

📝 بيانات الحساب:
• الاسم: {user_data[user_id]['name']}
• كلمة السر: {user_data[user_id]['password']}

⏰ الوقت: {update.message.date}
            """
            
            # إرسال للإدمن
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=request_text
            )
            
            # تأكيد للمستخدم
            await update.message.reply_text(
                "✅ تم إرسال طلبك بنجاح!\n\n"
                "سيتم مراجعة طلبك من قبل الإدمن وسنخبرك عند الموافقة.\n"
                "شكراً لثقتك بنا! 🌟"
            )
            
            # مسح البيانات المؤقتة
            del user_data[user_id]

# أمر /support
async def support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    support_text = """
🆘 الدعم الفني

للتواصل مع الإدمن مباشرة:
@trajibiny

📞 سيتم الرد عليك في أقرب وقت
    """
    await update.message.reply_text(support_text)

# أمر /deposit
async def deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    deposit_text = """
💳 طلب شحن رصيد

سيتم إضافة هذه الخدمة قريباً!
تابع التحديثات 👋
    """
    await update.message.reply_text(deposit_text)

# أمر /withdraw
async def withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    withdraw_text = """
💰 طلب سحب رصيد

سيتم إضافة هذه الخدمة قريباً!
تابع التحديثات 👋
    """
    await update.message.reply_text(withdraw_text)

# أمر /delete_account
async def delete_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    delete_text = """
🗑 حذف الحساب

سيتم إضافة هذه الخدمة قريباً!
تابع التحديثات 👋
    """
    await update.message.reply_text(delete_text)

# التشغيل الرئيسي
def main():
    application = Application.builder().token(BOT_TOKEN).build()
    
    # إضافة الأوامر
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("register", register))
    application.add_handler(CommandHandler("support", support))
    application.add_handler(CommandHandler("deposit", deposit))
    application.add_handler(CommandHandler("withdraw", withdraw))
    application.add_handler(CommandHandler("delete_account", delete_account))
    
    # معالجة الرسائل العادية
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("🚀 البوت يعمل الآن!")
    
    # التشغيل مع PORT
    application.run_polling()
    
    print(f"✅ Bot running on port {PORT}")

if __name__ == '__main__':
    main()
