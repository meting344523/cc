#!/bin/bash

# 量化分析系统启动脚本

echo "=== 量化分析系统启动脚本 ==="

# 检查Python版本
python_version=$(python3 --version 2>&1)
echo "Python版本: $python_version"

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
echo "激活虚拟环境..."
source venv/bin/activate

# 安装依赖
echo "安装依赖包..."
pip install --upgrade pip
pip install -r requirements.txt

# 创建必要目录
echo "创建必要目录..."
mkdir -p src/database
mkdir -p logs

# 设置环境变量
export FLASK_ENV=development
export DEBUG=True
export PORT=5000

echo "=== 启动量化分析系统 ==="
echo "访问地址: http://localhost:5000"
echo "按 Ctrl+C 停止服务"
echo ""

# 启动应用
cd src && python main.py

