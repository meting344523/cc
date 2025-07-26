import asyncio
import threading
from flask import Flask, render_template_string
import aiohttp
import random
import os
import traceback
import requests
import time
import json

app = Flask(__name__)

cache = {
    "crypto": [],
    "stocks": [],
    "funds": []
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)"
}

CRYPTO_SYMBOLS = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "ADAUSDT",
    "SOLUSDT", "DOGEUSDT", "DOTUSDT", "MATICUSDT", "LTCUSDT"
]

async def fetch_usd_cny_rate():
    url = "https://api.exchangerate-api.com/v4/latest/USD"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    print(f"汇率API请求失败，状态码: {resp.status}")
                    return 7.0
                data = await resp.json()
                rate = float(data["rates"]["CNY"])
                print(f"获取实时美元兑人民币汇率: {rate}")
                return rate
    except Exception as e:
        print("获取汇率失败，使用默认7:", e)
        traceback.print_exc()
        return 7.0

async def fetch_crypto_data():
    url = "https://api.binance.com/api/v3/ticker/price"
    result = []
    try:
        rate = await fetch_usd_cny_rate()
        async with aiohttp.ClientSession() as session:
            for symbol in CRYPTO_SYMBOLS:
                params = {"symbol": symbol}
                async with session.get(url, params=params) as resp:
                    if resp.status != 200:
                        print(f"Binance请求失败: {resp.status} {symbol}")
                        continue
                    data = await resp.json()
                    price_usdt = float(data.get("price", 0))
                    price_cny = round(price_usdt * rate, 2)
                    buy = round(price_cny * 0.95, 2)
                    sell = round(price_cny * 1.1, 2)
                    score = round(random.uniform(6, 9), 2)
                    name_map = {
                        "BTCUSDT": "Bitcoin",
                        "ETHUSDT": "Ethereum",
                        "BNBUSDT": "Binance Coin",
                        "XRPUSDT": "XRP",
                        "ADAUSDT": "Cardano",
                        "SOLUSDT": "Solana",
                        "DOGEUSDT": "Dogecoin",
                        "DOTUSDT": "Polkadot",
                        "MATICUSDT": "Polygon",
                        "LTCUSDT": "Litecoin"
                    }
                    name = name_map.get(symbol, symbol)
                    reason = "Binance交易所实时价格"
                    print(f"{name} 当前美元价格: {price_usdt}, 实时汇率: {rate}, 换算人民币: {price_cny}")
                    result.append({
                        "名称": name,
                        "当前价格": price_cny,
                        "推荐买入": buy,
                        "预测卖出": sell,
                        "理由": reason,
                        "评分": score
                    })
        cache["crypto"] = result
        print(f"Binance虚拟货币抓取成功，数量：{len(result)}")
    except Exception as e:
        print("Binance虚拟货币抓取失败:", e)
        traceback.print_exc()

def fetch_stock_data():
    try:
        url = "http://hq.sinajs.cn/list=sh600000,sh600519,sz000001,sz000002,sh601398,sz000651,sz000333,sh600276,sh601166,sh601318"
        resp = requests.get(url, headers=HEADERS)
        resp.encoding = 'gbk'
        text = resp.text
        result = []
        for line in text.splitlines():
            parts = line.split('="')
            if len(parts) != 2:
                continue
            code = parts[0].split('_')[-1]
            data_str = parts[1].strip('";')
            fields = data_str.split(',')
            if len(fields) < 4:
                continue
            name = fields[0]
            price = float(fields[3])  # 最新价
            buy = round(price * 0.97, 2)
            sell = round(price * 1.08, 2)
            reason = "新浪财经实时数据"
            score = round(random.uniform(6.5, 9.5), 2)
            result.append({
                "名称": name,
                "当前价格": price,
                "推荐买入": buy,
                "预测卖出": sell,
                "理由": reason,
                "评分": score
            })
        cache["stocks"] = result
        print(f"新浪财经A股抓取成功，数量：{len(result)}")
    except Exception as e:
        print("新浪财经A股抓取失败：", e)
        traceback.print_exc()

