import yfinance as yf
import asyncio
import os
from telegram import Bot
from flask import Flask
from threading import Thread
from datetime import datetime

# --- CONFIGURATION ---
TELEGRAM_TOKEN = '8287022829:AAEJfSnbsAgnGqoFbNESwDMifQ9S5Gf9bJk'
CHAT_ID = '7995220028'
bot = Bot(token=TELEGRAM_TOKEN)
PAIRS = ["EURUSD=X", "GBPUSD=X", "USDJPY=X", "AUDUSD=X", "EURJPY=X", "GBPJPY=X", "USDCAD=X", "EURGBP=X", "AUDJPY=X", "NZDUSD=X", "GBPAUD=X", "EURAUD=X"]

# --- WEB SERVER (Render Port Binding) ---
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
        # Batch Request to Yahoo Finance
        data = yf.download(PAIRS, period='2d', interval='5m', group_by='ticker', progress=False)
        
        for symbol in PAIRS:
            df = data[symbol]
            if df.empty or len(df) < 20: continue
            
            close = df['Close']
            ma20 = close.rolling(20).mean().iloc[-1]
            curr = float(close.iloc[-1])
            name = symbol.replace('=X', '')
            
            # Logic: Bollinger-like Mean Reversion
            if curr < (ma20 * 0.998):
                all_signals.append(f"🟢 **{name}**: BUY @ `{curr:.5f}`")
            elif curr > (ma20 * 1.002):
                all_signals.append(f"🔴 **{name}**: SELL @ `{curr:.5f}`")
    except Exception as e:
        print(f"Error: {e}")
    return all_signals

async def monitor():
    while True:
        now = datetime.now()
        # প্রতি ৫ মিনিট অন্তর চেক
        if now.minute % 5 == 0 and now.second < 10:
            sigs = await get_signals()
            if sigs:
                msg = f"💎 **MARKET SIGNAL - {now.strftime('%H:%M')}**\n━━━━━━━━━━━━━━\n"
                await bot.send_message(CHAT_ID, msg + "\n".join(sigs[:5]), parse_mode='Markdown')
            await asyncio.sleep(60)
        await asyncio.sleep(10)

if __name__ == "__main__":
    Thread(target=run_server, daemon=True).start()
    asyncio.run(monitor())