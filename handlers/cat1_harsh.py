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
