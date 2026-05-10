import requests
import random
import string
import re
from typing import Optional, List, Dict
from config import EMAIL_API_URL, EMAIL_DOMAINS

class EmailService:
    def __init__(self):
        self.api_base = EMAIL_API_URL
    
    def generate_random_email(self) -> tuple:
        """Generate random email address. Returns (full_email, login, domain)"""
        length = random.randint(8, 15)
        login = ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))
        domain = random.choice(EMAIL_DOMAINS)
        return f"{login}@{domain}", login, domain
    
    def generate_custom_email(self, prefix: str) -> tuple:
        """Generate email with custom prefix"""
        login = prefix.lower().replace(' ', '').replace('_', '')[:20]
        if not login:
            login = ''.join(random.choices(string.ascii_lowercase, k=8))
        domain = random.choice(EMAIL_DOMAINS)
        return f"{login}@{domain}", login, domain
    
    def get_inbox(self, login: str, domain: str) -> List[Dict]:
        """Get all messages from inbox"""
        try:
            url = f"{self.api_base}/?action=getMessages&login={login}&domain={domain}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            return data if isinstance(data, list) else []
        except Exception as e:
            print(f"Error fetching inbox: {e}")
            return []
    
    def read_message(self, login: str, domain: str, message_id: int) -> Optional[Dict]:
        """Read a specific message"""
        try:
            url = f"{self.api_base}/?action=readMessage&login={login}&domain={domain}&id={message_id}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error reading message: {e}")
            return None
    
    def extract_verification_codes(self, text: str) -> List[str]:
        """Extract all verification codes from text"""
        if not text:
            return []
        
        codes = []
        patterns = [
            r'\b\d{4,8}\b',  # 4-8 digits
            r'\b[A-Z0-9]{6,10}\b',  # Alphanumeric 6-10
            r'[Cc]ode[:\s]*([A-Z0-9]{4,8})',
            r'[Oo][Tt][Pp][:\s]*(\d{4,8})',
            r'[Vv]erification[:\s]*([A-Z0-9]{4,8})',
            r'[Pp]in[:\s]*(\d{4,8})',
            r'[Tt]oken[:\s]*([A-Z0-9]{6,12})'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    codes.extend(match)
                else:
                    codes.append(match)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_codes = []
        for code in codes:
            if code not in seen:
                seen.add(code)
                unique_codes.append(code)
        
        return unique_codes[:3]  # Max 3 codes per message
    
    def delete_mailbox(self, login: str, domain: str) -> bool:
        """Delete an email inbox"""
        try:
            url = f"{self.api_base}/?action=deleteMailbox&login={login}&domain={domain}"
            response = requests.get(url, timeout=10)
            return response.status_code == 200
        except:
            return False
    
    def check_message_exists(self, login: str, domain: str, expected_sender: str = None, timeout: int = 30) -> bool:
        """Check if a message exists (for waiting feature)"""
        import time
        start_time = time.time()
        while time.time() - start_time < timeout:
            messages = self.get_inbox(login, domain)
            if messages:
                if expected_sender:
                    for msg in messages:
                        if expected_sender.lower() in msg.get('from', '').lower():
                            return True
                else:
                    return True
            time.sleep(2)
        return False

email_service = EmailService()
