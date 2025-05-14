import os
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    MessageHandler,
    filters,
    CommandHandler,
    CallbackQueryHandler,
)
from collections import defaultdict

# Load bot token from .env
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Track message_id to seen users
seen_tracker = defaultdict(set)

# Send a message with a "👀 Mark as Seen" button
async def track_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message or message.chat.type == "private":
        return

    message_id = message.message_id
    chat_id = message.chat.id

    button = InlineKeyboardButton("👀 Mark as Seen", callback_data=f"seen:{message_id}")
    reply_markup = InlineKeyboardMarkup([[button]])

    await context.bot.send_message(
        chat_id=chat_id,
        text="Tap below to mark this message as seen.",
        reply_to_message_id=message_id,
        reply_markup=reply_markup
    )

# Handle button clicks
async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    data = query.data

    if data.startswith("seen:"):
        msg_id = int(data.split(":")[1])
        seen_tracker[msg_id].add(user.username or user.full_name)

        await query.answer("You marked this as seen.")
        await query.edit_message_text(f"👀 Seen by: {', '.join(seen_tracker[msg_id])}")

# /seen <message_id>
async def seen_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text("Please provide a message ID: /seen <message_id>")
        return

    try:
        msg_id = int(args[0])
    except ValueError:
        await update.message.reply_text("Invalid message ID.")
        return

    seen_users = seen_tracker.get(msg_id, set())
    if seen_users:
        reply = "These users have seen the message:\n" + "\n".join(f"- {u}" for u in seen_users)
    else:
        reply = "No one has marked this message as seen yet."

    await update.message.reply_text(reply)

# Setup app
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), track_message))
app.add_handler(CallbackQueryHandler(handle_button))
app.add_handler(CommandHandler("seen", seen_command))

if __name__ == "__main__":
    app.run_polling()
