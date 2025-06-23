from telethon import TelegramClient, events
from telethon.sessions import StringSession
import os
from keep_alive import keep_alive
from datetime import datetime, timedelta
import asyncio
import requests
import random
import pytz
from PIL import Image, ImageDraw, ImageFont

# Set Nigeria timezone
nigeria_tz = pytz.timezone('Africa/Lagos')

# Load credentials from environment variables
api_id = int(os.environ['API_ID'])
api_hash = os.environ['API_HASH']
session_string = os.environ['SESSION_STRING']

# Initialize Telegram client
client = TelegramClient(StringSession(session_string), api_id, api_hash)

# Channels to monitor
source_channels = [
    'firepipsignals',
    'Forex_Top_Premium_Signals',
    'forexsignals01_trade',
    'forexgdp0',
    'Goldforexsignalfx11',
    'habbyforex',
    'kojoforextrades',
    'HONG-SOCIETY'
]

# Your target channel
target_channel = '@DonwiseVault'

# Signal detection keywords
keywords = ['buy', 'sell', 'tp', 'sl', 'xauusd', 'nas100', 'us30', 'eurusd', 'gbpusd', 'gold', 'gbpjpy']

# Blocked phrases
blocked_phrases = [
    'weekly performance result', 'see you on monday', 'celebrate', 'instagram.com',
    'go check and comment to win', 'By @RealDonwise 🔥 | Donwise Copytrade Vault',
    'tp1', 'tp2', 'running', 'easy hit', 'smassshedd', 'closed another',
    'set breakeven', 'tp 1', 'tp 2', 'tp3'
]

# Signature for forwarded messages
signature = "\n\nBy @RealDonwise\nDonwise Copytrade Vault"

# Motivational quotes
motivational_quotes = [
    "Start your day with clarity and conviction. The pips you seek are on the other side of fear. Take the shot. 🧠📈",
    "Every pip is a step closer to freedom. Trade smart, stay disciplined, and keep building your edge. 💪📉",
    "The market doesn’t care about excuses—only execution. Stick to the plan and grow your account. 🚀📈",
    "Let your strategy speak louder than your emotions today. Risk little. Win big. 👊🔥",
    "There’s no growth in the comfort zone. Make smart moves today. Don’t chase—calculate. 📉📈",
    "No one became great by guessing. Analyze. Execute. Elevate. Today’s another shot. 🎯📈",
    "The charts don’t lie. Your discipline defines your destiny. Let’s get to work. 📈🔐"
]

# Image links for morning intro
motivational_images = [
    'https://i.ibb.co/g7Zwqft/motivation1.jpg',
    'https://i.ibb.co/LNRXJjJ/motivation2.jpg',
    'https://i.ibb.co/0ncsCK5/motivation3.jpg',
    'https://i.ibb.co/QJQPDKT/motivation4.jpg',
    'https://i.ibb.co/MfGmMLy/motivation5.jpg'
]

forwarded_today = set()
daily_count = 0
last_reset_date = datetime.now(nigeria_tz).date()
morning_posted = False
signal_log = []

# Fetch live prices from Yahoo Finance
async def get_price(pair):
    yahoo_map = {
        'xauusd': 'XAUUSD=X',
        'nas100': '^NDX',
        'eurusd': 'EURUSD=X',
        'gbpusd': 'GBPUSD=X',
        'us30': '^DJI'
    }
    yf_symbol = yahoo_map.get(pair.lower())
    if not yf_symbol:
        return None
    try:
        r = requests.get(f'https://query1.finance.yahoo.com/v7/finance/quote?symbols={yf_symbol}')
        data = r.json()
        return float(data['quoteResponse']['result'][0]['regularMarketPrice'])
    except:
        return None

# Morning welcome message
async def morning_intro():
    global morning_posted
    if not morning_posted:
        quote = random.choice(motivational_quotes)
        image = random.choice(motivational_images)
        await client.send_file(target_channel, image, caption=f"🌄 Good morning traders!\n\n{quote}\n\n— Donwise")
        await asyncio.sleep(2)
        await client.send_message(target_channel, "📢 Are you ready for today's signal of the day? Stay sharp. First one drops soon! 🚀")
        morning_posted = True

