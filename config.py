import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # إعدادات البوت
    BOT_TOKEN = os.getenv("BOT_TOKEN", "")
    
    # الإدارة
    ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "8219716285").split(',')))
    SUPPORT_USERNAME = os.getenv("SUPPORT_USERNAME", "@support")
    
    # إعدادات مالية
    CURRENCY = os.getenv("CURRENCY", "S.P")
    CURRENCY_SYMBOL = "S.P"
    MIN_DEPOSIT = float(os.getenv("MIN_DEPOSIT", 25000))
    MIN_WITHDRAWAL = float(os.getenv("MIN_WITHDRAWAL", 50000))
    WITHDRAWAL_FEE = float(os.getenv("WITHDRAWAL_FEE", 0.05))
    
    # معلومات الدفع
    PAYMENT_METHODS = {
        'sham': {'name': 'شام كاش', 'hash': '19f013ef640f4ab20aace84b8a617bd6'},
        'syriatel': {'name': 'سيرياتيل كاش', 'number': '0996099355'},
        'ethereum': {'name': 'Ethereum', 'address': '0x2abf01f2d131b83f7a9b2b9642638ebcaab67c43'}
    }
    
    # قاعدة البيانات
    DATABASE_PATH = "database/data.db"
