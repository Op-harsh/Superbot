import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes

# --- 1. Load Environment Variables ---
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("Bhai, .env file me BOT_TOKEN set nahi hai! Pehle wo daal.")

# --- 2. Logging Setup ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- 3. Import Moduler Handlers ---
from handlers.cat1_harsh import promote_harsh, demote_harsh, count_messages, toggle_freedom, process_harsh_activity, permission_callback
from handlers.cat2_admin import allow_user, rmv_user, allowed_list
from handlers.cat3_spam import spam_command, stop_spam, toggle_reaction, process_auto_reaction
from handlers.cat4_lock import lock_command, unlock_command, check_locked_content
from handlers.cat5_help import help_command

# NAYA IMPORT: Category 6 ke naye functions
from handlers.cat6_tag import create_tag_list, add_to_list, tag_custom_list, tag_all
from database import init_db, add_group_user

# --- 4. The Master Pipeline (Conflict Fixer) ---
async def master_message_pipeline(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    # STEP 0: Tagging Data Collection (/all command ke liye)
    # Jo bhi banda message karega, uski ID chup-chaap DB me save ho jayegi
    add_group_user(update.effective_user.id)

    # STEP 1: Lock Check (Category 4)
    is_deleted = await check_locked_content(update, context)
    if is_deleted:
        return 

    # STEP 2 & 3: Harsh Quota & Anti-Spam Check (Category 1)
    can_continue = await process_harsh_activity(update, context)
    if not can_continue:
        return 

    # STEP 4: Auto-Reaction (Category 3)
    await process_auto_reaction(update, context)
    

# --- 5. Main Bot Setup ---
def main():
    logger.info("Bot engine start ho raha hai...")
    
    # NAYI LINE: Database start hone par SuperAdmin fix karega
    init_db()
    
    # Application build karo
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # --- CATEGORY 1 Commands (Harsh Control) ---
    application.add_handler(CommandHandler("promoteharsh", promote_harsh))
    application.add_handler(CommandHandler("demoteharsh", demote_harsh))
    application.add_handler(CommandHandler("count", count_messages))
    application.add_handler(CommandHandler("freedom", toggle_freedom))
    application.add_handler(CallbackQueryHandler(permission_callback))

    # --- CATEGORY 2 Commands (Admin Control) ---
    application.add_handler(CommandHandler("allowuser", allow_user))
    application.add_handler(CommandHandler("rmvuser", rmv_user))
    application.add_handler(CommandHandler("allowedlist", allowed_list))

    # --- CATEGORY 3 Commands (Spam & React) ---
    application.add_handler(CommandHandler("spam", spam_command))
    application.add_handler(CommandHandler("stop", stop_spam))
    application.add_handler(CommandHandler("react", toggle_reaction))

    # --- CATEGORY 4 Commands (Lock System) ---
    application.add_handler(CommandHandler("lock", lock_command))
    application.add_handler(CommandHandler("unlock", unlock_command))

    # --- CATEGORY 5 Commands (Help) ---
    application.add_handler(CommandHandler("start", help_command))
    application.add_handler(CommandHandler("help", help_command))

    # --- CATEGORY 6 Commands (Tagging System) ---
    application.add_handler(CommandHandler("create", create_tag_list))
    application.add_handler(CommandHandler("add", add_to_list))
    application.add_handler(CommandHandler("all", tag_all))
    
    # CUSTOM TAGS WALA WOH HANDLER (Ise baaki commands ke baad rakhna zaroori hai)
    application.add_handler(MessageHandler(filters.Regex(r'^/[a-zA-Z0-9_]+'), tag_custom_list))

    # --- The Master Pipeline Handler ---
    # Ye pipeline sabse last me honi chahiye!
    application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, master_message_pipeline))

    logger.info("Jarvis is online! Polling started...")
    application.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
