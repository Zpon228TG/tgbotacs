import pymailtm
import time
import json
import os
import telebot

# Set up the bot token and chat ID
bot_token = '7426380650:AAEkJp4_EF4h8ZvLxBbNNWT8xXg7jRQ02n0'
chat_id = '7412395676'
bot = telebot.TeleBot(bot_token)

# File and record management
file_path = 'emails.txt'
max_entries = 2500
email_count = 0

# Notification thresholds
notify_threshold = 15
entries_for_notification = 0

def generate_email_data():
    global email_count, entries_for_notification

    while True:
        try:
            # Replace these with the correct methods after verifying the module
            client = pymailtm.Client()  # Initialize the client (Placeholder)
            domain = client.get_domains()  # Get available domains (Placeholder)

            # Generate email address, password, and token
            account = client.register(domain)
            email = account['address']
            password = account['password']
            token = account['token']

            # Write to file in the format "Email:Password:Token"
            with open(file_path, 'a') as f:
                f.write(f'{email}:{password}:{token}\n')

            email_count += 1
            entries_for_notification += 1

            # Notify every 15 emails
            if entries_for_notification >= notify_threshold:
                bot.send_message(chat_id, f'📧 Successfully generated {email_count} emails!')
                entries_for_notification = 0

            # Check if file reached max size or max entries
            if email_count >= max_entries or os.path.getsize(file_path) > 9 * 1024 * 1024:
                bot.send_document(chat_id, open(file_path, 'rb'), caption="#почты 📂")
                os.remove(file_path)
                email_count = 0

            time.sleep(3)  # Wait for 3 seconds before generating next email

        except Exception as e:
            bot.send_message(chat_id, f'Error: {str(e)}')

def main():
    bot.send_message(chat_id, '📧 Email generation bot started!')
    generate_email_data()

if __name__ == "__main__":
    main()
