import os
from dotenv import load_dotenv

load_dotenv()

# 🔐 الإعدادات الآمنة - تقرأ من .env
BOT_TOKEN = os.getenv("BOT_TOKEN")  # رح يقرأ من ملف .env
ADMIN_ID = 7625893170

# قاعدة البيانات الجديدة
DATABASE_URL = os.getenv("DATABASE_URL")

# إعدادات الدفع (تبقى كما هي)
SYRIATEL_CODE = "82492253"
SHAM_CODE = "131efe4fbccd83a811282761222eee69"
SITE_LINK = "https://www.55bets.net/#/casino/"
MIN_AMOUNT = 25000
