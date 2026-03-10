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
# পেয়ার সংখ্যা কিছুটা কমিয়ে রাখা ভালো যাতে ব্লক না হয়
PAIRS = ["EURUSD=X", "GBPUSD=X", "USDJPY=X", "AUDUSD=X", "EURJPY=X", "GBPJPY=X", "USDCAD=X", "EURGBP=X", "AUDJPY=X"]

BD_TZ = timezone(timedelta(hours=6))

# Render Port Binding Fix
app = Flask(__name__)
@app.route('/')
def home(): return "TrixWin Bot is Running"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

async def get_signals():
    all_signals = []
    print(f"[{datetime.datetime.now(BD_TZ).strftime('%H:%M:%S')}] Scanning pairs...")
    
    for symbol in PAIRS:
        try:
            # Rate limit এড়াতে ৩ সেকেন্ড বিরতি
            await asyncio.sleep(3) 
            
            # ডেটা ডাউনলোড (টাইমআউট ১০ সেকেন্ড)
            data = await asyncio.to_thread(yf.download, symbol, interval='5m', period='1d', progress=False, timeout=10)
            
            if data is None or data.empty or len(data) < 25:
                continue
            
            close = data['Close'].squeeze()
            ma20 = close.rolling(window=20).mean()
            std20 = close.rolling(window=20).std()
            
            # RSI Calculation
            delta = close.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rsi = 100 - (100 / (1 + (gain / loss))).iloc[-1]
            
            curr_price = float(close.iloc[-1])
            pair_name = symbol.replace('=X', '')

            # আগের লজিক (Bollinger Bands + RSI)
            if curr_price <= (ma20.iloc[-1] - (std20.iloc[-1] * 2)) and rsi < 35:
                all_signals.append({'pair': pair_name, 'dir': '🟢 CALL', 'price': curr_price})
            elif curr_price >= (ma20.iloc[-1] + (std20.iloc[-1] * 2)) and rsi > 65:
                all_signals.append({'pair': pair_name, 'dir': '🔴 PUT', 'price': curr_price})
                
        except Exception as e:
            if "Rate limited" in str(e) or "429" in str(e):
                print("⚠️ Yahoo Blocked! Waiting 5 minutes...")
                await asyncio.sleep(300) 
            continue
            
    return all_signals

async def monitor_market():
    print("🚀 Bot is Online with Error Protection!")
    while True:
        now = datetime.datetime.now(BD_TZ)
        
        # ৫ মিনিট ক্যান্ডেল শেষ হওয়ার ১০ সেকেন্ড আগে স্ক্যান শুরু
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
                        f"🏁 Exp: `{expiry_time}`\n"
                        f"━━━━━━━━━━━━━━"
                    )
                    await bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode='Markdown')
                    await asyncio.sleep(1) # টেলিগ্রাম ফ্ল্যাড প্রোটেকশন
            
            await asyncio.sleep(60) # পরের মিনিটের জন্য অপেক্ষা
        await asyncio.sleep(1)

if __name__ == "__main__":
    # ওয়েব সার্ভার চালু
    Thread(target=run_flask, daemon=True).start()
    # মনিটর লুপ চালু
    asyncio.run(monitor_market())