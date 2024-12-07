from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
import os

# Constants
BOT_TOKEN = "7525850725:7243095492:AAFIOpvDLv45g5PMk8tyUY0d5sb65RrErcQ"  # Replace with your actual bot token
ADMIN_CHAT_ID = 5187934508  # Replace with your admin's Telegram user ID
UPI_ID = "evilempire654@okicici"  # Replace with your actual UPI ID
IMAGE_FOLDER = "images"
TELEGRAM_CHANNEL_LINK = "https://t.me/+HEyXXgA_1hU4NmZl"  # Replace with your actual Telegram channel link

# Store user payment data temporarily
user_payment_data = {}
resellers = set()

# Prices
regular_prices = {1: 200, 3: 300, 7: 700}
reseller_prices = {
    3: {'1_day': 150, '3_days': 750, '7_days': 1200},
    5: {'1_day': 250, '3_days': 1250, '7_days': 2000},
    10: {'1_day': 500, '3_days': 2500, '7_days': 4000}
}

# Key storage for uploaded keys
stored_keys = {1: [], 3: [], 7: []}

# Start command
async def start(update: Update, context) -> None:
    keyboard = [
        [
            InlineKeyboardButton("Yes", callback_data="reseller_yes"),
            InlineKeyboardButton("No", callback_data="reseller_no"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Welcome! Are you a reseller?\nPlease choose Yes or No.",
        reply_markup=reply_markup
    )

# Handle reseller response
async def handle_reseller_response(update: Update, context) -> None:
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

    qr_image_path = os.path.join(IMAGE_FOLDER, "upi_qr.png")
    if os.path.exists(qr_image_path):
        await context.bot.send_photo(chat_id=chat_id, photo=open(qr_image_path, 'rb'), caption="Scan this QR code to make a payment.")
    else:
        await query.message.reply_text("QR code image not found.")

    user_payment_data[chat_id] = {"prices": prices}

# Handle payment duration or quantity
async def handle_duration_or_quantity(update: Update, context) -> None:
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
async def handle_photo(update: Update, context) -> None:
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

    try:
        user_paid_amount = int(user_message.split()[-1])
    except (ValueError, IndexError):
        await update.message.reply_text("Please include the amount you paid in your message with the screenshot.")
        return

    if user_paid_amount != expected_price:
        await update.message.reply_text(f"The amount you paid ({user_paid_amount} INR) does not match the expected amount ({expected_price} INR). Please check and send the correct amount.")
        return

    caption = (
        f"Payment screenshot received from {user.first_name or 'User'} (@{user.username or 'N/A'}).\n"
        f"User ID: {user.id}\nAmount Paid: {user_paid_amount} INR."
    )

    keyboard = [
        [
            InlineKeyboardButton("Approve", callback_data=f"approve:{chat_id}:{expected_price}"),
            InlineKeyboardButton("Reject", callback_data=f"reject:{chat_id}"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await context.bot.send_photo(chat_id=ADMIN_CHAT_ID, photo=photo_id, caption=caption, reply_markup=reply_markup)
    await update.message.reply_text("Thank you! Your payment is being verified by the admin.")

# Admin command to upload keys
async def upload_keys(update: Update, context) -> None:
    # Only the admin can upload keys
    if update.message.chat_id != ADMIN_CHAT_ID:
        await update.message.reply_text("You are not authorized to upload keys.")
        return

    # Get the command arguments
    args = context.args
    if len(args) < 2:
        await update.message.reply_text("Usage: /upload_keys <days> <key1> <key2> ... <keyN>")
        return

    try:
        # Extract days and keys from the command
        days = int(args[0])
        if days not in stored_keys:
            await update.message.reply_text("Invalid number of days. Allowed values are 1, 3, and 7.")
            return

        keys = args[1:]
        if len(keys) == 0:
            await update.message.reply_text("Please provide at least one key.")
            return

        # Store the keys
        stored_keys[days].extend(keys)

        await update.message.reply_text(f"Successfully uploaded {len(keys)} keys for {days} days.")
    except ValueError:
        await update.message.reply_text("Invalid input. Please specify the days and keys correctly.")

# Admin approval or rejection
async def admin_commands(update: Update, context) -> None:
    query = update.callback_query
    data = query.data.split(":")
    user_id = int(data[1])

    if data[0] == "approve":
        # Send key from the stored keys
        user_days = user_payment_data.get(user_id, {}).get("days", None)
        if user_days and stored_keys.get(user_days):
            key = stored_keys[user_days].pop(0)  # Get and remove the first key from the list
            telegram_channel_link = TELEGRAM_CHANNEL_LINK
            await context.bot.send_message(
                chat_id=user_id,
                text=(
                    "Your payment has been approved!\n\n"
                    f"Here is your key: {key}\n\n"
                    f"Join our Telegram channel for updates: {telegram_channel_link}"
                )
            )
            await query.edit_message_text(text=f"Approved payment from user {user_id}. Key sent.")
        else:
            await query.edit_message_text(text=f"No keys available for user {user_id}.")
    elif data[0] == "reject":
        await context.bot.send_message(chat_id=user_id, text="Your payment could not be verified. Please try again or contact support.")
        await query.edit_message_text(text=f"Rejected payment from user {user_id}.")

# Main function
def main():
    application = Application.builder().token(BOT_TOKEN).build()

    # Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(handle_reseller_response, pattern="^reseller_"))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_duration_or_quantity))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(CommandHandler("upload_keys", upload_keys))
    application.add_handler(CallbackQueryHandler(admin_commands, pattern="^(approve|reject):"))

    # Run the bot
    application.run_polling()

if __name__ == "__main__":
    main()
