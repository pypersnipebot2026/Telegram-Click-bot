# bot.py - Telegram Trading Bot using ClickShift API (inspired by @clicksolbot)
import telebot
from telebot.types import Message
import requests
import os  # For environment variables

# Get tokens from environment variables (set in Railway dashboard)
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CLICKSHIFT_API_KEY = os.getenv('CLICKSHIFT_API_KEY')

# ClickShift API base URL
API_BASE_URL = 'https://api.clickshift.io/v1'

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message: Message):
    bot.reply_to(message, "Welcome to your Telegram Trading Bot! Inspired by ClickBot (@clicksolbot).\n"
                          "Use /analyze <token_address> to get trading intelligence on a Solana token.\n"
                          "Features include risk assessment, predictions, and whale alerts.")

@bot.message_handler(commands=['analyze'])
def analyze_token(message: Message):
    # Extract token address from message
    text = message.text.split()
    if len(text) < 2:
        bot.reply_to(message, "Please provide a token address, e.g., /analyze <token_address>")
        return
    
    token_address = text[1]
    
    # Prepare API request
    headers = {
        'Authorization': f'Bearer {CLICKSHIFT_API_KEY}',
        'Content-Type': 'application/json'
    }
    data = {
        'address': token_address,  # Updated key based on your JSON example
        'include_predictions': True,
        'include_whale_alerts': True
    }
    
    try:
        response = requests.post(f'{API_BASE_URL}/analyze/token', headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        
        # Format the response based on your example JSON structure
        if not result.get('success', False):
            bot.reply_to(message, "API returned an error. Please try again.")
            return
        
        data = result['data']
        token_info = data['token']
        analysis = data['analysis']
        whale_activity = data['whale_activity']
        indicators = data['technical_indicators']
        
        formatted = f"Analysis for {token_info['symbol']} ({token_address}):\n"
        formatted += f"Price: ${token_info['price']}\n"
        formatted += f"Market Cap: ${token_info['market_cap']:,}\n\n"
        formatted += f"Signal: {analysis['signal']}\n"
        formatted += f"Confidence: {analysis['confidence']}%\n"
        formatted += f"Entry Price: ${analysis['entry_price']}\n"
        formatted += f"Stop Loss: ${analysis['stop_loss']}\n"
        formatted += f"Take Profit: ${analysis['take_profit']}\n"
        formatted += f"Risk Level: {analysis['risk_level']}\n"
        formatted += f"Prediction Expires: {analysis['prediction_expires']}\n\n"
        formatted += f"Whale Activity: {'Detected' if whale_activity['detected'] else 'None'}\n"
        if whale_activity['detected']:
            formatted += f" - Accumulation: {'Yes' if whale_activity['accumulation'] else 'No'}\n"
            formatted += f" - Large Holders: {whale_activity['large_holders']}\n"
            formatted += f" - Exit Clusters: {', '.join([f'${x}' for x in whale_activity['exit_clusters']])}\n\n"
        formatted += f"Technical Indicators:\n"
        formatted += f" - RSI: {indicators['rsi']} ({indicators['rsi_signal']})\n"
        formatted += f" - ATR: ${indicators['atr']}\n"
        formatted += f" - Pump Probability: {indicators['pump_probability']}%\n"
        
        bot.reply_to(message, formatted)
    except requests.exceptions.RequestException as e:
        bot.reply_to(message, f"Error analyzing token: {str(e)}")

# Polling mode (suitable for Railway)
if __name__ == '__main__':
    bot.infinity_polling()
