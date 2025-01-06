import logging
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import Command, Text
from pymongo import MongoClient
import certifi
import asyncio

# Bot Configurations
BOT_TOKEN = "7942937704:AAFM6qI8dd74bEuSu-E0UUqN0N9FioD4qa8"  # Replace with your bot token
ADMIN_USER_ID = 7083378335  # Replace with your Telegram user ID
LOG_CHANNEL_LINK = "https://t.me/vivekpvtddos01"  # Replace with your log channel link
MONGO_URI = "mongodb+srv://sharp:sharp@sharpx.x82gx.mongodb.net/?retryWrites=true&w=majority&appName=SharpX"  # Replace with your MongoDB connection URI

# Initialize Bot and Dispatcher
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Logging setup
logging.basicConfig(format="%(asctime)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# MongoDB Connection
client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
db = client["sharp"]
users_collection = db.users

# Constants
USERNAME = "@TREXVIVEK"  # Replace with your bot username


# Helper Functions
def get_user_info(user_id):
    """Fetch user information from the database."""
    return users_collection.find_one({"user_id": user_id})


def update_user_access(user_id, plan, days):
    """Update user plan and validity."""
    valid_until = (datetime.now() + timedelta(days=days)).date().isoformat()
    users_collection.update_one(
        {"user_id": user_id},
        {"$set": {"plan": plan, "valid_until": valid_until, "access_count": 0}},
        upsert=True
    )


async def log_to_channel(log_message):
    """Send logs to the specified Telegram channel."""
    await bot.send_message(chat_id=LOG_CHANNEL_LINK, text=log_message, parse_mode="Markdown")


# Commands and Callbacks
@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    """Handle the /start command."""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💀 Initiate Attack 🔥", callback_data="initiate_attack"),
            InlineKeyboardButton(text="🔍 Status Report", callback_data="status_report")
        ],
        [
            InlineKeyboardButton(text="📜 Mission Brief", callback_data="mission_brief"),
            InlineKeyboardButton(text="📞 Contact HQ", url=f"https://t.me/{USERNAME}")
        ]
    ])

    response = (
        f"👋 *Welcome, Agent {message.from_user.first_name}!*\n\n"
        f"🎯 *You are now connected to the Tactical Operations Center.*\n"
        f"💼 *Here, you can initiate operations, check your mission status, and receive directives.*\n\n"
        f"📌 *Your next move?* Select an option below to proceed."
    )

    logger.info(f"User {message.from_user.id} started the bot.")
    await log_to_channel(f"👤 User `{message.from_user.id}` started the bot.")
    await message.answer(response, reply_markup=keyboard, parse_mode="Markdown")


@dp.callback_query(Text("status_report"))
async def status_report(callback_query: types.CallbackQuery):
    """Provide the user's status report."""
    user_id = callback_query.from_user.id
    user_data = get_user_info(user_id)

    if user_data:
        plan = user_data.get("plan", "N/A")
        valid_until = user_data.get("valid_until", "N/A")
        response = (
            f"📊 *Mission Status Report*\n\n"
            f"👤 *Agent ID:* `{user_id}`\n"
            f"💼 *Current Plan:* `{plan}`\n"
            f"⏳ *Access Valid Until:* `{valid_until}`\n\n"
            f"🔎 *Keep your credentials safe, Agent. HQ monitors all activity.*\n"
            f"📅 *Checked At:* `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`"
        )
    else:
        response = (
            f"⚠️ *Unauthorized Access Detected*\n\n"
            f"🔒 *Agent, it appears you do not have the required clearance.*\n"
            f"📞 *Contact HQ at* {USERNAME} *to request access.*"
        )

    await callback_query.message.answer(response, parse_mode="Markdown")
    await callback_query.answer()


@dp.callback_query(Text("initiate_attack"))
async def initiate_attack(callback_query: types.CallbackQuery):
    """Handle attack initiation."""
    user_id = callback_query.from_user.id
    user_data = get_user_info(user_id)

    if not user_data or user_data.get("plan", 0) == 0:
        response = (
            f"🚨 *Access Denied!*\n\n"
            f"👤 *Agent ID:* `{user_id}`\n"
            f"❌ *You are not authorized to initiate an attack.*\n"
            f"💡 *Contact HQ at {USERNAME} for support and access approval.*"
        )
        await callback_query.message.answer(response, parse_mode="Markdown")
        await callback_query.answer()
        return

    # Cooldown check
    last_attack_time = user_data.get("last_attack_time")
    if last_attack_time:
        last_attack_time = datetime.fromisoformat(last_attack_time)
        time_diff = datetime.now() - last_attack_time
        if time_diff < timedelta(minutes=3):
            remaining_time = timedelta(minutes=3) - time_diff
            response = (
                f"⏳ *Cooldown Active!*\n\n"
                f"🚫 *You must wait for {remaining_time.seconds // 60} minutes and {remaining_time.seconds % 60} seconds before initiating another attack.*"
            )
            await callback_query.message.answer(response, parse_mode="Markdown")
            await callback_query.answer()
            return

    response = (
        f"⚔️ *Mission Briefing*\n\n"
        f"💥 *Prepare to execute your operation!*\n"
        f"📝 *Provide the following details in this format:*\n"
        f"`IP PORT DURATION`\n\n"
        f"📌 *Example:* `192.168.1.1 80 120` (120 seconds duration)\n"
        f"⚡ *Stay focused, Agent. HQ is monitoring your progress.*"
    )

    await callback_query.message.answer(response, parse_mode="Markdown")
    await callback_query.answer()


# Run the Bot
async def main():
    logger.info("🚀 Bot is starting...")
    await bot.delete_webhook(drop_pending_updates=True)
    dp.include_router(dp)  # Add all handlers
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
