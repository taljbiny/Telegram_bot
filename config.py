import os
from dotenv import load_dotenv

# حاول تحميل .env إذا كان موجوداً
try:
    load_dotenv()
except:
    pass  # على Render قد لا يكون .env موجوداً

class Config:
    # === إعدادات البوت ===
    BOT_TOKEN = os.getenv("BOT_TOKEN", "")
    
    # === الإدارة ===
    ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "8219716285").split(',')))
    SUPPORT_USERNAME = os.getenv("SUPPORT_USERNAME", "@support")
    
    # === الإعدادات المالية ===
    CURRENCY = os.getenv("CURRENCY", "S.P")
    CURRENCY_SYMBOL = "S.P"
    
    MIN_DEPOSIT = float(os.getenv("MIN_DEPOSIT", 25000))
    MIN_WITHDRAWAL = float(os.getenv("MIN_WITHDRAWAL", 50000))
    WITHDRAWAL_FEE = float(os.getenv("WITHDRAWAL_FEE", 0.05))
    
    # === معلومات الدفع ===
    PAYMENT_METHODS = {
        'sham': {
            'name': 'شام كاش',
            'hash': os.getenv("SHAM_CASH_HASH", "19f013ef640f4ab20aace84b8a617bd6"),
            'instructions': 'أرسل المبلغ إلى الرمز أعلاه'
        },
        'syriatel': {
            'name': 'سيرياتيل كاش',
            'number': os.getenv("SYRIATEL_CASH", "0996099355"),
            'instructions': 'أرسل المبلغ إلى الرقم أعلاه'
        },
        'ethereum': {
            'name': 'Ethereum',
            'address': os.getenv("ETHEREUM_ADDRESS", "0x2abf01f2d131b83f7a9b2b9642638ebcaab67c43"),
            'instructions': 'أرسل المبلغ إلى العنوان أعلاه'
        }
    }
    
    # === قاعدة البيانات ===
    # على Render، استخدم مسار مطلق
    DATABASE_PATH = os.getenv("DATABASE_PATH", "database/data.db")
