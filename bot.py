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
