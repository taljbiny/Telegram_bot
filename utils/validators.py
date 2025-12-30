import re
from config import Config

def validate_phone_number(phone):
    """التحقق من رقم الهاتف السوري"""
    patterns = [
        r'^09\d{8}$',  # 0996099355
        r'^\+9639\d{8}$',  # +963996099355
        r'^009639\d{8}$'  # 00963996099355
    ]
    
    for pattern in patterns:
        if re.match(pattern, phone):
            return True
    return False

def validate_amount(amount_str, min_amount=0, transaction_type='deposit'):
    """التحقق من المبلغ"""
    try:
        # إزالة الفواصل والمسافات
        amount_str = str(amount_str).replace(',', '').replace(' ', '')
        amount = float(amount_str)
        
        if amount <= 0:
            return False, "❌ المبلغ يجب أن يكون أكبر من صفر"
        
        if transaction_type == 'deposit' and amount < Config.MIN_DEPOSIT:
            return False, f"❌ الحد الأدنى للإيداع: {Config.CURRENCY_SYMBOL}{Config.MIN_DEPOSIT:,.0f}"
        
        if transaction_type == 'withdrawal' and amount < Config.MIN_WITHDRAWAL:
            return False, f"❌ الحد الأدنى للسحب: {Config.CURRENCY_SYMBOL}{Config.MIN_WITHDRAWAL:,.0f}"
        
        return True, amount
    except ValueError:
        return False, "❌ الرجاء إدخال رقم صحيح"
