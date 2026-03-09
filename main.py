import yfinance as yf
import asyncio
import os
import logging
from telegram import Bot
from flask import Flask
from threading import Thread
from datetime import datetime

# --- CONFIGURATION ---
TELEGRAM_TOKEN = '8287022829:AAEJfSnbsAgnGqoFbNESwDMifQ9S5Gf9bJk'
CHAT_ID = '7995220028'
bot = Bot(token=TELEGRAM_TOKEN)

PAIRS = ["EURUSD=X", "GBPUSD=X", "USDJPY=X", "AUDUSD=X", "EURJPY=X", "GBPJPY=X", "USDCAD=X", "EURGBP=X", "AUDJPY=X", "NZDUSD=X", "GBPAUD=X", "EURAUD=X"]

# --- SERVER ---
app = Flask(__name__)
@app.route('/')
def home(): return "Bot is live!"

def run_server():
    # Render-এর দেওয়া পোর্ট বা ডিফল্ট ১০০০০
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- BOT LOGIC ---
async def fetch_signals():
    try:
        # Batch download: সবগুলো একসাথে ডাউনলোড করলে ইয়াহু ব্লক করে না
        data = yf.download(PAIRS, period='5d', interval='5m', group_by='ticker', progress=False)
        
        for symbol in PAIRS:
            df = data[symbol]
            if df.empty: continue
            
            # সিম্পল রিভার্সাল সিগন্যাল (ইন্ডিকেটর লজিক)
            close = df['Close'].iloc[-1]
            ma20 = df['Close'].rolling(20).mean().iloc[-1]
            
            if close < (ma20 * 0.995): # BUY Condition
                await bot.send_message(CHAT_ID, f"🟢 BUY Signal: {symbol.replace('=X', '')} at {close:.5f}")
            elif close > (ma20 * 1.005): # SELL Condition
                await bot.send_message(CHAT_ID, f"🔴 SELL Signal: {symbol.replace('=X', '')} at {close:.5f}")
                
    except Exception as e:
        print(f"Fetch Error: {e}")

async def main_loop():
    while True:
        await fetch_signals()
        await asyncio.sleep(300) # প্রতি ৫ মিনিটে চেক করবে

if __name__ == "__main__":
    Thread(target=run_server, daemon=True).start()
    asyncio.run(main_loop())