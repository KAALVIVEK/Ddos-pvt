import os
import cv2
from PIL import Image
from telegram import Update, InputFile
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Store user images in a dictionary
user_images = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Respond to /start command."""
    await update.message.reply_text("Hi! Send me two pictures, and I'll create a hug video for you.")

async def receive_image(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle receiving images and create a video if two images are received."""
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

    # If we have two images, process them
    if len(user_images[user_id]) == 2:
        await update.message.reply_text("Processing your hug video, please wait...")
        await create_hug_video(user_id, context)

async def create_hug_video(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Create a hug video from two images and send it to the user."""
    try:
        image1_path, image2_path = user_images[user_id]
        hug_video_path = f"hug_video_{user_id}.mp4"

        # Load images
        img1 = Image.open(image1_path)
        img2 = Image.open(image2_path)

        # Resize images to the same size
        img2 = img2.resize(img1.size)

        # Save resized images temporarily
        img1.save(f"temp1_{user_id}.jpg")
        img2.save(f"temp2_{user_id}.jpg")

        # Load resized images as OpenCV frames
        frame1 = cv2.imread(f"temp1_{user_id}.jpg")
        frame2 = cv2.imread(f"temp2_{user_id}.jpg")

        # Create a list of frames alternating between the two images
        frames = [frame1, frame2] * 5  # Alternate 5 times

        # Video dimensions
        height, width, _ = frame1.shape
        size = (width, height)

        # Write frames to the video
        out = cv2.VideoWriter(hug_video_path, cv2.VideoWriter_fourcc(*'mp4v'), 2, size)
        for frame in frames:
            out.write(frame)
        out.release()

        # Send the video to the user
        await context.bot.send_video(chat_id=user_id, video=InputFile(hug_video_path), caption="Here's your hug video!")

        # Clean up temporary files
        os.remove(image1_path)
        os.remove(image2_path)
        os.remove(f"temp1_{user_id}.jpg")
        os.remove(f"temp2_{user_id}.jpg")
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
    
