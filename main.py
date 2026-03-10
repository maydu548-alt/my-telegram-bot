import yfinance as yf
import asyncio
from telegram import Bot
import datetime
from datetime import timezone, timedelta
import sys

# --- CONFIGURATION ---
TELEGRAM_TOKEN = '8287022829:AAEJfSnbsAgnGqoFbNESwDMifQ9S5Gf9bJk'
CHAT_ID = '7995220028'
bot = Bot(token=TELEGRAM_TOKEN)
PAIRS = ["EURUSD=X", "GBPUSD=X", "USDJPY=X", "AUDUSD=X", "EURJPY=X", "GBPJPY=X", "USDCAD=X", "EURGBP=X", "AUDJPY=X", "NZDUSD=X", "GBPAUD=X", "EURAUD=X"]
BD_TZ = timezone(timedelta(hours=6))

# ডেটা ডাউনলোডের জন্য একটি সহজ ফাংশন
async def get_price_data(symbol):
    try:
        # Ticker ব্যবহার করা Rate Limit এড়াতে কার্যকর
        ticker = yf.Ticker(symbol)
        # period কমিয়ে আনা হয়েছে যেন দ্রুত ডেটা আসে
        data = ticker.history(period="1d", interval="5m")
        return data
    except Exception:
        return None

async def get_signals():
    all_signals = []
    for symbol in PAIRS:
        data = await get_price_data(symbol)
        if data is None or len(data) < 20: continue
        
        # ইন্ডিকেটর ক্যালকুলেশন
        close = data['Close'].squeeze()
        ma20 = close.rolling(window=20).mean()
        std20 = close.rolling(window=20).std()
        curr = float(close.iloc[-1])
        
        # সিগন্যাল লজিক
        if curr <= (ma20.iloc[-1] - (std20.iloc[-1] * 2)):
            all_signals.append({'pair': symbol.replace('=X', ''), 'dir': '🟢 CALL', 'price': curr})
        elif curr >= (ma20.iloc[-1] + (std20.iloc[-1] * 2)):
            all_signals.append({'pair': symbol.replace('=X', ''), 'dir': '🔴 PUT', 'price': curr})
        
        # প্রতি পেয়ারের মাঝে বিরতি (Rate Limit এড়াতে)
        await asyncio.sleep(2) 
    return all_signals

async def main():
    print("🚀 TrixWin Stable v5.1 is Online!")
    while True:
        now = datetime.datetime.now(BD_TZ)
        # ৫ মিনিট ক্যান্ডেল ক্লোজের ৫ সেকেন্ড আগে সিগন্যাল
        if now.minute % 5 == 4 and now.second >= 55:
            sigs = await get_signals()
            if sigs:
                entry = now.strftime('%H:%M:%S')
                close_time = (now + timedelta(minutes=5)).strftime('%H:%M:%S')
                msg = f"💎 **MARKET SIGNAL**\nEntry: `{entry}` | Exp: `{close_time}`\n━━━━━━━━━━━━━━\n"
                for s in sigs:
                    msg += f"🔹 {s['pair']} → {s['dir']}\n   Price: `{s['price']:.5f}`\n\n"
                await bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode='Markdown')
            await asyncio.sleep(60)
        await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())