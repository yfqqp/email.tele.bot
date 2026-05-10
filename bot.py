import asyncio
import logging
from datetime import datetime
from typing import Dict, List

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ParseMode

from config import BOT_TOKEN, ADMIN_IDS, MESSAGES_PER_PAGE
from database import db
from mail_service import email_service
from keyboards import (
    get_main_keyboard, get_inbox_keyboard, get_message_actions_keyboard,
    get_settings_keyboard, get_admin_keyboard, get_wait_keyboard,
    get_otp_keyboard
)
from utils import clean_html, truncate_text, format_time, format_stats_text

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Store waiting users
waiting_users: Dict[int, asyncio.Task] = {}

# ================= Helper Functions =================

async def update_user_activity(user_id: int):
    """Update user's last activity"""
    db.update_activity(user_id)

async def get_or_create_user(message: types.Message):
    """Get or create user in database"""
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name
    
    user = db.get_user(user_id)
    
    if not user:
        email, login, domain = email_service.generate_random_email()
        db.create_user(user_id, username, first_name, last_name, email, login, domain)
        user = db.get_user(user_id)
        logger.info(f"New user created: {user_id} ({username})")
    
    return user

def is_admin(user_id: int) -> bool:
    """Check if user is admin"""
    return user_id in ADMIN_IDS

# ================= User Commands =================

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    """Start command handler"""
    user = await get_or_create_user(message)
    await update_user_activity(message.from_user.id)
    
    welcome_text = f"""
✨ *مرحباً بك في البوت المؤقت للإيميلات!* ✨

📧 *إيميلك الحالي:* `{user['email']}`

🎯 *المميزات:*
• 📧 إنشاء إيميلات مؤقتة فورية
• 📥 استلام الرسائل فور وصولها
• 🔑 كشف أكواد التحقق (OTP) تلقائياً
• ⏳ انتظار الرسائل من مواقع محددة
• 🔒 خصوصية تامة وأمان

استخدم الأزرار أدناه للبدء:
"""
    
    await message.answer(welcome_text, reply_markup=get_main_keyboard(), parse_mode=ParseMode.MARKDOWN)

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    """Help command"""
    help_text = """
❓ *مساعدة البوت*

*الأوامر المتاحة:*
/start - بدء البوت
/email - عرض بريدك الحالي
/new - إنشاء بريد جديد
/inbox - عرض صندوق الوارد
/otp - البحث عن أكواد التحقق
/help - عرض هذه المساعدة

*كيفية الاستخدام:*
1️⃣ استخدم "تحديث الإيميل" لإنشاء بريد مؤقت
2️⃣ استخدمه في التسجيل في المواقع
3️⃣ تحقق من "صندوق الوارد" للرسائل
4️⃣ يبحث البوت تلقائياً عن أكواد التحقق

*ملاحظات:* الإيميلات مؤقتة وقد تنتهي صلاحيتها بعد فترة.
    """
    await message.answer(help_text, parse_mode=ParseMode.MARKDOWN)

@dp.message(Command("email"))
async def cmd_email(message: types.Message):
    """Show current email"""
    user = db.get_user(message.from_user.id)
    if user:
        await message.answer(f"📧 *بريدك الحالي:*\n`{user['email']}`", parse_mode=ParseMode.MARKDOWN)
    else:
        await cmd_start(message)

@dp.message(Command("new"))
async def cmd_new(message: types.Message):
    """Create new email"""
    await create_new_email(message.from_user.id, message)

@dp.message(Command("inbox"))
async def cmd_inbox(message: types.Message):
    """Show inbox"""
    await show_inbox(message.from_user.id, message)

@dp.message(Command("otp"))
async def cmd_otp(message: types.Message):
    """Find OTP codes"""
    await find_otp_codes(message.from_user.id, message)

# ================= Callback Handlers =================

@dp.callback_query(F.data == "menu")
async def back_to_menu(callback: types.CallbackQuery):
    """Return to main menu"""
    user = db.get_user(callback.from_user.id)
    if user:
        text = f"📧 *بريدك الحالي:* `{user['email']}`\n\nاختر أحد الخيارات:"
    else:
        text = "✨ *القائمة الرئيسية* ✨\n\nاختر أحد الخيارات:"
    
    await callback.message.edit_text(text, reply_markup=get_main_keyboard(), parse_mode=ParseMode.MARKDOWN)
    await callback.answer()

