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
PAIRS = ["EURUSD=X", "GBPUSD=X", "USDJPY=X", "AUDUSD=X", "EURJPY=X", "GBPJPY=X", "USDCAD=X", "EURGBP=X", "AUDJPY=X", "NZDUSD=X", "GBPAUD=X", "EURAUD=X"]

# বাংলাদেশ টাইম জোন (UTC+6)
BD_TZ = timezone(timedelta(hours=6))

# Render এর পোর্ট বাইন্ডিং এরর ফিক্স করার জন্য ফ্লাস্ক সার্ভার
app = Flask(__name__)
@app.route('/')
def home(): return "TrixWin Bot is Online"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

async def get_signals():
    all_signals = []
    for symbol in PAIRS:
        try:
            # Rate Limit এড়াতে প্রতি রিকোয়েস্টের মাঝে ২ সেকেন্ড বিরতি
            await asyncio.sleep(2)
            
            # ডেটা ডাউনলোড (টাইমআউট হ্যান্ডলিং সহ)
            data = await asyncio.to_thread(yf.download, symbol, interval='5m', period='1d', progress=False)
            
            if data is None or len(data) < 30: continue
            
            # --- ANALYSIS LOGIC ---
            close = data['Close'].squeeze()
            high = data['High'].squeeze()
            low = data['Low'].squeeze()
            
            # Bollinger Bands
            ma20 = close.rolling(window=20).mean()
            std20 = close.rolling(window=20).std()
            upper_bb = ma20 + (std20 * 2)
            lower_bb = ma20 - (std20 * 2)
            
            # RSI
            delta = close.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rsi = 100 - (100 / (1 + (gain / loss))).iloc[-1]
            
            curr_price = float(close.iloc[-1])
            pair_name = symbol.replace('=X', '')

            # সিগন্যাল লজিক (Bollinger + RSI)
            if curr_price <= lower_bb.iloc[-1] and rsi < 35:
                all_signals.append({'pair': pair_name, 'dir': '🟢 CALL', 'price': curr_price})
            elif curr_price >= upper_bb.iloc[-1] and rsi > 65:
                all_signals.append({'pair': pair_name, 'dir': '🔴 PUT', 'price': curr_price})
                
        except Exception as e:
            print(f"Error on {symbol}: {e}")
            continue
            
    return all_signals

async def monitor_market():
    print("🚀 Monitoring started...")
    while True:
        now = datetime.datetime.now(BD_TZ)
        
        # প্রতি ৫ মিনিটের ক্যান্ডেল শেষ হওয়ার ৫ সেকেন্ড আগে (উদা: ১০:৫৪:৫৫)
        if now.minute % 5 == 4 and now.second >= 55:
            signals = await get_signals()
            
            if signals:
                entry_time = now.strftime('%H:%M:%S')
                expiry_time = (now + timedelta(minutes=5)).strftime('%H:%M:%S')
                
                msg = f"💎 **TOP SIGNALS FOUND**\n"
                msg += f"Entry: `{entry_time}` | Exp: `{expiry_time}`\n"
                msg += "━━━━━━━━━━━━━━\n"
                
                for s in signals:
                    msg += f"🔹 {s['pair']} → {s['dir']}\n   Price: `{s['price']:.5f}`\n\n"
                
                await bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode='Markdown')
            
            # ১ মিনিট অপেক্ষা যাতে একই ক্যান্ডেলে বারবার মেসেজ না যায়
            await asyncio.sleep(60)
            
        await asyncio.sleep(1)

if __name__ == "__main__":
    # ফ্লাস্ক সার্ভার ব্যাকগ্রাউন্ডে চালু করা
    Thread(target=run_flask, daemon=True).start()
    # মেইন মনিটর লুপ চালু করা
    asyncio.run(monitor_market())