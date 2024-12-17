import os
from telegram import Update, InputFile
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from moviepy.editor import ImageClip, concatenate_videoclips
from PIL import Image

# Dictionary to store images for each user
user_images: dict[int, list[str]] = {}

# Step 1: Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Hi! Send me two pictures, and I'll create a hug video for you.")

# Step 2: Receive images
async def receive_image(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_chat.id
    if user_id not in user_images:
        user_images[user_id] = []

    # Save the image
    photo = update.message.photo[-1]  # Get the highest resolution photo
    file = await photo.get_file()
    file_path = f"image_{user_id}_{len(user_images[user_id])}.jpg"
    await file.download_to_drive(file_path)
    user_images[user_id].append(file_path)

    await update.message.reply_text(f"Got it! {len(user_images[user_id])}/2 images received.")

    # If we have two images, process them
    if len(user_images[user_id]) == 2:
        await update.message.reply_text("Processing your hug video, please wait...")
        await create_hug_video(user_id, update, context)

# Step 3: Create hug video
async def create_hug_video(user_id: int, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        image1_path, image2_path = user_images[user_id]
        hug_video_path = f"hug_video_{user_id}.mp4"

        # Load images
        img1 = Image.open(image1_path)
        img2 = Image.open(image2_path)

        # Ensure the images are the same size
        img2 = img2.resize(img1.size)

        # Create a hug effect by alternating images
        clips = []
        for _ in range(5):  # Number of "hugs"
            clips.append(ImageClip(image1_path).set_duration(0.5))
            clips.append(ImageClip(image2_path).set_duration(0.5))

        # Combine clips into a video
        video = concatenate_videoclips(clips, method="compose")
        video.write_videofile(hug_video_path, fps=24, codec="libx264", audio=False)

        # Send the video
        with open(hug_video_path, "rb") as video_file:
            await context.bot.send_video(
                chat_id=user_id,
                video=InputFile(video_file),
                caption="Here's your hug video!"
            )

        # Clean up
        os.remove(image1_path)
        os.remove(image2_path)
        os.remove(hug_video_path)
        del user_images[user_id]

    except Exception as e:
        await update.message.reply_text(f"An error occurred: {e}")

# Main function to start the bot
async def main() -> None:
    TOKEN = "7990858994:AAGBSDQnCuNcgHXRK2F2xc7NSMYdJUOUJF4"

    # Build the application
    app = ApplicationBuilder().token(TOKEN).build()

    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, receive_image))

    # Run the bot
    print("Bot is running...")
    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
