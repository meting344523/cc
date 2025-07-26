import threading
import time
from flask import Flask, render_template_string
from data_sources import analyze_crypto, analyze_stocks, analyze_funds, fetch_sentiment_score

app = Flask(__name__)

# === 初始化全局推荐结果 ===
crypto_recommendations = []
stock_recommendations = []
fund_recommendations = []
current_sentiment = 0.0

# === 页面模板（调试信息已加） ===
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh">
<head>
    <meta charset="UTF-8">
    <title>量化系统推荐报告</title>
    <style>
        body { font-family: "Microsoft YaHei", sans-serif; padding: 20px; }
        .section { margin-bottom: 40px; }
        .item { margin: 10px 0; }
    </style>
</head>
<body>
    <h1>最新分析报告（{{ now_time }}）</h1>
    <p>情绪得分：{{ sentiment_score }}</p>
    <p>币种数量: {{ crypto_results|length }} | A股数量: {{ stock_results|length }} | 基金数量: {{ fund_results|length }}</p>

    <div class="section">
        <h2>📈 加密货币:</h2>
        {% for item in crypto_results %}
            <div class="item">{{ item }}</div>
        {% endfor %}
    </div>
    <div class="section">
        <h2>🏦 A股:</h2>
        {% for item in stock_results %}
            <div class="item">{{ item }}</div>
        {% endfor %}
    </div>
    <div class="section">
        <h2>💰 基金:</h2>
        {% for item in fund_results %}
            <div class="item">{{ item }}</div>
        {% endfor %}
    </div>
</body>
</html>
"""

# === 定时任务：每5分钟执行一次分析 ===
def schedule_task():
    global crypto_recommendations, stock_recommendations, fund_recommendations, current_sentiment
    while True:
        print("开始分析任务...")
        try:
            crypto_recommendations = analyze_crypto()
            print(f"加密货币推荐数量: {len(crypto_recommendations)}")
        except Exception as e:
            print("加密货币分析失败:", e)

        try:
            stock_recommendations = analyze_stocks()
            print(f"A股推荐数量: {len(stock_recommendations)}")
        except Exception as e:
            print("A股分析失败:", e)

        try:
            fund_recommendations = analyze_funds()
            print(f"基金推荐数量: {len(fund_recommendations)}")
        except Exception as e:
            print("基金分析失败:", e)

        try:
            current_sentiment = fetch_sentiment_score()
            print("情绪得分:", current_sentiment)
        except Exception as e:
            print("情绪分析失败:", e)

        print("分析任务完成，等待5分钟...")
        time.sleep(300)

@app.route('/')
def index():
    from datetime import datetime
    return render_template_string(
        HTML_TEMPLATE,
        now_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        sentiment_score=round(current_sentiment, 2),
        crypto_results=crypto_recommendations,
        stock_results=stock_recommendations,
        fund_results=fund_recommendations
    )

if __name__ == '__main__':
    # 启动分析线程
    t = threading.Thread(target=schedule_task)
    t.daemon = True
    t.start()

    # 启动 Flask
    print("启动 Flask 服务，监听端口 10000")
    app.run(host='0.0.0.0', port=10000)
