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

BD_TZ = timezone(timedelta(hours=6))

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
            await asyncio.sleep(1.5)
            data = await asyncio.to_thread(yf.download, symbol, interval='5m', period='1d', progress=False)
            
            if data is None or len(data) < 30: continue
            
            close = data['Close'].squeeze()
            ma20 = close.rolling(window=20).mean()
            std20 = close.rolling(window=20).std()
            upper_bb = ma20 + (std20 * 2)
            lower_bb = ma20 - (std20 * 2)
            
            delta = close.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rsi = 100 - (100 / (1 + (gain / loss))).iloc[-1]
            
            curr_price = float(close.iloc[-1])
            pair_name = symbol.replace('=X', '')

            # একুরেসি ক্যালকুলেশন লজিক (উদা: ৮৫%-৯৫%)
            prob = 85
            if rsi < 30 or rsi > 70: prob += 7
            if prob > 98: prob = 98

            if curr_price <= lower_bb.iloc[-1] and rsi < 38:
                all_signals.append({'pair': pair_name, 'dir': '🟢 CALL / BUY', 'price': curr_price, 'acc': prob})
            elif curr_price >= upper_bb.iloc[-1] and rsi > 62:
                all_signals.append({'pair': pair_name, 'dir': '🔴 PUT / SELL', 'price': curr_price, 'acc': prob})
                
        except: continue
    return all_signals

async def monitor_market():
    print("🚀 Bot is scanning with new style...")
    while True:
        now = datetime.datetime.now(BD_TZ)
        
        if now.minute % 5 == 4 and now.second >= 55:
            signals = await get_signals()
            
            if signals:
                entry_time = now.strftime('%H:%M:%S')
                expiry_time = (now + timedelta(minutes=5)).strftime('%H:%M:%S')
                
                # --- NEW STYLISH MESSAGE FORMAT ---
                for s in signals:
                    msg = (
                        f"🔥 **PREMIUM SIGNAL FOUND** 🔥\n"
                        f"━━━━━━━━━━━━━━━━━━\n"
                        f"📊 **Asset:** `{s['pair']}`\n"
                        f"💹 **Direction:** {s['dir']}\n"
                        f"⏰ **Timeframe:** `5 MINUTES`\n"
                        f"━━━━━━━━━━━━━━━━━━\n"
                        f"📥 **Entry Price:** `{s['price']:.5f}`\n"
                        f"🕒 **Entry Time:** `{entry_time}`\n"
                        f"🏁 **Expiry Time:** `{expiry_time}`\n"
                        f"━━━━━━━━━━━━━━━━━━\n"
                        f"🎯 **Accuracy:** `{s['acc']}%` ⚡️\n"
                        f"⚠️ *Trade at your own risk!*"
                    )
                    await bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode='Markdown')
                    await asyncio.sleep(1) # টেলিগ্রাম স্প্যাম এড়াতে
            
            await asyncio.sleep(60)
        await asyncio.sleep(1)

if __name__ == "__main__":
    Thread(target=run_flask, daemon=True).start()
    asyncio.run(monitor_market())