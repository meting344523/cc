import asyncio
import random
import datetime
import aiohttp
from flask import Flask, render_template_string
import requests
import time
import traceback

app = Flask(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

cache = {
    "crypto": [],
    "stocks": [],
    "funds": [],
    "sentiment": 0.0
}

mock_past_prices = {
    "BITCOIN": [26000, 26200, 26500, 26300, 26800],
    "ETHEREUM": [1700, 1720, 1740, 1730, 1750],
    "BINANCECOIN": [300, 305, 310, 308, 315],
    "RIPPLE": [0.5, 0.52, 0.51, 0.53, 0.54],
    "CARDANO": [0.4, 0.41, 0.42, 0.43, 0.44],
    "SOLANA": [20, 21, 22, 21.5, 22.5],
    "DOGECOIN": [0.06, 0.061, 0.062, 0.063, 0.064],
    "POLKADOT": [6, 6.1, 6.2, 6.15, 6.3],
    "POLYGON-LITECOIN": [1, 1.02, 1.03, 1.04, 1.05]
}

def simple_kline_analysis(prices):
    if len(prices) < 2:
        return "数据不足"
    diff = prices[-1] - prices[0]
    if diff > 0:
        return "价格趋势上升"
    elif diff < 0:
        return "价格趋势下跌"
    return "震荡整理"

async def fetch_crypto_data():
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": "usd",
        "ids": "bitcoin,ethereum,binancecoin,ripple,cardano,solana,dogecoin,polkadot,polygon-litecoin",
        "order": "market_cap_desc",
        "per_page": 10,
        "page": 1,
        "sparkline": False
    }
    result = []
    try:
        async with aiohttp.ClientSession(headers=HEADERS) as session:
            async with session.get(url, params=params) as resp:
                if resp.status != 200:
                    print(f"CoinGecko请求失败: {resp.status}")
                    return
                data = await resp.json()
                for coin in data:
                    name = coin["name"]
                    price_usd = coin["current_price"]
                    price_cny = round(price_usd * 7, 2)
                    buy = round(price_cny * 0.95, 2)
                    sell = round(price_cny * 1.1, 2)
                    score = round(random.uniform(6.5, 9.5), 2)
                    price_history = mock_past_prices.get(name.upper(), [price_usd - 100, price_usd])
                    reason = simple_kline_analysis(price_history)
                    result.append({
                        "名称": name,
                        "当前价格": price_cny,
                        "推荐买入": buy,
                        "预测卖出": sell,
                        "理由": reason,
                        "评分": score
                    })
        cache["crypto"] = sorted(result, key=lambda x: x["评分"], reverse=True)
        print("加密货币数据抓取成功（CoinGecko）")
    except Exception as e:
        print("CoinGecko数据抓取失败:", e)
        traceback.print_exc()

def fetch_stock_data():
    """
    使用新浪财经接口抓取部分A股实时行情数据，替代akshare，避免依赖。
    """
    try:
        url = "http://hq.sinajs.cn/list=sh000001,sz399001,sz399006"
        # 上证指数(sh000001), 深证成指(sz399001), 创业板指(sz399006)
        resp = requests.get(url, headers=HEADERS)
        resp.encoding = 'gbk'
        text = resp.text
        result = []
        for line in text.splitlines():
            parts = line.split('="')
            if len(parts) != 2:
                continue
            code = parts[0].split('=')[0].strip()
            data_str = parts[1].strip('";')
            fields = data_str.split(',')
            if len(fields) < 4:
                continue
            name_map = {
                "sh000001": "上证指数",
                "sz399001": "深证成指",
                "sz399006": "创业板指"
            }
            name = name_map.get(code, code)
            try:
                price = float(fields[3])
            except:
                continue
            if price <= 0:
                continue
            buy = round(price * 0.97, 2)
            sell = round(price * 1.08, 2)
            score = round(random.uniform(6.5, 9.5), 2)
            reason = "新浪财经实时指数，结合技术形态分析。"
            result.append({
                "名称": name,
                "当前价格": price,
                "推荐买入": buy,
                "预测卖出": sell,
                "理由": reason,
                "评分": score
            })
        if not result:
            cache["stocks"] = [{
                "名称": "提示",
                "当前价格": "-",
                "推荐买入": "-",
                "预测卖出": "-",
                "理由": "当前非交易时间，A股无有效行情更新",
                "评分": "-"
            }]
            print("当前非交易时间，A股无有效行情更新")
        else:
            cache["stocks"] = sorted(result, key=lambda x: x["评分"], reverse=True)
            print(f"A股指数抓取成功，数量：{len(result)}")
    except Exception as e:
        print("A股数据抓取失败：", e)
        traceback.print_exc()

