import uuid
import qrcode
import sqlite3
from telethon import TelegramClient, events
from telethon.errors import SessionPasswordNeededError

# Your Telegram API configuration
api_id = '27403509'  # Replace with your Telegram API ID
api_hash = '30515311a8dbe44c670841615688cee4'  # Replace with your Telegram API Hash
phone_number = '+917814581929'  # Your phone number associated with the account

client = TelegramClient('session_name', api_id, api_hash)

# Database setup (SQLite)
conn = sqlite3.connect('transactions.db', check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS transactions (
    transaction_id TEXT PRIMARY KEY,
    user_id TEXT,
    server TEXT,
    duration TEXT,
    amount REAL,
    verified INTEGER DEFAULT 0
)
""")
conn.commit()

# File to store server keys
key_file = 'keys.txt'

# Key prices (server and duration mapping to price)
key_prices = {
    "magic_server": {
        "1_Day": 150,
        "7_Days": 450,
        "1_Month": 1000
    },
    "not_available_server": {
        "1_month": 150,
        "3_months": 350,
        "6_months": 600
    }
}

# Helper functions
def generate_transaction_id():
    return str(uuid.uuid4())

def generate_upi_qr(upi_id, amount, transaction_id):
    upi_data = f"upi://pay?pa={upi_id}&pn=ServerPayment&am={amount}&cu=INR&tid={transaction_id}"
    qr = qrcode.make(upi_data)
    qr_path = f"qr_{transaction_id}.png"
    qr.save(qr_path)
    return qr_path

def assign_server_key(server, duration):
    with open(key_file, 'r') as f:
        keys = f.readlines()
    
    for line in keys:
        key_data = line.strip().split(" ", 1)
        if len(key_data) == 2 and key_data[1] == duration:
            key = key_data[0]
            keys.remove(line)
            
            # Save updated keys back
            with open(key_file, 'w') as f:
                f.writelines(keys)
            return key
    
    return None  # No keys available

# Event handlers
@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    await event.reply(
        f"Hello, {event.sender.first_name}!\n\nWelcome to the Server Key Payment Bot!\n"
        "Use the following commands to interact:\n\n"
        "/buy - To view available servers and their prices.\n"
        "Once you choose a server and duration, you'll receive a payment QR code."
    )

@client.on(events.NewMessage(pattern=r'/buy$'))
async def show_servers(event):
    # Show available servers and prices
    available_servers = "Here are the available servers and their prices:\n\n"
    for server, durations in key_prices.items():
        available_servers += f"**{server.replace('_', ' ').title()}**:\n"
        for duration, price in durations.items():
            available_servers += f"  - {duration.replace('_', ' ').title()}: ₹{price}\n"
    
    available_servers += "\nTo purchase a server, use the command `/buy <server> <duration>`, for example:\n"
    available_servers += "`/buy magic_server 1_Day` or `/buy not_available_server 3_months`."
    
    await event.reply(available_servers)

@client.on(events.NewMessage(pattern=r'/buy (\w+) (\w+)'))
async def process_buy(event):
    user_id = event.sender_id
    message = event.message.message.split()

    if len(message) != 3:
        await event.reply("Usage: /buy <server> <duration>")
        return
    
    server = message[1]
    duration = message[2]

    if server not in key_prices or duration not in key_prices[server]:
        await event.reply("Invalid server or duration. Please check and try again.")
        return

    amount = key_prices[server][duration]
    upi_id = "kaalvivek@fam"  # Replace with your UPI ID
    transaction_id = generate_transaction_id()
    qr_path = generate_upi_qr(upi_id, amount, transaction_id)
    
    # Send QR code to user and then save the transaction to database
    try:
        await client.send_file(user_id, qr_path, caption=(
            f"🔑 **Server Selection**: {server.replace('_', ' ').title()}\n"
            f"📅 **Duration**: {duration.replace('_', ' ').title()}\n"
            f"💵 **Amount**: ₹{amount}\n"
            f"📤 **Transaction ID**: {transaction_id}\n\n"
            f"📌 Scan this QR code to complete your payment via UPI."
        ))
        
        # Save transaction to database after sending QR code
        cursor.execute("INSERT INTO transactions (transaction_id, user_id, server, duration, amount, verified) VALUES (?, ?, ?, ?, ?, 0)", 
                       (transaction_id, user_id, server, duration, amount))
        conn.commit()
    except Exception as e:
        await event.reply(f"Error occurred: {str(e)}")

@client.on(events.NewMessage(pattern='/verify (.+)'))
async def verify(event):
    otr_number = event.pattern_match.group(1)
    cursor.execute("SELECT * FROM transactions WHERE transaction_id = ? AND verified = 0", (otr_number,))
    transaction = cursor.fetchone()

    if transaction:
        user_id, server, duration, amount = transaction[1], transaction[2], transaction[3], transaction[4]
        key = assign_server_key(server, duration)
        
        if key:
            cursor.execute("UPDATE transactions SET verified = 1 WHERE transaction_id = ?", (otr_number,))
            conn.commit()
            await client.send_message(
                user_id,
                f"✅ Payment verified!\nHere is your server key:\n\n**{key}**"
            )
            await event.reply(f"✅ Payment verified for user {user_id}. Key sent!")
        else:
            await event.reply("❌ No keys available for the selected server and duration.")
    else:
        await event.reply("❌ Invalid OTR or payment already verified.")

# Start the client
async def main():
    try:
        await client.start(phone=phone_number)
        print("Bot is running...")
        await client.run_until_disconnected()
    except SessionPasswordNeededError:
        await client.sign_in(password='YOUR_PASSWORD')  # Replace 'YOUR_PASSWORD' with your Telegram password
        await main()

# Run the client
import asyncio
asyncio.run(main())
