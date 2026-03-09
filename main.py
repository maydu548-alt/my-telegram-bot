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

# --- WEB SERVER (Render-এর জন্য) ---
app = Flask(__name__)
@app.route('/')
def home(): return "Bot is Online"

def run_server():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- SIGNAL LOGIC ---
async def get_signals():
    all_signals = []
    try:
        # Batch download: সবগুলো একসাথে ডাউনলোড করলে ইয়াহু ব্লক করে না
        data = yf.download(PAIRS, period='5d', interval='5m', group_by='ticker', progress=False)
        
        for symbol in PAIRS:
            df = data[symbol]
            if df.empty or len(df) < 50: continue
            
            # Indicators
            close = df['Close']
            ma20 = close.rolling(20).mean()
            std20 = close.rolling(20).std()
            upper = ma20 + (std20 * 2)
            lower = ma20 - (std20 * 2)
            
            # RSI Calculation
            delta = close.diff()
            gain = (delta.where(delta > 0, 0)).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rsi = 100 - (100 / (1 + (gain / loss)))
            
            # Latest values
            curr = float(close.iloc[-1])
            curr_rsi = rsi.iloc[-1]
            
            # Filter Logic
            name = symbol.replace('=X', '')
            if curr < lower.iloc[-1] and curr_rsi < 35:
                all_signals.append(f"🟢 **{name}**: BUY @ `{curr:.5f}`")
            elif curr > upper.iloc[-1] and curr_rsi > 65:
                all_signals.append(f"🔴 **{name}**: SELL @ `{curr:.5f}`")
    except Exception as e:
        print(f"Fetch Error: {e}")
    return all_signals

# --- MAIN LOOP ---
async def monitor():
    while True:
        now = datetime.now()
        if now.minute % 5 == 0 and now.second < 5:
            sigs = await get_signals()
            if sigs:
                msg = f"💎 **MARKET SIGNAL - {now.strftime('%H:%M')}**\n━━━━━━━━━━━━━━\n"
                await bot.send_message(CHAT_ID, msg + "\n".join(sigs), parse_mode='Markdown')
            await asyncio.sleep(60)
        await asyncio.sleep(1)

if __name__ == "__main__":
    Thread(target=run_server, daemon=True).start()
    asyncio.run(monitor())