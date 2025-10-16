from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)

# 🔐 Directly set your bot token and admin ID here
TOKEN = "7869537534:AAFS5eDlLkDctuyrUZ87xCT_JA8RwDrO0Yg"
ADMIN_ID = 7598974440  # Replace with your Telegram user ID

# 🧠 In-memory storage
user_sessions = {}  # user_id → selected leader
leaders = {}        # leader_name → Telegram ID
logs = []           # list of {"user_id", "leader", "message"}

# 🚀 Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    keyboard = [[InlineKeyboardButton("🙏 New Prayer Request", callback_data="new_request")]]

    if user_id == ADMIN_ID:
        keyboard.append([InlineKeyboardButton("👑 Admin Panel", callback_data="admin_panel")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Welcome to *Prayer Connect Bot!*\nChoose an option below:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

# 🎛️ Handle button actions
async def select_leader(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data == "admin_panel":
        keyboard = [
            [InlineKeyboardButton("➕ Add Leader", callback_data="add_leader")],
            [InlineKeyboardButton("➖ Remove Leader", callback_data="remove_leader")],
            [InlineKeyboardButton("📜 View Logs", callback_data="view_logs")],
            [InlineKeyboardButton("📢 Broadcast", callback_data="broadcast")],
        ]
        await query.edit_message_text("👑 Admin Panel:", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    if query.data == "new_request":
        if not leaders:
            await query.edit_message_text("No prayer leaders are currently available.")
            return
        keyboard = [[InlineKeyboardButton(name, callback_data=name)] for name in leaders.keys()]
        await query.edit_message_text("🙏 Choose your prayer leader:", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    if query.data == "add_leader":
        await query.edit_message_text("Send the new leader's name:")
        context.user_data["admin_action"] = "add"
        return

    if query.data == "remove_leader":
        if not leaders:
            await query.edit_message_text("No leaders to remove.")
            return
        keyboard = [[InlineKeyboardButton(name, callback_data=f"remove_{name}")] for name in leaders.keys()]
        await query.edit_message_text("Select a leader to remove:", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    if query.data.startswith("remove_"):
        name = query.data.replace("remove_", "")
        if name in leaders:
            del leaders[name]
            await query.edit_message_text(f"✅ Removed leader: {name}")
        else:
            await query.edit_message_text("Leader not found.")
        return

    if query.data == "view_logs":
        if not logs:
            await query.edit_message_text("No logs found.")
            return
        text = "\n".join([f"{log['leader']}: {log['message']}" for log in logs[-10:]])
        await query.edit_message_text(f"📜 Recent Prayer Logs:\n{text}")
        return

    if query.data == "broadcast":
        await query.edit_message_text("Send your broadcast message:")
        context.user_data["admin_action"] = "broadcast"
        return

    # Leader selected
    user_sessions[user_id] = query.data
    await query.edit_message_text(f"💬 You selected *{query.data}*.\nSend your prayer request:", parse_mode="Markdown")

# 💬 Handle messages
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    if user_id == ADMIN_ID and "admin_action" in context.user_data:
        action = context.user_data.pop("admin_action")
        if action == "add":
            leaders[text] = ADMIN_ID
            await update.message.reply_text(f"✅ Added leader: {text}")
        elif action == "broadcast":
            for uid in user_sessions.keys():
                try:
                    await context.bot.send_message(chat_id=uid, text=f"📢 Broadcast:\n{text}")
                except:
                    pass
            await update.message.reply_text("✅ Broadcast sent.")
        return

    if user_id in user_sessions:
        leader = user_sessions.pop(user_id)
        logs.append({"user_id": user_id, "leader": leader, "message": text})
        await update.message.reply_text(f"🙏 Your prayer request to *{leader}* has been sent.", parse_mode="Markdown")
        try:
            await context.bot.send_message(chat_id=leaders[leader], text=f"📥 New prayer request:\n{text}")
        except:
            await update.message.reply_text("⚠️ Failed to notify leader.")
    else:
        await update.message.reply_text("Please start with /start")

# 🧠 Main function
def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(select_leader))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == "__main__":
    main()