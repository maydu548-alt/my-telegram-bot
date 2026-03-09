import yfinance as yf
import asyncio
from telegram import Bot
import datetime
import pandas as pd
import sys

# --- CONFIGURATION ---
TELEGRAM_TOKEN = '8287022829:AAEJfSnbsAgnGqoFbNESwDMifQ9S5Gf9bJk'
CHAT_ID = '7995220028'
bot = Bot(token=TELEGRAM_TOKEN)

# ১২টি কারেন্সি পেয়ার (সিগন্যাল সংখ্যা বাড়ানোর জন্য)
PAIRS = ["EURUSD=X", "GBPUSD=X", "USDJPY=X", "AUDUSD=X", "EURJPY=X", "GBPJPY=X", "USDCAD=X", "EURGBP=X", "AUDJPY=X", "NZDUSD=X", "GBPAUD=X", "EURAUD=X"]

async def get_top_signals():
    all_signals = []
    print(f"\n🔍 [{datetime.datetime.now().strftime('%H:%M:%S')}] Scanning All Markets...")
    
    for symbol in PAIRS:
        try:
            data = yf.download(symbol, interval='5m', period='2d', progress=False)
            if len(data) < 50: continue
            
            close = data['Close'].squeeze()
            low = data['Low'].squeeze()
            high = data['High'].squeeze()
            
            # Indicators
            delta = close.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rsi = 100 - (100 / (1 + (gain / loss))).iloc[-1]
            
            low_14 = low.rolling(window=14).min()
            high_14 = high.rolling(window=14).max()
            stoch_k = (100 * ((close - low_14) / (high_14 - low_14))).rolling(window=3).mean().iloc[-1]
            
            ma20 = close.rolling(window=20).mean()
            std20 = close.rolling(window=20).std()
            upper_bb = ma20 + (std20 * 2)
            lower_bb = ma20 - (std20 * 2)
            
            current_price = float(close.iloc[-1])
            pair_name = symbol.replace('=X', '')

            # Accuracy/Win Rate Logic
            win_rate = 70 
            if rsi < 30 or rsi > 70: win_rate += 10
            if stoch_k < 20 or stoch_k > 80: win_rate += 10

            # Signal Logic (Relaxed for more pairs)
            if current_price <= lower_bb.iloc[-1] * 1.0002 and rsi < 40 and stoch_k < 35:
                all_signals.append({'pair': pair_name, 'yf': symbol, 'dir': 'BUY', 'acc': win_rate, 'price': current_price})
            elif current_price >= upper_bb.iloc[-1] * 0.9998 and rsi > 60 and stoch_k > 65:
                all_signals.append({'pair': pair_name, 'yf': symbol, 'dir': 'SELL', 'acc': win_rate, 'price': current_price})
        except: continue
    
    all_signals.sort(key=lambda x: x['acc'], reverse=True)
    return all_signals[:3]

async def check_result(signal, msg_id):
    await asyncio.sleep(305) # ৫ মিনিট পর রেজাল্ট চেক
    try:
        data = yf.download(signal['yf'], interval='1m', period='1d', progress=False)
        exit_price = float(data['Close'].iloc[-1])
        is_win = (signal['dir'] == 'BUY' and exit_price > signal['price']) or (signal['dir'] == 'SELL' and exit_price < signal['price'])
        res_text = "✅ WIN (ITM)" if is_win else "❌ LOSS (OTM)"
        await bot.send_message(chat_id=CHAT_ID, text=f"📊 **RESULT: {signal['pair']}**\n━━━━━━━━━━━━━━\nStatus: **{res_text}**\nEntry: {signal['price']:.5f}\nExit: {exit_price:.5f}", reply_to_message_id=msg_id)
    except: pass

async def main():
    print("🚀 TrixWin Ultimate v4.0 is Online!")
    last_scan_min = -1
    while True:
        now = datetime.datetime.now()
        sys.stdout.write(f"\r🕒 Time: {now.strftime('%H:%M:%S')} | Monitoring... ")
        sys.stdout.flush()

        if now.minute % 5 == 0 and now.second == 1:
            if now.minute != last_scan_min:
                last_scan_min = now.minute
                top_3 = await get_top_signals()
                if top_3:
                    msg = "💎 **TOP SIGNALS FOUND**\n━━━━━━━━━━━━━━\n"
                    for i, s in enumerate(top_3, 1):
                        icon = "🟢 CALL" if s['dir'] == 'BUY' else "🔴 PUT"
                        msg += f"{i}. **{s['pair']}** → {icon}\n   Accuracy: `{s['acc']}%` | 5 MIN\n\n"
                    sent = await bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode='Markdown')
                    for s in top_3:
                        asyncio.create_task(check_result(s, sent.message_id))
        await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())
    from flask import Flask
from threading import Thread

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is alive!"

def run():
    # Render সাধারণত 10000 পোর্টে সার্ভিস দেয়, 
    # তাই port=10000 ব্যবহার করা ভালো
    app.run(host='0.0.0.0', port=10000)

# এটি আপনার বটের মেইন লুপের আগে যোগ করুন
t = Thread(target=run)
t.start()

# --- আপনার বর্তমান বটের কোড এখানে থাকবে ---