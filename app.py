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
from datetime import datetime

# Load BOT_TOKEN from .env
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Seen tracker
seen_tracker = defaultdict(set)

# Active user tracker
active_users = defaultdict(dict)

# Track message and add 👀 button
async def track_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message or message.chat.type == "private":
        return

    chat_id = message.chat.id
    message_id = message.message_id
    user = message.from_user
    user_id = user.id
    username = user.username or user.full_name

    # Track activity
    active_users[chat_id][user_id] = (username, datetime.now())

    # Add 👀 button
    button = InlineKeyboardButton("👀 Mark as Seen", callback_data=f"seen:{message_id}")
    markup = InlineKeyboardMarkup([[button]])

    await context.bot.send_message(
        chat_id=chat_id,
        text="Tap below to mark this message as seen.",
        reply_to_message_id=message_id,
        reply_markup=markup
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

    elif data == "show_active":
        chat_id = query.message.chat.id
        users = active_users.get(chat_id, {})

        if not users:
            await query.edit_message_text("Koi active user nahi mila bhai.")
            return

        sorted_users = sorted(users.items(), key=lambda x: x[1][1], reverse=True)
        lines = [f"🔥 Active Users:"]
        for i, (uid, (username, last_seen)) in enumerate(sorted_users, 1):
            lines.append(f"{i}. {username} - {last_seen.strftime('%H:%M:%S')}")

        await query.edit_message_text("\n".join(lines))

# /seen <msg_id> command
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

# /active command with button
async def show_active_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    button = InlineKeyboardButton("📋 Show Active Users", callback_data="show_active")
    markup = InlineKeyboardMarkup([[button]])
    await update.message.reply_text("Tap the button below to see active users:", reply_markup=markup)

# Setup bot
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), track_message))
app.add_handler(CallbackQueryHandler(handle_button))
app.add_handler(CommandHandler("seen", seen_command))
app.add_handler(CommandHandler("active", show_active_users))

if __name__ == "__main__":
    app.run_polling()
