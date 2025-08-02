# 量化分析系统

一个全天候24小时运行的量化分析系统，集成多市场实时数据接入、智能技术指标分析、买卖点识别和风险控制，支持免费云端部署。

## 🚀 功能特性

### 核心功能
- **多市场实时数据接入**：支持加密货币、A股、基金三大市场
- **智能技术指标分析**：集成RSI、MACD、SMA/EMA、布林带等多种技术指标
- **AI机器学习预测**：基于Logistic Regression模型预测未来2-3日涨幅
- **买卖点识别**：精准识别支撑位和阻力位，提供买卖建议
- **风险控制策略**：多维度风险评估和智能预警系统
- **24小时运行**：全天候自动数据更新和分析

### 数据源
- **加密货币**：CoinGecko API（支持分页获取，内置限速机制）
- **A股市场**：AkShare 全量数据接口（结合缓存与限频）
- **基金市场**：天天基金网（维护20-50只基金代码池）

### 技术特点
- **防封机制**：严格的API请求限速，确保数据访问稳定
- **缓存优化**：智能缓存管理，减少重复请求
- **响应式设计**：黑色背景护眼界面，支持桌面和移动设备
- **云端部署**：支持GitHub + Render免费部署，无需本地依赖

## 🏗️ 系统架构

```
quantitative-analysis-system/
├── src/                          # 源代码目录
│   ├── analysis/                 # 分析模块
│   │   ├── technical_indicators.py  # 技术指标计算
│   │   └── ml_predictor.py          # 机器学习预测
│   ├── config/                   # 配置模块
│   │   └── settings.py              # 系统配置
│   ├── data_sources/             # 数据源模块
│   │   ├── coingecko_api.py         # CoinGecko API
│   │   ├── akshare_api.py           # AkShare API
│   │   ├── fund_api.py              # 基金API
│   │   └── data_manager.py          # 数据管理器
│   ├── models/                   # 数据模型
│   ├── routes/                   # API路由
│   │   ├── market.py                # 市场数据API
│   │   └── user.py                  # 用户API
│   ├── static/                   # 静态文件
│   │   ├── index.html               # 前端页面
│   │   ├── styles.css               # 样式文件
│   │   └── script.js                # 交互脚本
│   ├── strategies/               # 交易策略
│   │   └── trading_strategy.py      # 交易策略实现
│   ├── utils/                    # 工具模块
│   │   ├── cache_manager.py         # 缓存管理
│   │   ├── rate_limiter.py          # 限速器
│   │   └── logger.py                # 日志配置
│   └── main.py                   # 主应用入口
├── requirements.txt              # Python依赖
├── render.yaml                   # Render部署配置
├── Procfile                      # Heroku部署配置
├── start.sh                      # 启动脚本
└── README.md                     # 项目文档
```

## 🛠️ 本地开发

### 环境要求
- Python 3.11+
- pip 包管理器

### 快速开始

1. **克隆项目**
```bash
git clone <your-repo-url>
cd quantitative-analysis-system
```

2. **运行启动脚本**
```bash
chmod +x start.sh
./start.sh
```

3. **访问应用**
打开浏览器访问：http://localhost:5000

### 手动安装

1. **创建虚拟环境**
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **创建必要目录**
```bash
mkdir -p src/database logs
```

4. **启动应用**
```bash
cd src
python main.py
```

## ☁️ 云端部署

### Render 部署（推荐）

1. **准备代码**
   - 将代码推送到GitHub仓库
   - 确保包含 `render.yaml` 配置文件

