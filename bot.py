import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from config import BOT_TOKEN, ADMIN_USERNAME

# إعداد التسجيل
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# أمر البدء /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    welcome_text = f"""
🎯 **مرحباً {user.first_name}!**

أهلاً بك في [55Bets](https://www.55bets.net) ⚡

📋 **الخدمات المتاحة:**
/register - إنشاء حساب جديد
/deposit - شحن الرصيد  
/withdraw - سحب الرصيد
/support - التواصل مع الدعم
/delete_account - حذف الحساب

**نتمنى لك ربحاً وفيراً! 🎰**
    """
    await update.message.reply_text(welcome_text, parse_mode='Markdown')

# أمر الدعم /support
async def support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    support_text = f"""
🆘 **الدعم الفني**

للتواصل مع الإدمن مباشرة:
@{ADMIN_USERNAME}

📞 **سيتم الرد عليك في أقرب وقت**
    """
    await update.message.reply_text(support_text)

# أمر تجريبي /test
async def test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ البوت شغال بنجاح!")

# التشغيل الرئيسي
def main():
    # إنشاء تطبيق البوت
    application = Application.builder().token(BOT_TOKEN).build()
    
    # إضافة الأوامر
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("support", support))
    application.add_handler(CommandHandler("test", test))
    
    # بدء البوت
    print("🚀 البوت يعمل الآن!")
    application.run_polling()

if __name__ == '__main__':
    main()
