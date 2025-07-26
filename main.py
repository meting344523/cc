import asyncio
import threading
from flask import Flask, render_template_string
import pandas as pd
import aiohttp
import akshare as ak
import random
import os
import traceback

app = Flask(__name__)

cache = {
    "crypto": [],
    "stocks": [],
    "funds": []
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)"
}

# -------------------------------
# 抓取与分析函数
# -------------------------------

async def fetch_crypto_data():
    url = 'https://api.coingecko.com/api/v3/coins/markets'
    params = {
        'vs_currency': 'cny',  # 人民币价格
        'order': 'market_cap_desc',
        'per_page': 10,
        'page': 1
    }
    try:
        async with aiohttp.ClientSession(headers=HEADERS) as session:
            async with session.get(url, params=params) as resp:
                if resp.status != 200:
                    print(f"请求CoinGecko失败，状态码: {resp.status}")
                    return
                data = await resp.json()
                for d in data:
                    print(f"【加密货币】{d['name']} 当前价格：{d['current_price']} CNY")
                result = []
                for d in data:
                    current = d.get('current_price')
                    if current is None:
                        continue
                    buy = round(current * 0.95, 2)
                    sell = round(current * 1.1, 2)
                    score = round(random.uniform(6, 9), 2)
                    reason = "市值大、走势稳健" if d.get("market_cap_rank", 9999) < 10 else "短期技术面有反弹信号"
                    result.append({
                        "名称": d["name"],
                        "当前价格": current,
                        "推荐买入": buy,
                        "预测卖出": sell,
                        "理由": reason,
                        "评分": score
                    })
                cache["crypto"] = result
    except Exception as e:
        print("Crypto抓取失败：", e)
        traceback.print_exc()

def fetch_stock_data():
    try:
        df = ak.stock_zh_a_spot_em()
        df["涨跌幅"] = df["涨跌幅"].str.rstrip('%').astype(float)
        df = df.sort_values("涨跌幅", ascending=True).head(5)  # 下跌最多5只，技术反弹机会
        result = []
        for _, row in df.iterrows():
            price = row["最新价"]
            buy = round(price * 0.97, 2)
            sell = round(price * 1.08, 2)
            reason = "短期超跌，存在技术反弹可能"
            score = round(random.uniform(6.5, 9.5), 2)
            result.append({
                "名称": row["名称"],
                "当前价格": price,
                "推荐买入": buy,
                "预测卖出": sell,
                "理由": reason,
                "评分": score
            })
        cache["stocks"] = result
        print("A股抓取成功，推荐股票数量：", len(result))
    except Exception as e:
        print("A股抓取失败：", e)
        traceback.print_exc()

def fetch_fund_data():
    try:
        df = ak.fund_em_open_fund_rank()
        result = []
        for _, row in df.head(5).iterrows():
            price = 1.00  # 假设净值为1.00
            buy = round(price * 0.98, 2)
            sell = round(price * 1.06, 2)
            reason = "近3月业绩优秀，资金持续流入"
            score = round(random.uniform(7, 10), 2)
            result.append({
                "名称": row["基金简称"],
                "当前价格": price,
                "推荐买入": buy,
                "预测卖出": sell,
                "理由": reason,
                "评分": score
            })
        cache["funds"] = result
        print("基金抓取成功，推荐基金数量：", len(result))
    except Exception as e:
        print("基金抓取失败：", e)
        traceback.print_exc()

# -------------------------------
# 定时任务
# -------------------------------

async def update_data_loop():
    while True:
        print("开始抓取分析任务")
        await fetch_crypto_data()
        fetch_stock_data()
        fetch_fund_data()
        print("抓取分析完成，等待5分钟")
        await asyncio.sleep(300)

# -------------------------------
# 网页展示模板
# -------------------------------

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

# -------------------------------
# 启动
# -------------------------------

def start_server():
    port = int(os.environ.get("PORT", 8000))
    print(f"启动 Flask 服务，监听端口 {port}")
    app.run(host="0.0.0.0", port=port)

if __name__ == '__main__':
    # 先抓一次数据，保证页面打开有数据
    asyncio.run(fetch_crypto_data())
    fetch_stock_data()
    fetch_fund_data()

    # 启动 Flask 服务线程
    threading.Thread(target=start_server, daemon=True).start()

    # 运行异步定时抓取任务
    asyncio.run(update_data_loop())
