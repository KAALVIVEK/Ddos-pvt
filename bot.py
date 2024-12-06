from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, CallbackQueryHandler, filters
import os

# Constants
BOT_TOKEN = "7826454726:AAHlkjAVWpeFdcQJf76RJsHJMO2YavY71oU"  # Replace with your actual bot token
ADMIN_CHAT_ID = 7083378335  # Replace with your admin's Telegram user ID
UPI_ID = "evilempire654@okicici"  # Replace with your actual UPI ID

# Folder containing images and admin files
IMAGE_FOLDER = "images"
ADMIN_FILE_FOLDER = "admin_files"

# Ensure the folder exists
os.makedirs(ADMIN_FILE_FOLDER, exist_ok=True)

# Store user payment data temporarily
user_payment_data = {}

# Store reseller statuses
resellers = set()

# Store the current APK file path
current_apk_file_path = None

# Prices
regular_prices = {
    1: 200,  # 1 day for 200 INR
    3: 300,  # 3 days for 300 INR
    7: 700   # 7 days for 700 INR
}
reseller_prices = {
    3: {'1_day': 300, '3_days': 450, '7_days': 900},   # Minimum 3 keys
    5: {'1_day': 500, '3_days': 750, '7_days': 1500},  # 5 keys
    10: {'1_day': 1000, '3_days': 1500, '7_days': 3000} # 10 keys
}

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
    qr_image_path = os.path.join(IMAGE_FOLDER, "upi_qr.png")
    if os.path.exists(qr_image_path):
        await context.bot.send_photo(chat_id=chat_id, photo=open(qr_image_path, 'rb'), caption="Scan this QR code to make a payment.")
    else:
        await query.message.reply_text("QR code image not found.")

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
    await update.message.reply_text("Thank you! Your payment is being verified by the admin.")

# Admin approval or rejection
async def admin_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data.split(":")
    user_id = int(data[1])

    if data[0] == "approve":
        amount = int(data[2])
        await context.bot.send_message(chat_id=user_id, text="Your payment has been verified. The admin will send your key shortly.")
        await query.edit_message_text(text=f"Approved user {user_id} for {amount}.")
    elif data[0] == "reject":
        await context.bot.send_message(chat_id=user_id, text="Your payment has been rejected. Please check the amount and try again.")
        await query.edit_message_text(text=f"Rejected user {user_id}.")

# Admin upload APK
async def upload_apk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global current_apk_file_path

    if update.message.from_user.id == ADMIN_CHAT_ID:
        if update.message.document:
            file = update.message.document
            file_name = file.file_name

            if file_name.endswith(".apk"):
                file_path = os.path.join(ADMIN_FILE_FOLDER, file_name)
                await file.download_to_drive(file_path)
                current_apk_file_path = file_path
                await update.message.reply_text(f"APK file '{file_name}' has been uploaded successfully.")
            else:
                await update.message.reply_text("Please upload a valid APK file.")
        else:
            await update.message.reply_text("Please send a document file (APK) to upload.")
    else:
        await update.message.reply_text("You do not have permission to upload APK files.")

# Send APK to the user
async def send_apk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if current_apk_file_path:
        await update.message.reply_text("Sending APK file...")
        with open(current_apk_file_path, 'rb') as apk_file:
            await update.message.reply_document(document=apk_file)
    else:
        await update.message.reply_text("No APK file uploaded yet.")

def main():
    application = Application.builder().token(BOT_TOKEN).build()

    # Command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("upload_apk", upload_apk))
    application.add_handler(CommandHandler("send_apk", send_apk))

    # Message handler for the resellers or payment message
    application.add_handler(MessageHandler(filters.TEXT, handle_duration_or_quantity))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    # Callback query handler for reseller response and admin commands
    application.add_handler(CallbackQueryHandler(handle_reseller_response))
    application.add_handler(CallbackQueryHandler(admin_commands, pattern="^(approve|reject):"))

    application.run_polling()

if __name__ == "__main__":
    main()
