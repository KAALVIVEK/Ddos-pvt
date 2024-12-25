from telethon import TelegramClient, events, Button
import qrcode
import os
import random
import re

# Telegram API credentials
api_id = "27403509"
api_hash = "30515311a8dbe44c670841615688cee4"

# Payment details
UPI_ID = "kaalvivek@fam"

# Price dictionary
PRICES = {
    "safe_server": {"1_day": 100, "3_days": 250, "1_week": 450},
    "brutal_server": {"1_day": 200, "3_days": 300, "1_week": 700},
}

# Key files (Storing keys in bulk as a single file per server)
KEY_FILES = {
    "safe_server": "keys/safe_server_keys.txt",  # A file containing keys for all durations
    "brutal_server": "keys/brutal_server_keys.txt",  # A file containing keys for all durations
}

# Initialize Telegram client
client = TelegramClient('buy_keys_session', api_id, api_hash)

# Dictionary to store pending payments
pending_payments = {}

@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    """Handles the /start command."""
    welcome_message = (
        "👋 Welcome to the Key Buying Service Bot!\n\n"
        "Commands:\n"
        "/buy - View available servers and pricing.\n"
        "/select <server> <duration> - Generate a QR code for payment.\n"
        "Example: `/select safe_server 1_day`.\n\n"
        "Have questions? Just ask!"
    )
    await event.reply(welcome_message)

@client.on(events.NewMessage(pattern='/buy'))
async def buy(event):
    """Handles the /buy command."""
    message = (
        "Available Keys:\n\n"
        "1️⃣ Safe Server:\n"
        "   1 Day - ₹100\n"
        "   3 Days - ₹250\n"
        "   1 Week - ₹450\n\n"
        "2️⃣ Brutal Server:\n"
        "   1 Day - ₹200\n"
        "   3 Days - ₹300\n"
        "   1 Week - ₹700\n\n"
        "Reply with:\n"
        "`/select <server> <duration>`\n"
        "Example: `/select safe_server 1_day`"
    )
    await event.reply(message)

@client.on(events.NewMessage(pattern='/select (.+) (.+)'))
async def select(event):
    """Handles the /select command."""
    try:
        # Parse user input
        server, duration = event.pattern_match.groups()
        price = PRICES[server][duration]
        
        # Generate UPI QR code
        upi_string = f"upi://pay?pa={UPI_ID}&pn=YourName&am={price}&cu=INR"
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(upi_string)
        qr.make(fit=True)
        img = qr.make_image(fill="black", back_color="white")

        # Save QR code to a file
        file_path = f"{server}_{duration}.png"
        img.save(file_path)

        # Store the pending payment
        pending_payments[event.chat_id] = (server, duration, file_path)

        # Send the QR code to the user
        await event.reply(
            f"Selected: {server.replace('_', ' ').title()}, {duration.replace('_', ' ').title()}\n"
            f"Price: ₹{price}\n"
            f"Scan the QR code below to complete the payment or use this UPI ID: `{UPI_ID}`\n"
            f"Payment will be approved by the ID owner."
        )
        await client.send_file(event.chat_id, file_path, caption="Scan to Pay")

        # Notify the owner with an inline button for approval
        await client.send_message(
            event.chat_id,  # Sending the message to the same chat where the bot is running
            f"Payment pending approval:\nUser: {event.chat_id}\nServer: {server}\nDuration: {duration}\nPrice: ₹{price}\nUPI ID: {UPI_ID}",
            buttons=[Button.inline("Approve Payment", data=f"approve_{event.chat_id}")]
        )
        
        # Remove the file after sending
        os.remove(file_path)
    except KeyError:
        await event.reply("Invalid selection. Please use `/buy` to see valid options.")

@client.on(events.CallbackQuery(data=re.compile(b"approve_(\d+)")))
async def approve(event):
    """Handles the approval button click."""
    user_id = int(event.data.decode().split("_")[1])
    if user_id in pending_payments:
        server, duration, _ = pending_payments.pop(user_id)
        key_file = KEY_FILES[server]
        
        # Read the key from the file (Selecting the correct key based on duration)
        with open(key_file, 'r') as f:
            keys = f.readlines()

        # Select the appropriate key based on the duration
        key_index = {
            "1_day": 0,
            "3_days": 1,
            "1_week": 2
        }[duration]

        key = keys[key_index].strip()  # Get the key for the selected duration
        
        # Send the key to the user
        await client.send_message(user_id, f"Your key for {server.replace('_', ' ').title()} ({duration.replace('_', ' ').title()}):\n{key}")
        await event.edit(f"Payment approved and key sent to user {user_id}.")
    else:
        await event.edit("No pending payment found for the specified user ID.")

# Start the client
print("Bot is running...")
client.start()
client.run_until_disconnected()
