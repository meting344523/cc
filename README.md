# Quant Alpha System

## 项目简介
本项目是一个全天候运行的量化分析系统，实时监测虚拟货币、中国A股及基金市场，筛选价格约5元附近且未来可能上涨的标的，提供买入/卖出点位建议，并生成美化的HTML报告。

## 文件说明
- `main.py` ：主程序，抓取数据、分析并生成HTML报告
- `requirements.txt` ：Python依赖包列表
- `render.yaml` ：Render部署配置，定时每5分钟执行
- `report.html` ：美化的HTML报告模板
- `.gitignore` ：忽略文件配置

## 部署说明
1. 创建GitHub仓库并上传所有文件。
2. 在[Render.com](https://render.com/)注册并连接GitHub仓库。
3. 创建新服务，选择Worker类型，Render会自动识别`render.yaml`文件。
4. 部署后，程序将每5分钟运行一次，自动更新`output.html`报告。
5. 可通过Render的文件访问或GitHub Pages等方式展示生成的HTML报告。

## 注意事项
- 使用免费API，数据可能有一定延迟。
- 你可根据需求进一步完善技术指标计算逻辑。