import logging
import random
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatPermissions
from telegram.ext import ContextTypes

# config.py se variables import kar rahe hain
from config import (
    HARSH_USER_ID, MAX_DAILY_MESSAGES, MUTE_DURATION_HOURS, 
    SPAM_TIME_WINDOW_MINUTES, SPAM_MESSAGE_LIMIT, ROAST_LINES
)

logger = logging.getLogger(__name__)
# ==========================================
# 1. ADMIN CONTROLS (/promoteharsh & /demoteharsh)
# ==========================================

async def promote_harsh(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != HARSH_USER_ID:
        await update.message.reply_text("Arre bhai, ye aukaat sirf Harsh ki hai! 😅")
        return
    
    chat_id = update.effective_chat.id
    try:
        bot_member = await context.bot.get_chat_member(chat_id, context.bot.id)
        if bot_member.status != 'administrator' or not bot_member.can_promote_members:
            await update.message.reply_text("Bhai pehle mujhe admin banao with 'Add new admins' permission! 🤖")
            return
    except Exception as e:
        await update.message.reply_text(f"Error checking bot permissions: {e}")
        return
    
    # Tumhara Original Keyboard wapas aa gaya!
    keyboard = [
        [InlineKeyboardButton("All Permissions 🚀", callback_data="all_perms"),
         InlineKeyboardButton("Custom Select 🎯", callback_data="custom_perms")],
        [InlineKeyboardButton("Cancel ❌", callback_data="cancel_perms")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Bhai, konse permissions chahiye? 🤔", reply_markup=reply_markup)


# --- NAYA FUNCTION: INLINE BUTTONS KO HANDLE KARNE KE LIYE ---
async def permission_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "cancel_perms":
        await query.edit_message_text("Cancelled bhai! 👍")
        context.user_data.clear()
        return

    if query.data == "all_perms":
        await query.edit_message_text("Admin title kya rakhna hai? (reply kar de)")
        context.user_data['promotion_type'] = 'all'
        context.user_data['waiting_for_title'] = True

    elif query.data == "custom_perms":
        await query.edit_message_text("🛠️ Custom Select abhi aage add karenge! Abhi ke liye 'All Permissions' use kar le.")
        # Note: Tumne purane code me bhi custom ka logic nahi diya tha, agar iska poora toggle menu banwana hai toh bata dena, wo bhi bana dunga!


# ==========================================
# 2. STATS & FREEDOM MODE (/count & /freedom)
# ==========================================

async def count_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != HARSH_USER_ID:
        return

    # Check Freedom Status
    if context.bot_data.get('freedom_mode', False):
        expiry = context.bot_data.get('freedom_until')
        if expiry and datetime.now() < expiry:
            await update.message.reply_text(f"🕊️ Tu abhi Freedom Mode me hai bhai! Date: {expiry.strftime('%d-%m')} tak koi limit nahi hai. Maje kar!")
            return

    now = datetime.now()
    today = now.date()

    if 'msg_date' not in context.user_data or context.user_data['msg_date'] != today:
        count = 0
    else:
        count = context.user_data.get('daily_msg_count', 0)

    remaining = MAX_DAILY_MESSAGES - count
    
    if remaining <= 0:
        await update.message.reply_text("🚨 Tera aaj ka quota khatam! Tu mute ho chuka hai. Padhle ab!")
    else:
        await update.message.reply_text(f"📊 Tera aaj ka hisaab:\n✉️ Messages sent: {count}/{MAX_DAILY_MESSAGES}\n⏳ Bache hue: {remaining}\n\nLimit cross ki to seedha 12 ghante ka mute! ⚠️")


async def toggle_freedom(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Usage: /freedom 25-10 (DD-MM)"""
    if update.effective_user.id != HARSH_USER_ID:
        return
    
    args = context.args
    if not args:
        # Turn OFF Freedom mode manually
        context.bot_data['freedom_mode'] = False
        await update.message.reply_text("🔒 Freedom Mode OFF! Wapas protection mode On ho gaya hai. Padhai shuru!")
        return

    date_str = args[0]
    try:
        # Date parse (DD-MM)
        now = datetime.now()
        target_date = datetime.strptime(date_str, "%d-%m")
        # Ensure year is correct (Current or next year)
        target_date = target_date.replace(year=now.year)
        if target_date < now:
            target_date = target_date.replace(year=now.year + 1)
        
        context.bot_data['freedom_mode'] = True
        context.bot_data['freedom_until'] = target_date
        await update.message.reply_text(f"🕊️ **FREEDOM MODE ON!** 🕊️\nTere saare limitations {target_date.strftime('%d-%m-%Y')} tak disable kar diye gaye hain. Jee le apni zindagi!")
    
    except ValueError:
        await update.message.reply_text("❌ Galat format bhai! Aise likh: /freedom 25-10")


# ==========================================
# 3. CORE LOGIC PIPELINE (Quota & Spam)
# ==========================================
async def process_harsh_activity(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    user_id = update.effective_user.id

    # --- PART 1: ADMIN TITLE INTERCEPT (Tumhara logic) ---
    if context.user_data.get('waiting_for_title') and user_id == HARSH_USER_ID:
        title = update.message.text
        try:
            await context.bot.promote_chat_member(
                chat_id=update.effective_chat.id,
                user_id=HARSH_USER_ID,
                can_change_info=True, can_delete_messages=True, can_invite_users=True,
                can_restrict_members=True, can_pin_messages=True, can_promote_members=True,
                is_anonymous=False
            )
            await context.bot.set_chat_administrator_custom_title(
                chat_id=update.effective_chat.id,
                user_id=HARSH_USER_ID,
                custom_title=title[:16] 
            )
            await update.message.reply_text(f"🎉 **Hogaya bhai!** Ab tu admin hai with title: '{title}' 👑")
        except Exception as e:
            await update.message.reply_text(f"❌ Error aaya bhai: {str(e)}")
        
        context.user_data.clear() # Title mil gaya, state clear karo
        return False # Message process ho gaya, pipeline yahin rok do
        
    # --- ISKE NEECHE TUMHARA PURANA QUOTA AUR SPAM WALA CODE RAHEGA ---
    if user_id != HARSH_USER_ID:
        return True 
    # ... baki code same ...

async def process_harsh_activity(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """
    Ye function main.py se call hoga. 
    Agar Harsh mute ho gaya, toh ye False return karega taaki pipeline aage react na kare.
    """
    user_id = update.effective_user.id
    if user_id != HARSH_USER_ID:
        return True # Harsh nahi hai, aage badho

    now = datetime.now()
    today = now.date()

    # --- FREEDOM CHECK ---
    if context.bot_data.get('freedom_mode', False):
        expiry = context.bot_data.get('freedom_until')
        if expiry and now < expiry:
            return True # Freedom on hai, na spam count, na quota count
        else:
            context.bot_data['freedom_mode'] = False # Time khatam, wapas jail me

    # --- INIT USER DATA ---
    if 'msg_date' not in context.user_data or context.user_data['msg_date'] != today:
        context.user_data['msg_date'] = today
        context.user_data['daily_msg_count'] = 0
        context.user_data['msg_timestamps'] = []

    # --- QUOTA CHECK ---
    context.user_data['daily_msg_count'] += 1
    count = context.user_data['daily_msg_count']

    if count >= MAX_DAILY_MESSAGES:
        chat_id = update.effective_chat.id
        try:
            # 1. Demote
            await context.bot.promote_chat_member(
                chat_id=chat_id, user_id=HARSH_USER_ID,
                can_change_info=False, can_delete_messages=False, can_invite_users=False,
                can_restrict_members=False, can_pin_messages=False, can_promote_members=False,
                is_anonymous=False
            )
            # 2. Mute (12 Hours)
            until_date = now + timedelta(hours=MUTE_DURATION_HOURS)
            await context.bot.restrict_chat_member(
                chat_id=chat_id, user_id=HARSH_USER_ID,
                permissions=ChatPermissions(can_send_messages=False),
                until_date=until_date
            )
            await update.message.reply_text(
                "🚨 **LIMIT CROSSED!** 🚨\n"
                "100 messages poore ho gaye! Admin role chheen liya gaya hai aur 12 ghante ke liye mute. "
                "Chup chaap Physics Wallah ka lecture laga! 😡📚"
            )
        except Exception as e:
            logger.error(f"Action failed: {e}")
        
        return False # False ka matlab pipeline yahin rok do

    # --- ANTI-SPAM (ROASTING) ---
    timestamps = context.user_data['msg_timestamps']
    timestamps.append(now)
    
    # Purane messages clear karo jo 5 minute window se bahar hain
    five_mins_ago = now - timedelta(minutes=SPAM_TIME_WINDOW_MINUTES)
    timestamps = [t for t in timestamps if t > five_mins_ago]
    context.user_data['msg_timestamps'] = timestamps
    
    if len(timestamps) >= SPAM_MESSAGE_LIMIT:
        random_line = random.choice(ROAST_LINES)
        # Roast bhejenge par auto-delete nahi karenge (1.2 Request)
        await update.message.reply_text(f"@{update.effective_user.username} {random_line}")
        context.user_data['msg_timestamps'] = [] # Reset kar do taaki lagatar roasts na aayen

    return True # Sab theek hai, aage badho
