import requests
import re
from config import API

def create_email():
    r = requests.post(API + "/new", json={
        "min_name_length": 10,
        "max_name_length": 10
    })
    return r.json()["email"]

def get_messages(email):
    try:
        r = requests.get(f"{API}/{email}/messages")
        return r.json()
    except:
        return []

def extract_code(text):
    if not text:
        return None
    match = re.search(r"\b\d{4,8}\b", text)
    return match.group(0) if match else None