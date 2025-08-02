# 部署指导文档

本文档详细说明如何将量化分析系统部署到各种云平台，实现24小时免费运行。

## 🎯 部署目标

- ✅ 24小时不间断运行
- ✅ 免费云端部署
- ✅ 自动数据更新
- ✅ 高可用性保障
- ✅ 零本地依赖

## 🚀 Render 部署（推荐）

Render 是最推荐的免费部署平台，提供稳定的服务和简单的部署流程。

### 步骤1：准备代码仓库

1. **创建GitHub仓库**
```bash
# 初始化Git仓库
git init
git add .
git commit -m "Initial commit: 量化分析系统"

# 添加远程仓库
git remote add origin https://github.com/your-username/quantitative-analysis-system.git
git push -u origin main
```

2. **确认必要文件**
确保以下文件存在于根目录：
- `render.yaml` - Render部署配置
- `requirements.txt` - Python依赖
- `src/main.py` - 应用入口

### 步骤2：创建Render服务

1. **注册Render账号**
   - 访问 [render.com](https://render.com)
   - 使用GitHub账号注册/登录

2. **创建Web Service**
   - 点击 "New +" → "Web Service"
   - 选择 "Build and deploy from a Git repository"
   - 连接GitHub账号并选择项目仓库

3. **配置服务设置**
   ```
   Name: quantitative-analysis-system
   Environment: Python 3
   Build Command: pip install -r requirements.txt
   Start Command: cd src && python main.py
   ```

4. **设置环境变量**
   在 Environment Variables 中添加：
   ```
   FLASK_ENV=production
   DEBUG=false
   PORT=10000
   SECRET_KEY=your-random-secret-key-here
   ```

### 步骤3：部署和验证

1. **开始部署**
   - 点击 "Create Web Service"
   - Render会自动开始构建和部署

2. **监控部署过程**
   - 在 Logs 标签页查看构建日志
   - 等待状态变为 "Live"

3. **验证部署**
   - 访问Render提供的URL
   - 检查系统是否正常运行
   - 验证数据是否正常更新

### Render 免费计划限制

- **运行时间**：每月750小时免费（约31天）
- **休眠机制**：15分钟无访问会自动休眠
- **唤醒时间**：约30秒冷启动时间
- **带宽**：100GB/月
- **存储**：临时存储，重启后清空

### 保持服务活跃

为避免服务休眠，可以设置定时ping：

1. **使用外部监控服务**
   - [UptimeRobot](https://uptimerobot.com/) - 免费监控服务
   - 设置每5分钟ping一次你的应用URL

2. **配置健康检查**
   应用已内置 `/health` 端点，可用于监控检查

## 🔧 Heroku 部署

Heroku 是另一个优秀的免费部署选择。

### 步骤1：安装Heroku CLI

```bash
# macOS
brew tap heroku/brew && brew install heroku

# Ubuntu/Debian
curl https://cli-assets.heroku.com/install-ubuntu.sh | sh

# Windows
# 下载并安装 Heroku CLI for Windows
```

### 步骤2：创建Heroku应用

```bash
# 登录Heroku
heroku login

# 创建应用
heroku create your-app-name

# 设置环境变量
heroku config:set FLASK_ENV=production
heroku config:set DEBUG=false
heroku config:set SECRET_KEY=your-random-secret-key
```

### 步骤3：部署应用

```bash
# 添加Heroku远程仓库
git remote add heroku https://git.heroku.com/your-app-name.git

# 部署到Heroku
git push heroku main

# 查看应用状态
heroku ps:scale web=1
heroku logs --tail
```

### Heroku 免费计划限制

- **运行时间**：每月550小时免费
- **休眠机制**：30分钟无访问会休眠
- **唤醒时间**：约10-30秒
- **内存**：512MB RAM
- **存储**：临时文件系统

## 🌐 Railway 部署

Railway 是新兴的部署平台，提供简单的部署体验。

### 步骤1：准备Railway

1. **注册Railway账号**
   - 访问 [railway.app](https://railway.app)
   - 使用GitHub账号注册

2. **创建项目**
   - 点击 "New Project"
   - 选择 "Deploy from GitHub repo"
   - 选择你的仓库

### 步骤2：配置部署

1. **设置环境变量**
   ```
   FLASK_ENV=production
   DEBUG=false
   PORT=5000
   SECRET_KEY=your-secret-key
   ```

2. **配置启动命令**
   ```
   cd src && python main.py
   ```

### Railway 免费计划

- **运行时间**：每月500小时
- **内存**：512MB RAM
- **存储**：1GB
- **带宽**：100GB/月

## 🔄 自动部署配置

### GitHub Actions 自动部署

创建 `.github/workflows/deploy.yml`：

```yaml
name: Deploy to Render

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    
    - name: Deploy to Render
      uses: johnbeynon/render-deploy-action@v0.0.8
      with:
        service-id: ${{ secrets.RENDER_SERVICE_ID }}
        api-key: ${{ secrets.RENDER_API_KEY }}
```

### 环境变量管理

在GitHub仓库设置中添加Secrets：
- `RENDER_SERVICE_ID` - Render服务ID
- `RENDER_API_KEY` - Render API密钥

## 📊 监控和维护

### 应用监控

1. **健康检查端点**
   ```
   GET /health
   ```
   返回系统状态信息

2. **系统信息端点**
   ```
   GET /api/system-info
   ```
   返回详细系统信息

### 日志监控

1. **Render日志**
   - 在Render控制台查看实时日志
   - 支持日志搜索和过滤

2. **应用内日志**
   ```python
   # 查看日志级别
   LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR
   ```

### 性能优化

1. **缓存配置**
   ```python
   # 调整缓存过期时间
   CACHE_EXPIRE_TIME=300  # 5分钟
   ```

2. **数据更新频率**
   ```python
   # 在data_manager.py中调整更新间隔
   UPDATE_INTERVAL = 300  # 5分钟
   ```

## 🚨 故障排除

### 常见部署问题

1. **构建失败**
   ```bash
   # 检查requirements.txt
   pip install -r requirements.txt
   
   # 检查Python版本
   python --version  # 需要3.11+
   ```

2. **启动失败**
   ```bash
   # 检查端口配置
   PORT=10000  # Render默认端口
   
   # 检查主机绑定
   app.run(host='0.0.0.0', port=port)
   ```

3. **数据获取失败**
   ```bash
   # 检查网络连接
   curl -I https://api.coingecko.com/api/v3/ping
   
   # 检查API限制
   # 确认rate_limiter配置正确
   ```

### 调试技巧

1. **本地测试**
   ```bash
   # 模拟生产环境
   export FLASK_ENV=production
   export DEBUG=false
   cd src && python main.py
   ```

2. **日志调试**
   ```python
   # 临时启用调试日志
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

3. **API测试**
   ```bash
   # 测试API端点
   curl http://localhost:5000/health
   curl http://localhost:5000/api/market-data
   ```

## 🔐 安全配置

### 环境变量安全

1. **生成安全密钥**
   ```python
   import secrets
   secret_key = secrets.token_hex(32)
   print(secret_key)
   ```

2. **敏感信息保护**
   - 不要在代码中硬编码密钥
   - 使用环境变量存储敏感信息
   - 定期更换密钥

### API安全

1. **请求限制**
   ```python
   # 在rate_limiter.py中配置
   MAX_REQUESTS_PER_MINUTE = 60
   ```

2. **CORS配置**
   ```python
   # 生产环境建议限制域名
   CORS(app, origins=["https://yourdomain.com"])
   ```

## 📈 扩展部署

### 多实例部署

1. **负载均衡**
   - 使用Render的多实例功能
   - 配置健康检查

2. **数据库分离**
   ```python
   # 使用外部数据库
   DATABASE_URL = "postgresql://user:pass@host:port/db"
   ```

### 高级配置

1. **Redis缓存**
   ```python
   # 添加Redis支持
   REDIS_URL = "redis://localhost:6379/0"
   ```

2. **CDN加速**
   - 使用Cloudflare等CDN服务
   - 加速静态资源访问

## 📞 支持和帮助

### 获取帮助

1. **官方文档**
   - [Render文档](https://render.com/docs)
   - [Heroku文档](https://devcenter.heroku.com/)

2. **社区支持**
   - GitHub Issues
   - Stack Overflow

3. **联系方式**
   - 项目Issues: [GitHub Issues](https://github.com/your-username/quantitative-analysis-system/issues)

---

🎉 **恭喜！** 按照本指导文档，你应该能够成功将量化分析系统部署到云端，实现24小时免费运行。

