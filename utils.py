import re
import html
from datetime import datetime
from typing import List, Tuple
import hashlib

def clean_html(raw_html: str) -> str:
    """Remove HTML tags from string"""
    if not raw_html:
        return ""
    clean = re.compile('<.*?>')
    text = re.sub(clean, '', raw_html)
    text = html.unescape(text)
    return text.strip()

def truncate_text(text: str, max_length: int = 500) -> str:
    """Truncate text to max length"""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."

def format_time(timestamp) -> str:
    """Format datetime for display"""
    if isinstance(timestamp, str):
        try:
            timestamp = datetime.fromisoformat(timestamp)
        except:
            return timestamp
    now = datetime.now()
    diff = now - timestamp
    
    if diff.days > 0:
        return timestamp.strftime("%Y-%m-%d %H:%M")
    elif diff.seconds < 60:
        return "الآن"
    elif diff.seconds < 3600:
        minutes = diff.seconds // 60
        return f"منذ {minutes} دقيقة"
    else:
        hours = diff.seconds // 3600
        return f"منذ {hours} ساعة"

def extract_links(text: str) -> List[str]:
    """Extract all links from text"""
    pattern = r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[^\s]*'
    return re.findall(pattern, text)

def generate_user_hash(user_id: int) -> str:
    """Generate unique hash for user"""
    return hashlib.md5(f"{user_id}_{datetime.now().timestamp()}".encode()).hexdigest()[:8]

def format_stats_text(stats: dict, active_today: int) -> str:
    """Format statistics for display"""
    text = """
📊 *إحصائيات البوت*

👥 *المستخدمين:* `{total_users}`
📧 *إيميلات تم إنشاؤها:* `{total_emails_created}`
📨 *رسائل مستلمة:* `{total_messages_received}`
⭐ *نشطاء اليوم:* `{active_today}`

🕐 آخر تحديث: {time}
    """
    return text.format(
        total_users=stats.get('total_users', 0),
        total_emails_created=stats.get('total_emails_created', 0),
        total_messages_received=stats.get('total_messages_received', 0),
        active_today=active_today,
        time=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )

def is_valid_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None
