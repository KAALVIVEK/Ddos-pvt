from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, CallbackQueryHandler, filters

# Constants
BOT_TOKEN = "7525850725:AAFj6u8yOSMr5oEYsXueSx9pQGAWoEEy5cc"  # Replace with your bot token

# Moderators and their QR code paths with UPI IDs
moderators = {
    7083378335: {"qr_path": "images/admin_qr.png", "upi": "kaalvivek@fam"},  # Admin's UPI and QR code
    6469998312: {"qr_path": "images/mod_qr.png", "upi": "mod@upi"}       # Moderator's UPI and QR code
}

# Store online moderators
online_moderators = set()

# Store user payment data temporarily
user_payment_data = {}

# Mark moderator as online
async def online(update: Update, context: ContextTypes.DEFAULT_TYPE):
    moderator_id = update.message.chat_id
    if moderator_id in moderators:
        online_moderators.add(moderator_id)
        await update.message.reply_text("You are now marked as online.")
    else:
        await update.message.reply_text("You are not a registered moderator.")

# Mark moderator as offline
async def offline(update: Update, context: ContextTypes.DEFAULT_TYPE):
    moderator_id = update.message.chat_id
    if moderator_id in online_moderators:
        online_moderators.remove(moderator_id)
        await update.message.reply_text("You are now marked as offline.")
    else:
        await update.message.reply_text("You are already offline or not a registered moderator.")

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prices = {
        1: 150,  # 1 day for 10 INR
        3: 300,  # 3 days for 25 INR
        7: 700   # 7 days for 50 INR
    }
    price_info = "\n".join([f"{days} days: {price} INR" for days, price in prices.items()])

    message = (
        f"Welcome! Please choose the number of days for which you are paying (1, 3, or 7 days):\n\n"
        f"Prices:\n{price_info}\n\n"
        "After payment, send a screenshot of your payment here. A moderator will assist you shortly."
    )
    
    await update.message.reply_text(message)

    user_payment_data[update.message.chat_id] = {"prices": prices}

# Handle payment duration
async def handle_duration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    prices = user_payment_data.get(chat_id, {}).get("prices", {})

    try:
        days = int(update.message.text)
        if days in prices:
            user_payment_data[chat_id]['days'] = days
            amount = prices[days]
            await update.message.reply_text(f"Please send your payment screenshot for verification. The amount is {amount} INR.")
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

    # Send the payment screenshot to the first online moderator
    if online_moderators:
        online_id = next(iter(online_moderators))  # Get the first online moderator
        qr_path = moderators[online_id]["qr_path"]
        upi_id = moderators[online_id]["upi"]

        # Send QR and UPI details to the user
        qr_caption = f"Please pay to the UPI ID below and upload the payment screenshot.\n\n**UPI ID:** {upi_id}"
        await context.bot.send_photo(chat_id=chat_id, photo=open(qr_path, 'rb'), caption=qr_caption, parse_mode="Markdown")

        # Send payment screenshot to the moderator
        await context.bot.send_photo(chat_id=online_id, photo=photo_id, caption=caption, reply_markup=reply_markup)
    else:
        await update.message.reply_text("No moderators are currently online. Please try again later.")

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
    if update.message.chat_id not in moderators.keys():
        await update.message.reply_text("You are not authorized to use this command.")
        return

    try:
        user_id = int(context.args[0])
        key = context.args[1]
        
        success_message = (
            f"Your payment has been verified. Here is your key:\n\n"
            f"**Key:** `{key}`\n\n"
            f"Thank you for your purchase!"
        )
        
        await context.bot.send_message(chat_id=user_id, text=success_message, parse_mode="Markdown")
        await update.message.reply_text("Key sent successfully.")
    except (IndexError, ValueError):
        await update.message.reply_text("Usage: /sendkey <user_id> <key>")

# Main function
def main():
    application = Application.builder().token(BOT_TOKEN).build()

    # Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("online", online))
    application.add_handler(CommandHandler("offline", offline))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_duration))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(CallbackQueryHandler(admin_commands))
    application.add_handler(CommandHandler("sendkey", send_key))

    # Start the bot
    application.run_polling()

if __name__ == "__main__":
    main()
