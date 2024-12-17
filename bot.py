import os
import cv2
from PIL import Image
from telegram import Update, InputFile
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
import asyncio

# Dictionary to store user images
user_images: dict[int, list[str]] = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Start command handler."""
    await update.message.reply_text("Hi! Send me two pictures, and I'll create a hug video for you.")

async def receive_image(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle receiving images."""
    user_id = update.effective_chat.id
    if user_id not in user_images:
        user_images[user_id] = []

    # Save the received image
    photo = update.message.photo[-1]
    file = await photo.get_file()
    file_path = f"image_{user_id}_{len(user_images[user_id])}.jpg"
    await file.download_to_drive(file_path)
    user_images[user_id].append(file_path)

    await update.message.reply_text(f"Got it! {len(user_images[user_id])}/2 images received.")

    # If we have two images, process them
    if len(user_images[user_id]) == 2:
        await update.message.reply_text("Processing your hug video, please wait...")
        await create_hug_video(user_id, update, context)

async def create_hug_video(user_id: int, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Create a hug video from two images."""
    try:
        image1_path, image2_path = user_images[user_id]
        hug_video_path = f"hug_video_{user_id}.mp4"

        # Load images using Pillow
        img1 = Image.open(image1_path)
        img2 = Image.open(image2_path)

        # Resize images to match dimensions
        img2 = img2.resize(img1.size)

        # Save resized images (optional)
        resized1_path = f"resized_{user_id}_1.jpg"
        resized2_path = f"resized_{user_id}_2.jpg"
        img1.save(resized1_path)
        img2.save(resized2_path)

        # Create a list of frames
        frames = []
        for _ in range(5):  # Number of "hugs" (5 alternations)
            frames.append(cv2.imread(resized1_path))
            frames.append(cv2.imread(resized2_path))

        # Video dimensions
        height, width, layers = frames[0].shape
        size = (width, height)

        # Create a video writer
        out = cv2.VideoWriter(hug_video_path, cv2.VideoWriter_fourcc(*'mp4v'), 2, size)

        # Write frames to the video
        for frame in frames:
            out.write(frame)
        out.release()

        # Send the video to the user
        with open(hug_video_path, "rb") as video_file:
            await context.bot.send_video(chat_id=user_id, video=InputFile(video_file), caption="Here's your hug video!")

        # Clean up
        os.remove(image1_path)
        os.remove(image2_path)
        os.remove(resized1_path)
        os.remove(resized2_path)
        os.remove(hug_video_path)
        del user_images[user_id]

    except Exception as e:
        await update.message.reply_text(f"An error occurred: {e}")

def main():
    """Main entry point for the bot."""
    TOKEN = "7990858994:AAGBSDQnCuNcgHXRK2F2xc7NSMYdJUOUJF4"

    # Create the application
    app = Application.builder().token(TOKEN).build()

    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, receive_image))

    # Run the bot
    async def run():
        print("Bot is running...")
        await app.start()
        await app.updater.start_polling()
        await app.idle()  # Wait for shutdown signal

    # Handle asyncio loop properly
    try:
        asyncio.run(run())
    except RuntimeError as e:
        if "no running event loop" in str(e):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(run())

if __name__ == "__main__":
    main()
