from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def main_menu_keyboard():
    """القائمة الرئيسية"""
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = [
        KeyboardButton("💰 رصيدي"),
        KeyboardButton("📥 إيداع"),
        KeyboardButton("📤 سحب"),
        KeyboardButton("📋 السجل"),
        KeyboardButton("🛟 الدعم"),
        KeyboardButton("⚙️ الإعدادات")
    ]
    keyboard.add(*buttons)
    return keyboard

def cancel_keyboard():
    """زر الإلغاء"""
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("❌ إلغاء", callback_data="cancel"))
    return keyboard
