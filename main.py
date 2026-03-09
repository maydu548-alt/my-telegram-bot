import yfinance as yf
import asyncio
import os
from telegram import Bot
from flask import Flask
from threading import Thread
from datetime import datetime, timedelta

# --- CONFIGURATION ---
TOKEN = '8287022829:AAEJfSnbsAgnGqoFbNESwDMifQ9S5Gf9bJk'
CHAT_ID = '7995220028'
bot = Bot(token=TOKEN)
PAIRS = ["EURUSD=X", "GBPUSD=X", "USDJPY=X", "AUDUSD=X", "EURJPY=X", "GBPJPY=X", "USDCAD=X", "EURGBP=X", "AUDJPY=X", "NZDUSD=X", "GBPAUD=X", "EURAUD=X"]

app = Flask(__name__)
@app.route('/')
def home(): return "Bot is Online"

def run_server():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

async def get_signals():
    all_signals = []
    try:
        # Batch Request to Yahoo Finance
        data = yf.download(PAIRS, period='2d', interval='5m', group_by='ticker', progress=False)
        
        for symbol in PAIRS:
            df = data[symbol]
            if df.empty or len(df) < 20: continue
            
            close = df['Close']
            ma20 = close.rolling(20).mean().iloc[-1]
            curr = float(close.iloc[-1])
            name = symbol.replace('=X', '')
            
            entry_time = datetime.now().strftime('%H:%M:%S')
            close_time = (datetime.now() + timedelta(minutes=5)).strftime('%H:%M:%S')
            
            # Logic: Mean Reversion
            if curr < (ma20 * 0.998):
                msg = (f"💎 **MARKET SIGNAL**\n━━━━━━━━━━━━━━\n"
                       f"🔹 Pair: {name}\n🔹 Type: 🟢 BUY\n🔹 Timeframe: 5m\n"
                       f"🔹 Entry Price: `{curr:.5f}`\n🔹 Entry Time: `{entry_time}`\n"
                       f"🔹 Exp. Close: `{close_time}`\n━━━━━━━━━━━━━━")
                all_signals.append(msg)
            elif curr > (ma20 * 1.002):
                msg = (f"💎 **MARKET SIGNAL**\n━━━━━━━━━━━━━━\n"
                       f"🔹 Pair: {name}\n🔹 Type: 🔴 SELL\n🔹 Timeframe: 5m\n"
                       f"🔹 Entry Price: `{curr:.5f}`\n🔹 Entry Time: `{entry_time}`\n"
                       f"🔹 Exp. Close: `{close_time}`\n━━━━━━━━━━━━━━")
                all_signals.append(msg)
    except Exception as e:
        print(f"Error: {e}")
    return all_signals

async def monitor():
    while True:
        # ৫ মিনিট অন্তর চেক
        if datetime.now().minute % 5 == 0:
            sigs = await get_signals()
            for msg in sigs:
                await bot.send_message(CHAT_ID, msg, parse_mode='Markdown')
            await asyncio.sleep(60)
        await asyncio.sleep(10)

if __name__ == "__main__":
    Thread(target=run_server, daemon=True).start()
    asyncio.run(monitor())