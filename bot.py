from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, CallbackQueryHandler, filters
import os
import qrcode

# Constants
BOT_TOKEN = "7826454726:AAHlkjAVWpeFdcQJf76RJsHJMO2YavY71oU"  # Replace with your actual bot token
ADMIN_CHAT_ID = 6531606240  # Replace with your admin's Telegram user ID
UPI_ID = "7307184945@omni"  # Replace with your actual UPI ID

# Folder containing images
IMAGE_FOLDER = "images"

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

# Ensure QR code exists
def generate_qr_code():
    qr_image_path = os.path.join(IMAGE_FOLDER, "upi_qr.png")
    if not os.path.exists(qr_image_path):
        qr = qrcode.make(UPI_ID)  # Generate QR for UPI ID
        qr.save(qr_image_path)

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("Yes", callback_data="reseller_yes"),
            InlineKeyboardButton("No", callback_data="reseller_no"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    message = (
        "Welcome! Are you a reseller?\n"
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
    generate_qr_code()
    qr_image_path = os.path.join(IMAGE_FOLDER, "upi_qr.png")

    if os.path.exists(qr_image_path):
        try:
            with open(qr_image_path, 'rb') as qr_file:
                await context.bot.send_photo(chat_id=chat_id, photo=qr_file, caption="Scan this QR code to make a payment.")
        except Exception as e:
            await query.message.reply_text(f"Error sending QR code: {str(e)}")
    else:
        await query.message.reply_text("QR code image not found. Please check the file location.")

    user_payment_data[chat_id] = {"prices": prices}

# Handle payment duration or quantity
async def handle_duration_or_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    prices = user_payment_data.get(chat_id, {}).get("prices", {})

    try:
        input_data = update.message.text.split()
        amount = int(input_data[0])
        if chat_id in resellers:
            if amount in prices:
                duration = input_data[1]
                if duration in prices[amount]:
                    user_payment_data[chat_id]['amount'] = amount
                    user_payment_data[chat_id]['duration'] = duration
                    price = prices[amount][duration]
                    await update.message.reply_text(f"Please send your payment screenshot for verification. The amount is {price} INR. Mention the amount you paid in your message.")
                else:
                    await update.message.reply_text("Invalid choice. Please select '1_day', '3_days', or '7_days'.")
            else:
                await update.message.reply_text("Invalid choice. Please select a valid key quantity (3, 5, 10).")
        else:
            days = amount
            if days in prices:
                user_payment_data[chat_id]['days'] = days
                price = prices[days]
                await update.message.reply_text(f"Please send your payment screenshot for verification. The amount is {price} INR. Mention the amount you paid in your message.")
            else:
                await update.message.reply_text("Invalid choice. Please select 1, 3, or 7 days.")
    except ValueError:
        await update.message.reply_text("Please enter a valid number and duration/key (e.g., '3 1_day' for resellers or '3' for regular users).")

# Handle payment screenshot with amount
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    if 'amount' not in user_payment_data.get(chat_id, {}) and 'days' not in user_payment_data.get(chat_id, {}):
        await update.message.reply_text("Please specify the number of days/keys first.")
        return

    user_message = update.message.caption
    user = update.message.from_user
    photo_id = update.message.photo[-1].file_id

    if chat_id in resellers:
        amount = user_payment_data[chat_id]['amount']
        duration = user_payment_data[chat_id]['duration']
        expected_price = user_payment_data[chat_id]['prices'][amount][duration]
    else:
        days = user_payment_data[chat_id]['days']
        expected_price = user_payment_data[chat_id]['prices'][days]

    # Extract the amount from the user's message
    try:
        user_paid_amount = int(user_message.split()[-1])
    except (ValueError, IndexError):
        await update.message.reply_text("Please include the amount you paid in your message with the screenshot.")
        return

    # Check if the paid amount matches the expected amount
    if user_paid_amount != expected_price:
        await update.message.reply_text(f"The amount you paid ({user_paid_amount} INR) does not match the expected amount ({expected_price} INR). Please check and send the correct amount.")
        return

    # Prepare the caption
    if chat_id in resellers:
        caption = (
            f"Payment screenshot received from {user.first_name or 'User'} (@{user.username or 'N/A'}).\n"
            f"User ID: {user.id}\nKeys: {amount}\nDuration: {duration}\nAmount Paid: {user_paid_amount} INR."
        )
    else:
        caption = (
            f"Payment screenshot received from {user.first_name or 'User'} (@{user.username or 'N/A'}).\n"
            f"User ID: {user.id}\nDays: {days}\nAmount Paid: {user_paid_amount} INR."
        )

    # Truncate the caption if necessary
    if len(caption) > 1024:  # Telegram's max caption length is 1024 characters
        caption = caption[:1020] + "..."

    keyboard = [
        [
            InlineKeyboardButton("Approve", callback_data=f"approve:{chat_id}:{expected_price}"),
            InlineKeyboardButton("Reject", callback_data=f"reject:{chat_id}"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Send the photo with the truncated caption
    await context.bot.send_photo(chat_id=ADMIN_CHAT_ID, photo=photo_id, caption=caption, reply_markup=reply_markup)

# Admin command to send APK
async def send_apk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    if chat_id == ADMIN_CHAT_ID:
        if len(context.args) == 1:
            user_id = int(context.args[0])
            if update.message.document and update.message.document.file_name.endswith(".apk"):
                apk_file = update.message.document
                try:
                    await context.bot.send_document(chat_id=user_id, document=apk_file.file_id, caption="Here is your APK file.")
                    await update.message.reply_text(f"APK file sent to user {user_id}.")
                except Exception as e:
                    await update.message.reply_text(f"Error sending APK: {str(e)}")
            else:
                await update.message.reply_text("Please send a valid APK file.")
        else:
            await update.message.reply_text("Usage: /send_apk <user_id>")

# Admin command to send key
async def send_key(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    if chat_id == ADMIN_CHAT_ID:
        if len(context.args) == 2:
            user_id = int(context.args[0])
            key = context.args[1]
            await context.bot.send_message(chat_id=user_id, text=f"Here is your key: {key}")
            await update.message.reply_text(f"Key sent to user {user_id}.")
        else:
            await update.message.reply_text("Please provide a user ID and key. Usage: /send_key <user_id> <key>")

# Main function to set up the bot
def main():
    generate_qr_code()  # Ensure QR code exists

    application = Application.builder().token(BOT_TOKEN).build()

    # Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(handle_reseller_response, pattern="^reseller_"))
    application.add_handler(MessageHandler(filters.TEXT, handle_duration_or_quantity))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(CommandHandler("send_apk", send_apk))  # Add the send_apk command
    application.add_handler(CommandHandler("send_key", send_key))  # Add the send_key command

    # Run the bot
    application.run_polling()

if __name__ == "__main__":
    main()
    
