from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, CallbackQueryHandler, filters
import os

# Constants
BOT_TOKEN = "7826454726:AAHlkjAVWpeFdcQJf76RJsHJMO2YavY71oU"  # Replace with your actual bot token
ADMIN_CHAT_ID = 6531606240  # Replace with your admin's Telegram user ID
UPI_ID = "7307184945@omni"  # Replace with your actual UPI ID

# Store user payment data temporarily
user_payment_data = {}

# Store reseller statuses
resellers = set()

# Prices
regular_prices = {
    1: 120,  # 1 day for 150 INR
    3: 250,  # 3 days for 300 INR
    7: 500   # 7 days for 700 INR
}
reseller_prices = {
    3: {'1_day': 240, '3_days': 450, '7_days': 900},   # Minimum 3 keys
    5: {'1_day': 400, '3_days': 750, '7_days': 1500},  # 5 keys
    10: {'1_day': 800, '3_days': 1500, '7_days': 3000} # 10 keys
}

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    # Send welcome message and ask if the user is a reseller
    keyboard = [
        [
            InlineKeyboardButton("Yes", callback_data="reseller_yes"),
            InlineKeyboardButton("No", callback_data="reseller_no"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    message = (
        f"Welcome! Your User ID is: {chat_id}\n\n"
        "Are you a reseller?\n"
        "Please choose Yes or No."
    )
    
    await update.message.reply_text(message, reply_markup=reply_markup)

# Handle reseller response
async def handle_reseller_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    chat_id = query.message.chat_id
    data = query.data

    if data == "reseller_yes":
        resellers.add(chat_id)
        prices = reseller_prices
        price_info = "\n".join([
            f"{keys} keys:\n 1 day: {price['1_day']} INR\n 3 days: {price['3_days']} INR\n 7 days: {price['7_days']} INR"
            for keys, price in prices.items()
        ])
        message = (
            f"Welcome Reseller! Please choose the number of keys you want to purchase (minimum 3 keys):\n\n"
            f"Bulk Prices:\n{price_info}\n\n"
            f"Make your payment to the following UPI ID: {UPI_ID}\n\n"
            f"Scan the QR code below to make the payment.\n\n"
            "After payment, send a screenshot of your payment here along with the amount you paid."
        )
    else:
        prices = regular_prices
        price_info = "\n".join([f"{days} days: {price} INR" for days, price in prices.items()])
        message = (
            f"Welcome! Please choose the number of days for which you are paying (1, 3, or 7 days):\n\n"
            f"Prices:\n{price_info}\n\n"
            f"Make your payment to the following UPI ID: {UPI_ID}\n\n"
            f"Scan the QR code below to make the payment.\n\n"
            "After payment, send a screenshot of your payment here along with the amount you paid."
        )

    await query.message.reply_text(message)

    # Send QR code
    qr_image_path = os.path.join("images", "upi_qr.png")
    if os.path.exists(qr_image_path):
        await context.bot.send_photo(chat_id=chat_id, photo=open(qr_image_path, 'rb'), caption="Scan this QR code to make a payment.")
    else:
        await query.message.reply_text("QR code image not found.")

    user_payment_data[chat_id] = {"prices": prices}

# Admin command to send APK manually
async def send_apk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat_id != ADMIN_CHAT_ID:
        await update.message.reply_text("You are not authorized to use this command.")
        return

    if len(context.args) != 1:
        await update.message.reply_text("Please provide a valid user ID. Usage: /send_apk <user_id>")
        return

    user_id = context.args[0]
    try:
        user_id = int(user_id)
    except ValueError:
        await update.message.reply_text("Invalid user ID.")
        return

    # Ask the admin to send the APK file
    await update.message.reply_text(f"Please send the APK file that you wish to send to user {user_id}.")

    # Set the state to await the APK file
    context.user_data['apk_recipient'] = user_id

# Handle the APK file sent by the admin
async def handle_apk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if 'apk_recipient' not in context.user_data:
        return

    # Get the user ID from context
    user_id = context.user_data['apk_recipient']

    # Check if the sent file is an APK
    if update.message.document and update.message.document.mime_type == "application/vnd.android.package-archive":
        file = update.message.document
        # Send the APK to the user
        await context.bot.send_document(chat_id=user_id, document=file.file_id, caption=f"Here is your APK file. User ID: {user_id}")
        await update.message.reply_text(f"APK sent to user {user_id}.")
        
        # Clean up context data after sending the file
        del context.user_data['apk_recipient']
    else:
        await update.message.reply_text("Please send a valid APK file.")

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_reseller_response, pattern="^reseller_"))
    app.add_handler(CommandHandler("send_apk", send_apk))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_apk))

    app.run_polling()

if __name__ == "__main__":
    main()
