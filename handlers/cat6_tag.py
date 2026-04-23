import logging
from telegram import Update
from telegram.ext import ContextTypes
from database import create_custom_list, add_user_to_list, get_list_users, get_all_group_users

logger = logging.getLogger(__name__)

async def create_tag_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⚠️ Bhai list ka naam toh de! Example: `/create ff`")
        return
        
    list_name = context.args[0].lower()
    chat_id = update.effective_chat.id
    
    success = create_custom_list(chat_id, list_name) 
    if success:
        await update.message.reply_text(f"✅ List '{list_name}' ban gayi! Bando ko add karne ke liye `/add {list_name}` use kar.")
    else:
        await update.message.reply_text(f"⚠️ '{list_name}' naam ki list pehle se bani hui hai.")

async def add_to_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⚠️ Command sahi likh bhai: `/add <list_name>`")
        return
        
    list_name = context.args[0].lower()
    chat_id = update.effective_chat.id
    target_user = None

    if update.message.reply_to_message:
        target_user = update.message.reply_to_message.from_user
    elif len(context.args) > 1 and context.args[1].isdigit():
        try:
            member = await context.bot.get_chat_member(chat_id, int(context.args[1]))
            target_user = member.user
        except Exception:
            await update.message.reply_text("⚠️ Invalid ID ya banda group me nahi hai.")
            return
    else:
        await update.message.reply_text("⚠️ Ya toh reply kar, ya ID de: `/add ff 12345678`")
        return

    if target_user:
        if target_user.is_bot:
            await update.message.reply_text("🤖 Bots ko tag list me nahi daal sakte.")
            return
            
        add_user_to_list(chat_id, list_name, target_user.id)
        mention = f"[{target_user.first_name}](tg://user?id={target_user.id})"
        await update.message.reply_text(f"✅ Done! {mention} ko '{list_name}' list me daal diya.", parse_mode="Markdown")

async def tag_custom_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if not text or not text.startswith('/'):
        return
        
    command_name = text.split()[0][1:].lower()
    chat_id = update.effective_chat.id
    
    # Standard commands ko ignore karo
    standard_cmds = ['create', 'add', 'all', 'lock', 'unlock', 'spam', 'react', 'allowuser', 'rmvuser', 'allowedlist', 'start', 'help', 'count', 'freedom']
    if command_name in standard_cmds:
        return

    user_ids = get_list_users(chat_id, command_name)
    if user_ids:
        mentions = "".join([f"[\u200b](tg://user?id={uid})" for uid in user_ids])
        await update.message.reply_text(f"🔔 **Tagging members for {command_name.upper()}!**\n{mentions}", parse_mode="Markdown")

async def tag_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    all_users = get_all_group_users() 
    
    if not all_users:
        await update.message.reply_text("⚠️ Database me log nahi hain!")
        return

    await update.message.reply_text("📢 **Sabko tag kar raha hu...**")
    
    mentions = ""
    for idx, uid in enumerate(all_users):
        mentions += f"[\u200b](tg://user?id={uid})"
        if (idx + 1) % 50 == 0:
            await update.message.reply_text(f"Wake up guys! {mentions}", parse_mode="Markdown")
            mentions = ""
            
    if mentions:
        await update.message.reply_text(f"Wake up guys! {mentions}", parse_mode="Markdown")
