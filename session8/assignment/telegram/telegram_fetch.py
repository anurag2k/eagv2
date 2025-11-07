import requests
import time
import urllib3
from dotenv import load_dotenv
import os

# Suppress the warning for unverified HTTPS requests
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
load_dotenv()


# --- Configuration ---

# 1. Get your Bot Token:
#    - Open Telegram and search for the "@BotFather" user.
#    - Start a chat and send the "/newbot" command.
#    - Follow the instructions to create a bot.
#    - BotFather will give you a token. Paste it here.
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# 2. Get your Group Chat ID:


# --- Configuration ---


# 2. Get your Group Chat ID:
#    (If you can't add @RawDataBot, try one of these other methods)
#
#    METHOD 1 (Easiest & Most Reliable):
#    - Add your new bot (the one you just created) to the group chat.
#    - Send any message to the group (e.g., "hello").
#    - Open this URL in your web browser:
#      https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates
#      (Replace <YOUR_BOT_TOKEN> with your actual token)
#    - Look at the JSON response. You will see something like:
#      ..."message":{"chat":{"id":-1001234567890, "title":...
#    - The "id" (e.g., -1001234567890) is your TARGET_CHAT_ID.
#
#    METHOD 2 (Web Browser):
#    - Open web.telegram.org in your browser.
#    - Go to your group.
#    - The URL in your browser bar will look like:
#      https://web.telegram.org/k/#-123456789
#    - Your chat ID is the number after the /k/# (e.g., -123456789).
#    - NOTE: If the ID is *not* negative (e.g., 123456789), you may need
#      to add "-100" to the front, making it "-100123456789".
#      Method 1 is more reliable.

#    METHOD 3(rawdatabot)
#    - Add your new bot to the group chat you want to monitor.
#    - Add the "@RawDataBot" user to the group as well.
#    - @RawDataBot will post a large JSON message.
#    - Look for the 'chat' -> 'id' field in that JSON. It will be a negative number.
#    - Paste that number here (e.g., -1001234567890).
#TARGET_CHAT_ID = "TELEGRAM_CHAT_ID" # <-- IMPORTANT: REPLACE 0 WITH YOUR CHAT ID (e.g., -100123456789)
TARGET_CHAT_ID = int(os.getenv('TELEGRAM_CHAT_ID', 0))

# --- End Configuration ---

# This is the URL for all Bot API actions
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

# This ID is used to tell Telegram which messages we've already seen.
# We start at 0, and the API will send us the first unread message.
last_update_id = 0

# Timeout for the long poll (in seconds)
# The server will wait up to this long for a new message.
POLL_TIMEOUT = 60

def get_bot_info():
    """Helper function to test the bot token."""
    try:
        url = f"{BASE_URL}/getMe"
        response = requests.get(url, timeout=5, verify=False)
        response.raise_for_status() # Raise an error for bad responses (4xx, 5xx)
        data = response.json()
        if data.get("ok"):
            bot_name = data.get("result", {}).get("username", "Unknown")
            print(f"Successfully connected. Bot Name: @{bot_name}")
            return True
        else:
            print(f"Error from Telegram: {data.get('description')}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"Error connecting to Telegram API: {e}")
        return False

def poll_for_messages():
    """
    Performs a single long poll request to the Telegram API.
    """
    global last_update_id
    
    # Parameters for the getUpdates API call
    params = {
        'offset': last_update_id,      # Start from the message after the last one we processed
        'timeout': POLL_TIMEOUT,       # Tell Telegram to wait up to 60s
        'allowed_updates': ['message', 'channel_post'] # We only care about new messages
    }
    
    url = f"{BASE_URL}/getUpdates"
    
    try:
        response = requests.get(url, params=params, timeout=POLL_TIMEOUT + 5, verify=False)
        response.raise_for_status()
        data = response.json()

        if not data.get("ok"):
            print(f"API Error: {data.get('description')}")
            return

        updates = data.get("result", [])
        if not updates:
            # This just means the poll timed out, no new messages.
            # print("No new messages, polling again...")
            return

        for update in updates:
            # IMPORTANT: We must increment the update_id to avoid processing
            # the same message again in the next poll.
            last_update_id = update['update_id'] + 1

            # Check for a regular group message
            if 'message' in update:
                message = update['message']
                chat_id = message['chat']['id']
                
                # Check if this message is from our target group
                if chat_id == TARGET_CHAT_ID:
                    sender_name = message.get('from', {}).get('first_name', 'Unknown')
                    message_text = message.get('text', '[Media or non-text content]')
                    
                    print("\n--- NEW MESSAGE ---")
                    print(f"From: {sender_name}")
                    print(f"Message: {message_text}")
                    print("-------------------")
            
            # This handles posts in a "Channel" (which groups can be)
            elif 'channel_post' in update:
                message = update['channel_post']
                chat_id = message['chat']['id']

                if chat_id == TARGET_CHAT_ID:
                    sender_name = message.get('author_signature', 'Channel Post')
                    message_text = message.get('text', '[Media or non-text content]')

                    print("\n--- NEW CHANNEL POST ---")
                    print(f"From: {sender_name}")
                    print(f"Message: {message_text}")
                    print("------------------------")


    except requests.exceptions.RequestException as e:
        print(f"Network error during poll: {e}")
        # Wait a bit before retrying to avoid spamming on network failure
        time.sleep(5)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        time.sleep(5)


def main():
    """Main function to start the bot."""
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE" or TARGET_CHAT_ID == 0:
        print("="*40)
        print("ERROR: Please update BOT_TOKEN and")
        print("       TARGET_CHAT_ID at the top of the script.")
        print("See the comments for instructions.")
        print("="*40)
        return

    print("Starting message poller...")
    if not get_bot_info():
        print("Exiting due to invalid token or connection issue.")
        return
        
    print(f"Monitoring group chat: {TARGET_CHAT_ID}")
    print("Press Ctrl+C to stop.")

    try:
        while True:
            # This function will run, wait for messages,
            # process them, and then return.
            # The loop immediately calls it again to start the
            # next long poll.
            poll_for_messages()
            
            # No 'time.sleep()' is needed here because the
            # 'timeout' in the request already provides the "wait".
            
    except KeyboardInterrupt:
        print("\nStopping bot...")

if __name__ == "__main__":
    main()

