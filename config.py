import os
from dotenv import load_dotenv

# .env file se variables load karne ke liye
load_dotenv()

# --- 1. Bot & Admin Setup ---
# Token ko direct yahan mat likhna, .env file me likhna security ke liye
BOT_TOKEN = os.getenv("BOT_TOKEN") 

# Super Admin (Tumhari ID - Category 2 & 3.2 se)
MAIN_ADMIN_ID = int(os.getenv("MAIN_ADMIN_ID", "7712492008"))

# Target User (Harsh ki ID - Category 1)
HARSH_USER_ID = 8483875806


# --- 2. Category 1: Harsh Control Limits ---
MAX_DAILY_MESSAGES = 100
MUTE_DURATION_HOURS = 12

# Agar 5 minute me 8 messages aaye, toh spam trigger hoga
SPAM_TIME_WINDOW_MINUTES = 5
SPAM_MESSAGE_LIMIT = 8


# --- 3. Category 3: Spam & Troll Settings ---
# Message copy karne ke beech ka delay (taaki bot freeze na ho)
ANTI_SPAM_DELAY = 0.15 

# Auto-Reaction me use hone wale emojis (Category 3.1)
BIG_REACTIONS = ["👍", "❤️", "🔥", "👏", "😎", "🤩", "🤡", "💀", "💩"]

# Spam Command Power Levels Caps (Category 3.2)
LEVEL_CAPS = {
    1: 10,  # Level 1 user can spam max 10 times
    2: 30,  # Level 2 user can spam max 30 times
    3: 60,  # Level 3 user can spam max 60 times
    99: 9999 # Level ALL (Super Admin) - practically unlimited
}


# --- 4. Roast Lines Database ---
# Yahan tum apni marzi se aur bhi khatarnak taane add kar sakte ho
ROAST_LINES = [
    "Na mujhe nhi lagta tumhara jee hoga.",
    "rj sir ka danda dekha hai?? ha whi apne wha daal lo chomu",
    "padhle warna nali ka keeda bankr rh jaiga",
    "hass kya rha chomu , padhle!!",
    "tum jisko reply kiya wo dharti ka bojh hai bade wala  (execpt agar koi didi hai to)",
    "bhai blow job krna padega agar padhai nhi kiye to",
    "tumse gf na banegi. kyuki tum collage nhi ja paoge",
    "collage ke sath sex krna hai to kalam uthao",
    "kalam chalao juban nhi",
    "abe ohh machhar ka jhaat padhle",
    "hass kya rha hai gandu",
    "bas ek bar socho collage jane ke baad kya life hoge",
    "lagta hai majdooro ka salary badh gya hai isliye tum majdoori krne ka soch rhe",
    "pdhle bc"
]
