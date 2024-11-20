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
BOT_TOKEN = "YOUR_BOT_TOKEN"  # Replace with your bot token
ADMIN_CHAT_ID = 123456789  # Replace with the admin's Telegram user ID
PANEL_LOGIN_URL = "https://noobmodz.online/SONU/login"
PANEL_KEY_GENERATION_URL = "https://noobmodz.online/SONU/keys/generate"
PANEL_USERNAME = "VIVEK"
PANEL_PASSWORD = "13579780"

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
        try:
            session_token = authenticate_with_panel()  # Authenticate with the panel
            key_data = generate_key(session_token, days)  # Generate key from the panel

            if key_data.get("success"):
                key = key_data["key"]
                username = key_data["username"]
                password = key_data["password"]
                
                # Prepare the message with key information
                success_message = (
                    f"Your payment has been verified. Here are your details:\n\n"
                    f"**Key:** `{key}`\n"
                    f"**Username:** `{username}`\n"
                    f"**Password:** `{password}`\n\n"
                    f"Valid for {days} day(s)."
                )
                
                # Send the key information in multiple chunks if it's too long
                success_messages = split_message(success_message)
                for msg in success_messages:
                    await context.bot.send_message(chat_id=user_id, text=msg, parse_mode="Markdown")
                
                await query.edit_message_text(text=f"Approved user {user_id} for {days} days and sent the key.")
            else:
                await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=f"Failed to generate key for user {user_id}.\nError: {key_data.get('error')}")
                await query.edit_message_text(text="Key generation failed.")
        except Exception as e:
            await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=f"Error: {e}")
            await query.edit_message_text(text="Authentication or key generation failed.")
    elif data[0] == "reject":
        await context.bot.send_message(chat_id=user_id, text="Your payment could not be verified. Please contact support.")
        await query.edit_message_text(text=f"Rejected payment for user {user_id}.")

# Function to split long messages into chunks
def split_message(text, max_length=4096):
    return [text[i:i+max_length] for i in range(0, len(text), max_length)]

# Main function
def main():
    application = Application.builder().token(BOT_TOKEN).build()

    # Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_duration))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(CallbackQueryHandler(admin_commands))

    # Start polling
    application.run_polling()

if __name__ == "__main__":
    main()
