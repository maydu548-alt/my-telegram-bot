import yfinance as yf
import asyncio
import os
from telegram import Bot
from flask import Flask
from threading import Thread
import datetime
from datetime import timezone, timedelta

# --- CONFIGURATION ---
TOKEN = '8287022829:AAEJfSnbsAgnGqoFbNESwDMifQ9S5Gf9bJk'
CHAT_ID = '7995220028'
bot = Bot(token=TOKEN)
# পেয়ারের সংখ্যা কমিয়ে ৪-৫টি করুন যাতে রেট লিমিট না হয়
PAIRS = ["EURUSD=X", "GBPUSD=X", "USDJPY=X", "AUDUSD=X", "EURJPY=X"]

BD_TZ = timezone(timedelta(hours=6))

app = Flask(__name__)
@app.route('/')
def home(): return "TrixWin Bot is Online"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

async def get_signals():
    all_signals = []
    print(f"--- Scanning started at {datetime.datetime.now(BD_TZ)} ---")
    
    for symbol in PAIRS:
        try:
            # খুব ধীরগতিতে রিকোয়েস্ট পাঠানো (৫ সেকেন্ড গ্যাপ)
            await asyncio.sleep(5) 
            
            # ডেটা ডাউনলোড
            data = await asyncio.to_thread(yf.download, symbol, interval='5m', period='1d', progress=False, timeout=10)
            
            if data is None or data.empty or len(data) < 20:
                continue
            
            close = data['Close'].squeeze()
            ma20 = close.rolling(window=20).mean()
            std20 = close.rolling(window=20).std()
            
            # RSI Calculation
            delta = close.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rsi = 100 - (100 / (1 + (gain / loss))).iloc[-1]
            
            curr = float(close.iloc[-1])
            pair_name = symbol.replace('=X', '')

            if curr <= (ma20.iloc[-1] - (std20.iloc[-1] * 2)) and rsi < 35:
                all_signals.append({'pair': pair_name, 'dir': '🟢 CALL', 'price': curr})
            elif curr >= (ma20.iloc[-1] + (std20.iloc[-1] * 2)) and rsi > 65:
                all_signals.append({'pair': pair_name, 'dir': '🔴 PUT', 'price': curr})
                
        except Exception as e:
            if "Rate limited" in str(e):
                print("⚠️ Rate limit hit! Waiting 3 minutes...")
                await asyncio.sleep(180) # ৩ মিনিট টোটাল বিরতি
            continue
            
    return all_signals

async def monitor_market():
    while True:
        now = datetime.datetime.now(BD_TZ)
        # ৫ মিনিটের ক্যান্ডেল শেষ হওয়ার ১০ সেকেন্ড আগে স্ক্যান শুরু
        if now.minute % 5 == 4 and now.second >= 50:
            signals = await get_signals()
            
            if signals:
                entry_time = now.strftime('%H:%M:%S')
                expiry_time = (now + timedelta(minutes=5)).strftime('%H:%M:%S')
                
                for s in signals:
                    msg = (
                        f"🔥 **PREMIUM SIGNAL** 🔥\n"
                        f"━━━━━━━━━━━━━━\n"
                        f"📊 Asset: `{s['pair']}`\n"
                        f"💹 Direction: {s['dir']}\n"
                        f"📥 Entry: `{s['price']:.5f}`\n"
                        f"🕒 Time: `{entry_time}`\n"
                        f"━━━━━━━━━━━━━━"
                    )
                    await bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode='Markdown')
            
            await asyncio.sleep(60) # পরের মিনিটের জন্য ওয়েট
        await asyncio.sleep(1)

if __name__ == "__main__":
    Thread(target=run_flask, daemon=True).start()
    asyncio.run(monitor_market())