@dp.callback_query(F.data == "new_email")
async def create_new_email(callback: types.CallbackQuery):
    """Create new email"""
    user_id = callback.from_user.id
    
    # Delete old email
    old_user = db.get_user(user_id)
    if old_user:
        email_service.delete_mailbox(old_user['login'], old_user['domain'])
    
    # Create new email
    email, login, domain = email_service.generate_random_email()
    db.update_user_email(user_id, email, login, domain)
    db.clear_user_messages(user_id)
    
    await callback.message.edit_text(
        f"✅ *تم إنشاء بريد جديد!*\n\n📧 `{email}`\n\n"
        f"يمكنك استخدام هذا البريد الآن.",
        reply_markup=get_main_keyboard(),
        parse_mode=ParseMode.MARKDOWN
    )
    await callback.answer("تم تحديث البريد!")

@dp.callback_query(F.data == "inbox")
async def show_inbox(user_id: int = None, message_obj = None, callback: types.CallbackQuery = None):
    """Show user inbox"""
    if callback:
        user_id = callback.from_user.id
        message_obj = callback.message
    
    user = db.get_user(user_id)
    if not user:
        if callback:
            await callback.answer("يرجى إعادة تشغيل البوت بـ /start")
        return
    
    # Get messages from API
    messages = email_service.get_inbox(user['login'], user['domain'])
    
    if not messages:
        text = f"📭 *صندوق الوارد فارغ*\n\n📧 `{user['email']}`\n\n"
        text += "📬 أرسل رسالة اختبارية لتراها هنا."
        
        if callback:
            await callback.message.edit_text(text, reply_markup=get_main_keyboard(), parse_mode=ParseMode.MARKDOWN)
            await callback.answer()
        else:
            await message_obj.answer(text, parse_mode=ParseMode.MARKDOWN)
        return
    
    # Save messages to DB
    for msg in messages:
        db.save_message(user_id, msg)
        db.increment_message_count(user_id)
    
    # Build message list
    text = f"📬 *صندوق الوارد*\n📧 `{user['email']}`\n\n"
    
    for i, msg in enumerate(messages[:MESSAGES_PER_PAGE], 1):
        subject = msg.get('subject', 'بدون موضوع')
        from_addr = msg.get('from', 'غير معروف')
        
        # Truncate long text
        if len(subject) > 40:
            subject = subject[:37] + "..."
        if len(from_addr) > 35:
            from_addr = from_addr[:32] + "..."
        
        # Check if OTP exists
        full_msg = email_service.read_message(user['login'], user['domain'], msg['id'])
        if full_msg:
            body = full_msg.get('textBody', '') or full_msg.get('htmlBody', '')
            body = clean_html(body)
            otps = email_service.extract_verification_codes(body)
            otp_indicator = " 🔑" if otps else ""
        
        text += f"{i}. 📩 *{subject}*{otp_indicator}\n   👤 {from_addr}\n"
        text += f"   🆔 `{msg['id']}`\n\n"
    
    # Create message buttons
    buttons = []
    for msg in messages[:MESSAGES_PER_PAGE]:
        buttons.append([InlineKeyboardButton(
            text=f"📖 قراءة الرسالة {msg['id']}",
            callback_data=f"read_{msg['id']}"
        )])
    
    # Add navigation
    buttons.extend([
        [InlineKeyboardButton(text="🔄 تحديث", callback_data="refresh_inbox")],
        [InlineKeyboardButton(text="🔑 البحث عن أكواد", callback_data="otp_finder")],
        [InlineKeyboardButton(text="🏠 القائمة الرئيسية", callback_data="menu")]
    ])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    if callback:
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode=ParseMode.MARKDOWN)
        await callback.answer()
    else:
        await message_obj.answer(text, reply_markup=keyboard, parse_mode=ParseMode.MARKDOWN)

