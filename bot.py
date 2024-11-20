import requests
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Updater, CommandHandler, MessageHandler, filters, CallbackContext, CallbackQueryHandler

# Constants
BOT_TOKEN = "7525850725:AAFj6u8yOSMr5oEYsXueSx9pQGAWoEEy5cc"
ADMIN_CHAT_ID = "7525850725"  # Replace with your admin's Telegram ID
PANEL_LOGIN_URL = "https://noobmodz.online/SONU/login"  # Replace with your panel login URL
PANEL_KEY_GENERATION_URL = "https://noobmodz.online/SONU/keys/generate"  # Replace with your panel's key generation endpoint
PANEL_USERNAME = "VIVEK"  # Replace with your panel's username
PANEL_PASSWORD = "13579780"  # Replace with your panel's password

# Store user payment data temporarily
user_payment_data = {}

# Authenticate with the panel
def authenticate_with_panel():
    response = requests.post(PANEL_LOGIN_URL, json={"username": PANEL_USERNAME, "password": PANEL_PASSWORD})
    if response.status_code == 200 and response.json().get("success"):
        return response.json().get("token")  # Return the session token
    else:
        raise Exception(f"Authentication failed: {response.text}")

# Generate a key from the panel based on the duration
def generate_key(session_token, days):
    headers = {"Authorization": f"Bearer {session_token}"}
    response = requests.post(PANEL_KEY_GENERATION_URL, headers=headers, json={"days": days})
    if response.status_code == 200 and response.json().get("success"):
        return response.json()  # Expected: {"success": true, "key": "...", "username": "...", "password": "..."}
    else:
        return {"success": False, "error": response.text}

# Start command
def start(update: Update, context: CallbackContext):
    update.message.reply_text("Welcome! How many days are you paying for? (1, 3, or 7 days)")
    user_payment_data[update.message.chat_id] = {}

# Handle payment duration
def handle_duration(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    try:
        days = int(update.message.text)
        if days in [1, 3, 7]:
            user_payment_data[chat_id]['days'] = days
            update.message.reply_text("Please send your payment screenshot for verification.")
        else:
            update.message.reply_text("Invalid choice. Please select 1, 3, or 7 days.")
    except ValueError:
        update.message.reply_text("Please enter a valid number (1, 3, or 7).")

# Handle payment screenshot
def handle_photo(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    if 'days' not in user_payment_data.get(chat_id, {}):
        update.message.reply_text("Please specify the number of days first.")
        return

    days = user_payment_data[chat_id]['days']
    user = update.message.from_user

    # Store the screenshot info
    user_payment_data[chat_id]['photo'] = update.message.photo[-1].file_id

    # Notify the admin
    caption = (f"Payment screenshot received from {user.first_name} (@{user.username}).\n"
               f"User ID: {user.id}\nDuration: {days} days.")
    context.bot.forward_message(chat_id=ADMIN_CHAT_ID, from_chat_id=chat_id, message_id=update.message.message_id)
    context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=caption)
    update.message.reply_text("Thank you! Your payment is being verified by the admin.")

# Admin approval or rejection
def admin_commands(update: Update, context: CallbackContext):
    query = update.callback_query
    data = query.data.split(":")
    user_id = int(data[1])

    if data[0] == "approve":
        days = int(data[2])
        try:
            session_token = authenticate_with_panel()  # Authenticate with the panel
            key_data = generate_key(session_token, days)  # Generate key from the panel

            if key_data.get("success"):
                key = key_data["key"]
                username = key_data["username"]
                password = key_data["password"]
                context.bot.send_message(chat_id=user_id, text=f"Your payment has been verified. Here are your details:\n\n"
                                                               f"**Key:** `{key}`\n"
                                                               f"**Username:** `{username}`\n"
                                                               f"**Password:** `{password}`\n\n"
                                                               f"Valid for {days} day(s).", parse_mode="Markdown")
                query.edit_message_text(text=f"Approved user {user_id} for {days} days and sent the key.")
            else:
                context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=f"Failed to generate key for user {user_id}.\nError: {key_data.get('error')}")
                query.edit_message_text(text="Key generation failed.")
        except Exception as e:
            context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=f"Error: {e}")
            query.edit_message_text(text="Authentication or key generation failed.")
    elif data[0] == "reject":
        context.bot.send_message(chat_id=user_id, text="Your payment could not be verified. Please contact support.")
        query.edit_message_text(text=f"Rejected payment for user {user_id}.")

# Verification handler
def verify_payment(update: Update, context: CallbackContext):
    if str(update.message.chat_id) != ADMIN_CHAT_ID:
        return
    try:
        user_id = int(update.message.reply_to_message.caption.split("User ID: ")[1].split("\n")[0])
        days = int(update.message.reply_to_message.caption.split("Duration: ")[1].split(" days")[0])

        keyboard = [
            [
                InlineKeyboardButton("Approve", callback_data=f"approve:{user_id}:{days}"),
                InlineKeyboardButton("Reject", callback_data=f"reject:{user_id}"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text("Approve or reject payment?", reply_markup=reply_markup)
    except Exception as e:
        update.message.reply_text(f"Error: {e}")

# Main function
def main():
    updater = Updater(BOT_TOKEN)
    dp = updater.dispatcher

    # Handlers
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_duration))
    dp.add_handler(MessageHandler(Filters.photo, handle_photo))
    dp.add_handler(MessageHandler(Filters.reply & Filters.text, verify_payment))
    dp.add_handler(CallbackQueryHandler(admin_commands))

    # Start polling
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
