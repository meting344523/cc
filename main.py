import asyncio
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
import os
import time
import akshare as ak
import aiohttp
import random

PORT = int(os.environ.get('PORT', 8000))  # 兼容 Render 端口配置

# HTTP Server：保持服务在线（适配 Render Web Service 模式）
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write("✅ 量化行情系统运行中".encode('utf-8'))

def run_server():
    server = HTTPServer(('0.0.0.0', PORT), Handler)
    print(f"🌐 HTTP Server 启动于端口 {PORT}")
    server.serve_forever()

# 请求头伪装
HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"),
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Referer": "https://www.coingecko.com/"
}

# 缓存机制
cache = {
    'crypto': [],
    'stocks': [],
    'funds': []
}

# ✅ 虚拟货币（CoinGecko）
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
        async with aiohttp.ClientSession(headers=HEADERS) as session:
            async with session.get(url, params=params, timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    print("✅ 虚拟货币数据抓取成功")
                    cache['crypto'] = data
                    return data
                else:
                    print(f"⚠️ 虚拟货币接口返回异常: {resp.status}")
                    return cache['crypto']
    except Exception as e:
        print("❌ 虚拟货币抓取异常:", e)
        return cache['crypto']

# ✅ A股数据（AkShare）
def fetch_stock_data():
    try:
        df = ak.stock_zh_a_spot_em()
        df['涨跌幅'] = df['涨跌幅'].str.rstrip('%').astype(float)
        selected = df[['名称', '最新价', '涨跌幅']].sort_values('涨跌幅', ascending=False).head(5)
        print("✅ A股数据抓取成功")
        cache['stocks'] = selected.to_dict(orient='records')
        return cache['stocks']
    except Exception as e:
        print("❌ A股抓取失败:", e)
        return cache['stocks']

# ✅ 基金数据（AkShare）
def fetch_fund_data():
    try:
        df = ak.fund_em_open_fund_rank()
        needed = ['基金代码', '基金简称', '近1月', '近3月']
        if not all(col in df.columns for col in needed):
            raise ValueError("字段缺失")
        top = df[needed].head(5)
        print("✅ 基金数据抓取成功")
        cache['funds'] = top.to_dict(orient='records')
        return cache['funds']
    except Exception as e:
        print("❌ 基金抓取失败:", e)
        return cache['funds']

# 主循环，每 5 分钟轮询
async def periodic_fetch(interval_sec=300):
    while True:
        print("\n📡 开始抓取行情数据...")
        await fetch_crypto_data()
        fetch_stock_data()
        fetch_fund_data()
        print(f"📊 当前缓存：Crypto {len(cache['crypto'])} 条，A股 {len(cache['stocks'])} 条，基金 {len(cache['funds'])} 条")
        wait = interval_sec + random.randint(0, 60)
        print(f"⏱️ 等待 {wait} 秒后继续抓取")
        await asyncio.sleep(wait)

if __name__ == '__main__':
    threading.Thread(target=run_server, daemon=True).start()
    asyncio.run(periodic_fetch(interval_sec=300))
