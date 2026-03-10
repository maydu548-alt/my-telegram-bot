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
PAIRS = ["EURUSD=X", "GBPUSD=X", "USDJPY=X", "AUDUSD=X", "EURJPY=X", "GBPJPY=X", "USDCAD=X", "EURGBP=X", "AUDJPY=X", "NZDUSD=X", "GBPAUD=X", "EURAUD=X"]

async def get_top_signals():
    all_signals = []
    
    for symbol in PAIRS:
        try:
            # Rate limit এড়াতে ছোট বিরতি
            await asyncio.sleep(1)
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

            win_rate = 70 
            if rsi < 30 or rsi > 70: win_rate += 10
            if stoch_k < 20 or stoch_k > 80: win_rate += 10

            if current_price <= lower_bb.iloc[-1] * 1.0002 and rsi < 40 and stoch_k < 35:
                all_signals.append({'pair': pair_name, 'yf': symbol, 'dir': 'CALL', 'acc': win_rate, 'price': current_price})
            elif current_price >= upper_bb.iloc[-1] * 0.9998 and rsi > 60 and stoch_k > 65:
                all_signals.append({'pair': pair_name, 'yf': symbol, 'dir': 'PUT', 'acc': win_rate, 'price': current_price})
        except: continue
    
    all_signals.sort(key=lambda x: x['acc'], reverse=True)
    return all_signals[:3]

async def main():
    print("🚀 TrixWin Ultimate v4.0 is Online!")
    while True:
        now = datetime.datetime.now()
        # ৫ মিনিট পর পর ৫ সেকেন্ড আগে সিগন্যাল পাওয়ার জন্য
        if now.minute % 5 == 4 and now.second >= 55:
            top_signals = await get_top_signals()
            if top_signals:
                entry_time = datetime.datetime.now().strftime('%H:%M:%S')
                close_time = (datetime.datetime.now() + datetime.timedelta(minutes=5)).strftime('%H:%M:%S')
                
                msg = f"💎 **MARKET SIGNAL**\nEntry Time: `{entry_time}`\nExp. Close: `{close_time}`\n━━━━━━━━━━━━━━\n"
                for s in top_signals:
                    msg += f"🔹 {s['pair']} → {s['dir']}\n   Price: `{s['price']:.5f}` | Win Prob: `{s['acc']}%`\n\n"
                
                await bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode='Markdown')
            
            await asyncio.sleep(60) # পরবর্তী ৫ মিনিটের জন্য ওয়েট
        await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())