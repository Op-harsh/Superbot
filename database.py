import json
import os
from config import MAIN_ADMIN_ID

# Database file ka naam
DB_FILE = "users.json"

# --- Helper Functions (Read/Write) ---
def _load_data():
    """JSON file ko read karta hai. Agar file nahi hai, toh default structure banata hai."""
    if not os.path.exists(DB_FILE):
        return {"users": {str(MAIN_ADMIN_ID): {"level": 99, "locks": []}}}
    
    with open(DB_FILE, 'r') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            # Agar file corrupt ho jaye, toh reset kar do
            return {"users": {str(MAIN_ADMIN_ID): {"level": 99, "locks": []}}}

def _save_data(data):
    """Data ko JSON file me save karta hai."""
    with open(DB_FILE, 'w') as f:
        json.dump(data, f, indent=4)


# --- Initialization ---
def init_db():
    """Bot start hone par check karega ki Super Admin (Tum) database me ho ya nahi."""
    data = _load_data()
    if str(MAIN_ADMIN_ID) not in data["users"]:
        data["users"][str(MAIN_ADMIN_ID)] = {"level": 99, "locks": []}
        _save_data(data)


# --- Category 2 & 3: User Management & Levels ---
def add_user(user_id: int, level: int = 1):
    """Naye user ko allow karega aur level dega (Default Level 1)."""
    data = _load_data()
    uid_str = str(user_id)
    
    if uid_str not in data["users"]:
        data["users"][uid_str] = {"level": level, "locks": []}
    else:
        data["users"][uid_str]["level"] = level # Agar pehle se hai toh level update kar do
        
    _save_data(data)

def remove_user(user_id: int):
    """User ko database se nikal dega (Super admin ko nahi nikal sakta)."""
    data = _load_data()
    uid_str = str(user_id)
    
    if uid_str in data["users"] and uid_str != str(MAIN_ADMIN_ID):
        del data["users"][uid_str]
        _save_data(data)

def get_all_users() -> dict:
    """Saare allowed users ki list dega."""
    return _load_data()["users"]

def is_user_allowed(user_id: int) -> bool:
    """Check karega ki banda allowed hai ya nahi."""
    return str(user_id) in _load_data()["users"]

def get_user_level(user_id: int) -> int:
    """Spam command ke liye user ka level check karega."""
    data = _load_data()
    return data["users"].get(str(user_id), {}).get("level", 0)


# --- Category 4: Lock/Moderation System ---
def lock_user_feature(user_id: int, feature: str):
    """Kisi user ke liye specific feature (sticker, link, etc.) lock karega."""
    data = _load_data()
    uid_str = str(user_id)
    
    # User ko pehle DB me hona zaroori hai lock hone ke liye
    if uid_str not in data["users"]:
        data["users"][uid_str] = {"level": 0, "locks": []}
        
    if feature not in data["users"][uid_str]["locks"]:
        data["users"][uid_str]["locks"].append(feature)
        
    _save_data(data)

def unlock_user_feature(user_id: int, feature: str):
    """Lock hatane ke liye."""
    data = _load_data()
    uid_str = str(user_id)
    
    if uid_str in data["users"]:
        if feature in data["users"][uid_str]["locks"]:
            data["users"][uid_str]["locks"].remove(feature)
        _save_data(data)

def get_user_locks(user_id: int) -> list:
    """Check karega ki is user par kya-kya pabandi (locks) lagi hain."""
    data = _load_data()
    return data["users"].get(str(user_id), {}).get("locks", [])

# --- Category 6: Tagging System ---
def create_custom_list(chat_id: int, list_name: str) -> bool:
    data = _load_data()
    cid = str(chat_id)
    if "lists" not in data: data["lists"] = {}
    if cid not in data["lists"]: data["lists"][cid] = {}
    if list_name in data["lists"][cid]: return False
        
    data["lists"][cid][list_name] = []
    _save_data(data)
    return True

def add_user_to_list(chat_id: int, list_name: str, user_id: int):
    data = _load_data()
    cid = str(chat_id)
    if "lists" not in data: data["lists"] = {}
    if cid not in data["lists"]: data["lists"][cid] = {}
    if list_name not in data["lists"][cid]: data["lists"][cid][list_name] = []
        
    if user_id not in data["lists"][cid][list_name]:
        data["lists"][cid][list_name].append(user_id)
        _save_data(data)

def get_list_users(chat_id: int, list_name: str) -> list:
    data = _load_data()
    return data.get("lists", {}).get(str(chat_id), {}).get(list_name, [])

def add_group_user(user_id: int):
    data = _load_data()
    if "group_users" not in data: data["group_users"] = []
    if user_id not in data["group_users"]:
        data["group_users"].append(user_id)
        _save_data(data)

def get_all_group_users() -> list:
    return _load_data().get("group_users", [])