@dp.callback_query(F.data.startswith("read_"))
async def read_message(callback: types.CallbackQuery):
    """Read a specific message"""
    message_id = int(callback.data.split("_")[1])
    user_id = callback.from_user.id
    
    user = db.get_user(user_id)
    if not user:
        await callback.answer("يرجى إعادة تشغيل البوت!")
        return
    
    msg_data = email_service.read_message(user['login'], user['domain'], message_id)
    
    if not msg_data:
        await callback.answer("الرسالة غير موجودة!", show_alert=True)
        return
    
    # Extract data
    subject = msg_data.get('subject', 'بدون موضوع')
    from_addr = msg_data.get('from', 'غير معروف')
    body = msg_data.get('textBody', '') or msg_data.get('htmlBody', '')
    body = clean_html(body)
    
    # Find OTPs
    otps = email_service.extract_verification_codes(body)
    
    # Build message text
    text = f"📧 *من:* {from_addr}\n"
    text += f"📌 *الموضوع:* {subject}\n\n"
    
    if otps:
        text += "🔐 *أكواد التحقق:*\n"
        for otp in otps:
            text += f"`{otp}`\n"
        text += "\n"
    
    # Show body (truncated)
    if body:
        body_preview = truncate_text(body, 800)
        text += f"📝 *الرسالة:*\n{body_preview}"
    else:
        text += "📝 *(لا يوجد محتوى نصي)*"
    
    # Add action buttons
    buttons = [
        [InlineKeyboardButton(text="📋 نسخ البريد", callback_data=f"copy_email_{from_addr}")],
        [InlineKeyboardButton(text="🗑 حذف", callback_data=f"delete_msg_{message_id}")],
        [InlineKeyboardButton(text="🔙 رجوع للوارد", callback_data="inbox")],
        [InlineKeyboardButton(text="🏠 القائمة", callback_data="menu")]
    ]
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    # Mark as read
    db.mark_message_read(user_id, str(message_id))
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode=ParseMode.MARKDOWN)
    await callback.answer()

@dp.callback_query(F.data == "otp_finder")
async def find_otp_codes(user_id: int = None, message_obj = None, callback: types.CallbackQuery = None):
    """Find all OTP codes in inbox"""
    if callback:
        user_id = callback.from_user.id
        message_obj = callback.message
    
    user = db.get_user(user_id)
    if not user:
        if callback:
            await callback.answer("يرجى إعادة تشغيل البوت!")
        return
    
    await callback.message.edit_text("🔍 *جاري البحث عن أكواد التحقق...*", parse_mode=ParseMode.MARKDOWN)
    
    messages = email_service.get_inbox(user['login'], user['domain'])
    
    if not messages:
        await callback.message.edit_text(
            "❌ *لا توجد رسائل في صندوق الوارد*\n\n"
            "📭 قم بإرسال رسالة تحتوي على كود تحقق أولاً.",
            reply_markup=get_otp_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )
        await callback.answer()
        return
    
    found_codes = []
    
    for msg in messages[:10]:
        full_msg = email_service.read_message(user['login'], user['domain'], msg['id'])
        if full_msg:
            body = full_msg.get('textBody', '') or full_msg.get('htmlBody', '')
            body = clean_html(body)
            codes = email_service.extract_verification_codes(body)
            if codes:
                found_codes.append({
                    'from': msg.get('from', 'Unknown'),
                    'subject': msg.get('subject', 'No Subject'),
                    'codes': codes
                })
    
    if not found_codes:
        text = "🔍 *لم يتم العثور على أكواد تحقق*\n\n"
        text += "📝 تأكد من:\n"
        text += "• وجود رسائل في البريد\n"
        text += "• الرسالة تحتوي على أرقام\n"
        text += "• يمكنك المحاولة مرة أخرى"
        
        await callback.message.edit_text(text, reply_markup=get_otp_keyboard(), parse_mode=ParseMode.MARKDOWN)
    else:
        text = "🔐 *أكواد التحقق الموجودة*\n\n"
        for item in found_codes:
            text += f"📧 {item['from'][:40]}\n"
            text += f"📌 {item['subject'][:40]}\n"
            text += "🔑 الأكواد:\n"
            for code in item['codes']:
                text += f"   `{code}`\n"
            text += "\n"
        
        await callback.message.edit_text(text, reply_markup=get_otp_keyboard(), parse_mode=ParseMode.MARKDOWN)
    
    if callback:
        await callback.answer()

