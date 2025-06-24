import requests
import pandas as pd
from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import datetime
import logging

# === Config ===
BOT_TOKEN = "7629957008:AAFfh2fUcphlVbkJ5tgiKEQr9uQdNs3PNjE"
CHAT_ID = "5610535083"
COINS = {"bitcoin": "BTC", "ethereum": "ETH"}

# === Indicator Calculations ===
def calculate_indicators(df):
    df['MA20'] = df['close'].rolling(window=20).mean()
    df['STD'] = df['close'].rolling(window=20).std()
    df['Upper'] = df['MA20'] + 2 * df['STD']
    df['Lower'] = df['MA20'] - 2 * df['STD']
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    return df

# === Get OHLC Data from CoinGecko ===
def get_ohlc_data(coin_id):
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/ohlc?vs_currency=usd&days=1"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        return calculate_indicators(df)
    return None

# === Send Telegram Message ===
def send_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": text})

# === Check for Reversal ===
def check_and_alert():
    for coin_id, symbol in COINS.items():
        df = get_ohlc_data(coin_id)
        if df is not None and len(df) >= 21:
            rsi = df.iloc[-1]['RSI']
            close = df.iloc[-1]['close']
            upper = df.iloc[-1]['Upper']
            lower = df.iloc[-1]['Lower']

            if rsi < 30 and close < lower:
                send_message(f"🔁 Possible *UP Reversal* in {symbol}.\n💹 RSI: {rsi:.2f}, Price: {close:.2f} USD")
            elif rsi > 70 and close > upper:
                send_message(f"🔁 Possible *DOWN Reversal* in {symbol}.\n💹 RSI: {rsi:.2f}, Price: {close:.2f} USD")

# === Scheduler ===
scheduler = BlockingScheduler()
scheduler.add_job(check_and_alert, 'interval', minutes=1)

# === Start ===
if __name__ == "__main__":
    send_message("✅ Bot is live and monitoring BTC/ETH every 1 min.")
    scheduler.start()