# Forward valid signals only
@client.on(events.NewMessage(chats=source_channels))
async def forward_signal(event):
    global daily_count, last_reset_date, morning_posted

    now = datetime.now(nigeria_tz).date()
    if now != last_reset_date:
        daily_count = 0
        forwarded_today.clear()
        morning_posted = False
        last_reset_date = now
        signal_log.clear()

    if not morning_posted:
        await morning_intro()

    msg_id = (event.chat_id, event.message.id)
    if msg_id in forwarded_today or daily_count >= 7:
        return

    text = event.raw_text.lower()
    if any(blocked in text for blocked in blocked_phrases):
        return
    if event.message.media:
        return

    if any(k in text for k in keywords):
        action = 'buy' if 'buy' in text else 'sell' if 'sell' in text else None
        pair = next((k for k in ['xauusd', 'nas100', 'eurusd', 'gbpusd', 'us30'] if k in text), None)
        tp = sl = None
        for line in text.splitlines():
            if 'tp' in line:
                tp = ''.join([c for c in line if c.isdigit() or c == '.'])
            if 'sl' in line:
                sl = ''.join([c for c in line if c.isdigit() or c == '.'])

        if pair and action and tp and sl:
            try:
                signal_log.append({
                    'pair': pair,
                    'action': action,
                    'tp': float(tp),
                    'sl': float(sl)
                })
            except:
                pass

        await client.send_message(target_channel, event.message.message + signature)
        forwarded_today.add(msg_id)
        daily_count += 1
        print(f"✅ Signal Forwarded | {daily_count}/7 for {now}")

# Weekly summary generator
async def post_weekly_summary():
    wins = losses = pending = 0

    for signal in signal_log:
        current = await get_price(signal['pair'])
        if current is None:
            pending += 1
            continue
        if signal['action'] == 'buy':
            if current >= signal['tp']:
                wins += 1
            elif current <= signal['sl']:
                losses += 1
            else:
                pending += 1
        elif signal['action'] == 'sell':
            if current <= signal['tp']:
                wins += 1
            elif current >= signal['sl']:
                losses += 1
            else:
                pending += 1

    total = wins + losses + pending
    win_rate = round((wins / (wins + losses)) * 100, 1) if wins + losses > 0 else 0
    text_summary = f"📊 Weekly Summary Report\nDate: {datetime.now(nigeria_tz).strftime('%A %d %B %Y')}\n\nTotal Signals: {total}\nTotal Wins: {wins} ✅\nTotal Losses: {losses} ❌\nPending: {pending} ⏳\n\n🔥 Win Rate: {win_rate}%\n\n@RealDonwise | Donwise Copytrade Vault"

    # Create chart image
    img = Image.new('RGB', (720, 500), color='white')
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
    except:
        font = ImageFont.load_default()

    draw.text((30, 30), "📈 Weekly Signal Accuracy", fill='black', font=font)
    draw.text((30, 100), text_summary, fill='black', font=font)
    draw.rectangle([(0, 460), (720, 500)], fill='lightgray')
    draw.text((20, 470), "@RealDonwise", fill='black', font=font)

    img.save("summary.png")
    await client.send_file(target_channel, "summary.png", caption=text_summary)
    os.remove("summary.png")

# Schedule weekly summary every Saturday at 9 AM
def schedule_weekly_summary():
    async def job():
        while True:
            now = datetime.now(nigeria_tz)
            if now.weekday() == 5 and now.hour == 9 and now.minute == 0:
                await post_weekly_summary()
                await asyncio.sleep(60)
            await asyncio.sleep(30)
    client.loop.create_task(job())

# Keep-alive & run
keep_alive()
schedule_weekly_summary()
client.start()
client.run_until_disconnected()
          
