from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def skip_phone_keyboard():
    """زر تخطي إضافة الهاتف"""
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("⏭️ تخطي", callback_data="skip_phone"))
    return keyboard

def confirm_registration_keyboard():
    """تأكيد التسجيل"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("✅ تأكيد", callback_data="confirm_registration"),
        InlineKeyboardButton("❌ إلغاء", callback_data="cancel_registration")
    )
    return keyboard
