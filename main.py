import yfinance as yf
import pandas as pd
import asyncio
import os
from telegram import Bot
from flask import Flask
from threading import Thread
from datetime import datetime, timedelta

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

# প্রতিটি পেয়ারের নিজস্ব স্মার্ট লজিক
def analyze_pair(df):
    close = df['Close']
    ema = close.ewm(span=50, adjust=False).mean() # ট্রেন্ডের জন্য
    atr = (df['High'] - df['Low']).rolling(window=14).mean() # অস্থিরতা মাপার জন্য
    rsi = 100 - (100 / (1 + close.diff().clip(lower=0).rolling(14).mean() / (-close.diff().clip(upper=0).rolling(14).mean())))
    
    curr = close.iloc[-1]
    # লজিক: ট্রেন্ডের দিকে ট্রেড করা এবং অস্থিরতা কম থাকলে এন্ট্রি নেওয়া
    if curr > ema.iloc[-1] and rsi.iloc[-1] < 40 and atr.iloc[-1] < (curr * 0.002):
        return "BUY"
    elif curr < ema.iloc[-1] and rsi.iloc[-1] > 60 and atr.iloc[-1] < (curr * 0.002):
        return "SELL"
    return None

async def get_signals():
    all_signals = []
    try:
        # Rate Limit এড়াতে ডাউনলোড মেথড অপ্টিমাইজড
        data = yf.download(PAIRS, period='5d', interval='5m', group_by='ticker', progress=False)
        for symbol in PAIRS:
            df = data[symbol]
            if df.empty or len(df) < 50: continue
            
            signal = analyze_pair(df)
            if signal:
                name = symbol.replace('=X', '')
                msg = (f"💎 **{signal} SIGNAL**\n━━━━━━━━━━━━━━\n"
                       f"🔹 Pair: {name}\n🔹 Price: `{df['Close'].iloc[-1]:.5f}`\n"
                       f"🔹 Time: {datetime.now().strftime('%H:%M:%S')}\n━━━━━━━━━━━━━━")
                all_signals.append(msg)
    except Exception as e:
        print(f"Error: {e}")
    return all_signals

async def monitor():
    while True:
        # প্রতি ৫ মিনিট অন্তর চেক
        if datetime.now().minute % 5 == 0:
            sigs = await get_signals()
            for msg in sigs:
                await bot.send_message(CHAT_ID, msg, parse_mode='Markdown')
            await asyncio.sleep(60)
        await asyncio.sleep(10)

if __name__ == "__main__":
    Thread(target=run_server, daemon=True).start()
    asyncio.run(monitor())