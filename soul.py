import os
import telebot
import logging
import asyncio
from pymongo import MongoClient
from datetime import datetime, timedelta
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from threading import Thread
import certifi

# Configuration
TOKEN = '7942937704:AAFM6qI8dd74bEuSu-E0UUqN0N9FioD4qa8'
ADMIN_USER_ID = 7083378335  # Replace with your admin user ID
MONGO_URI = 'mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority'

USERNAME = "@TREXVIVEK"  # Your bot username
COMMAND_LIMIT = 10  # Max commands per user per hour
loop = asyncio.get_event_loop()
logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)

# MongoDB setup
client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
db = client['your_database']
users_collection = db.users

# Initialize bot
bot = telebot.TeleBot(TOKEN)
user_command_counts = {}

# Asyncio loop
async def start_asyncio_loop():
    while True:
        await asyncio.sleep(1)

# Asyncio thread
def start_asyncio_thread():
    asyncio.set_event_loop(loop)
    loop.run_until_complete(start_asyncio_loop())

# --- Utility Functions ---
def is_admin(user_id):
    return user_id == ADMIN_USER_ID

def update_user_access(user_id, plan, days):
    valid_until = (datetime.now() + timedelta(days=days)).isoformat()
    users_collection.update_one(
        {"user_id": user_id},
        {"$set": {"plan": plan, "valid_until": valid_until, "access_count": 0}},
        upsert=True
    )

def check_user_limit(plan):
    plan_limit = {1: 99, 2: 499}  # Example limits for different plans
    return users_collection.count_documents({"plan": plan}) < plan_limit.get(plan, 0)

# --- Commands ---

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("💀 Initiate Attack 🔥", callback_data="initiate_attack"),
        InlineKeyboardButton("🔍 Status Report", callback_data="status_report"),
        InlineKeyboardButton("📜 Mission Brief", callback_data="mission_brief"),
        InlineKeyboardButton("📞 Contact HQ", callback_data="contact_hq")
    )
    bot.send_message(
        message.chat.id,
        f"👋 Welcome, Agent! Choose your directive below. Managed by {USERNAME}",
        reply_markup=markup,
        parse_mode="Markdown"
    )

@bot.message_handler(commands=['approve'])
def approve_user(message):
    if not is_admin(message.from_user.id):
        bot.send_message(message.chat.id, "🚫 You do not have permission to use this command.")
        return

    args = message.text.split()
    if len(args) < 4:
        bot.send_message(
            message.chat.id,
            "📝 Format: /approve <user_id> <plan> <days>\nExample: /approve 123456789 1 30"
        )
        return

    try:
        target_user_id = int(args[1])
        plan = int(args[2])
        days = int(args[3])

        if not check_user_limit(plan):
            bot.send_message(message.chat.id, f"⚠️ Plan {plan} is full. Contact {USERNAME}.")
            return

        update_user_access(target_user_id, plan, days)
        bot.send_message(
            message.chat.id,
            f"✅ User {target_user_id} approved for Plan {plan} for {days} days."
        )
    except Exception as e:
        bot.send_message(message.chat.id, f"⚠️ Error: {e}")

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    if call.data == "initiate_attack":
        bot.send_message(call.message.chat.id, "⚡ Preparing to initiate an attack. Provide details.")
    elif call.data == "status_report":
        user_data = users_collection.find_one({"user_id": call.message.chat.id})
        if user_data:
            response = (f"📊 *Status Report*\n"
                        f"👤 User ID: `{call.message.chat.id}`\n"
                        f"💳 Plan: `{user_data['plan']}`\n"
                        f"📅 Valid Until: `{user_data['valid_until']}`\n")
        else:
            response = "🚫 No status found. Contact HQ for assistance."
        bot.send_message(call.message.chat.id, response, parse_mode="Markdown")
    elif call.data == "mission_brief":
        bot.send_message(call.message.chat.id, "📜 Your mission briefing: Stay vigilant.")
    elif call.data == "contact_hq":
        bot.send_message(call.message.chat.id, f"📞 Contact HQ: {USERNAME}")

@bot.message_handler(commands=['stats'])
def user_stats(message):
    user_id = message.from_user.id
    user_data = users_collection.find_one({"user_id": user_id})
    if user_data:
        response = (f"📊 *User Statistics*\n"
                    f"👤 User ID: `{user_id}`\n"
                    f"💳 Plan: `{user_data['plan']}`\n"
                    f"🔢 Commands Used: `{user_data.get('access_count', 0)}`\n"
                    f"📅 Valid Until: `{user_data['valid_until']}`")
    else:
        response = "🚫 No statistics available for your account."
    bot.send_message(message.chat.id, response, parse_mode="Markdown")

# --- Main ---

if __name__ == "__main__":
    thread = Thread(target=start_asyncio_thread, daemon=True)
    thread.start()
    logging.info("🚀 Bot is operational.")

    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            logging.error(f"Polling error: {e}")
