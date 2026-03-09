import yfinance as yf
import pandas as pd
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

def get_indicators(df):
    close = df['Close']
    ema200 = close.ewm(span=200, adjust=False).mean()
    delta = close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return ema200, rsi

async def get_signals():
    all_signals = []
    try:
        # Batch Request: ১টি রিকোয়েস্টে সব পেয়ার
        data = yf.download(PAIRS, period='5d', interval='5m', group_by='ticker', progress=False)
        for symbol in PAIRS:
            df = data[symbol]
            if df.empty or len(df) < 200: continue
            
            ema200, rsi = get_indicators(df)
            curr = float(df['Close'].iloc[-1])
            name = symbol.replace('=X', '')
            
            # Win Chance (Probability Logic)
            score = 65
            if abs(curr - ema200.iloc[-1]) > 0.001: score += 10
            if rsi.iloc[-1] < 25 or rsi.iloc[-1] > 75: score += 10
            win_chance = min(score, 95)
            
            entry_time = datetime.now().strftime('%H:%M:%S')
            close_time = (datetime.now() + timedelta(minutes=5)).strftime('%H:%M:%S')

            # Logic: Trend Filter (EMA200) + Momentum (RSI)
            if curr > ema200.iloc[-1] and rsi.iloc[-1] < 30:
                msg = (f"💎 **MARKET SIGNAL**\n━━━━━━━━━━━━━━\n"
                       f"🔹 Pair: {name}\n🔹 Type: 🟢 BUY\n🔹 Price: `{curr:.5f}`\n"
                       f"🔹 Win Chance: `{win_chance}%`\n🔹 RSI: `{rsi.iloc[-1]:.1f}`\n"
                       f"🔹 Entry: `{entry_time}` | Close: `{close_time}`\n━━━━━━━━━━━━━━")
                all_signals.append(msg)
            elif curr < ema200.iloc[-1] and rsi.iloc[-1] > 70:
                msg = (f"💎 **MARKET SIGNAL**\n━━━━━━━━━━━━━━\n"
                       f"🔹 Pair: {name}\n🔹 Type: 🔴 SELL\n🔹 Price: `{curr:.5f}`\n"
                       f"🔹 Win Chance: `{win_chance}%`\n🔹 RSI: `{rsi.iloc[-1]:.1f}`\n"
                       f"🔹 Entry: `{entry_time}` | Close: `{close_time}`\n━━━━━━━━━━━━━━")
                all_signals.append(msg)
    except Exception as e:
        print(f"Fetch Error: {e}")
    return all_signals

async def monitor():
    while True:
        if datetime.now().minute % 5 == 0:
            sigs = await get_signals()
            for msg in sigs:
                await bot.send_message(CHAT_ID, msg, parse_mode='Markdown')
            await asyncio.sleep(60)
        await asyncio.sleep(10)

if __name__ == "__main__":
    Thread(target=run_server, daemon=True).start()
    asyncio.run(monitor())