import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from config import BOT_TOKEN, ADMIN_USERNAME

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎯 **البوت شغال!** ✅", parse_mode='Markdown')

def main():
    try:
        application = Application.builder().token(BOT_TOKEN).build()
        application.add_handler(CommandHandler("start", start))
        
        logger.info("🚀 Starting bot...")
        application.run_polling()
    except Exception as e:
        logger.error(f"❌ Error: {e}")

if __name__ == '__main__':
    main()
