import time
import qrcode
import os
from telethon import TelegramClient, events
import re

# UPI ID and Telegram API credentials
UPI_ID = "kaalvivek@fam"
api_id = "27403509"
api_hash = "30515311a8dbe44c670841615688cee4"

# Price dictionary
PRICES = {
    "magic_server": {"1_day": 150, "7_days": 800, "1_month": 1800},
    "brutal_server": {"1_day": 200},
}

# Initialize the Telegram Client
client = TelegramClient('buy_keys_session', api_id, api_hash)

# Dictionary to store pending payments (chat_id -> transaction_id, amount)
pending_payments = {}

# Function to generate a unique UPI QR code
def generate_upi_qr(amount, transaction_id):
    upi_string = f"upi://pay?pa={UPI_ID}&pn=YourName&am={amount}&cu=INR&tn=TransactionID_{transaction_id}"
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(upi_string)
    qr.make(fit=True)
    img = qr.make_image(fill="black", back_color="white")

    # Save the QR code to a file
    file_path = f"qr_{transaction_id}.png"
    img.save(file_path)
    return file_path, upi_string

# Command to handle server selection and payment generation
@client.on(events.NewMessage(pattern=r'/select (.+) (.+)'))
async def select(event):
    try:
        # Parse user input
        server, duration = event.pattern_match.groups()
        
        # Check if the server and duration exist in the price dictionary
        if server not in PRICES or duration not in PRICES[server]:
            await event.reply("❌ Invalid selection. Use `/buy` to see valid options.")
            return
        
        # Get price for the selected server and duration
        price = PRICES[server][duration]
        transaction_id = int(time.time())  # Generate a unique transaction ID
        
        # Generate the UPI QR code
        qr_path, upi_link = generate_upi_qr(price, transaction_id)

        # Store the pending payment
        pending_payments[event.chat_id] = {
            "transaction_id": transaction_id, 
            "amount": price, 
            "server": server,
            "duration": duration,
            "qr_path": qr_path
        }

        # Send the QR code to the user
        await event.reply(f"Please scan the QR code to pay ₹{price} for {server.replace('_', ' ').title()} ({duration.replace('_', ' ').title()}). After payment, reply with your OTR number to verify.")
        await client.send_file(event.chat_id, qr_path, caption=f"Pay ₹{price} for {server.replace('_', ' ').title()} - {duration.replace('_', ' ').title()}")

        # Clean up by deleting the QR code image after sending it
        os.remove(qr_path)

    except KeyError:
        await event.reply("❌ Invalid selection. Please use `/buy` to see valid options.")

# Command to verify the payment
@client.on(events.NewMessage(pattern=r'/verify (.+)'))
async def verify_payment(event):
    otr_number = event.pattern_match.group(1)

    # Check if the user has any pending payments
    if event.chat_id not in pending_payments:
        await event.reply("❌ No pending payments found. Please use `/select <server> <duration>` to make a payment first.")
        return

    # Retrieve the pending payment details
    payment_details = pending_payments[event.chat_id]
    transaction_id = payment_details["transaction_id"]
    amount = payment_details["amount"]
    server = payment_details["server"]
    duration = payment_details["duration"]

    # Simulate verifying the OTR (this part can be automated using SMS scraping, email parsing, etc.)
    if verify_transaction(otr_number, amount):
        # Payment verified successfully
        await event.reply(f"✅ Payment of ₹{amount} with OTR {otr_number} verified successfully! You have selected {server.replace('_', ' ').title()} for {duration.replace('_', ' ').title()}.")
        await send_key(event.chat_id, server, duration)
        del pending_payments[event.chat_id]  # Remove the pending payment
    else:
        await event.reply("❌ Payment verification failed. Please check the OTR and try again.")

# Simulated payment verification (this would be more complex in a real system)
def verify_transaction(otr_number, amount):
    # Simulated check: In real scenarios, this could involve matching the OTR and amount with data from your payment provider.
    # For now, we assume the OTR matches the expected format, and the amount is correct.
    expected_otr = f"TransactionID_{int(time.time()) - 1}"  # Simulated expected OTR based on a previous transaction ID
    if otr_number == expected_otr and amount == 150:
        return True
    return False

# Function to simulate sending a key after payment verification
async def send_key(chat_id, server, duration):
    # Simulate sending a key for the server
    key = f"YourServerKey123456 for {server.replace('_', ' ').title()} ({duration.replace('_', ' ').title()})"
    await client.send_message(chat_id, f"Here is your server key: {key}")

# Start the Telegram client
client.start()
client.run_until_disconnected()
