# bot.py - Telegram Trading Bot using FREE DexScreener API (no ClickShift needed)
import telebot
from telebot.types import Message
import requests
import os

# Load Telegram token from env (Railway variable)
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

if not TELEGRAM_BOT_TOKEN:
    raise ValueError("Missing required environment variable: TELEGRAM_BOT_TOKEN")

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

DEXSCREENER_BASE = "https://api.dexscreener.com/latest/dex"

@bot.message_handler(commands=['start'])
def send_welcome(message: Message):
    welcome_text = (
        "Welcome to your FREE Solana Token Tracker Bot! 🚀\n\n"
        "No API keys needed – powered by public DexScreener data.\n"
        "Great for quick memecoin checks: price, volume, liquidity & momentum.\n\n"
        "Commands:\n"
        "/check <token_address>  → Get real-time stats & basic insight\n\n"
        "Example: /check DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263  (BONK)"
    )
    bot.reply_to(message, welcome_text)

@bot.message_handler(commands=['check', 'analyze'])
def check_token(message: Message):
    text = message.text.split()
    if len(text) < 2:
        bot.reply_to(message, "Please provide a Solana token address!\nExample: /check DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263")
        return

    token_address = text[1].strip()

    try:
        # Step 1: Search for pairs involving this token on Solana
        search_url = f"{DEXSCREENER_BASE}/search?q={token_address}"
        search_resp = requests.get(search_url, timeout=10)
        search_resp.raise_for_status()
        search_data = search_resp.json()

        if 'pairs' not in search_data or not search_data['pairs']:
            bot.reply_to(message, f"No active trading pairs found for {token_address} on DexScreener.\n"
                                  "Token might be too new, delisted, or not traded yet.")
            return

        # Take the top pair (usually the main one with highest liquidity)
        pair = search_data['pairs'][0]
        symbol = pair.get('baseToken', {}).get('symbol', 'Unknown')
        price_usd = pair.get('priceUsd', 'N/A')
        market_cap = pair.get('fdv', 'N/A')  # Fully Diluted Value ≈ market cap for most memecoins
        liquidity_usd = pair.get('liquidity', {}).get('usd', 'N/A')
        volume_24h = pair.get('volume', {}).get('h24', 'N/A')
        txns_24h = pair.get('txns', {}).get('h24', {})
        buys_24h = txns_24h.get('buys', 'N/A')
        sells_24h = txns_24h.get('sells', 'N/A')
        price_change_24h = pair.get('priceChange', {}).get('h24', 'N/A')

        # Build readable reply
        reply = f"**DexScreener Stats for {symbol} ({token_address})**\n\n"
        reply += f"💰 **Price**: ${price_usd}\n"
        reply += f"📊 **Market Cap / FDV**: ${market_cap:,} (if available)\n"
        reply += f"💧 **Liquidity**: ${liquidity_usd:,}\n"
        reply += f"🔄 **24h Volume**: ${volume_24h:,}\n"
        reply += f"📈 **24h Buys/Sells**: {buys_24h} / {sells_24h}\n"
        reply += f"**24h Price Change**: {price_change_24h}%\n\n"

        # Simple momentum insight
        if isinstance(price_change_24h, (int, float)):
            if price_change_24h > 20:
                reply += "🔥 **Strong pump momentum** detected!\n"
            elif price_change_24h > 5:
                reply += "📈 **Positive momentum** – watch for continuation.\n"
            elif price_change_24h < -10:
                reply += "⚠️ **Dumping** – high risk right now.\n"
            else:
                reply += "🟡 **Neutral** – low volatility currently.\n"
        else:
            reply += "No price change data available.\n"

        reply += "\nNote: This is public data – no advanced AI/whale predictions. DYOR!"

        bot.reply_to(message, reply, parse_mode='Markdown')

    except requests.exceptions.RequestException as e:
        bot.reply_to(message, f"Error fetching data: {str(e)}\nDexScreener might be rate-limited or down temporarily.")

# Start polling
if __name__ == '__main__':
    print("Free Solana Token Tracker Bot is starting...")
    bot.infinity_polling(timeout=20, long_polling_timeout=10)
