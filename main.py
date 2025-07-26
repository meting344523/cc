import asyncio
import pandas as pd
from ta.volatility import AverageTrueRange
from ta.trend import MACD
from ta.momentum import RSIIndicator
import requests
from bs4 import BeautifulSoup
from textblob import TextBlob
import akshare as ak
import json


async def fetch_crypto_data():
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": "cny",
        "order": "market_cap_desc",
        "per_page": 300,
        "page": 1,
        "sparkline": False
    }
    r = requests.get(url, params=params)
    data = r.json()
    if isinstance(data, list):
        print("Crypto data sample:", data[:3])
    else:
        print("Crypto API返回异常:", data)
        return pd.DataFrame()  # 返回空DataFrame，避免后续出错

    df = pd.DataFrame(data)
    needed_cols = ['id', 'symbol', 'name', 'current_price', 'high_24h', 'low_24h', 'total_volume']
    valid_cols = [col for col in needed_cols if col in df.columns]
    df = df[valid_cols]
    if 'current_price' in df.columns:
        df = df[df['current_price'] < 6]
    return df


def fetch_a_stock():
    stock_list = ak.stock_zh_a_spot_em()
    df = stock
