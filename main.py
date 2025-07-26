import time
import json
import random
import requests
import akshare as ak
from flask import Flask, render_template_string
from datetime import datetime

app = Flask(__name__)

# ===== CoinGecko 缓存机制 =====
crypto_cache = {"data": {}, "timestamp": 0}
crypto_ids = ['bitcoin', 'ethereum', 'dogecoin', 'solana', 'shiba-inu', 'cardano', 'polkadot', 'tron', 'avalanche-2', 'chainlink']

def get_crypto_prices(ids):
    url = 'https://api.coingecko.com/api/v3/simple/price'
    params = {
        'ids': ','.join(ids),
        'vs_currencies': 'usdt'
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()

def safe_get_crypto_prices(ids):
    now = time.time()
    if now - crypto_cache["timestamp"] < 60:
        return crypto_cache["data"]
    try:
        data = get_crypto_prices(ids)
        crypto_cache["data"] = data
        crypto_cache["timestamp"] = now
        return data
    except Exception as e:
        print("CoinGecko 请求失败:", e)
        return crypto_cache["data"]

# ===== A股数据 =====
def get_cn_stocks():
    try:
        df = ak.stock_zh_a_spot_em()
        df = df[df['最新价'] > 0]
        return df[['代码', '名称', '最新价']].head(10).to_dict(orient='records')
    except Exception as e:
        print("A股数据请求失败:", e)
        return []

# ===== 基金数据 =====
def get_fund_list():
    try:
        fund_rank = ak.fund_rank_fund_em()
        codes = fund_rank['基金代码'].tolist()[:10]  # 前10只
        return codes
    except Exception as e:
        print("基金列表获取失败:", e)
        return []

def get_fund_realtime(code):
    try:
        df = ak.fund_em_open_fund_info(fund_code=code)
        name = df[df['item'] == '基金全称']['value'].values[0]
        net_value = float(df[df['item'] == '单位净值']['value'].values[0])
        return {'代码': code, '名称': name, '最新价': net_value}
    except:
        return None

def get_funds():
    codes = get_fund_list()
    result = []
    for code in codes:
        data = get_fund_realtime(code)
        if data:
            result.append(data)
    return result

# ===== 分析推荐逻辑（可扩展）=====
def analyze(data_list, type_name):
    results = []
    for d in data_list:
        price = d['最新价']
        score = 5 + random.random() * 5
        buy = round(price * 0.95, 2)
        sell = round(price * 1.1, 2)
        reason = ""

        if 4.5 <= price <= 6:
            reason += "当前价格接近5元，属于低价潜力标的。"
            score += 0.5
        if price < 0.01:
            reason += "当前价格极低，可能存在高波动潜力。"
            score += 0.3

        reason += "模拟评分，仅供参考。"
        score = round(min(score, 10), 2)

        results.append({
            '名称': d.get('名称', ''),
            '代码': d.get('代码', ''),
            '当前价': price,
            '推荐买入': buy,
            '预测卖出': sell,
            '理由': reason,
            '评分': score
        })
    return sorted(results, key=lambda x: -x['评分'])

# ===== 网页模板 =====
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh">
<head>
  <meta charset="UTF-8">
  <title>量化系统推荐报告</title>
  <style>
    body { font-family: "Microsoft YaHei", sans-serif; padding: 20px; background: #f6f6f6; }
    h2 { color: #333; }
    table { width: 100%%; border-collapse: collapse; margin-bottom: 40px; background: #fff; }
    th, td { padding: 10px; border: 1px solid #ccc; text-align: center; }
    th { background: #eee; }
  </style>
</head>
<body>
  <h2>最新分析报告（{{ time }}）</h2>

  <h3>📈 加密货币:</h3>
  <table>
    <tr><th>名称</th><th>代码</th><th>当前价</th><th>推荐买入</th><th>预测卖出</th><th>评分</th><th>理由</th></tr>
    {% for item in crypto %}
    <tr>
      <td>{{ item.名称 }}</td><td>{{ item.代码 }}</td><td>{{ item.当前价 }}</td>
      <td>{{ item.推荐买入 }}</td><td>{{ item.预测卖出 }}</td>
      <td>{{ item.评分 }}</td><td>{{ item.理由 }}</td>
    </tr>
    {% endfor %}
  </table>

  <h3>🏦 A股:</h3>
  <table>
    <tr><th>名称</th><th>代码</th><th>当前价</th><th>推荐买入</th><th>预测卖出</th><th>评分</th><th>理由</th></tr>
    {% for item in stocks %}
    <tr>
      <td>{{ item.名称 }}</td><td>{{ item.代码 }}</td><td>{{ item.当前价 }}</td>
      <td>{{ item.推荐买入 }}</td><td>{{ item.预测卖出 }}</td>
      <td>{{ item.评分 }}</td><td>{{ item.理由 }}</td>
    </tr>
    {% endfor %}
  </table>

  <h3>💰 基金:</h3>
  <table>
    <tr><th>名称</th><th>代码</th><th>当前价</th><th>推荐买入</th><th>预测卖出</th><th>评分</th><th>理由</th></tr>
    {% for item in funds %}
    <tr>
      <td>{{ item.名称 }}</td><td>{{ item.代码 }}</td><td>{{ item.当前价 }}</td>
      <td>{{ item.推荐买入 }}</td><td>{{ item.预测卖出 }}</td>
      <td>{{ item.评分 }}</td><td>{{ item.理由 }}</td>
    </tr>
    {% endfor %}
  </table>
</body>
</html>
"""

# ===== Web 展示入口 =====
@app.route('/')
def index():
    crypto_data_raw = safe_get_crypto_prices(crypto_ids)
    crypto_data = []
    for cid in crypto_ids:
        price = crypto_data_raw.get(cid, {}).get('usdt')
        if price:
            crypto_data.append({'名称': cid.title(), '代码': cid, '最新价': price})

    stock_data = get_cn_stocks()
    fund_data = get_funds()

    crypto_result = analyze(crypto_data, "币")
    stock_result = analyze(stock_data, "股")
    fund_result = analyze(fund_data, "基")

    return render_template_string(HTML_TEMPLATE,
                                  time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                  crypto=crypto_result,
                                  stocks=stock_result,
                                  funds=fund_result)

# ===== 启动 Flask 服务 =====
if __name__ == '__main__':
    print("启动 Flask 服务，监听端口 10000")
    app.run(host="0.0.0.0", port=10000)
