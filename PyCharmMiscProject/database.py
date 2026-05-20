import json
import os
from datetime import datetime

DB_FILE = "data.json"

def load_data():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"users": {}, "messages": [], "activity": []}

def save_data(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def save_user(telegram_id, username, first_name):
    data = load_data()
    user_id = str(telegram_id)
    if user_id not in data["users"]:
        data["users"][user_id] = {
            "telegram_id": telegram_id,
            "username": username,
            "first_name": first_name,
            "created_at": datetime.now().strftime("%d.%m.%Y %H:%M"),
        }
        print(f"✅ Новый пользователь: {first_name} (@{username})")
    save_data(data)

def save_message(telegram_id, text):
    data = load_data()
    data["messages"].append({
        "user_id": telegram_id,
        "text": text,
        "time": datetime.now().strftime("%d.%m.%Y %H:%M"),
    })
    save_data(data)

def save_activity(telegram_id, action):
    data = load_data()
    data["activity"].append({
        "user_id": telegram_id,
        "action": action,
        "time": datetime.now().strftime("%d.%m.%Y %H:%M"),
    })
    save_data(data)