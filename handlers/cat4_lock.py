import logging
from telegram import Update
from telegram.ext import ContextTypes

# Database se function import kar rahe hain
from database import lock_user_feature, unlock_user_feature, get_user_locks, get_user_level

logger = logging.getLogger(__name__)

# ==========================================
# 1. LOCK COMMAND (/lock)
# ==========================================
async def lock_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Kisi user ko restrict karne ke liye.
    Usage: Reply to a message with `/lock [feature]` 
    Features: text, sticker, link, emoji, all
    """
    # Check if the user trying to lock is authorized (Level > 0)
    if get_user_level(update.effective_user.id) == 0:
        await update.message.reply_text("⛔ **Access Denied:** Tera level 0 hai bhai, tu kisi ko lock nahi kar sakta!")
        return

    # Check if command is a reply
    if not update.message.reply_to_message:
        await update.message.reply_text("⚠️ **Format galat hai!** Kisi user ke message par reply karke likh: `/lock [feature]`\nFeatures: `text`, `sticker`, `link`, `emoji`, `all`")
        return

    target_user = update.message.reply_to_message.from_user
    target_id = target_user.id

    # Arguments check
    if not context.args:
        await update.message.reply_text("⚠️ **Feature missing!** Bata toh sahi kya lock karna hai? (e.g., `/lock sticker`)")
        return

    feature = context.args[0].lower()
    valid_features = ['text', 'sticker', 'link', 'emoji', 'all']

    if feature not in valid_features:
        await update.message.reply_text(f"❌ **Invalid Feature!** Sirf inme se choose kar: {', '.join(valid_features)}")
        return

    try:
        lock_user_feature(target_id, feature)
        await update.message.reply_text(f"🔒 **Target Locked!**\nAb `{target_user.first_name}` group me **{feature}** nahi bhej payega. Bhejte hi gayab! 🥷")
    except Exception as e:
        await update.message.reply_text(f"❌ Error locking user: {e}")


# ==========================================
# 2. UNLOCK COMMAND (/unlock)
# ==========================================
async def unlock_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Lock hatane ke liye.
    Usage: Reply to a message with `/unlock [feature]`
    """
    if get_user_level(update.effective_user.id) == 0:
        return

    if not update.message.reply_to_message:
        await update.message.reply_text("⚠️ Kisi ke message par reply karke feature batao: `/unlock sticker`")
        return

    target_user = update.message.reply_to_message.from_user
    target_id = target_user.id

    if not context.args:
        await update.message.reply_text("⚠️ **Feature missing!** Kya unlock karna hai? (e.g., `/unlock all`)")
        return

    feature = context.args[0].lower()

    try:
        if feature == 'all':
            # Agar 'all' unlock karna hai, toh saare features loop karke hatane padenge
            locks = get_user_locks(target_id)
            for lk in locks:
                unlock_user_feature(target_id, lk)
            await update.message.reply_text(f"🔓 **Target Fully Unlocked!**\n`{target_user.first_name}` ab poori tarah azaad hai.")
        else:
            unlock_user_feature(target_id, feature)
            await update.message.reply_text(f"🔓 **Feature Unlocked!**\n`{target_user.first_name}` ab **{feature}** bhej sakta hai.")
    except Exception as e:
        await update.message.reply_text(f"❌ Error unlocking user: {e}")


# ==========================================
# 3. MASTER PIPELINE CHECKER (Auto-Delete)
# ==========================================
async def check_locked_content(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """
    Ye function main.py ki master pipeline ke sabse pehle (STEP 1) chalta hai.
    Agar message me wo cheez hui jo locked hai, toh ye usko delete kar dega aur True return karega.
    """
    msg = update.message
    if not msg:
        return False

    user_id = update.effective_user.id
    locks = get_user_locks(user_id)

    # Agar user par koi lock nahi hai, toh safe hai
    if not locks:
        return False

    should_delete = False

    # 1. Total Lockdown check
    if 'all' in locks:
        should_delete = True

    # 2. Sticker check
    elif 'sticker' in locks and msg.sticker:
        should_delete = True

    # 3. Link (URL) check
    elif 'link' in locks:
        # Check text or caption entities for URLs
        entities = msg.entities or msg.caption_entities or []
        if any(ent.type in ['url', 'text_link'] for ent in entities):
            should_delete = True

    # 4. Text check (Sirf text, commands nahi)
    elif 'text' in locks and msg.text and not msg.text.startswith('/'):
        should_delete = True

    # 5. Emoji check (Basic Unicode Filter)
    elif 'emoji' in locks and msg.text:
        # Check if any character in the text is an emoji (Unicode range test)
        if any(ord(char) > 0x2600 for char in msg.text):
            should_delete = True

    # Agar koi rule match hua, toh delete karo
    if should_delete:
        try:
            await msg.delete()
            return True # Delete ho gaya, Master pipeline aage nahi badhegi!
        except Exception as e:
            logger.error(f"Failed to delete locked message: {e}")
            return False # Admin permission nahi hai
            
    return False # Koi rule match nahi hua, safe hai
