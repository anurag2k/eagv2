import asyncio
import requests
import os
from dotenv import load_dotenv
from agent import CortexAgent

load_dotenv()

# Use your existing config
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TARGET_CHAT_ID = int(os.getenv('TELEGRAM_CHAT_ID', 0))
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

def get_latest_message():
    """Get latest message from your target chat (non-blocking)"""
    try:
        url = f"{BASE_URL}/getUpdates"
        params = {'limit': 100, 'timeout': 0}  # Non-blocking
        
        response = requests.get(url, params=params, timeout=5, verify=False)
        response.raise_for_status()
        data = response.json()
        
        if not data.get("ok") or not data.get("result"):
            return None
            
        # Find latest message from target chat
        for update in reversed(data["result"]):
            if 'message' in update:
                message = update['message']
                if message['chat']['id'] == TARGET_CHAT_ID and message.get('text'):
                    return {
                        'text': message['text'],
                        'from': message.get('from', {}).get('first_name', 'Unknown'),
                        'message_id': message['message_id']
                    }
        return None
        
    except Exception as e:
        print(f"Error getting latest message: {e}")
        return None

def send_telegram_message(text):
    """Send message back to telegram chat"""
    try:
        url = f"{BASE_URL}/sendMessage"
        data = {
            'chat_id': TARGET_CHAT_ID,
            'text': text
        }
        response = requests.post(url, json=data, verify=False)
        response.raise_for_status()
        return True
    except Exception as e:
        print(f"Error sending telegram message: {e}")
        return False

async def main():
    """Main integration function"""
    print("🤖 Telegram-Agent Bridge Starting...")
    
    if not BOT_TOKEN or TARGET_CHAT_ID == 0:
        print("❌ Please set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env")
        return
    
    # Get latest message
    message = get_latest_message()
    if not message:
        print("📭 No new messages found")
        return
    
    print(f"📨 Processing message from {message['from']}: {message['text'][:50]}...")
    
    # Initialize agent
    agent = CortexAgent()
    
    # Process with agent
    response = await agent.process_input(message['text'])
    
    print(f"🧠 Agent response: {response[:100]}...")
    
    # Send back to Telegram
    if send_telegram_message(response):
        print("✅ Response sent to Telegram")
    else:
        print("❌ Failed to send to Telegram")
    
if __name__ == "__main__":
    asyncio.run(main())
