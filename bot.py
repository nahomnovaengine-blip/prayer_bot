import os
import logging
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

# ✅ Load environment variables
load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# ✅ Admin Telegram ID (replace with your actual ID)
ADMIN_ID = 7598974440

# ✅ Prayer leaders (manually managed)
def get_leaders():
    return {
        "Nahom": 7598974440,
        "Eleni": 987654321,
        "Rediet": 456789123
    }

# 🧠 Store temporary user sessions
user_sessions = {}

# 🚀 /start command - show leader selection
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    leaders = get_leaders()
    if not leaders:
        await update.message.reply_text(
            "🙏 Welcome to *Prayer Connect Bot!*\n\n"
            "No prayer leaders are currently available. Please check back later.",
            parse_mode="Markdown"
        )
        return

    keyboard = [
        [InlineKeyboardButton(name, callback_data=name)] for name in leaders.keys()
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "🙏 Welcome to *Prayer Connect Bot!*\n\n"
        "Choose your prayer leader from the list below:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

# 🙋 Handle leader selection
async def select_leader(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    leader_name = query.data
    user_id = query.from_user.id

    user_sessions[user_id] = leader_name

    await query.edit_message_text(
        f"💬 You selected *{leader_name}*.\n\n"
        "Please type your prayer request below:",
        parse_mode="Markdown"
    )

# 🙏 Receive and forward prayer requests
async def receive_prayer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    prayer_text = update.message.text
    leaders = get_leaders()

    if user_id not in user_sessions:
        await update.message.reply_text(
            "❌ Please start by choosing a leader using /start first."
        )
        return

    leader_name = user_sessions[user_id]
    leader_id = leaders.get(leader_name)

    if not leader_id:
        await update.message.reply_text(
            "❌ The selected leader is no longer available. Please use /start to choose another leader."
        )
        del user_sessions[user_id]
        return

    message_to_leader = (
        f"🙏 *New Prayer Request*\n"
        f"To: *{leader_name}*\n"
        f"Message:\n\n{prayer_text}\n\n"
        f"---\n"
        f"💫 *Please pray for this request*"
    )

    try:
        await context.bot.send_message(
            chat_id=leader_id,
            text=message_to_leader,
            parse_mode="Markdown"
        )

        await update.message.reply_text(
            f"✅ Your prayer request has been sent anonymously to *{leader_name}*.\n\n"
            f"God bless you! 🙏",
            parse_mode="Markdown"
        )

        del user_sessions[user_id]

    except Exception as e:
        await update.message.reply_text(
            "❌ Sorry, we couldn't deliver your prayer request. "
            "The leader might be unavailable. Please try again later."
        )
        del user_sessions[user_id]
        logging.error(f"Error sending message: {e}")

# 🛡️ /leaders command - admin only
async def show_leaders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ This command is for admins only.")
        return

    leaders = get_leaders()
    if not leaders:
        await update.message.reply_text("No leaders are currently configured.")
        return

    leader_list = "\n".join([f"• {name} (ID: {id})" for name, id in leaders.items()])
    await update.message.reply_text(
        f"📋 Current Leaders ({len(leaders)}):\n\n{leader_list}"
    )

# ❌ /cancel command - clear session
async def cancel_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in user_sessions:
        del user_sessions[user_id]
    await update.message.reply_text(
        "Session cleared. Use /start to begin again."
    )

# 🆘 /help command
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🙏 *Prayer Connect Bot Help*\n\n"
        "/start - Choose a prayer leader\n"
        "/cancel - Cancel current session\n"
        "/leaders - View available leaders (admin only)\n"
        "/help - Show this help message",
        parse_mode="Markdown"
    )

# ✅ Log bot info after startup
async def on_startup(app):
    bot_info = await app.bot.get_me()
    print(f"✅ Bot started as @{bot_info.username} (ID: {bot_info.id})")
    print("🤖 Prayer Connect Bot is running...")
    print(f"🙏 {len(get_leaders())} leaders configured")
    print("💫 Users can use /start to send prayer requests")
    print("👑 Admins can use /leaders to view leader list")

# 🧩 Main entry point
def main():
    logging.basicConfig(level=logging.INFO)

    if not TOKEN:
        print("⚠️ TELEGRAM_BOT_TOKEN not found. Set it in your .env file.")
        return

    app = ApplicationBuilder().token(TOKEN).post_init(on_startup).build()

    # Register handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("leaders", show_leaders))
    app.add_handler(CommandHandler("cancel", cancel_request))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CallbackQueryHandler(select_leader))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, receive_prayer))

    app.run_polling()

if __name__ == '__main__':
    main()