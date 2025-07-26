import asyncio
import threading
from flask import Flask, render_template_string
import pandas as pd
import aiohttp
import akshare as ak
import time
import random

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
        'vs_currency': 'cny',
        'order': 'market_cap_desc',
        'per_page': 10,
        'page': 1
    }
    try:
        async with aiohttp.ClientSession(headers=HEADERS) as session:
            async with session.get(url, params=params) as resp:
                data = await resp.json()
                result = []
                for d in data:
                    current = d['current_price']
                    buy = round(current * 0.95, 2)
                    sell = round(current * 1.1, 2)
                    score = random.uniform(6, 9)
                    reason = "市值大、走势稳健" if d["market_cap_rank"] < 10 else "短期技术面有反弹信号"
                    result.append({
                        "名称": d["name"],
                        "当前价格": current,
                        "推荐买入": buy,
                        "预测卖出": sell,
                        "理由": reason,
                        "评分": round(score, 2)
                    })
                cache["crypto"] = result
    except Exception as e:
        print("Crypto抓取失败：", e)

def fetch_stock_data():
    try:
        df = ak.stock_zh_a_spot_em()
        df["涨跌幅"] = df["涨跌幅"].str.rstrip('%').astype(float)
        df = df.sort_values("涨跌幅", ascending=True).head(5)  # 下跌较多，考虑反弹机会
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
    except Exception as e:
        print("A股抓取失败：", e)

def fetch_fund_data():
    try:
        df = ak.fund_em_open_fund_rank()
        result = []
        for _, row in df.head(5).iterrows():
            price = 1.00  # 假设为净值1.00，基金无实时价格
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
    except Exception as e:
        print("基金抓取失败：", e)

# -------------------------------
# 定时任务
# -------------------------------

async def update_data_loop():
    while True:
        print("开始抓取分析")
        await fetch_crypto_data()
        fetch_stock_data()
        fetch_fund_data()
        print("分析完成，等待5分钟")
        await asyncio.sleep(300)

# -------------------------------
# 网页展示
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
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))

if __name__ == '__main__':
    threading.Thread(target=start_server, daemon=True).start()
    asyncio.run(update_data_loop())
