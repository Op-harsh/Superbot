import logging
from telegram import Update
from telegram.ext import ContextTypes

# Importing configurations and database functions
from config import MAIN_ADMIN_ID
from database import add_user, remove_user, get_all_users

logger = logging.getLogger(__name__)

# ==========================================
# HELPER FUNCTION: EXTRACT TARGET USER
# ==========================================
def extract_target_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Ek smart helper function jo detect karta hai ki command kisi message 
    ka reply hai, ya fir direct user ID pass ki gayi hai arguments mein.
    Returns: (target_user_id, level)
    """
    target_id = None
    level = 1 # Default level

    # Case 1: Command is a reply to another user's message
    if update.message.reply_to_message:
        target_id = update.message.reply_to_message.from_user.id
        # Agar reply ke sath level bhi bheja hai (e.g., /allowuser 2)
        if context.args and context.args[0].isdigit():
            level = int(context.args[0])
            
    # Case 2: Command contains a direct User ID (e.g., /allowuser 123456789 3)
    elif context.args:
        if context.args[0].isdigit():
            target_id = int(context.args[0])
            # Agar ID ke baad level bhi diya hai
            if len(context.args) > 1 and context.args[1].isdigit():
                level = int(context.args[1])
                
    return target_id, level

# ==========================================
# 1. ALLOW USER COMMAND (/allowuser)
# ==========================================
async def allow_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Naye users ko bot ka access dene ke liye. 
    Usage: Reply to a message with /allowuser [level] OR /allowuser [user_id] [level]
    """
    # Security Check: Sirf Super Admin ye command chala sakta hai
    if update.effective_user.id != MAIN_ADMIN_ID:
        await update.message.reply_text("⛔ **Access Denied:** Ye command sirf Super Admin (Tum) use kar sakte ho!")
        return

    target_id, level = extract_target_data(update, context)

    if not target_id:
        await update.message.reply_text(
            "⚠️ **Sahi format use karo bhai:**\n"
            "1. Kisi ke message par reply karke likho: `/allowuser`\n"
            "2. Ya fir ID daalo: `/allowuser 123456789`\n"
            "*(Optional: Space dekar Level bhi de sakte ho, e.g., `/allowuser 123456789 3`)*",
            parse_mode="Markdown"
        )
        return

    try:
        # Saving to JSON Database
        add_user(target_id, level)
        await update.message.reply_text(
            f"✅ **Success!**\n"
            f"User `{target_id}` ko database me add kar diya gaya hai.\n"
            f"🏅 **Assigned Level:** {level}",
            parse_mode="Markdown"
        )
        logger.info(f"SuperAdmin authorized user {target_id} with level {level}")
    except Exception as e:
        await update.message.reply_text(f"❌ Database error: {e}")
        logger.error(f"Failed to add user {target_id}: {e}")

# ==========================================
# 2. REMOVE USER COMMAND (/rmvuser)
# ==========================================
async def rmv_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Kisi user ka access chheen lene ke liye.
    Usage: Reply to a message with /rmvuser OR /rmvuser [user_id]
    """
    if update.effective_user.id != MAIN_ADMIN_ID:
        await update.message.reply_text("⛔ **Access Denied!**")
        return

    target_id, _ = extract_target_data(update, context)

    if not target_id:
        await update.message.reply_text("⚠️ User ki ID daalo ya uske message par reply karo.")
        return

    # Super Admin protection
    if str(target_id) == str(MAIN_ADMIN_ID):
        await update.message.reply_text("🤡 **Bhai tu khud ko hi block karega kya?** Super Admin ko remove nahi kiya ja sakta.")
        return

    try:
        remove_user(target_id)
        await update.message.reply_text(f"🗑️ **User Revoked:** `{target_id}` ko system se nikal diya gaya hai. Ab wo koi command use nahi kar payega.", parse_mode="Markdown")
        logger.info(f"SuperAdmin removed user {target_id}")
    except Exception as e:
        await update.message.reply_text(f"❌ Error removing user: {e}")

# ==========================================
# 3. ALLOWED USERS LIST COMMAND (/allowedlist)
# ==========================================
async def allowed_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Database me maujood saare authorized users ki list aur unke power levels dikhata hai.
    """
    if update.effective_user.id != MAIN_ADMIN_ID:
        await update.message.reply_text("⛔ **Access Denied!**")
        return

    users_data = get_all_users()
    
    if not users_data:
        await update.message.reply_text("📂 Database ekdam khali hai bhai. Koi authorized user nahi hai.")
        return

    # Message formatting
    response_text = "📜 **Authorized Users Dashboard** 📜\n\n"
    
    total_users = 0
    for uid, info in users_data.items():
        total_users += 1
        level = info.get('level', 1)
        locks = info.get('locks', [])
        
        # Determine Title based on level
        if str(uid) == str(MAIN_ADMIN_ID):
            title = "👑 Super Admin"
        elif level == 99:
            title = "⭐ Co-Admin"
        else:
            title = f"🛡️ Level {level} User"

        # Format user entry
        response_text += f"**{total_users}. ID:** `{uid}`\n"
        response_text += f"   ├ Role: {title}\n"
        if locks:
            response_text += f"   └ 🔒 Restrictions: {', '.join(locks)}\n"
        else:
            response_text += f"   └ 🟢 Restrictions: None\n"
        response_text += "\n"

    response_text += f"**Total Allowed Accounts:** {total_users}"
    
    await update.message.reply_text(response_text, parse_mode="Markdown")