@dp.callback_query(F.data == "wait_msg")
async def wait_for_message(callback: types.CallbackQuery):
    """Wait for a message from specific sender"""
    user_id = callback.from_user.id
    
    await callback.message.edit_text(
        "⏳ *انتظار رسالة*\n\n"
        "📝 أرسل اسم المرسل أو جزء من عنوانه\n"
        "مثال: `@gmail.com` أو `verify`\n\n"
        "🕐 سأنتظر لمدة 60 ثانية ثم أبحث.",
        reply_markup=get_wait_keyboard(),
        parse_mode=ParseMode.MARKDOWN
    )
    
    # Store waiting state
    waiting_users[user_id] = True
    
    @dp.message(lambda msg: msg.from_user.id == user_id and waiting_users.get(user_id))
    async def get_sender_query(message: types.Message):
        sender_filter = message.text
        
        if waiting_users.get(user_id):
            del waiting_users[user_id]
        
        user = db.get_user(user_id)
        
        await message.answer(f"🔍 *جاري البحث عن رسائل من:* `{sender_filter}`\n⏱️ يرجى الانتظار...", parse_mode=ParseMode.MARKDOWN)
        
        # Poll for messages
        found = False
        for _ in range(15):  # 30 seconds total
            await asyncio.sleep(2)
            messages = email_service.get_inbox(user['login'], user['domain'])
            for msg in messages:
                if sender_filter.lower() in msg.get('from', '').lower():
                    found = True
                    full_msg = email_service.read_message(user['login'], user['domain'], msg['id'])
                    
                    # Extract OTP
                    body = full_msg.get('textBody', '') or full_msg.get('htmlBody', '')
                    body = clean_html(body)
                    otps = email_service.extract_verification_codes(body)
                    
                    result_text = f"✅ *تم العثور على رسالة!*\n\n"
                    result_text += f"📧 من: {msg['from']}\n"
                    result_text += f"📌 الموضوع: {msg['subject']}\n\n"
                    if otps:
                        result_text += f"🔑 *الكود:* `{otps[0]}`\n"
                    
                    await message.answer(result_text, reply_markup=get_main_keyboard(), parse_mode=ParseMode.MARKDOWN)
                    break
            if found:
                break
        
        if not found:
            await message.answer(
                "❌ *لم يتم العثور على رسائل*\n\n"
                "🔄 يمكنك المحاولة مرة أخرى أو استخدام صندوق الوارد.",
                reply_markup=get_main_keyboard(),
                parse_mode=ParseMode.MARKDOWN
            )
    
    await callback.answer()

@dp.callback_query(F.data == "settings")
async def show_settings(callback: types.CallbackQuery):
    """Show settings menu"""
    await callback.message.edit_text(
        "⚙️ *الإعدادات*\n\n"
        "🔧 قم بتخصيص تجربتك:",
        reply_markup=get_settings_keyboard(),
        parse_mode=ParseMode.MARKDOWN
    )
    await callback.answer()

@dp.callback_query(F.data == "info")
async def show_info(callback: types.CallbackQuery):
    """Show bot information"""
    user = db.get_user(callback.from_user.id)
    stats = db.get_stats()
    
    text = f"""
ℹ️ *معلومات البوت*

👤 *بياناتك:*
• 📧 البريد: `{user['email']}`
• 📨 رسائل مستلمة: {user['total_emails_received']}
• 🕐 آخر نشاط: {format_time(user['last_activity'])}

📊 *إحصائيات عامة:*
• 👥 مستخدمين: {stats.get('total_users', 0)}
• 📧 إيميلات تم إنشاؤها: {stats.get('total_emails_created', 0)}
• 📨 رسائل مستلمة: {stats.get('total_messages_received', 0)}

💡 *نصائح:*
• استخدم "تحديث الإيميل" لإنشاء بريد جديد
• يقوم البوت باستخراج أكواد التحقق تلقائياً
• يمكنك انتظار رسائل من مواقع محددة

👨‍💻 المطور: @DevZone
    """
    
    await callback.message.edit_text(text, reply_markup=get_main_keyboard(), parse_mode=ParseMode.MARKDOWN)
    await callback.answer()

