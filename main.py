import os
import json
import time
import asyncio
import threading
import requests
from flask import Flask
from datetime import datetime
from textblob import TextBlob
import akshare as ak
import pandas as pd

app = Flask(__name__)

def fetch_crypto_data():
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {"vs_currency": "usd", "order": "market_cap_desc", "per_page": 10, "page": 1}
    try:
        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code == 429:
            print("Crypto API返回异常:", resp.json())
            return []
        return resp.json()
    except Exception as e:
        print("Crypto数据获取异常:", e)
        return []

def fetch_a_stock():
    try:
        stock_list = ak.stock_zh_a_spot_em()
        return stock_list[["代码", "名称", "最新价", "涨跌幅"]].head(10).to_dict(orient="records")
    except Exception as e:
        print("A股数据获取异常:", e)
        return []

def fetch_fund_data():
    try:
        fund_list = ak.fund_open_fund_rank()
        return fund_list[["基金代码", "基金简称", "日增长率"]].head(10).to_dict(orient="records")
    except Exception as e:
        print("基金数据获取异常:", e)
        return []

def sentiment_score(text):
    try:
        blob = TextBlob(text)
        return blob.sentiment.polarity
    except:
        return 0

def fetch_news_sentiment():
    try:
        url = "https://news.google.com/rss/search?q=stock+OR+crypto+OR+fund"
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            from xml.etree import ElementTree as ET
            root = ET.fromstring(resp.content)
            titles = [item.find("title").text for item in root.findall(".//item")]
            sentiments = [sentiment_score(t) for t in titles]
            return sum(sentiments) / len(sentiments) if sentiments else 0
    except:
        return 0

async def run_analysis():
    crypto = fetch_crypto_data()
    stock = fetch_a_stock()
    fund = fetch_fund_data()
    news_sent = fetch_news_sentiment()

    report = {
        "时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "情绪评分": news_sent,
        "加密货币": crypto,
        "A股": stock,
        "基金": fund,
    }

    with open("latest_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"[{report['时间']}] 数据更新完毕 ✅")

def start_loop():
    while True:
        try:
            asyncio.run(run_analysis())
        except Exception as e:
            print("运行异常:", e)
        time.sleep(300)

@app.route("/")
def home():
    try:
        with open("latest_report.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            return f"""
            <h2>最新分析报告（{data['时间']}）</h2>
            <p>情绪得分：{data['情绪评分']:.2f}</p>
            <h3>📈 加密货币:</h3>
            <pre>{json.dumps(data['加密货币'], ensure_ascii=False, indent=2)}</pre>
            <h3>🏦 A股:</h3>
            <pre>{json.dumps(data['A股'], ensure_ascii=False, indent=2)}</pre>
            <h3>💰 基金:</h3>
            <pre>{json.dumps(data['基金'], ensure_ascii=False, indent=2)}</pre>
            """
    except Exception as e:
        return f"<p>加载数据失败: {e}</p>"

if __name__ == "__main__":
    threading.Thread(target=start_loop, daemon=True).start()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
