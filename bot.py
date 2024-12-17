import os
from PIL import Image
import subprocess
from telegram import Update, InputFile
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Dictionary to store user images
user_images = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Respond to /start command."""
    await update.message.reply_text("Hi! Send me two pictures, and I'll create a hug video for you.")

async def receive_image(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle image upload and process after receiving two images."""
    user_id = update.effective_chat.id
    if user_id not in user_images:
        user_images[user_id] = []

    # Save the received image
    photo = update.message.photo[-1]
    file = await photo.get_file()
    file_path = f"image_{user_id}_{len(user_images[user_id])}.jpg"
    await file.download_to_drive(file_path)
    user_images[user_id].append(file_path)

    await update.message.reply_text(f"Image {len(user_images[user_id])}/2 received.")

    # Once two images are received, create the hug video
    if len(user_images[user_id]) == 2:
        await update.message.reply_text("Processing your hug video, please wait...")
        await create_hug_video(user_id, context)

async def create_hug_video(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Create and send a hug video."""
    try:
        image1_path, image2_path = user_images[user_id]
        hug_video_path = f"hug_video_{user_id}.mp4"

        # Resize images to the same size using Pillow
        img1 = Image.open(image1_path)
        img2 = Image.open(image2_path)
        img2 = img2.resize(img1.size)  # Resize img2 to match img1

        # Save resized images
        temp1_path = f"temp1_{user_id}.jpg"
        temp2_path = f"temp2_{user_id}.jpg"
        img1.save(temp1_path)
        img2.save(temp2_path)

        # Generate a frame list for ffmpeg
        frame_list_path = f"frames_{user_id}.txt"
        with open(frame_list_path, "w") as f:
            for _ in range(5):  # Alternate the two images 5 times
                f.write(f"file '{temp1_path}'\n")
                f.write(f"file '{temp2_path}'\n")

        # Use ffmpeg to create the video
        ffmpeg_command = [
            "ffmpeg",
            "-y",  # Overwrite output file
            "-f", "concat",
            "-safe", "0",
            "-i", frame_list_path,
            "-vf", "fps=2",  # Frames per second
            "-pix_fmt", "yuv420p",
            hug_video_path
        ]
        subprocess.run(ffmpeg_command, check=True)

        # Check if the video was created successfully
        if not os.path.exists(hug_video_path) or os.stat(hug_video_path).st_size == 0:
            raise ValueError("Video creation failed. File is empty or invalid.")

        # Send the generated video to the user
        await context.bot.send_video(chat_id=user_id, video=InputFile(hug_video_path), caption="Here's your hug video!")

        # Cleanup temporary files
        os.remove(image1_path)
        os.remove(image2_path)
        os.remove(temp1_path)
        os.remove(temp2_path)
        os.remove(frame_list_path)
        os.remove(hug_video_path)
        del user_images[user_id]

    except Exception as e:
        await context.bot.send_message(chat_id=user_id, text=f"An error occurred: {e}")

def main() -> None:
    """Run the bot."""
    TOKEN = "7990858994:AAGBSDQnCuNcgHXRK2F2xc7NSMYdJUOUJF4"
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, receive_image))

    app.run_polling()

if __name__ == "__main__":
    main()
    
