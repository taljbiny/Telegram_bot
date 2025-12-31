from aiogram import types
from database import db
from config import Config
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime

async def admin_panel(message: types.Message):
    if message.from_user.id not in Config.ADMIN_IDS:
        await message.answer("⛔ غير مصرح")
        return
    
    # إحصائيات بسيطة
    pending_deposits = len(db.get_pending_deposits())
    pending_withdrawals = len(db.get_pending_withdrawals())
    
    await message.answer(
        f"👑 **لوحة الإدارة**\n\n"
        f"📥 **طلبات إيداع معلقة:** {pending_deposits}\n"
        f"📤 **طلبات سحب معلقة:** {pending_withdrawals}\n\n"
        f"📋 **الأوامر:**\n"
        f"/admin_deposits - طلبات الإيداع\n"
        f"/admin_withdrawals - طلبات السحب",
        parse_mode="Markdown"
    )

async def admin_deposits(message: types.Message):
    if message.from_user.id not in Config.ADMIN_IDS:
        return
    
    deposits = db.get_pending_deposits()
    
    if not deposits:
        await message.answer("📭 لا توجد طلبات إيداع معلقة")
        return
    
    for deposit in deposits[:5]:
        text = (
            f"📥 **طلب إيداع #{deposit['id']}**\n\n"
            f"👤 **المستخدم:** @{deposit['username']}\n"
            f"💰 **المبلغ:** {deposit['amount']:,} {Config.CURRENCY_SYMBOL}\n"
            f"💳 **الطريقة:** {deposit['method']}\n"
            f"🔢 **رقم العملية:** {deposit['transaction_id']}\n"
            f"📅 **الوقت:** {deposit['created_at'][:16]}"
        )
        
        keyboard = InlineKeyboardMarkup()
        keyboard.add(
            InlineKeyboardButton("✅ قبول", callback_data=f"admin_approve_deposit_{deposit['id']}"),
            InlineKeyboardButton("❌ رفض", callback_data=f"admin_reject_deposit_{deposit['id']}")
        )
        
        await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")

async def admin_withdrawals(message: types.Message):
    if message.from_user.id not in Config.ADMIN_IDS:
        return
    
    withdrawals = db.get_pending_withdrawals()
    
    if not withdrawals:
        await message.answer("📭 لا توجد طلبات سحب معلقة")
        return
    
    for withdrawal in withdrawals[:5]:
        text = (
            f"📤 **طلب سحب #{withdrawal['id']}**\n\n"
            f"👤 **المستخدم:** @{withdrawal['username']}\n"
            f"💰 **المبلغ:** {withdrawal['amount']:,} {Config.CURRENCY_SYMBOL}\n"
            f"💸 **الرسوم:** {withdrawal['fee']:,} {Config.CURRENCY_SYMBOL}\n"
            f"✅ **الصافي:** {withdrawal['net_amount']:,} {Config.CURRENCY_SYMBOL}\n"
            f"💳 **الطريقة:** {withdrawal['method']}\n"
            f"📅 **الوقت:** {withdrawal['created_at'][:16]}"
        )
        
        keyboard = InlineKeyboardMarkup()
        keyboard.add(
            InlineKeyboardButton("✅ معالجة", callback_data=f"admin_approve_withdrawal_{withdrawal['id']}"),
            InlineKeyboardButton("❌ رفض", callback_data=f"admin_reject_withdrawal_{withdrawal['id']}")
        )
        
        await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")

async def admin_approve_deposit(callback: types.CallbackQuery):
    deposit_id = int(callback.data.split('_')[3])
    
    # الموافقة
    success = db.approve_deposit(deposit_id, callback.from_user.id)
    
    if success:
        deposit = db.get_deposit(deposit_id)
        
        # إعلام المستخدم
        from bot import bot
        try:
            user_data = db.get_user_by_id(deposit['user_id'])
            if user_data:
                await bot.send_message(
                    user_data['telegram_id'],
                    f"✅ **تمت الموافقة على إيداعك!**\n\n"
                    f"💰 **المبلغ:** {deposit['amount']:,} {Config.CURRENCY_SYMBOL}\n"
                    f"💳 **الطريقة:** {deposit['method']}\n"
                    f"🎉 تم إضافة المبلغ إلى رصيدك"
                )
        except:
            pass
        
        await callback.message.edit_text(f"✅ تمت الموافقة على الإيداع #{deposit_id}")
    else:
        await callback.message.edit_text(f"❌ فشل الموافقة")
    
    await callback.answer()

async def admin_approve_withdrawal(callback: types.CallbackQuery):
    withdrawal_id = int(callback.data.split('_')[3])
    
    # الموافقة
    success = db.approve_withdrawal(withdrawal_id, callback.from_user.id)
    
    if success:
        withdrawal = db.get_withdrawal(withdrawal_id)
        
        # إعلام المستخدم
        from bot import bot
        try:
            user_data = db.get_user_by_id(withdrawal['user_id'])
            if user_data:
                await bot.send_message(
                    user_data['telegram_id'],
                    f"✅ **تمت معالجة سحبك!**\n\n"
                    f"💰 **المبلغ:** {withdrawal['net_amount']:,} {Config.CURRENCY_SYMBOL}\n"
                    f"💳 **الطريقة:** {withdrawal['method']}\n"
                    f"📝 **سيتم إرسال المبلغ قريباً**"
                )
        except:
            pass
        
        await callback.message.edit_text(f"✅ تمت معالجة السحب #{withdrawal_id}")
    else:
        await callback.message.edit_text(f"❌ فشل المعالجة")
    
    await callback.answer()
