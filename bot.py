import qrcode
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, InputFile
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
UPI_ID = "kaalvivek@fam"  # Replace with your UPI ID

# Store user payment data temporarily
user_payment_data = {}

# Generate UPI QR code
def generate_upi_qr(upi_id: str, amount: float, transaction_note: str) -> str:
    upi_uri = f"upi://pay?pa={upi_id}&pn=YourName&am={amount}&tn={transaction_note}&cu=INR"
    qr = qrcode.make(upi_uri)
    file_path = "/tmp/upi_qr.png"
    qr.save(file_path)
    return file_path

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prices = {
        1: 10,  # 1 day for 150 INR
        3: 25,  # 3 days for 300 INR
        7: 50   # 7 days for 700 INR
    }
    price_info = "\n".join([f"{days} days: {price} INR" for days, price in prices.items()])

    message = (
        f"Welcome! Please choose the number of days for which you are paying (1, 3, or 7 days):\n\n"
        f"Prices:\n{price_info}\n\n"
        f"Make your payment to the following UPI ID: {UPI_ID}"
    )
    
    # Generate QR code for 1 day as an example (you can generate more dynamically based on user input)
    qr_path = generate_upi_qr(UPI_ID, prices[1], "Payment for 1 day")
    
    await update.message.reply_text(message)
    await context.bot.send_photo(chat_id=update.message.chat_id, photo=open(qr_path, 'rb'), caption="Scan this QR code to pay.")

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
            qr_path = generate_upi_qr(UPI_ID, amount, f"Payment for {days} days")
            
            await update.message.reply_text(f"Please send your payment screenshot for verification. The amount is {amount} INR.")
            await context.bot.send_photo(chat_id=update.message.chat_id, photo=open(qr_path, 'rb'), caption=f"Scan this QR code to pay {amount} INR.")
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
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_duration))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(CallbackQueryHandler(admin_commands))
    application.add_handler(CommandHandler("sendkey", send_key))

    # Start polling
    application.run_polling()

if __name__ == "__main__":
    main()
