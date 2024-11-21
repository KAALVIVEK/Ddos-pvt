from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, CallbackQueryHandler, filters
import os

# Constants
BOT_TOKEN = "YOUR_BOT_TOKEN"  # Replace with your actual bot token
ADMIN_CHAT_ID = 7083378335  # Replace with your admin's Telegram user ID
UPI_ID = "kaalvivek@fam"  # Replace with your actual UPI ID

# Folder containing images
IMAGE_FOLDER = "images"

# Store user payment data temporarily
user_payment_data = {}

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prices = {
        1: 150,  # 1 day for 150 INR
        3: 300,  # 3 days for 300 INR
        7: 700   # 7 days for 700 INR
    }
    price_info = "\n".join([f"{days} days: {price} INR" for days, price in prices.items()])

    message = (
        f"Welcome! Please choose the number of days for which you are paying (1, 3, or 7 days):\n\n"
        f"Prices:\n{price_info}\n\n"
        f"Make your payment to the following UPI ID: {UPI_ID}\n\n"
        f"Scan the QR code below to make the payment.\n\n"
        "After payment, send a screenshot of your payment here along with the amount you paid."
    )
    
    await update.message.reply_text(message)

    # Send QR code
    qr_image_path = os.path.join(IMAGE_FOLDER, "upi_qr.png")
    if os.path.exists(qr_image_path):
        await context.bot.send_photo(chat_id=update.message.chat_id, photo=open(qr_image_path, 'rb'), caption="Scan this QR code to make a payment.")
    else:
        await update.message.reply_text("QR code image not found.")

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
            await update.message.reply_text(f"Please send your payment screenshot for verification. The amount is {amount} INR. Mention the amount you paid in your message.")
        else:
            await update.message.reply_text("Invalid choice. Please select 1, 3, or 7 days.")
    except ValueError:
        await update.message.reply_text("Please enter a valid number (1, 3, or 7).")

# Handle payment screenshot with amount
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    if 'days' not in user_payment_data.get(chat_id, {}):
        await update.message.reply_text("Please specify the number of days first.")
        return

    user_message = update.message.caption
    days = user_payment_data[chat_id]['days']
    expected_amount = user_payment_data[chat_id]['prices'][days]
    user = update.message.from_user
    photo_id = update.message.photo[-1].file_id

    # Extract the amount from the user's message
    try:
        user_amount = int(user_message.split()[-1])
    except (ValueError, IndexError):
        await update.message.reply_text("Please include the amount you paid in your message with the screenshot.")
        return

    # Check if the paid amount matches the expected amount
    if user_amount != expected_amount:
        await update.message.reply_text(f"The amount you paid ({user_amount} INR) does not match the expected amount ({expected_amount} INR). Please check and send the correct amount.")
        return

    # Prepare the caption
    caption = (
        f"Payment screenshot received from {user.first_name or 'User'} (@{user.username or 'N/A'}).\n"
        f"User ID: {user.id}\nDuration: {days} days.\nAmount Paid: {user_amount} INR."
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
        
        success_message = (
            f"Your payment has been verified. Here is your key:\n\n"
            f"**Key:** `{key}`\n\n"
            f"Thank you for your purchase!"
        )
        
        await context.bot.send_message(chat_id=user_id, text=success_message, parse_mode="Markdown")
        await update.message.reply_text("Key sent successfully.")
    except (IndexError, ValueError):
        await update.message.reply_text("Usage: /sendkey <user_id> <key>")

# Help command
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_message = (
        "/start - Begin the payment process and get UPI details.\n"
        "/sendkey <user_id> <key> - Admin command to send the key to a user.\n"
        "/send_qr - Send the QR code for UPI payment.\n"
        "/help - Show this help message."
    )
    await update.message.reply_text(help_message)

# Send QR code image to user
async def send_qr_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_chat_id = update.message.chat_id
    
    # Path to the QR code image (relative to the current directory)
    qr_image_path = os.path.join("images", "upi_qr.png")
    
    if os.path.exists(qr_image_path):
        # Send the QR code image
        await context.bot.send_photo(chat_id=user_chat_id, photo=open(qr_image_path, 'rb'), caption="Scan this QR code to make a payment.")
    else:
        await update.message.reply_text("QR code image not found.")

# Main function
def main():
    application = Application.builder().token(BOT_TOKEN).build()

    # Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_duration))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(CallbackQueryHandler(admin_commands))  # This is the correct import for handling callback queries
    application.add_handler(CommandHandler("sendkey", send_key))
    application.add_handler(CommandHandler("send_qr", send_qr_code))  # Handler for sending QR code
    application.add_handler(CommandHandler("help", help_command))  # Handler for help command

    # Start the bot
    application.run_polling()

if __name__ == "__main__":
    main()
