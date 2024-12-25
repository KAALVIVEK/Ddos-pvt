from telethon import TelegramClient, events, Button
import qrcode
import os
import re

# Telegram API credentials
api_id = "27403509"
api_hash = "30515311a8dbe44c670841615688cee4"

# Payment details
UPI_ID = "kaalvivek@fam"

# Price dictionary
PRICES = {
    "magic_server": {"1_day": 150, "7_days": 800, "1_month": 1800},
    "brutal_server": {"1_day": 200},
}

# Key files (Storing keys in bulk with duration included)
KEY_FILES = {
    "magic_server": r"keys/magic_server_keys.txt",
    "brutal_server": r"keys/brutal_server_keys.txt",
}

# Telegram bot session
client = TelegramClient('buy_keys_session', api_id, api_hash)

# Dictionary to store pending payments
pending_payments = {}

# Owner ID (replace with your Telegram ID)
YOUR_OWNER_TELEGRAM_ID = 7083378335  # Replace with your Telegram ID


@client.on(events.NewMessage(pattern=r'/start'))
async def start(event):
    """Handles the /start command."""
    welcome_message = (
        "👋 Welcome to the Key Buying Service Bot!\n\n"
        "Commands:\n"
        "/buy - View available servers and pricing.\n"
        "/select <server> <duration> - Generate a QR code for payment.\n"
        "Example: `/select magic_server 1_day`.\n\n"
        "Have questions? Just ask!"
    )
    await event.reply(welcome_message)


@client.on(events.NewMessage(pattern=r'/buy'))
async def buy(event):
    """Handles the /buy command."""
    message = (
        "Available Keys:\n\n"
        "1️⃣ Magic Server:\n"
        "   1 Day - ₹150\n"
        "   7 Days - ₹800\n"
        "   1 Month - ₹1800\n\n"
        "2️⃣ Brutal Server:\n"
        "   1 Day - ₹200\n\n"
        "Reply with:\n"
        "`/select <server> <duration>`\n"
        "Example: `/select magic_server 1_day`"
    )
    await event.reply(message)


@client.on(events.NewMessage(pattern=r'/select (.+) (.+)'))
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

        # Remove the file after sending
        os.remove(file_path)
    except KeyError:
        await event.reply("Invalid selection. Please use `/buy` to see valid options.")


@client.on(events.NewMessage(pattern=r'/approve'))
async def approve_payment_in_chat(event):
    """Handles the /approve command dynamically by replying to a message."""
    # Restrict this command to the owner
    if event.sender_id != YOUR_OWNER_TELEGRAM_ID:
        await event.reply("Unauthorized access. This command is for the owner only.")
        return

    # Check if the message is a reply
    if not event.is_reply:
        await event.reply("Please reply to the customer's payment confirmation message to approve.")
        return

    try:
        # Fetch the replied message and extract the user ID
        replied_message = await event.get_reply_message()
        user_id = replied_message.sender_id

        # Check if the user has a pending payment
        if user_id in pending_payments:
            server, duration, _ = pending_payments.pop(user_id)
            key_file = KEY_FILES[server]

            # Read keys from the file
            with open(key_file, 'r') as f:
                keys = f.readlines()

            # Find the first matching key for the duration
            key = None
            remaining_keys = []
            for line in keys:
                key_data = line.strip().split(" ", 1)  # Split key and duration
                if len(key_data) == 2 and key_data[1] == duration:
                    key = key_data[0]  # Use this key
                    continue
                remaining_keys.append(line)  # Keep unmatched keys

            if key:
                # Save the remaining keys back to the file
                with open(key_file, 'w') as f:
                    f.writelines(remaining_keys)

                # Send the key to the user
                await client.send_message(
                    user_id,
                    f"✅ Payment approved!\nHere is your key for {server.replace('_', ' ').title()} "
                    f"({duration.replace('_', ' ').title()}):\n`{key}`"
                )
                await event.reply(f"✅ Payment approved for user {user_id}. Key sent!")
            else:
                await event.reply("No keys available for the selected server and duration.")
        else:
            await event.reply("No pending payment found for this user ID.")
    except Exception as e:
        await event.reply(f"An error occurred: {str(e)}")


# Start the client
print("Bot is running...")
client.start()
client.run_until_disconnected()
