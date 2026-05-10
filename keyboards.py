from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

def get_main_keyboard() -> InlineKeyboardMarkup:
    """Main menu keyboard"""
    buttons = [
        [
            InlineKeyboardButton(text="🆕 تحديث الإيميل", callback_data="new_email"),
            InlineKeyboardButton(text="📥 صندوق الوارد", callback_data="inbox")
        ],
        [
            InlineKeyboardButton(text="🔑 OTP Finder", callback_data="otp_finder"),
            InlineKeyboardButton(text="⏳ انتظار رسالة", callback_data="wait_msg")
        ],
        [
            InlineKeyboardButton(text="⚙️ الإعدادات", callback_data="settings"),
            InlineKeyboardButton(text="ℹ️ معلومات", callback_data="info")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_inbox_keyboard(page: int = 0, total_pages: int = 1) -> InlineKeyboardMarkup:
    """Inbox navigation keyboard"""
    buttons = []
    
    # Navigation buttons
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(text="◀️ السابق", callback_data=f"inbox_page_{page-1}"))
    if page < total_pages - 1:
        nav_buttons.append(InlineKeyboardButton(text="التالي ▶️", callback_data=f"inbox_page_{page+1}"))
    
    if nav_buttons:
        buttons.append(nav_buttons)
    
    # Action buttons
    buttons.extend([
        [InlineKeyboardButton(text="🔄 تحديث", callback_data="refresh_inbox")],
        [InlineKeyboardButton(text="🏠 القائمة الرئيسية", callback_data="menu")],
        [InlineKeyboardButton(text="🗑 مسح الكل", callback_data="clear_all_messages")]
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_message_actions_keyboard(message_id: int) -> InlineKeyboardMarkup:
    """Message action buttons"""
    buttons = [
        [
            InlineKeyboardButton(text="📖 قراءة", callback_data=f"read_{message_id}"),
            InlineKeyboardButton(text="📋 نسخ الكود", callback_data=f"copy_code_{message_id}")
        ],
        [InlineKeyboardButton(text="🗑 حذف", callback_data=f"delete_msg_{message_id}")],
        [InlineKeyboardButton(text="🔙 رجوع للوارد", callback_data="inbox")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_settings_keyboard() -> InlineKeyboardMarkup:
    """Settings menu"""
    buttons = [
        [InlineKeyboardButton(text="📧 إيميل مخصص", callback_data="custom_email")],
        [InlineKeyboardButton(text="🌐 تغيير اللغة", callback_data="change_language")],
        [InlineKeyboardButton(text="🔄 إعادة تعيين", callback_data="reset_account")],
        [InlineKeyboardButton(text="🔙 رجوع", callback_data="menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_admin_keyboard() -> InlineKeyboardMarkup:
    """Admin panel keyboard"""
    buttons = [
        [InlineKeyboardButton(text="📊 إحصائيات", callback_data="admin_stats")],
        [InlineKeyboardButton(text="👥 المستخدمين", callback_data="admin_users")],
        [InlineKeyboardButton(text="🚫 إدارة الحظر", callback_data="admin_ban")],
        [InlineKeyboardButton(text="📢 إذاعة", callback_data="admin_broadcast")],
        [InlineKeyboardButton(text="🔤 كلمات ممنوعة", callback_data="admin_banned_words")],
        [InlineKeyboardButton(text="💾 نسخة احتياطية", callback_data="admin_backup")],
        [InlineKeyboardButton(text="🔙 رجوع", callback_data="menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_wait_keyboard() -> InlineKeyboardMarkup:
    """Wait for message keyboard"""
    buttons = [
        [InlineKeyboardButton(text="🔄 تحديث يدوي", callback_data="check_wait")],
        [InlineKeyboardButton(text="❌ إلغاء", callback_data="cancel_wait")],
        [InlineKeyboardButton(text="🏠 القائمة", callback_data="menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_otp_keyboard() -> InlineKeyboardMarkup:
    """OTP keyboard"""
    buttons = [
        [InlineKeyboardButton(text="🔄 البحث مرة أخرى", callback_data="otp_finder")],
        [InlineKeyboardButton(text="🏠 القائمة", callback_data="menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