def fetch_fund_data():
    try:
        url = "http://fund.eastmoney.com/data/rankhandler.aspx"
        params = {
            "op": "ph",
            "dt": "kf",
            "ft": "all",
            "rs": "",
            "gs": "0",
            "sc": "1nzf",
            "st": "desc",
            "sd": "",
            "ed": "",
            "pn": "1",
            "pi": "50",
            "_": str(int(time.time() * 1000))
        }
        headers = HEADERS.copy()
        headers["Referer"] = "http://fund.eastmoney.com/data/fundranking.html"
        resp = requests.get(url, params=params, headers=headers)
        text = resp.text
        json_str = text[text.find('['):text.rfind(']') + 1]
        data_list = json.loads(json_str)
        result = []
        for item in data_list[:5]:
            name = item[1]
            net_value = float(item[2]) if item[2] != '-' else 1.0
            buy = round(net_value * 0.98, 2)
            sell = round(net_value * 1.06, 2)
            reason = "天天基金最新净值"
            score = round(random.uniform(7, 10), 2)
            result.append({
                "名称": name,
                "当前价格": net_value,
                "推荐买入": buy,
                "预测卖出": sell,
                "理由": reason,
                "评分": score
            })
        cache["funds"] = result
        print(f"天天基金基金抓取成功，数量：{len(result)}")
    except Exception as e:
        print("天天基金基金抓取失败：", e)
        traceback.print_exc()

async def update_data_loop():
    while True:
        print("开始抓取分析任务")
        await fetch_crypto_data()
        fetch_stock_data()
        fetch_fund_data()
        print("抓取分析完成，等待5分钟")
        await asyncio.sleep(300)

TEMPLATE = """
<!DOCTYPE html>
<html lang="zh">
<head>
  <meta charset="UTF-8">
  <title>量化行情推荐</title>
  <style>
    body { font-family: Arial, sans-serif; padding: 20px; background: #f6f8fa; }
    h2 { color: #333; }
    table { border-collapse: collapse; width: 100%; margin-bottom: 30px; }
    th, td { border: 1px solid #ccc; padding: 8px; text-align: center; }
    th { background-color: #eee; }
  </style>
</head>
<body>
  <h1>📈 量化行情系统分析结果</h1>

  {% for category, items in data.items() %}
    <h2>{{ category }}</h2>
    {% if items %}
      <table>
        <tr>
          <th>名称</th>
          <th>当前价格</th>
          <th>推荐买入</th>
          <th>预测卖出</th>
          <th>分析理由</th>
          <th>评分/10</th>
        </tr>
        {% for row in items %}
          <tr>
            <td>{{ row['名称'] }}</td>
            <td>{{ row['当前价格'] }}</td>
            <td>{{ row['推荐买入'] }}</td>
            <td>{{ row['预测卖出'] }}</td>
            <td>{{ row['理由'] }}</td>
            <td>{{ row['评分'] }}</td>
          </tr>
        {% endfor %}
      </table>
    {% else %}
      <p>暂无数据</p>
    {% endif %}
  {% endfor %}
</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(TEMPLATE, data={
        "虚拟货币推荐": cache["crypto"],
        "A股推荐": cache["stocks"],
        "基金推荐": cache["funds"]
    })

def start_server():
    port = int(os.environ.get("PORT", 8000))
    print(f"启动 Flask 服务，监听端口 {port}")
    app.run(host="0.0.0.0", port=port)

if __name__ == '__main__':
    # 启动前先抓一次，避免空白页面
    asyncio.run(fetch_crypto_data())
    fetch_stock_data()
    fetch_fund_data()

    threading.Thread(target=start_server, daemon=True).start()

    asyncio.run(update_data_loop())
