import os
import requests
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# Replace these with your own credentials
TELEGRAM_BOT_TOKEN = "7990858994:AAGBSDQnCuNcgHXRK2F2xc7NSMYdJUOUJF4"
INSTAGRAM_API_URL = "https://rapidapi.com"  # Replace with the API URL
INSTAGRAM_API_KEY = "b5fb37ec92msh443f01d809e471ap11f165jsn96fc3ff776a5"  # Replace with your API Key

def start(update: Update, context: CallbackContext) -> None:
    """Send a welcome message when the bot starts."""
    update.message.reply_text("Welcome! Send me an Instagram link, and I'll download the video or story for you.")

def download_instagram_media(instagram_url: str) -> str:
    """Downloads Instagram media using an API and returns the file URL."""
    headers = {
        "X-RapidAPI-Key": INSTAGRAM_API_KEY,
        "X-RapidAPI-Host": "instagram-downloader-api-host"  # Replace with the API host
    }
    params = {"url": instagram_url}

    response = requests.get(INSTAGRAM_API_URL, headers=headers, params=params)
    if response.status_code == 200:
        data = response.json()
        return data.get("media_url")  # Adjust the key based on the API response
    else:
        return None

def handle_message(update: Update, context: CallbackContext) -> None:
    """Handle incoming messages and process Instagram links."""
    instagram_url = update.message.text
    update.message.reply_text("Processing your link...")

    try:
        # Step 1: Get the media URL
        media_url = download_instagram_media(instagram_url)
        if media_url:
            # Step 2: Download the video file
            video_response = requests.get(media_url)
            if video_response.status_code == 200:
                file_name = "video.mp4"
                with open(file_name, "wb") as file:
                    file.write(video_response.content)

                # Step 3: Send the video to the user
                with open(file_name, "rb") as file:
                    update.message.reply_video(file)

                # Step 4: Cleanup the downloaded file
                os.remove(file_name)
            else:
                update.message.reply_text("Failed to download the video from Instagram.")
        else:
            update.message.reply_text("Failed to process the link. Please check the link or try again later.")
    except Exception as e:
        update.message.reply_text(f"An error occurred: {e}")

def main():
    """Run the Telegram bot."""
    updater = Updater(TELEGRAM_BOT_TOKEN)

    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