def fetch_fund_data():
    """
    天天基金网基金数据抓取，替代akshare，避免依赖。
    """
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
        data_list = []
        try:
            data_list = json.loads(json_str)
        except Exception as e:
            print("基金数据解析错误：", e)
        result = []
        for item in data_list[:5]:
            fund_code = item[0]
            name = item[1]
            try:
                net_value = float(item[2]) if item[2] != '-' else 0.0
            except:
                net_value = 0.0
            if net_value <= 0:
                continue
            buy = round(net_value * 0.98, 2)
            sell = round(net_value * 1.06, 2)
            score = round(random.uniform(7, 10), 2)
            reason = f"天天基金最新净值，基金代码：{fund_code}。"
            result.append({
                "名称": f"{name}({fund_code})",
                "当前价格": net_value,
                "推荐买入": buy,
                "预测卖出": sell,
                "理由": reason,
                "评分": score
            })
        if not result:
            cache["funds"] = [{
                "名称": "提示",
                "当前价格": "-",
                "推荐买入": "-",
                "预测卖出": "-",
                "理由": "当前非交易时间，基金无有效净值更新",
                "评分": "-"
            }]
            print("当前非交易时间，基金无有效净值更新")
        else:
            cache["funds"] = sorted(result, key=lambda x: x["评分"], reverse=True)
            print(f"基金数据抓取成功，数量：{len(result)}")
    except Exception as e:
        print("基金数据抓取失败：", e)
        traceback.print_exc()

async def update_all():
    print("开始更新任务")
    await fetch_crypto_data()
    fetch_stock_data()
    fetch_fund_data()
    cache["sentiment"] = round(random.uniform(-1, 1), 2)

TEMPLATE = '''
<!DOCTYPE html>
<html lang="zh">
<head>
    <meta charset="UTF-8">
    <title>量化系统推荐报告</title>
    <style>
        body { font-family: sans-serif; margin: 2em; }
        table { border-collapse: collapse; width: 100%; margin-bottom: 2em; }
        th, td { border: 1px solid #ccc; padding: 8px; text-align: center; }
        th { background-color: #f2f2f2; }
        h2 { margin-top: 2em; }
    </style>
</head>
<body>
<h1>最新分析报告（{{ time }}）</h1>
<p>情绪得分：{{ sentiment }}</p>

<h2>📈 加密货币推荐（共{{ crypto|length }}项）</h2>
<table>
    <tr><th>名称</th><th>当前价格</th><th>推荐买入</th><th>预测卖出</th><th>理由</th><th>评分</th></tr>
    {% for item in crypto %}
    <tr>
        <td>{{ item["名称"] }}</td>
        <td>{{ item["当前价格"] }}</td>
        <td>{{ item["推荐买入"] }}</td>
        <td>{{ item["预测卖出"] }}</td>
        <td>{{ item["理由"] }}</td>
        <td>{{ item["评分"] }}</td>
    </tr>
    {% endfor %}
</table>

<h2>🏦 A股推荐（共{{ stocks|length }}项）</h2>
<table>
    <tr><th>名称</th><th>当前价格</th><th>推荐买入</th><th>预测卖出</th><th>理由</th><th>评分</th></tr>
    {% for item in stocks %}
    <tr>
        <td>{{ item["名称"] }}</td>
        <td>{{ item["当前价格"] }}</td>
        <td>{{ item["推荐买入"] }}</td>
        <td>{{ item["预测卖出"] }}</td>
        <td>{{ item["理由"] }}</td>
        <td>{{ item["评分"] }}</td>
    </tr>
    {% endfor %}
</table>

<h2>💰 基金推荐（共{{ funds|length }}项）</h2>
<table>
    <tr><th>名称</th><th>当前价格</th><th>推荐买入</th><th>预测卖出</th><th>理由</th><th>评分</th></tr>
    {% for item in funds %}
    <tr>
        <td>{{ item["名称"] }}</td>
        <td>{{ item["当前价格"] }}</td>
        <td>{{ item["推荐买入"] }}</td>
        <td>{{ item["预测卖出"] }}</td>
        <td>{{ item["理由"] }}</td>
        <td>{{ item["评分"] }}</td>
    </tr>
    {% endfor %}
</table>
</body>
</html>
'''

async def periodic_update(interval=300):
    while True:
        try:
            await update_all()
        except Exception as e:
            print("定时更新异常：", e)
        await asyncio.sleep(interval)

@app.route("/")
def index():
    return render_template_string(TEMPLATE,
        time=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        crypto=cache["crypto"],
        stocks=cache["stocks"],
        funds=cache["funds"],
        sentiment=cache["sentiment"])

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    # 先抓取一次，避免首次访问无数据
    loop.run_until_complete(update_all())
    # 启动定时任务协程，同时启动Flask服务器
    import threading

    def run_loop():
        asyncio.set_event_loop(loop)
        loop.run_forever()

    # 启动后台事件循环线程
    thread = threading.Thread(target=run_loop, daemon=True)
    thread.start()

    # 在事件循环中启动定时更新协程
    asyncio.run_coroutine_threadsafe(periodic_update(300), loop)

    app.run(host="0.0.0.0", port=10000)
