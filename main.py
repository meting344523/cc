import asyncio
import aiohttp
import akshare as ak
from datetime import datetime
from jinja2 import Environment, FileSystemLoader

# 加密货币数据
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
                    return data
                else:
                    print(f"Crypto API 返回状态码异常: {resp.status}")
                    return []
    except Exception as e:
        print("抓取Crypto失败：", e)
        return []

# A股数据
def fetch_stock_data():
    try:
        df = ak.stock_zh_a_spot_em()
        selected = df[['名称', '最新价', '涨跌幅']].copy()
        # 转换涨跌幅为数值，方便排序
        selected['涨跌幅'] = selected['涨跌幅'].str.rstrip('%').astype(float)
        selected = selected.sort_values(by='涨跌幅', ascending=False).head(5)
        print("Stock data sample:\n", selected)
        return selected.to_dict(orient='records')
    except Exception as e:
        print("抓取A股失败：", e)
        return []

# 基金数据
def fetch_fund_data():
    try:
        df = ak.fund_rank_return()
        top_funds = df[['基金代码', '基金简称', '近1月', '近3月']].head(5)
        print("Fund data sample:\n", top_funds)
        return top_funds.to_dict(orient='records')
    except Exception as e:
        print("抓取基金失败：", e)
        return []

# 渲染HTML报告
def render_report(crypto_data, stock_data, fund_data):
    env = Environment(loader=FileSystemLoader('.'))
    template = env.get_template('output.html')
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    html_content = template.render(
        update_time=now,
        crypto=crypto_data,
        stocks=stock_data,
        funds=fund_data
    )
    with open('output.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    print("报告已生成：output.html")

async def main():
    crypto = await fetch_crypto_data()
    stocks = fetch_stock_data()
    funds = fetch_fund_data()
    render_report(crypto, stocks, funds)

if __name__ == '__main__':
    asyncio.run(main())
