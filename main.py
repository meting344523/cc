import time
import json
import os
import pandas as pd
import requests
from bs4 import BeautifulSoup
from textblob import TextBlob
import akshare as ak

CACHE_DIR = './cache'
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

def save_cache(name, data):
    with open(f"{CACHE_DIR}/{name}.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)

def load_cache(name):
    path = f"{CACHE_DIR}/{name}.json"
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

def request_with_retry(url, params=None, headers=None, retries=3, timeout=10):
    for attempt in range(retries):
        try:
            r = requests.get(url, params=params, headers=headers, timeout=timeout)
            if r.status_code == 429:
                print("API访问频率限制，等待30秒后重试...")
                time.sleep(30)
                continue
            r.raise_for_status()
            return r
        except requests.RequestException as e:
            print(f"请求失败，重试 {attempt+1}/{retries}，错误: {e}")
            time.sleep(5)
    return None

def fetch_crypto_data():
    cache_name = 'crypto'
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": "cny",
        "order": "market_cap_desc",
        "per_page": 300,
        "page": 1,
        "sparkline": False
    }

    r = request_with_retry(url, params=params)
    if r:
        data = r.json()
        if isinstance(data, list):
            save_cache(cache_name, data)
            df = pd.DataFrame(data)
            if 'current_price' in df.columns:
                df = df[df['current_price'] < 6]
            return df
        else:
            print("CoinGecko返回异常，使用缓存数据")
    else:
        print("请求CoinGecko失败，使用缓存数据")

    cached = load_cache(cache_name)
    if cached:
        print("读取CoinGecko缓存数据")
        df = pd.DataFrame(cached)
        if 'current_price' in df.columns:
            df = df[df['current_price'] < 6]
        return df
    return pd.DataFrame()

def fetch_a_stock():
    cache_name = 'astock'
    try:
        df = ak.stock_zh_a_spot_em()
        save_cache(cache_name, df.to_dict(orient='records'))
        df = df[df['最新价'] < 6]
        return df[['代码', '名称', '最新价', '涨跌幅', '成交量']]
    except Exception as e:
        print(f"请求A股数据失败，错误: {e}，尝试读取缓存")
        cached = load_cache(cache_name)
        if cached:
            df = pd.DataFrame(cached)
            return df[df['最新价'] < 6][['代码', '名称', '最新价', '涨跌幅', '成交量']]
    return pd.DataFrame()

def fetch_funds():
    cache_name = 'funds'
    try:
        df = ak.fund_etf_spot_em()
        save_cache(cache_name, df.to_dict(orient='records'))
        df = df[df['最新价'] < 6]
        return df[['基金代码', '基金简称', '最新价', '涨跌幅']]
    except Exception as e:
        print(f"请求基金数据失败，错误: {e}，尝试读取缓存")
        cached = load_cache(cache_name)
        if cached:
            df = pd.DataFrame(cached)
            return df[df['最新价'] < 6][['基金代码', '基金简称', '最新价', '涨跌幅']]
    return pd.DataFrame()

def sentiment_analysis(keyword):
    url = f"https://news.google.com/rss/search?q={keyword}"
    r = request_with_retry(url)
    if r:
        soup = BeautifulSoup(r.content, 'xml')
        titles = [item.text for item in soup.find_all('title')]
        sentiments = [TextBlob(title).sentiment.polarity for title in titles]
        if sentiments:
            return sum(sentiments) / len(sentiments)
    return 0

def main():
    print("开始抓取虚拟货币数据...")
    crypto_df = fetch_crypto_data()
    time.sleep(30)  # 避免频繁请求

    print("开始抓取A股数据...")
    stock_df = fetch_a_stock()
    time.sleep(30)

    print("开始抓取基金数据...")
    fund_df = fetch_funds()

    print(f"虚拟货币数量: {len(crypto_df)}")
    print(f"A股数量: {len(stock_df)}")
    print(f"基金数量: {len(fund_df)}")

    # TODO: 根据你的分析逻辑，筛选满足条件的标的，生成交易信号和HTML报告

if __name__ == '__main__':
    main()
