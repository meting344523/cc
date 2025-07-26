import asyncio
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
import os
import time
import akshare as ak
import aiohttp

PORT = int(os.environ.get('PORT', 8000))

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(b"量化行情系统运行中")

def run_server():
    server = HTTPServer(('0.0.0.0', PORT), Handler)
    print(f"Serving HTTP on port {PORT}")
    server.serve_forever()

cache = {
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
                    print("Crypto数据抓取成功")
                    return data
                elif resp.status == 429:
                    print("Crypto API限流，使用缓存数据")
                    return None
                else:
                    print(f"Crypto API异常状态码: {resp.status}")
                    return None
    except Exception as e:
        print("抓取Crypto异常：", e)
        return None

def fetch_stock_data(retry=3):
    for i in range(retry):
        try:
            df = ak.stock_zh_a_spot()
            df['涨跌幅'] = df['涨跌幅'].str.rstrip('%').astype(float)
            selected = df[['名称', '最新价', '涨跌幅']].sort_values('涨跌幅', ascending=False).head(5)
            print("A股数据抓取成功")
            cache['stocks'] = selected.to_dict(orient='records')
            return cache['stocks']
        except Exception as e:
            print(f"A股抓取失败({i+1}/{retry})：", e)
            time.sleep(1)
    print("A股抓取失败，使用缓存数据" if cache['stocks'] else "A股无可用数据")
    return cache['stocks']

def fetch_fund_data():
    try:
        df = ak.fund_rank()
        needed_cols = ['基金代码', '基金简称', '近1月', '近3月']
        for col in needed_cols:
            if col not in df.columns:
                raise ValueError(f"基金数据缺少字段: {col}")
        top_funds = df[needed_cols].head(5)
        print("基金数据抓取成功")
        cache['funds'] = top_funds.to_dict(orient='records')
        return cache['funds']
    except Exception as e:
        print("基金抓取失败:", e)
        print("使用缓存数据" if cache['funds'] else "无可用基金缓存")
        return cache['funds']

async def main():
    print("开始抓取行情数据...")
    crypto = await fetch_crypto_data()
    if crypto is None:
        print("使用Crypto缓存或空数据")
        crypto = []

    stocks = fetch_stock_data() or []
    funds = fetch_fund_data() or []

    # 这里可扩展报告生成或其他逻辑
    print(f"抓取完成，Crypto {len(crypto)}条，A股 {len(stocks)}条，基金 {len(funds)}条")

if __name__ == '__main__':
    # 启动HTTP服务线程，保持监听端口
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    # 运行抓取主程序（单次）
    asyncio.run(main())

    # 主线程阻塞，保持HTTP服务持续运行
    server_thread.join()
