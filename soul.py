import os
import telebot
import asyncio
import logging
from pymongo import MongoClient
from datetime import datetime, timedelta
import certifi
import random
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from threading import Thread

# Configuration
TOKEN = '7942937704:AAFM6qI8dd74bEuSu-E0UUqN0N9FioD4qa8'
ADMIN_USER_ID = 7083378335
MONGO_URI = 'mongodb+srv://sharp:sharp@sharpx.x82gx.mongodb.net/?retryWrites=true&w=majority&appName=SharpX'
USERNAME = "@TREXVIVEK"

# Attack Status
attack_in_progress = False

# Logging Setup
logging.basicConfig(format='%(asctime)s - ⚔️ %(message)s', level=logging.INFO)

# MongoDB Connection
client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
db = client['sharp']
users_collection = db.users

# Bot Initialization
bot = telebot.TeleBot(TOKEN)
loop = asyncio.get_event_loop()

# Blocked Ports
blocked_ports = [8700, 20000, 443, 17500, 9031, 20002, 20001]

# Function to Simulate Attack
def simulate_attack(target_ip, target_port, duration):
    global attack_in_progress
    logging.info(f"Attack initiated on {target_ip}:{target_port} for {duration} seconds.")
    # Simulated delay to represent attack execution
    time.sleep(duration)
    attack_in_progress = False
    notify_attack_finished(target_ip, target_port, duration)

# Notify on Attack Completion
def notify_attack_finished(target_ip, target_port, duration):
    bot.send_message(
        ADMIN_USER_ID,
        f"""
🔥 *MISSION ACCOMPLISHED!* 🔥
━━━━━━━━━━━━━━━━━━━━━━━
🎯 *Target Neutralized:* `{target_ip}`
💣 *Port Breached:* `{target_port}`
⏳ *Duration:* `{duration} seconds`

🔒 *Mission Complete. No Evidence Left Behind.*
        """,
        parse_mode='Markdown'
    )

# Process Attack Command
def process_attack_command(message):
    global attack_in_progress
    try:
        args = message.text.split()
        if len(args) != 3:
            bot.send_message(
                message.chat.id,
                "⚠️ *Invalid format.*\nUse: `<IP> <Port> <Duration>`\n\nExample: `192.168.1.1 8080 60`",
                parse_mode='Markdown'
            )
            return

        target_ip, target_port, duration = args[0], int(args[1]), int(args[2])
        user_id = message.from_user.id
        username = message.from_user.username or "Unknown Agent"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Check for blocked ports
        if target_port in blocked_ports:
            bot.send_message(
                message.chat.id,
                f"🚫 *Port {target_port} is restricted.*\nPlease select a different target.",
                parse_mode='Markdown'
            )
            return

        attack_in_progress = True

        # Start attack simulation
        loop.run_in_executor(None, simulate_attack, target_ip, target_port, duration)

        bot.send_message(
            message.chat.id,
            f"""
🚀 *⚠️ OPERATION INITIATED!* 🚀
━━━━━━━━━━━━━━━━━━━━━━━
🎯 *Target IP:* `{target_ip}`
🔒 *Port Accessed:* `{target_port}`
⏳ *Duration:* `{duration} seconds`

🕵️‍♂️ *Agent ID:* `{username}`
📌 *User ID:* `{user_id}`
📅 *Timestamp:* `{timestamp}`

🔥 *MISSION STATUS:* UNLEASHED
━━━━━━━━━━━━━━━━━━━━━━━
⚡ *"Operation Thunderstorm is LIVE. Let the storm begin!"*
            """,
            parse_mode='Markdown'
        )

    except Exception as e:
        bot.send_message(message.chat.id, f"❌ *Error:* {e}", parse_mode='Markdown')
        logging.error(e)

# Command Handlers
@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=True)
    options = [
        "💀 Initiate Attack 🔥", 
        "🔍 Status Report", 
        "📜 Mission Brief", 
        "📞 Contact HQ"
    ]
    buttons = [KeyboardButton(option) for option in options]
    markup.add(*buttons)

    bot.send_message(
        message.chat.id,
        f"👊 *Welcome to Command, Agent. Choose your directive.* Managed by {USERNAME}",
        reply_markup=markup,
        parse_mode='Markdown'
    )

@bot.message_handler(commands=['Attack'])
def attack_command(message):
    global attack_in_progress
    chat_id = message.chat.id

    if attack_in_progress:
        bot.send_message(
            chat_id,
            f"⚠️ *An attack is already in progress. Please wait until it completes, {USERNAME}.*",
            parse_mode='Markdown'
        )
        return

    user_id = message.from_user.id
    user_data = users_collection.find_one({"user_id": user_id})

    if not user_data or user_data.get('plan') == 0:
        bot.send_message(chat_id, f"🚫 Unauthorized. Access limited to {USERNAME}.")
        return

    bot.send_message(
        chat_id,
        f"📝 Provide target details – IP, Port, Duration (seconds). Controlled by {USERNAME}",
        parse_mode='Markdown'
    )
    bot.register_next_step_handler(message, process_attack_command)

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    if message.text == "💀 Initiate Attack 🔥":
        bot.reply_to(message, f"*Command received. Preparing deployment. Stand by, {USERNAME}*", parse_mode='Markdown')
        attack_command(message)
    elif message.text == "🔍 Status Report":
        user_id = message.from_user.id
        user_data = users_collection.find_one({"user_id": user_id})
        if user_data:
            username = message.from_user.username
            plan, valid_until = user_data.get('plan', 'N/A'), user_data.get('valid_until', 'N/A')
            response = (f"*Agent ID: {username}\n"
                        f"Plan Level: {plan}\n"
                        f"Authorized Until: {valid_until}\n"
                        f"Timestamp: {datetime.now().isoformat()}.*")
        else:
            response = f"*Profile unknown. Contact {USERNAME} for authorization.*"
        bot.reply_to(message, response, parse_mode='Markdown')
    elif message.text == "📜 Mission Brief":
        bot.reply_to(message, f"*For support, type /help or contact {USERNAME} at HQ.*", parse_mode='Markdown')
    elif message.text == "📞 Contact HQ":
        bot.reply_to(message, f"*Direct Line to HQ: {USERNAME}*", parse_mode='Markdown')
    else:
        bot.reply_to(message, f"❗*Unknown command. Focus, Agent. Managed by {USERNAME}*", parse_mode='Markdown')

# Asyncio Loop Thread
def start_asyncio_thread():
    asyncio.set_event_loop(loop)
    loop.run_forever()

if __name__ == "__main__":
    asyncio_thread = Thread(target=start_asyncio_thread, daemon=True)
    asyncio_thread.start()
    logging.info("🚀 Bot is operational and mission-ready.")

    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            logging.error(f"Polling error: {e}")
