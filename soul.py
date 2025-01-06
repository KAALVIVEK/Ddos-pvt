import os
import telebot
import json
import logging
import time
from pymongo import MongoClient
from datetime import datetime, timedelta
import certifi
import asyncio
import random
from threading import Thread
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from apscheduler.schedulers.background import BackgroundScheduler

# ** Configuration ** #
TOKEN = '7942937704:AAFM6qI8dd74bEuSu-E0UUqN0N9FioD4qa8'
ADMIN_USER_ID = 7083378335  # Replace with your user ID
MONGO_URI = 'mongodb+srv://sharp:sharp@sharpx.x82gx.mongodb.net/?retryWrites=true&w=majority&appName=SharpX'
USERNAME = "@TREXVIVEK"

# Initialize MongoDB Client
client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
db = client['bot_database']
users_collection = db.users
logs_collection = db.logs

# Initialize Bot and Logging
bot = telebot.TeleBot(TOKEN)
logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)

# Global Variables
attack_in_progress = False
languages = {
    "en": {"welcome": "Welcome, Agent!", "status": "Viewing status..."},
    "es": {"welcome": "¡Bienvenido, Agente!", "status": "Viendo el estado..."}
}
user_cooldowns = {}
blocked_ports = [8700, 20000, 443, 17500, 9031, 20002, 20001]
scheduler = BackgroundScheduler()

# ** Helper Functions ** #
def is_rate_limited(user_id):
    now = time.time()
    if user_id in user_cooldowns and now - user_cooldowns[user_id] < 5:
        return True
    user_cooldowns[user_id] = now
    return False

def validate_ip(ip):
    import re
    return re.match(r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$", ip) is not None

def notify_expiring_users():
    today = datetime.now().date()
    expiring_users = users_collection.find({"valid_until": {"$lte": (today + timedelta(days=2)).isoformat()}})
    for user in expiring_users:
        bot.send_message(user["user_id"], f"⚠️ Your plan expires on {user['valid_until']}. Renew soon!")

scheduler.add_job(notify_expiring_users, 'interval', hours=24)
scheduler.start()

# ** Command Handlers ** #
@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    options = [
        "💀 Initiate Attack 🔥", 
        "🔍 View Status", 
        "📜 Read Guidelines", 
        "📞 Contact Support", 
        "⚙️ Settings"
    ]
    buttons = [KeyboardButton(option) for option in options]
    markup.add(*buttons)
    bot.send_message(
        message.chat.id,
        f"👊 *Welcome to Command, Agent. Choose your directive.* Managed by {USERNAME}",
        reply_markup=markup,
        parse_mode='Markdown'
    )

@bot.message_handler(commands=['stats'])
def view_stats(message):
    stats = {
        "Active Users": users_collection.count_documents({"plan": {"$gt": 0}}),
        "Proxy Status": "Operational",
        "Active Attacks": "0 (Sample Data)"
    }
    report = "\n".join([f"{key}: {value}" for key, value in stats.items()])
    bot.reply_to(message, f"📊 Current Stats:\n{report}")

@bot.message_handler(commands=['language'])
def set_language(message):
    markup = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    lang_options = [KeyboardButton(lang) for lang in languages.keys()]
    markup.add(*lang_options)
    bot.send_message(message.chat.id, "🌐 Select your language:", reply_markup=markup)

@bot.message_handler(func=lambda msg: msg.text in languages.keys())
def apply_language(message):
    user_lang = message.text
    bot.send_message(message.chat.id, languages[user_lang]["welcome"])

@bot.message_handler(commands=['logs'])
def view_logs(message):
    user_logs = logs_collection.find({"user_id": message.from_user.id})
    if not user_logs:
        bot.reply_to(message, "📜 No logs found.")
    else:
        logs_text = "\n".join([f"{log['timestamp']} - Target: {log['target_ip']} Port: {log['port']}" for log in user_logs])
        bot.reply_to(message, f"📜 Your Logs:\n{logs_text}")

@bot.message_handler(commands=['Attack'])
def attack_command(message):
    global attack_in_progress
    if attack_in_progress:
        bot.send_message(message.chat.id, f"⚠️ *Attack already in progress. Wait for completion.*")
        return

    bot.send_message(message.chat.id, "📝 Provide target details: IP, Port, Duration (seconds).")
    bot.register_next_step_handler(message, process_attack_command)

def process_attack_command(message):
    global attack_in_progress
    args = message.text.split()
    if len(args) != 3:
        bot.send_message(message.chat.id, "⚠️ Format: /Attack <IP> <Port> <Duration>")
        return

    target_ip, target_port, duration = args[0], int(args[1]), int(args[2])

    if not validate_ip(target_ip):
        bot.send_message(message.chat.id, "⚠️ Invalid IP address. Try again.")
        return

    if target_port in blocked_ports:
        bot.send_message(message.chat.id, f"🚫 Port {target_port} restricted.")
        return

    # Simulated attack (replace with real implementation)
    attack_in_progress = True
    bot.send_message(
        message.chat.id,
        f"💀 *Attack initiated on {target_ip}:{target_port} for {duration} seconds.*"
    )
    time.sleep(duration)
    attack_in_progress = False
    logs_collection.insert_one({
        "user_id": message.from_user.id,
        "target_ip": target_ip,
        "port": target_port,
        "timestamp": datetime.now().isoformat()
    })
    bot.send_message(message.chat.id, "✅ Attack complete.")

# ** Start Bot ** #
if __name__ == "__main__":
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            logging.error(f"Polling error: {e}")
            
