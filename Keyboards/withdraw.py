from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def withdraw_methods_keyboard():
    """طرق السحب"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    methods = [
        ("شام كاش 💳", "withdraw_sham"),
        ("سيرياتيل كاش 📱", "withdraw_syriatel"),
        ("Ethereum ₿", "withdraw_ethereum"),
        ("PayPal 💎", "withdraw_paypal"),
        ("بنك 🏦", "withdraw_bank")
    ]
    
    for text, callback in methods:
        keyboard.add(InlineKeyboardButton(text, callback_data=callback))
    
    keyboard.add(InlineKeyboardButton("❌ إلغاء", callback_data="cancel_withdraw"))
    return keyboard

def confirm_withdrawal_keyboard(withdrawal_id):
    """تأكيد السحب"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("✅ تأكيد الطلب", callback_data=f"confirm_withdrawal_{withdrawal_id}"),
        InlineKeyboardButton("❌ إلغاء", callback_data=f"cancel_withdrawal_{withdrawal_id}")
    )
    return keyboard
