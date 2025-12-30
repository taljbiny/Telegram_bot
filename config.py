import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # === إعدادات البوت ===
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    
    # === الإدارة ===
    ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "").split(',')))
    SUPPORT_USERNAME = os.getenv("SUPPORT_USERNAME", "@support")
    
    # === الإعدادات المالية ===
    CURRENCY = os.getenv("CURRENCY", "S.P")
    CURRENCY_SYMBOL = "S.P"
    
    MIN_DEPOSIT = float(os.getenv("MIN_DEPOSIT", 25000))
    MIN_WITHDRAWAL = float(os.getenv("MIN_WITHDRAWAL", 50000))
    WITHDRAWAL_FEE = float(os.getenv("WITHDRAWAL_FEE", 0.05))  # 5%
    
    # === معلومات الدفع ===
    PAYMENT_METHODS = {
        'sham_cash': {
            'name': 'شام كاش',
            'hash': os.getenv("SHAM_CASH_HASH"),
            'instructions': 'أرسل المبلغ إلى الرمز أعلاه وأرفق الإيصال'
        },
        'syriatel_cash': {
            'name': 'سيرياتيل كاش',
            'number': os.getenv("SYRIATEL_CASH"),
            'instructions': 'أرسل المبلغ إلى الرقم أعلاه وأرفق الإيصال'
        },
        'ethereum': {
            'name': 'Ethereum',
            'address': os.getenv("ETHEREUM_ADDRESS"),
            'instructions': 'أرسل المبلغ إلى العنوان أعلاه وأرفق هاش العملية'
        }
    }
    
    # === قاعدة البيانات ===
    DATABASE_PATH = "database/data.db"
    
    # === روابط ===
    SUPPORT_LINK = f"https://t.me/{SUPPORT_USERNAME.lstrip('@')}"
