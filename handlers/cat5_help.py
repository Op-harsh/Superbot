import logging
from telegram import Update
from telegram.ext import ContextTypes

# config aur database imports
from config import HARSH_USER_ID
from database import get_user_level

logger = logging.getLogger(__name__)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Dynamic Help Dashboard: User ke level ke hisaab se commands dikhata hai.
    """
    user_id = update.effective_user.id
    level = get_user_level(user_id)
    
    # Agar user allowed nahi hai aur Harsh bhi nahi hai
    if level == 0 and user_id != HARSH_USER_ID:
        await update.message.reply_text("⛔ **Bhai tu kaun hai?** Tera database me naam nahi hai. Pehle Super Admin se access leke aa!")
        return

    # --- Dashboard Header ---
    help_text = "🤖 **Jarvis Master Control Panel** 🤖\n\n"

    # --- CATEGORY 1: Harsh (Dikhega sabko, par use wahi log kar payenge jinko access hai) ---
    help_text += "🛡️ **Category 1: Harsh Control**\n"
    help_text += "├ `/promoteharsh` - Custom Title ke sath Admin banao\n"
    help_text += "├ `/demoteharsh` - Saare rights chheen lo\n"
    help_text += "├ `/count` - Aaj ka quota check karo (Max 100)\n"
    help_text += "└ `/freedom DD-MM` - Limits off karo (Target Date tak)\n\n"

    # --- CATEGORY 2: Super Admin Commands ---
    if level == 99:
        help_text += "👑 **Category 2: Super Admin Only**\n"
        help_text += "├ `/allowuser` (Reply/ID) - Naye user ko access do\n"
        help_text += "├ `/rmvuser` (Reply/ID) - Access chheen lo\n"
        help_text += "└ `/allowedlist` - Saare allowed users ki list dekho\n\n"

    # --- CATEGORY 3: Spam & Troll (Allowed Users) ---
    if level > 0:
        help_text += "🚀 **Category 3: Trolling & Spam**\n"
        help_text += "├ `/spam N` (Reply) - Message ko N times spam karo\n"
        help_text += "├ `/stop` - Ongoing spam ko roko\n"
        help_text += "└ `/react on N` - Agle N minutes tak auto-reaction do\n\n"

    # --- CATEGORY 4: Moderation (Allowed Users) ---
    if level > 0:
        help_text += "🚨 **Category 4: Master Moderation**\n"
        help_text += "├ `/lock [feature]` (Reply) - User pe ban lagao\n"
        help_text += "│   └ *Features: text, sticker, link, emoji, all*\n"
        help_text += "└ `/unlock [feature]` (Reply) - Ban hatao\n\n"

    help_text += "💡 *Note: Category 4 ka lock immediately message delete kar dega.*"

    await update.message.reply_text(help_text, parse_mode="Markdown")
