import requests
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# Constants
BOT_TOKEN = "7525850725:AAFj6u8yOSMr5oEYsXueSx9pQGAWoEEy5cc"  # Replace with your bot token
ADMIN_CHAT_ID = 7083378335  # Replace with the admin's Telegram user ID

# Store user payment data temporarily
user_payment_data = {}

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome! How many days are you paying for? (1, 3, or 7 days)")
    user_payment_data[update.message.chat_id] = {}

# Handle payment duration
async def handle_duration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    try:
        days = int(update.message.text)
        if days in [1, 3, 7]:
            user_payment_data[chat_id]['days'] = days
            await update.message.reply_text("Please send your payment screenshot for verification.")
        else:
            await update.message.reply_text("Invalid choice. Please select 1, 3, or 7 days.")
    except ValueError:
        await update.message.reply_text("Please enter a valid number (1, 3, or 7).")

# Handle payment screenshot
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    if 'days' not in user_payment_data.get(chat_id, {}):
        await update.message.reply_text("Please specify the number of days first.")
        return

    days = user_payment_data[chat_id]['days']
    user = update.message.from_user
    photo_id = update.message.photo[-1].file_id

    # Prepare the caption
    caption = (
        f"Payment screenshot received from {user.first_name or 'User'} (@{user.username or 'N/A'}).\n"
        f"User ID: {user.id}\nDuration: {days} days."
    )
    
    # Truncate the caption if necessary
    if len(caption) > 1024:  # Telegram's max caption length is 1024 characters
        caption = caption[:1020] + "..."

    keyboard = [
        [
            InlineKeyboardButton("Approve", callback_data=f"approve:{chat_id}:{days}"),
            InlineKeyboardButton("Reject", callback_data=f"reject:{chat_id}"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Send the photo with the truncated caption
    await context.bot.send_photo(chat_id=ADMIN_CHAT_ID, photo=photo_id, caption=caption, reply_markup=reply_markup)
    await update.message.reply_text("Thank you! Your payment is being verified by the admin.")

# Admin approval or rejection
async def admin_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data.split(":")
    user_id = int(data[1])

    if data[0] == "approve":
        days = int(data[2])
        await context.bot.send_message(chat_id=user_id, text="Your payment has been verified. The admin will send your key shortly.")
        await query.edit_message_text(text=f"Approved user {user_id} for {days} days. Remember to send the key manually.")
    elif data[0] == "reject":
        await context.bot.send_message(chat_id=user_id, text="Your payment could not be verified. Please contact support.")
        await query.edit_message_text(text=f"Rejected payment for user {user_id}.")

# Admin send key command
async def send_key(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat_id != ADMIN_CHAT_ID:
        await update.message.reply_text("You are not authorized to use this command.")
        return

    try:
        user_id = int(context.args[0])
        key = context.args[1]
        username = context.args[2]
        password = context.args[3]
        
        success_message = (
            f"Your payment has been verified. Here are your details:\n\n"
            f"**Key:** `{key}`\n"
            f"**Username:** `{username}`\n"
            f"**Password:** `{password}`\n\n"
            f"Thank you for your purchase!"
        )
        
        await context.bot.send_message(chat_id=user_id, text=success_message, parse_mode="Markdown")
        await update.message.reply_text("Key sent successfully.")
    except (IndexError, ValueError):
        await update.message.reply_text("Usage: /sendkey <user_id> <key> <username> <password>")

# Main function
def main():
    application = Application.builder().token(BOT_TOKEN).build()

    # Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_duration))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(CallbackQueryHandler(admin_commands))
    application.add_handler(CommandHandler("sendkey", send_key))

    # Start polling
    application.run_polling()

if __name__ == "__main__":
    main()
