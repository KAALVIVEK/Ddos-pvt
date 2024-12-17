from telegram import Update, InputFile
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from moviepy.editor import *
from PIL import Image
import os

# Step 1: Start command
def start(update: Update, context: CallbackContext):
    update.message.reply_text("Hi! Send me two pictures, and I'll create a hug video for you.")

# Step 2: Receive images
user_images = {}

def receive_image(update: Update, context: CallbackContext):
    user_id = update.message.chat_id
    if user_id not in user_images:
        user_images[user_id] = []
    
    # Save the image
    photo = update.message.photo[-1]  # Get the best quality photo
    file = photo.get_file()
    file_path = f"image_{user_id}_{len(user_images[user_id])}.jpg"
    file.download(file_path)
    user_images[user_id].append(file_path)
    
    update.message.reply_text(f"Got it! {len(user_images[user_id])}/2 images received.")
    
    # If we have two images, process them
    if len(user_images[user_id]) == 2:
        update.message.reply_text("Processing your hug video, please wait...")
        create_hug_video(user_id, update, context)

# Step 3: Create hug video
def create_hug_video(user_id, update, context):
    try:
        image1_path, image2_path = user_images[user_id]
        hug_video_path = f"hug_video_{user_id}.mp4"
        
        # Load images
        img1 = Image.open(image1_path)
        img2 = Image.open(image2_path)

        # Ensure the images are the same size
        img2 = img2.resize(img1.size)
        
        # Create a hug effect by combining the images alternately
        clips = []
        for i in range(5):  # Number of "hugs"
            clips.append(ImageClip(image1_path).set_duration(0.5))
            clips.append(ImageClip(image2_path).set_duration(0.5))
        
        # Combine clips
        video = concatenate_videoclips(clips, method="compose")
        video.write_videofile(hug_video_path, fps=24)

        # Send the video
        context.bot.send_video(chat_id=user_id, video=open(hug_video_path, 'rb'), caption="Here's your hug video!")
        
        # Clean up
        os.remove(image1_path)
        os.remove(image2_path)
        os.remove(hug_video_path)
        del user_images[user_id]
    except Exception as e:
        update.message.reply_text(f"An error occurred: {e}")

# Main function to start the bot
def main():
    TOKEN = "7990858994:AAGBSDQnCuNcgHXRK2F2xc7NSMYdJUOUJF4"
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.photo, receive_image))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
