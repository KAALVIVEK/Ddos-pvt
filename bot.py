import os
from PIL import Image
import subprocess
from telegram import Update, InputFile
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Store user images
user_images = {}

def resize_image(image: Image.Image) -> Image.Image:
    """Resize image while ensuring dimensions are divisible by 2."""
    width, height = image.size

    # Adjust width and height to be divisible by 2
    new_width = width if width % 2 == 0 else width - 1
    new_height = height if height % 2 == 0 else height - 1

    # Resize image to new dimensions while maintaining the aspect ratio
    image = image.resize((new_width, new_height))
    return image

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Respond to /start command."""
    await update.message.reply_text("Hi! Send me two pictures, and I'll create a hug video for you.")

async def receive_image(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle receiving images and create a video if two images are received."""
    user_id = update.effective_chat.id
    if user_id not in user_images:
        user_images[user_id] = []

    # Handle the uploaded file (whether it's an image or octet-stream)
    photo = update.message.photo[-1] if update.message.photo else update.message.document
    file = await photo.get_file()
    file_path = f"image_{user_id}_{len(user_images[user_id])}.jpg"  # Default save as .jpg

    # Check if file is an octet-stream and handle it
    if file.file_path.endswith('.octet-stream'):
        file_path = f"image_{user_id}_{len(user_images[user_id])}.jpg"  # Default name as .jpg
    await file.download_to_drive(file_path)

    # Add to user images list
    user_images[user_id].append(file_path)

    await update.message.reply_text(f"Image {len(user_images[user_id])}/2 received.")

    # If we have two images, process them
    if len(user_images[user_id]) == 2:
        await update.message.reply_text("Processing your hug video, please wait...")
        await create_hug_video(user_id, context)

async def create_hug_video(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Create a hug video from two images and send it to the user."""
    try:
        image1_path, image2_path = user_images[user_id]
        hug_video_path = f"hug_video_{user_id}.mp4"

        # Load and resize images, ensuring height and width are divisible by 2
        img1 = Image.open(image1_path)
        img2 = Image.open(image2_path)

        # Resize images to ensure dimensions are divisible by 2
        img1 = resize_image(img1)
        img2 = resize_image(img2)

        # Save resized images temporarily
        temp1_path = f"temp1_{user_id}.jpg"
        temp2_path = f"temp2_{user_id}.jpg"
        img1.save(temp1_path)
        img2.save(temp2_path)

        # Create a frame list file for ffmpeg
        frame_list_path = f"frames_{user_id}.txt"
        with open(frame_list_path, "w") as f:
            for _ in range(5):  # Repeat each image 5 times for a hug effect
                f.write(f"file '{temp1_path}'\n")
                f.write(f"file '{temp2_path}'\n")

        # Use ffmpeg to create the video
        ffmpeg_command = [
            "ffmpeg",
            "-y",  # Overwrite output file
            "-f", "concat",  # Concatenate frames
            "-safe", "0",  # Allow unsafe file paths
            "-i", frame_list_path,
            "-vf", "fps=2",  # Frames per second
            "-pix_fmt", "yuv420p",  # Ensure compatibility
            hug_video_path
        ]
        result = subprocess.run(ffmpeg_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Check ffmpeg output
        if result.returncode != 0:
            raise RuntimeError(f"ffmpeg error: {result.stderr.decode()}")

        # Validate the video file
        if not os.path.exists(hug_video_path) or os.stat(hug_video_path).st_size == 0:
            raise ValueError("Video creation failed. File is empty or invalid.")

        # Send the video to the user
        await context.bot.send_video(chat_id=user_id, video=InputFile(hug_video_path), caption="Here's your hug video!")

        # Clean up temporary files
        os.remove(image1_path)
        os.remove(image2_path)
        os.remove(temp1_path)
        os.remove(temp2_path)
        os.remove(frame_list_path)
        os.remove(hug_video_path)
        del user_images[user_id]

    except Exception as e:
        await context.bot.send_message(chat_id=user_id, text=f"An error occurred while creating your video: {e}")

def main() -> None:
    """Run the bot."""
    TOKEN = "7990858994:AAGBSDQnCuNcgHXRK2F2xc7NSMYdJUOUJF4"
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, receive_image))

    app.run_polling()

if __name__ == "__main__":
    main()