2. **创建Render服务**
   - 登录 [Render](https://render.com)
   - 选择 "New Web Service"
   - 连接GitHub仓库
   - Render会自动检测 `render.yaml` 配置

3. **环境变量配置**
   ```
   FLASK_ENV=production
   DEBUG=false
   PORT=10000
   ```

4. **部署完成**
   - Render会自动构建和部署
   - 获得永久访问URL

### Heroku 部署

1. **安装Heroku CLI**
```bash
# 安装Heroku CLI
curl https://cli-assets.heroku.com/install.sh | sh
```

2. **创建应用**
```bash
heroku create your-app-name
```

3. **设置环境变量**
```bash
heroku config:set FLASK_ENV=production
heroku config:set DEBUG=false
```

4. **部署应用**
```bash
git push heroku main
```

## 📊 API 接口

### 市场数据
- `GET /api/market-data` - 获取所有市场数据
- `GET /api/asset-analysis/{type}/{id}` - 获取资产分析详情
- `GET /api/data-status` - 获取数据状态信息
- `POST /api/force-update` - 强制更新数据

### 系统信息
- `GET /health` - 健康检查
- `GET /api/system-info` - 系统信息

## ⚙️ 配置说明

### 环境变量
```bash
# Flask配置
FLASK_ENV=production          # 运行环境
DEBUG=False                   # 调试模式
SECRET_KEY=your-secret-key    # 密钥

# 数据库配置
DATABASE_URL=sqlite:///database/app.db

# 缓存配置
CACHE_EXPIRE_TIME=300         # 缓存过期时间（秒）

# 端口配置
PORT=5000                     # 服务端口
```

### 基金代码池配置
在 `src/config/settings.py` 中可以修改基金代码池：
```python
FUND_CODES = [
    '000001',  # 华夏成长混合
    '110022',  # 易方达消费行业股票
    # ... 添加更多基金代码
]
```

## 🔧 技术栈

### 后端技术
- **Flask** - Web框架
- **SQLAlchemy** - ORM数据库
- **AkShare** - 金融数据获取
- **scikit-learn** - 机器学习
- **pandas/numpy** - 数据处理
- **requests** - HTTP客户端

### 前端技术
- **HTML5/CSS3** - 页面结构和样式
- **JavaScript** - 交互逻辑
- **响应式设计** - 多设备适配

### 部署技术
- **Render** - 云端部署平台
- **Gunicorn** - WSGI服务器
- **GitHub** - 代码托管

## 📈 使用说明

### 界面功能

1. **实时监控**
   - 显示各市场最新数据和更新时间
   - 自动5分钟刷新，支持手动刷新

2. **市场展示**
   - **加密货币**：显示币种代码和USDT价格
   - **A股**：显示股票代码和名称
   - **基金**：显示基金代码和名称

3. **信号系统**
   - 🟢 强烈买入/买入 - 绿色显示
   - 🔴 强烈卖出/卖出 - 红色显示
   - 🟡 持有观望 - 黄色显示

4. **详情分析**
   - 点击任意资产卡片查看详细分析
   - 包含买卖点位、风险评估、AI预测等

### 投资建议使用

⚠️ **重要声明**：本系统仅供学习和研究使用，不构成投资建议。投资有风险，决策需谨慎。

## 🐛 故障排除

### 常见问题

1. **数据获取失败**
   - 检查网络连接
   - 确认API限速设置
   - 查看日志文件 `logs/error.log`

2. **启动失败**
   - 检查Python版本（需要3.11+）
   - 确认依赖包安装完整
   - 检查端口是否被占用

3. **部署问题**
   - 确认环境变量设置正确
   - 检查 `requirements.txt` 是否完整
   - 查看部署平台日志

### 日志查看
```bash
# 查看应用日志
tail -f logs/app.log

# 查看错误日志
tail -f logs/error.log

# 查看数据获取日志
tail -f logs/data_fetch.log
```

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 📞 联系方式

- 项目链接：[GitHub Repository](https://github.com/your-username/quantitative-analysis-system)
- 问题反馈：[Issues](https://github.com/your-username/quantitative-analysis-system/issues)

## 🙏 致谢

- [CoinGecko](https://www.coingecko.com/) - 加密货币数据API
- [AkShare](https://github.com/akfamily/akshare) - 金融数据获取库
- [天天基金网](http://fund.eastmoney.com/) - 基金数据来源
- [Render](https://render.com/) - 免费云端部署平台

---

⭐ 如果这个项目对你有帮助，请给它一个星标！

