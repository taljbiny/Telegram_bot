import hashlib
from config import Config

def hash_password(password):
    """تشفير كلمة السر"""
    return hashlib.sha256(password.encode()).hexdigest()

def format_currency(amount):
    """تنسيق العملة"""
    return f"{Config.CURRENCY_SYMBOL}{amount:,.0f}"

def validate_phone(phone):
    """التحقق من رقم الهاتف"""
    if not phone:
        return True
    
    phone = str(phone).strip()
    return phone.isdigit() and len(phone) == 10 and phone.startswith('09')

def calculate_withdrawal(amount):
    """حساب السحب مع الرسوم"""
    fee = amount * Config.WITHDRAWAL_FEE
    net_amount = amount - fee
    return fee, net_amount
