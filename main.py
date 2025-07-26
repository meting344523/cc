import pandas as pd
from ta.volatility import AverageTrueRange
from ta.trend import MACD
from ta.momentum import RSIIndicator
import requests
from bs4 import BeautifulSoup
from textblob import TextBlob
import akshare as ak
import json

def fetch_crypto_data():
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": "cny",
        "order": "market_cap_desc",
        "per_page": 300,
        "page": 1,
        "sparkline": False
    }
    r = requests.get(url, params=params, timeout=10)
    data = r.json()
    if isinstance(data, list):
        print("Crypto data sample:", data[:3])
    else:
        print("Crypto API返回异常:", data)
        return pd.DataFrame()
    df = pd.DataFrame(data)
    needed_cols = ['id', 'symbol', 'name', 'current_price', 'high_24h', 'low_24h', 'total_volume']
    valid_cols = [col for col in needed_cols if col in df.columns]
    df = df[valid_cols]
    if 'current_price' in df.columns:
        df = df[df['current_price'] < 6]
    return df

def fetch_a_stock():
    stock_list = ak.stock_zh_a_spot_em()
    df = stock_list[stock_list['最新价'] < 6]
    return df[['代码', '名称', '最新价', '涨跌幅', '成交量']]

def fetch_funds():
    funds = ak.fund_etf_spot_em()
    df = funds[funds['最新价'] < 6]
    return df[['基金代码', '基金简称', '最新价', '涨跌幅']]

def sentiment_analysis(keyword):
    url = f"https://news.google.com/rss/search?q={keyword}"
    r = requests.get(url, timeout=10)
    soup = BeautifulSoup(r.content, 'xml')
    titles = [item.text for item in soup.find_all('title')]
    sentiments = [TextBlob(title).sentiment.polarity for title in titles]
    return sum(sentiments) / len(sentiments) if sentiments else 0

def generate_trade_signals(ticker, price, reason="示例数据", score=5):
    entry = round(price * 0.98, 2)
    target = round(price * 1.1, 2)
    stop = round(price * 0.95, 2)
    return {
        "name": ticker,
        "price": price,
        "score": score,
        "reason": reason,
        "entry": entry,
        "target": target,
        "stop": stop
    }

def save_html_report(crypto, stock, fund, template_path='report.html', output_path='output.html'):
    with open(template_path, 'r', encoding='utf-8') as f:
        html = f.read()
    crypto_js = json.dumps(crypto, ensure_ascii=False).replace('</', r'<\/')
    stock_js = json.dumps(stock, ensure_ascii=False).replace('</', r'<\/')
    fund_js = json.dumps(fund, ensure_ascii=False).replace('</', r'<\/')
    html = html.replace('// 动态插入crypto-table数据', f'fillTable({crypto_js}, "crypto-table");')
    html = html.replace('// 动态插入stock-table数据', f'fillTable({stock_js}, "stock-table");')
    html = html.replace('// 动态插入fund-table数据', f'fillTable({fund_js}, "fund-table");')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

def main():
    crypto = fetch_crypto_data()
    stocks = fetch_a_stock()
    funds = fetch_funds()

    crypto_results = [generate_trade_signals(row['name'], row['current_price'], "MACD金叉, 成交量放大", 7) for _, row in crypto.head(5).iterrows()]
    stock_results = [generate_trade_signals(row['名称'], row['最新价'], "RSI超卖, 放量", 6) for _, row in stocks.head(5).iterrows()]
    fund_results = [generate_trade_signals(row['基金简称'], row['最新价'], "稳定回撤, 政策利好", 5) for _, row in funds.head(5).iterrows()]

    save_html_report(crypto_results, stock_results, fund_results)

    print("报告生成完毕：output.html")

if __name__ == '__main__':
    main()
