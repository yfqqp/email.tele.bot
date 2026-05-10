import sqlite3
from datetime import datetime, timedelta
from contextlib import contextmanager
from typing import Optional, Dict, List, Any
import json

class Database:
    def __init__(self, db_path: str = "bot.db"):
        self.db_path = db_path
        self._init_db()
    
    @contextmanager
    def get_connection(self):
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def _init_db(self):
        with self.get_connection() as conn:
            # Users table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    email TEXT NOT NULL,
                    login TEXT,
                    domain TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_activity TIMESTAMP,
                    total_emails_received INTEGER DEFAULT 0,
                    is_banned BOOLEAN DEFAULT 0,
                    language TEXT DEFAULT 'en'
                )
            """)
            
            # Messages table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    message_id TEXT,
                    from_email TEXT,
                    subject TEXT,
                    body TEXT,
                    received_at TIMESTAMP,
                    is_read BOOLEAN DEFAULT 0,
                    UNIQUE(user_id, message_id)
                )
            """)
            
            # Statistics table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS stats (
                    stat_key TEXT PRIMARY KEY,
                    stat_value INTEGER DEFAULT 0,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Initialize stats
            for stat in ['total_users', 'total_emails_created', 'total_messages_received']:
                conn.execute("""
                    INSERT OR IGNORE INTO stats (stat_key, stat_value) VALUES (?, 0)
                """, (stat,))
            
            # Banned words table for spam
            conn.execute("""
                CREATE TABLE IF NOT EXISTS banned_words (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    word TEXT UNIQUE
                )
            """)
    
    # User methods
    def get_user(self, user_id: int) -> Optional[Dict]:
        with self.get_connection() as conn:
            result = conn.execute(
                "SELECT * FROM users WHERE user_id = ? AND is_banned = 0",
                (user_id,)
            ).fetchone()
            return dict(result) if result else None
    
    def get_all_users(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        with self.get_connection() as conn:
            results = conn.execute(
                "SELECT user_id, username, first_name, email, created_at, last_activity, total_emails_received "
                "FROM users WHERE is_banned = 0 ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (limit, offset)
            ).fetchall()
            return [dict(row) for row in results]
    
    def get_total_users(self) -> int:
        with self.get_connection() as conn:
            result = conn.execute("SELECT COUNT(*) as count FROM users WHERE is_banned = 0").fetchone()
            return result['count']
    
    def create_user(self, user_id: int, username: str, first_name: str, last_name: str, 
                    email: str, login: str, domain: str) -> None:
        with self.get_connection() as conn:
            conn.execute("""
                INSERT INTO users (user_id, username, first_name, last_name, email, login, domain, last_activity)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (user_id, username, first_name, last_name, email, login, domain, datetime.now()))
            
            # Update stats
            conn.execute("""
                UPDATE stats SET stat_value = stat_value + 1, updated_at = CURRENT_TIMESTAMP
                WHERE stat_key = 'total_users'
            """)
            conn.execute("""
                UPDATE stats SET stat_value = stat_value + 1, updated_at = CURRENT_TIMESTAMP
                WHERE stat_key = 'total_emails_created'
            """)
    
    def update_user_email(self, user_id: int, email: str, login: str, domain: str) -> None:
        with self.get_connection() as conn:
            conn.execute("""
                UPDATE users SET email = ?, login = ?, domain = ?, last_activity = ?
                WHERE user_id = ?
            """, (email, login, domain, datetime.now(), user_id))
            
            conn.execute("""
                UPDATE stats SET stat_value = stat_value + 1, updated_at = CURRENT_TIMESTAMP
                WHERE stat_key = 'total_emails_created'
            """)
    
    def update_activity(self, user_id: int) -> None:
        with self.get_connection() as conn:
            conn.execute(
                "UPDATE users SET last_activity = ? WHERE user_id = ?",
                (datetime.now(), user_id)
            )
    
    def increment_message_count(self, user_id: int) -> None:
        with self.get_connection() as conn:
            conn.execute(
                "UPDATE users SET total_emails_received = total_emails_received + 1 WHERE user_id = ?",
                (user_id,)
            )
            conn.execute("""
                UPDATE stats SET stat_value = stat_value + 1, updated_at = CURRENT_TIMESTAMP
                WHERE stat_key = 'total_messages_received'
            """)
    
    def ban_user(self, user_id: int) -> None:
        with self.get_connection() as conn:
            conn.execute("UPDATE users SET is_banned = 1 WHERE user_id = ?", (user_id,))
    
    def unban_user(self, user_id: int) -> None:
        with self.get_connection() as conn:
            conn.execute("UPDATE users SET is_banned = 0 WHERE user_id = ?", (user_id,))
    
    # Message methods
    def save_message(self, user_id: int, message_data: Dict) -> None:
        with self.get_connection() as conn:
            conn.execute("""
                INSERT OR IGNORE INTO messages 
                (user_id, message_id, from_email, subject, body, received_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                user_id,
                message_data.get('id'),
                message_data.get('from'),
                message_data.get('subject'),
                message_data.get('body', ''),
                datetime.now()
            ))
    
    def get_user_messages(self, user_id: int, limit: int = 50) -> List[Dict]:
        with self.get_connection() as conn:
            results = conn.execute("""
                SELECT * FROM messages 
                WHERE user_id = ? 
                ORDER BY received_at DESC 
                LIMIT ?
            """, (user_id, limit)).fetchall()
            return [dict(row) for row in results]
    
    def mark_message_read(self, user_id: int, message_id: str) -> None:
        with self.get_connection() as conn:
            conn.execute("""
                UPDATE messages SET is_read = 1 
                WHERE user_id = ? AND message_id = ?
            """, (user_id, message_id))
    
    def clear_user_messages(self, user_id: int) -> None:
        with self.get_connection() as conn:
            conn.execute("DELETE FROM messages WHERE user_id = ?", (user_id,))
    
    # Stats methods
    def get_stats(self) -> Dict:
        with self.get_connection() as conn:
            stats = {}
            results = conn.execute("SELECT stat_key, stat_value FROM stats").fetchall()
            for row in results:
                stats[row['stat_key']] = row['stat_value']
            return stats
    
    def get_active_users_today(self) -> int:
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        with self.get_connection() as conn:
            result = conn.execute(
                "SELECT COUNT(*) as count FROM users WHERE last_activity >= ?",
                (today,)
            ).fetchone()
            return result['count']
    
    # Banned words
    def add_banned_word(self, word: str) -> bool:
        with self.get_connection() as conn:
            try:
                conn.execute("INSERT INTO banned_words (word) VALUES (?)", (word.lower(),))
                return True
            except sqlite3.IntegrityError:
                return False
    
    def remove_banned_word(self, word: str) -> bool:
        with self.get_connection() as conn:
            result = conn.execute("DELETE FROM banned_words WHERE word = ?", (word.lower(),))
            return result.rowcount > 0
    
    def get_banned_words(self) -> List[str]:
        with self.get_connection() as conn:
            results = conn.execute("SELECT word FROM banned_words").fetchall()
            return [row['word'] for row in results]

# Global instance
db = Database()
