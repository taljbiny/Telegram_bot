from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import Config

def deposit_methods_keyboard():
    """طرق الإيداع"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    methods = [
        ("شام كاش 💳", "deposit_sham"),
        ("سيرياتيل كاش 📱", "deposit_syriatel"),
        ("Ethereum ₿", "deposit_ethereum")
    ]
    
    for text, callback in methods:
        keyboard.add(InlineKeyboardButton(text, callback_data=callback))
    
    keyboard.add(InlineKeyboardButton("❌ إلغاء", callback_data="cancel_deposit"))
    return keyboard

def deposit_amounts_keyboard():
    """مبالغ سريعة للإيداع"""
    keyboard = InlineKeyboardMarkup(row_width=3)
    
    amounts = [
        ("25,000", "amount_25000"),
        ("50,000", "amount_50000"),
        ("100,000", "amount_100000"),
        ("250,000", "amount_250000"),
        ("500,000", "amount_500000"),
        ("1,000,000", "amount_1000000")
    ]
    
    for text, callback in amounts:
        keyboard.add(InlineKeyboardButton(text, callback_data=callback))
    
    keyboard.add(InlineKeyboardButton("✏️ مبلغ مخصص", callback_data="custom_amount"))
    keyboard.add(InlineKeyboardButton("❌ إلغاء", callback_data="cancel_deposit"))
    return keyboard

def confirm_deposit_keyboard(deposit_id):
    """تأكيد الإيداع"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("✅ تأكيد الإرسال", callback_data=f"confirm_deposit_{deposit_id}"),
        InlineKeyboardButton("❌ إلغاء", callback_data=f"cancel_deposit_{deposit_id}")
    )
    return keyboard
