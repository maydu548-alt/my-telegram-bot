import yfinance as yf
import asyncio
import os
import random
from telegram import Bot
from flask import Flask
from threading import Thread
import datetime
from datetime import timezone, timedelta

# --- CONFIGURATION ---
TOKEN = '8287022829:AAEJfSnbsAgnGqoFbNESwDMifQ9S5Gf9bJk'
CHAT_ID = '7995220028'
bot = Bot(token=TOKEN)
PAIRS = ["EURUSD=X", "GBPUSD=X", "USDJPY=X", "AUDUSD=X", "EURJPY=X", "GBPJPY=X", "USDCAD=X", "EURGBP=X"]

BD_TZ = timezone(timedelta(hours=6))

# Flask Server (Render Port Fix)
app = Flask(__name__)
@app.route('/')
def home(): return "Bot is Online"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

async def check_single_pair(symbol):
    try:
        data = await asyncio.to_thread(yf.download, symbol, interval='5m', period='1d', progress=False, timeout=10)
        if data is None or data.empty or len(data) < 20: return None
        
        close = data['Close'].squeeze()
        ma20 = close.rolling(window=20).mean()
        std20 = close.rolling(window=20).std()
        
        # RSI
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rsi = 100 - (100 / (1 + (gain / loss))).iloc[-1]
        
        curr = float(close.iloc[-1])
        pair_name = symbol.replace('=X', '')
        
        if curr <= (ma20.iloc[-1] - (std20.iloc[-1] * 2)) and rsi < 35:
            return {'pair': pair_name, 'dir': '🟢 CALL', 'price': curr}
        elif curr >= (ma20.iloc[-1] + (std20.iloc[-1] * 2)) and rsi > 65:
            return {'pair': pair_name, 'dir': '🔴 PUT', 'price': curr}
    except: return None
    return None

async def monitor_market():
    while True:
        now = datetime.datetime.now(BD_TZ)
        if now.minute % 5 == 4 and now.second >= 50:
            for symbol in PAIRS:
                result = await check_single_pair(symbol)
                
                if result:
                    # আপনার দেওয়া ফরম্যাট অনুযায়ী মেসেজ
                    msg = (
                        f"🔥 **PREMIUM SIGNAL** 🔥\n"
                        f"━━━━━━━━━━━━━━\n"
                        f"📊 Asset: {result['pair']}\n"
                        f"💹 Direction: {result['dir']}\n"
                        f"📥 Entry: `{result['price']:.5f}`\n"
                        f"🕒 Time: `{now.strftime('%H:%M:%S')}`\n"
                        f"━━━━━━━━━━━━━━"
                    )
                    await bot.send_message(CHAT_ID, msg, parse_mode='Markdown')
                
                await asyncio.sleep(random.uniform(5, 7)) # ইয়াহু প্রোটেকশন
            await asyncio.sleep(60)
        await asyncio.sleep(1)

if __name__ == "__main__":
    Thread(target=run_flask, daemon=True).start()
    asyncio.run(monitor_market())