@dp.callback_query(F.data == "refresh_inbox")
async def refresh_inbox(callback: types.CallbackQuery):
    """Refresh inbox"""
    await show_inbox(callback.from_user.id, callback.message, callback)

@dp.callback_query(F.data == "clear_all_messages")
async def clear_all_messages(callback: types.CallbackQuery):
    """Clear all messages from DB"""
    user_id = callback.from_user.id
    db.clear_user_messages(user_id)
    
    await callback.message.edit_text(
        "✅ *تم مسح جميع الرسائل من جهازك*\n\n"
        "📬 يمكنك تحديث الصفحة لرؤية الرسائل الجديدة.",
        reply_markup=get_main_keyboard(),
        parse_mode=ParseMode.MARKDOWN
    )
    await callback.answer("تم المسح!")

# ================= Admin Handlers =================

@dp.callback_query(F.data == "admin_stats")
async def admin_stats(callback: types.CallbackQuery):
    """Show admin statistics"""
    if not is_admin(callback.from_user.id):
        await callback.answer("ليس لديك صلاحية!", show_alert=True)
        return
    
    stats = db.get_stats()
    active_today = db.get_active_users_today()
    total_users = db.get_total_users()
    
    text = format_stats_text(stats, active_today)
    
    await callback.message.edit_text(text, reply_markup=get_admin_keyboard(), parse_mode=ParseMode.MARKDOWN)
    await callback.answer()

@dp.callback_query(F.data == "admin_users")
async def admin_users(callback: types.CallbackQuery):
    """Show users list"""
    if not is_admin(callback.from_user.id):
        await callback.answer("ليس لديك صلاحية!", show_alert=True)
        return
    
    users = db.get_all_users(limit=20)
    
    if not users:
        text = "👥 *لا يوجد مستخدمين بعد*"
    else:
        text = "👥 *قائمة المستخدمين (آخر 20)*\n\n"
        for user in users:
            text += f"🆔 {user['user_id']}\n"
            text += f"📝 {user['username'] or user['first_name']}\n"
            text += f"📧 {user['email']}\n"
            text += f"📨 {user['total_emails_received']} رسائل\n"
            text += f"🕐 {format_time(user['created_at'])}\n"
            text += "➖➖➖➖➖\n"
    
    await callback.message.edit_text(text, reply_markup=get_admin_keyboard(), parse_mode=ParseMode.MARKDOWN)
    await callback.answer()

@dp.callback_query(F.data == "admin_broadcast")
async def admin_broadcast(callback: types.CallbackQuery):
    """Start broadcast"""
    if not is_admin(callback.from_user.id):
        await callback.answer("ليس لديك صلاحية!", show_alert=True)
        return
    
    await callback.message.edit_text(
        "📢 *إذاعة*\n\n"
        "📝 أرسل الرسالة التي تريد إذاعتها لجميع المستخدمين.\n"
        "🚫 أرسل `cancel` للإلغاء.",
        parse_mode=ParseMode.MARKDOWN
    )
    
    @dp.message(lambda msg: is_admin(msg.from_user.id))
    async def handle_broadcast(message: types.Message):
        if message.text.lower() == 'cancel':
            await message.answer("❌ تم إلغاء الإذاعة.", reply_markup=get_admin_keyboard())
            return
        
        # Get all users
        users = db.get_all_users(limit=1000)
        success_count = 0
        fail_count = 0
        
        status_msg = await message.answer("📤 *جاري الإرسال...*", parse_mode=ParseMode.MARKDOWN)
        
        for user in users:
            try:
                await bot.send_message(user['user_id'], f"📢 *إذاعة:*\n\n{message.text}", parse_mode=ParseMode.MARKDOWN)
                success_count += 1
                await asyncio.sleep(0.05)  # Avoid flooding
            except:
                fail_count += 1
        
        await status_msg.edit_text(
            f"✅ *تم الإرسال!*\n\n"
            f"📨 تم الإرسال: {success_count}\n"
            f"❌ فشل: {fail_count}",
            reply_markup=get_admin_
