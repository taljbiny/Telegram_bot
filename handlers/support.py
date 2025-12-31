from aiogram import types
from aiogram.dispatcher import FSMContext
from database import db
from keyboards.support import *
from keyboards.main import main_menu_keyboard
from handlers.states import SupportStates
from config import Config

async def support_menu(message: types.Message):
    """قائمة الدعم"""
    await message.answer(
        "🛟 **الدعم الفني**\n\n"
        "اختر طريقة التواصل:\n\n"
        "📞 **مباشر:** اضغط على الزر أدناه للتواصل مع الدعم\n"
        "📝 **تذكرة:** أرسل رسالتك وسنرد عليك قريباً\n\n"
        "⏰ **وقت الاستجابة:** 15 دقيقة",
        reply_markup=support_menu_keyboard(),
        parse_mode="Markdown"
    )

async def contact_support(callback: types.CallbackQuery, state: FSMContext):
    """الاتصال بالدعم"""
    await callback.message.answer(
        "📞 **تواصل مع الدعم**\n\n"
        "الرجاء مشاركة رقم هاتفك أو أرسل رسالتك:",
        reply_markup=share_contact_keyboard(),
        parse_mode="Markdown"
    )
    await SupportStates.waiting_for_message.set()
    await callback.answer()

async def process_support_message(message: types.Message, state: FSMContext):
    """معالجة رسالة الدعم"""
    user = message.from_user
    user_data = db.get_user(user.id)
    
    if not user_data:
        await message.answer("⚠️ ليس لديك حساب. استخدم /register أولاً")
        await state.finish()
        return
    
    # الحصول على الرسالة
    if message.contact:
        # إذا شارك جهة اتصال
        support_message = f"📞 **رقم الهاتف:** {message.contact.phone_number}"
        if message.caption:
            support_message += f"\n📝 **الرسالة:** {message.caption}"
    else:
        # إذا أرسل رسالة نصية
        support_message = message.text
    
    # إنشاء تذكرة دعم
    ticket_id = db.create_support_ticket(user_data['id'], support_message)
    
    # إرسال للإدارة
    from bot import bot
    admin_message = f"""
🆘 **تذكرة دعم جديدة #{ticket_id}**

👤 **المستخدم:** {user.first_name} (@{user.username or 'لا يوجد'})
🆔 **ID:** {user.id}
👤 **اسم المستخدم:** {user_data['username']}
📱 **الهاتف:** {user_data['phone'] or 'غير مضاف'}

📝 **الرسالة:**
{support_message}

📅 **الوقت:** {datetime.now().strftime('%Y-%m-%d %H:%M')}
"""
    
    for admin_id in Config.ADMIN_IDS:
        try:
            await bot.send_message(
                chat_id=admin_id,
                text=admin_message,
                reply_markup=admin_ticket_actions_keyboard(ticket_id, user.id)
            )
        except:
            pass
    
    await message.answer(
        "✅ **تم إرسال رسالتك للإدارة**\n\n"
        "📩 **رقم التذكرة:** #{}\n"
        "⏰ **وقت الاستجابة:** 15 دقيقة\n"
        "💬 **سنرد عليك قريباً**".format(ticket_id),
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard()
    )
    
    await state.finish()
