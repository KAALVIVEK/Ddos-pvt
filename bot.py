from telethon import TelegramClient, events
import qrcode
from io import BytesIO

# Telegram API credentials
api_id = "27403509"
api_hash = "30515311a8dbe44c670841615688cee4"

# Payment details
UPI_ID = "kaalvivek@fam"

# Price dictionary
PRICES = {
    "safe_server": {"1_day": 50, "3_days": 120, "1_week": 300},
    "brutal_server": {"1_day": 100, "3_days": 250, "1_week": 600},
}

# Initialize Telegram client
client = TelegramClient('buy_keys_session', api_id, api_hash)

@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    await event.reply(
        "Welcome! Use /buy to see available keys and prices.\n"
        "Commands:\n"
        "/buy - View keys and prices"
    )

@client.on(events.NewMessage(pattern='/buy'))
async def buy(event):
    message = (
        "Available Keys:\n\n"
        "1️⃣ Safe Server:\n"
        "   1 Day - ₹50\n"
        "   3 Days - ₹120\n"
        "   1 Week - ₹300\n\n"
        "2️⃣ Brutal Server:\n"
        "   1 Day - ₹100\n"
        "   3 Days - ₹250\n"
        "   1 Week - ₹600\n\n"
        "Reply with:\n"
        "`/select <server> <duration>`\n"
        "Example: `/select safe_server 1_day`"
    )
    await event.reply(message)

@client.on(events.NewMessage(pattern='/select (.+) (.+)'))
async def select(event):
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

        # Save QR code to a buffer
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)

        # Send response with QR code
        await event.reply(
            f"Selected: {server.replace('_', ' ').title()}, {duration.replace('_', ' ').title()}\n"
            f"Price: ₹{price}\n"
            f"Scan the QR code below to complete the payment or use this UPI ID: `{UPI_ID}`"
        )
        await client.send_file(event.chat_id, buffer, caption="UPI QR Code")
    except KeyError:
        await event.reply("Invalid selection. Please use `/buy` to see valid options.")

# Start the client
print("Bot is running...")
client.start()
client.run_until_disconnected()
