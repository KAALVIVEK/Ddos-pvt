from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, CallbackQueryHandler, filters
import os

# Constants
BOT_TOKEN = "7826454726:AAHlkjAVWpeFdcQJf76RJsHJMO2YavY71oU"  # Replace with your actual bot token
ADMIN_CHAT_ID = 6531606240  # Replace with your admin's Telegram user ID
UPI_ID = "7307184945@omni"  # Replace with your actual UPI ID

# Folder containing APKs (Keys)
KEYS_FOLDER = "keys"  # Folder where your APK or keys are stored

# Store user payment data temporarily
user_payment_data = {}

# Store reseller statuses
resellers = set()

# Prices
regular_prices = {
    1: 120,   # 1 days for 120 INR
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

# Admin command to send key to user
async def send_key(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Check if the user issuing the command is the admin
    if update.message.chat_id != ADMIN_CHAT_ID:
        await update.message.reply_text("You are not authorized to use this command.")
        return
    
    # Command should be in the format: /send_key <user_id> <key>
    if len(context.args) != 2:
        await update.message.reply_text("Usage: /send_key <user_id> <key>")
        return
    
    try:
        user_id = int(context.args[0])  # Get user ID
        key = context.args[1]  # Get the key (e.g., APK file or key string)
        
        # Check if the key exists in the KEYS_FOLDER (APK or other file)
        key_path = os.path.join(KEYS_FOLDER, key)
        if os.path.exists(key_path):
            # If the key is an APK file, send the file
            await context.bot.send_document(chat_id=user_id, document=open(key_path, 'rb'))
            await update.message.reply_text(f"Key (APK) sent to user {user_id}.")
        else:
            # If it's just a string key, send the text as a message
            await context.bot.send_message(chat_id=user_id, text=f"Your key: {key}")
            await update.message.reply_text(f"Key sent to user {user_id}.")
    
    except ValueError:
        await update.message.reply_text("Invalid user ID or key format. Please try again.")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_reseller_response, pattern="^reseller_"))
    app.add_handler(CommandHandler("send_key", send_key))  # Remove pass_args here

    app.run_polling()

if __name__ == "__main__":
    main()
