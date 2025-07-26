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
    "User-Agent": "Mozilla/5.0"
}

CRYPTO_SYMBOLS = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "ADAUSDT",
    "SOLUSDT", "DOGEUSDT", "DOTUSDT", "MATICUSDT", "LTCUSDT"
]

mock_past_prices = {
    "BTCUSDT": [26000, 26200, 26500, 26300, 26800],
    "ETHUSDT": [1700, 1720, 1740, 1730, 1750],
    "BNBUSDT": [300, 305, 310, 308, 315],
    "XRPUSDT": [0.5, 0.52, 0.51, 0.53, 0.54],
    "ADAUSDT": [0.4, 0.41, 0.42, 0.43, 0.44],
    "SOLUSDT": [20, 21, 22, 21.5, 22.5],
    "DOGEUSDT": [0.06, 0.061, 0.062, 0.063, 0.064],
    "DOTUSDT": [6, 6.1, 6.2, 6.15, 6.3],
    "MATICUSDT": [1, 1.02, 1.03, 1.04, 1.05],
    "LTCUSDT": [90, 92, 91, 93, 94],
}

def simple_kline_analysis(prices):
    if len(prices) < 5:
        return "无足够历史数据判断K线形态"
    ma3 = sum(prices[-3:]) / 3
    ma5 = sum(prices[-5:]) / 5
    last_price = prices[-1]

    if ma3 > ma5 and last_price > ma3:
        return "多头趋势，短期看涨"
    elif ma3 < ma5 and last_price < ma3:
        return "空头趋势，短期看跌"
    else:
        return "趋势不明，建议观望"

async def fetch_crypto_data():
    url = "https://api.binance.com/api/v3/ticker/price"
    result = []
    try:
        async with aiohttp.ClientSession(headers=HEADERS) as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    print(f"Binance请求失败: {resp.status}")
                    return
                data = await resp.json()
                price_map = {item["symbol"]: float(item["price"]) for item in data}
                for symbol in CRYPTO_SYMBOLS:
                    price_usdt = price_map.get(symbol)
                    if price_usdt is None:
                        continue
                    price_cny = round(price_usdt * 7, 2)
                    buy = round(price_cny * 0.95, 2)
                    sell = round(price_cny * 1.1, 2)
                    score = round(random.uniform(6, 9), 2)
                    prices = mock_past_prices.get(symbol, [])
                    kline_reason = simple_kline_analysis(prices)

                    if len(prices) >= 2:
                        change_pct = (prices[-1] - prices[-2]) / prices[-2] * 100
                        change_text = f"日涨跌幅 {change_pct:.2f}%。"
                    else:
                        change_text = ""

                    name_map = {
                        "BTCUSDT": "Bitcoin",
                        "ETHUSDT": "Ethereum",
                        "BNBUSDT": "BNB",
                        "XRPUSDT": "XRP",
                        "ADAUSDT": "Cardano",
                        "SOLUSDT": "Solana",
                        "DOGEUSDT": "Dogecoin",
                        "DOTUSDT": "Polkadot",
                        "MATICUSDT": "Polygon",
                        "LTCUSDT": "Litecoin"
                    }
                    name = name_map.get(symbol, symbol)
                    reason = f"{change_text}{kline_reason} 综合评分：{score}/10。"

                    result.append({
                        "名称": name,
                        "当前价格": price_cny,
                        "推荐买入": buy,
                        "预测卖出": sell,
                        "理由": reason,
                        "评分": score
                    })
        cache["crypto"] = sorted(result, key=lambda x: x["评分"], reverse=True)
        print("加密货币数据抓取成功")
    except Exception as e:
        print("加密货币数据抓取失败:", e)

def fetch_stock_data():
    try:
        url = "http://hq.sinajs.cn/list=sh600000,sh600519,sz000001,sz000002"
        resp = requests.get(url, headers=HEADERS)
        resp.encoding = 'gbk'
        result = []
        for line in resp.text.splitlines():
            parts = line.split('="')
            if len(parts) != 2:
                continue
            fields = parts[1].strip('";').split(',')
            if len(fields) < 4:
                continue
            name = fields[0]
            try:
                price = float(fields[3])
            except:
                continue
            buy = round(price * 0.97, 2)
            sell = round(price * 1.08, 2)
            score = round(random.uniform(6.5, 9.5), 2)
            result.append({
                "名称": name,
                "当前价格": price,
                "推荐买入": buy,
                "预测卖出": sell,
                "理由": "实时A股行情分析",
                "评分": score
            })
        cache["stocks"] = sorted(result, key=lambda x: x["评分"], reverse=True)
        print("A股数据抓取成功")
    except Exception as e:
        print("A股数据抓取失败:", e)

def fetch_fund_data():
    try:
        url = "http://fund.eastmoney.com/data/rankhandler.aspx"
        params = {
            "op": "ph", "dt": "kf", "ft": "all", "rs": "", "gs": "0", "sc": "1nzf",
            "st": "desc", "pn": "1", "pi": "50", "_": str(int(time.time() * 1000))
        }
        headers = HEADERS.copy()
        headers["Referer"] = "http://fund.eastmoney.com/data/fundranking.html"
        resp = requests.get(url, params=params, headers=headers)
        text = resp.text
        json_str = text[text.find('['):text.rfind(']') + 1]
        data_list = json.loads(json_str)
        result = []
        for item in data_list[:5]:
            fund_code = item[0]
            name = item[1]
            try:
                net_value = float(item[2]) if item[2] != '-' else 0.0
            except:
                continue
            buy = round(net_value * 0.98, 2)
            sell = round(net_value * 1.06, 2)
            score = round(random.uniform(7, 10), 2)
            result.append({
                "名称": f"{name}({fund_code})",
                "当前价格": net_value,
                "推荐买入": buy,
                "预测卖出": sell,
                "理由": f"基金净值分析",
                "评分": score
            })
        cache["funds"] = sorted(result, key=lambda x: x["评分"], reverse=True)
        print("基金数据抓取成功")
    except Exception as e:
        print("基金数据抓取失败:", e)

async def periodic_task():
    while True:
        print("开始更新任务")
        await fetch_crypto_data()
        fetch_stock_data()
        fetch_fund_data()
        await asyncio.sleep(600)

def start_background_loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(periodic_task())

TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>量化行情推荐</title>
  <style>
    body { font-family: Arial; padding: 20px; background: #f8f9fa; }
    h2 { color: #333; }
    table { border-collapse: collapse; width: 100%; margin-bottom: 30px; }
    th, td { border: 1px solid #ccc; padding: 8px; text-align: center; }
    th { background-color: #eee; }
  </style>
</head>
<body>
  <h1>📈 量化推荐系统</h1>
  {% for cat, items in data.items() %}
    <h2>{{ cat }}</h2>
    {% if items %}
      <table>
        <tr>
          <th>名称</th><th>当前价格</th><th>推荐买入</th><th>预测卖出</th><th>理由</th><th>评分</th>
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

if __name__ == "__main__":
    # 启动前先抓取一次
    asyncio.run(fetch_crypto_data())
    fetch_stock_data()
    fetch_fund_data()

    # 启动异步循环线程（后台持续更新数据）
    threading.Thread(target=start_background_loop, daemon=True).start()

    # 启动 Flask
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
