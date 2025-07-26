import asyncio
import aiohttp
import akshare as ak
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
import os
import time

# 简单缓存，防止空数据输出
cache = {
    'crypto': None,
    'stocks': None,
    'funds': None
}

async def fetch_crypto_data():
    url = 'https://api.coingecko.com/api/v3/coins/markets'
    params = {
        'vs_currency': 'cny',
        'order': 'market_cap_desc',
        'per_page': 10,
        'page': 1,
        'sparkline': 'false'
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    print("Crypto data sample:", data[:2])
                    cache['crypto'] = data
                    return data
                elif resp.status == 429:
                    print("Crypto API限流，使用缓存数据")
                else:
                    print(f"Crypto API 返回状态码异常: {resp.status}")
    except Exception as e:
        print("抓取Crypto失败：", e)
    return cache['crypto']  # 失败则返回缓存或None

def fetch_stock_data(retry=3):
    for attempt in range(retry):
        try:
            df = ak.stock_zh_a_spot()
            df['涨跌幅'] = df['涨跌幅'].str.rstrip('%').astype(float)
            selected = df[['名称', '最新价', '涨跌幅']].sort_values('涨跌幅', ascending=False).head(5)
            print("A股数据样例：\n", selected)
            cache['stocks'] = selected.to_dict(orient='records')
            return cache['stocks']
        except Exception as e:
            print(f"抓取A股失败({attempt+1}/{retry})：", e)
            time.sleep(1)
    print("A股数据抓取失败，使用缓存数据")
    return cache['stocks']

def fetch_fund_data():
    try:
        df = ak.fund_rank()
        columns = df.columns
        needed_cols = ['基金代码', '基金简称', '近1月', '近3月']
        for col in needed_cols:
            if col not in columns:
                raise ValueError(f"基金数据中缺少字段: {col}")
        top_funds = df[needed_cols].head(5)
        print("基金数据样例：\n", top_funds)
        cache['funds'] = top_funds.to_dict(orient='records')
        return cache['funds']
    except Exception as e:
        print("抓取基金失败：", e)
        print("使用缓存基金数据")
        return cache['funds']

def render_report(crypto_data, stock_data, fund_data):
    cur_dir = os.path.dirname(os.path.abspath(__file__))
    env = Environment(loader=FileSystemLoader(cur_dir))
    try:
        template = env.get_template('output.html')
    except Exception as e:
        print("加载模板失败:", e)
        return
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # 过滤空值，确保报告只显示有数据的部分
    crypto_data = crypto_data or []
    stock_data = stock_data or []
    fund_data = fund_data or []

    html_content = template.render(
        update_time=now,
        crypto=crypto_data,
        stocks=stock_data,
        funds=fund_data
    )
    output_path = os.path.join(cur_dir, 'output.html')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print("报告已生成：", output_path)

async def main():
    crypto = await fetch_crypto_data()
    stocks = fetch_stock_data()
    funds = fetch_fund_data()
    render_report(crypto, stocks, funds)

if __name__ == '__main__':
    asyncio.run(main())
