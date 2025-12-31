from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def support_menu_keyboard():
    """قائمة الدعم"""
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("📞 تواصل مع الدعم", callback_data="contact_support"))
    return keyboard

def share_contact_keyboard():
    """مشاركة جهة الاتصال"""
    from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
    
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    keyboard.add(KeyboardButton("📞 مشاركة رقمي", request_contact=True))
    keyboard.add(KeyboardButton("❌ إلغاء"))
    return keyboard
