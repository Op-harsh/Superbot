import asyncio
import logging
import random
from datetime import datetime, timedelta
from telegram import Update, ReactionTypeEmoji
from telegram.ext import ContextTypes

# config.py aur database.py se imports
from config import ANTI_SPAM_DELAY, BIG_REACTIONS, LEVEL_CAPS
from database import get_user_level

logger = logging.getLogger(__name__)

# ==========================================
# 1. LEVEL-BASED SPAMMER (/spam & /stop)
# ==========================================

async def spam_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Usage: 
    - Reply karke: /spam 10
    - Text ke sath: /spam 10 Bhai padhle
    """
    user_id = update.effective_user.id
    level = get_user_level(user_id)
    
    # Check Access
    if level == 0:
        await update.message.reply_text("❌ **Access Denied:** Aukat me reh bhai, ye command sirf allowed users ke liye hai!")
        return
        
    args = context.args
    if not args:
        await update.message.reply_text("⚠️ **Format galat hai!** Aise likh: `/spam 10 bhai padhle` ya kisi message ko reply karke `/spam 10`")
        return
        
    try:
        n = int(args[0])
    except ValueError:
        await update.message.reply_text("⚠️ Bhai pehla argument number hona chahiye! (e.g., /spam 10)")
        return

    # Check Level Caps
    cap = LEVEL_CAPS.get(level, 0)
    # Agar 99 (Super Admin) nahi hai aur limit cross kar raha hai
    if cap != 9999 and n > cap:
        n = cap
        await update.message.reply_text(f"⚠️ **Limit Auto-Adjusted:** Tera level {level} hai, tu max {cap} messages bhej sakta hai. Main {cap} messages bhej raha hoon.")

    # Reset Stop Flag
    context.chat_data['stop_spam'] = False
    
    custom_text = " ".join(args[1:]) if len(args) > 1 else None
    reply_to = update.message.reply_to_message

    if not custom_text and not reply_to:
        await update.message.reply_text("⚠️ Are bhai! Ya toh custom text de, ya kisi message pe reply kar jisko copy karna hai.")
        return

    sent_count = 0
    # Async Loop: Bot freeze nahi hoga isse!
    for i in range(n):
        # Agar kisi ne /stop daba diya
        if context.chat_data.get('stop_spam'):
            await update.message.reply_text(f"🛑 **Spam Stopped!** ({sent_count}/{n} messages sent)")
            break
            
        try:
            if custom_text:
                await context.bot.send_message(chat_id=update.effective_chat.id, text=custom_text)
            elif reply_to:
                await context.bot.copy_message(
                    chat_id=update.effective_chat.id, 
                    from_chat_id=update.effective_chat.id, 
                    message_id=reply_to.message_id
                )
            
            sent_count += 1
            await asyncio.sleep(ANTI_SPAM_DELAY) # Non-blocking sleep!
            
        except Exception as e:
            logger.error(f"Spam error: {e}")
            await asyncio.sleep(1) # Agar error aaye toh 1 sec ruk jao


async def stop_spam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ongoing spam loop ko rokne ke liye."""
    if get_user_level(update.effective_user.id) == 0:
        return # Un-authorized user ignore hoga
        
    context.chat_data['stop_spam'] = True
    await update.message.reply_text("⛔ **Emergency Brake applied!** Spamming roki ja rahi hai...")


# ==========================================
# 2. AUTO-REACTOR SYSTEM (/react)
# ==========================================

async def toggle_reaction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Usage: 
    - /react on 10 (Sabke liye 10 mins tak ON)
    - Reply to a user with: /react on 10 (Sirf us bande ke liye 10 mins tak ON)
    - /react off (Band karne ke liye)
    """
    if get_user_level(update.effective_user.id) == 0:
        return
        
    args = context.args
    if not args or args[0].lower() == 'off':
        context.chat_data['react_mode'] = False
        await update.message.reply_text("📴 **Auto-Reactor OFF!** Ab kisi ko reactions nahi milenge.")
        return
        
    if args[0].lower() == 'on':
        # Default 10 minutes agar time na diya ho
        mins = int(args[1]) if len(args) > 1 and args[1].isdigit() else 10
        
        context.chat_data['react_mode'] = True
        context.chat_data['react_expiry'] = datetime.now() + timedelta(minutes=mins)
        
        # Target Lock Logic (Agar reply kiya hai)
        if update.message.reply_to_message:
            target_user = update.message.reply_to_message.from_user
            context.chat_data['react_target_id'] = target_user.id
            await update.message.reply_text(f"🎯 **Target Locked!**\nAgle {mins} minute tak **{target_user.first_name}** ke har message pe main big reaction doonga! 🔥")
        else:
            context.chat_data['react_target_id'] = None
            await update.message.reply_text(f"🚀 **Group Reactor ON!**\nAgle {mins} minute tak group me aane wale har message pe reaction aayega! 🎉")


async def process_auto_reaction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Ye function main.py ki master pipeline se call hoga.
    """
    # 1. Check if reaction mode is ON
    if not context.chat_data.get('react_mode'):
        return
        
    # 2. Check Expiry Time
    expiry = context.chat_data.get('react_expiry')
    if not expiry or datetime.now() > expiry:
        context.chat_data['react_mode'] = False
        return
        
    # 3. Check Target (Agar kisi specific bande pe lock lagaya hai)
    target_id = context.chat_data.get('react_target_id')
    if target_id and update.effective_user.id != target_id:
        return # Agar ye message target ka nahi hai, toh kuch mat karo
        
    # 4. Fire the Big Reaction!
    try:
        emoji = random.choice(BIG_REACTIONS)
        # python-telegram-bot v20+ syntax for reactions
        await update.message.set_reaction(reaction=ReactionTypeEmoji(emoji), is_big=True)
    except Exception as e:
        # Ignore errors (jaise agar admin rights nahi hain react karne ke)
        logger.debug(f"Reaction failed: {e}")
