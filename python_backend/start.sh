#!/bin/bash

# 钉钉机器人 + LLM + MCP 集成系统启动脚本

# [INTERNAL_ACTION: Updating start.sh to include static file directory checks]
# {{CHENGQI:
# Action: Modified; Timestamp: 2024-12-28 XX:XX:XX; Reason: Add static file directory checks and web interface support;
# }}
# {{START MODIFICATIONS}}

set -e

echo "🚀 启动钉钉K8s运维机器人..."

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安装"
    exit 1
fi

# 检查pip
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 未安装"
    exit 1
fi

# 创建必要目录
echo "📁 创建必要目录..."
mkdir -p static/{css,js,images}
mkdir -p logs

# 检查静态文件
echo "🔍 检查静态文件..."
if [[ ! -f "static/index.html" ]]; then
    echo "❌ 静态文件不存在，请确保前端文件已正确部署"
    exit 1
fi

# 检查依赖
echo "📦 检查依赖..."
pip3 install -r requirements.txt

# 检查配置文件
if [[ ! -f ".env" && ! -f "config.json" ]]; then
    echo "⚠️  未找到配置文件，将使用默认配置"
    echo "📝 请访问 http://localhost:8000 进行配置"
fi

# 检查Kubernetes连接（可选）
if command -v kubectl &> /dev/null; then
    echo "☸️  检查Kubernetes连接..."
    if kubectl cluster-info &> /dev/null; then
        echo "✅ Kubernetes连接正常"
    else
        echo "⚠️  Kubernetes连接失败，K8s功能将受限"
    fi
else
    echo "⚠️  kubectl未安装，K8s功能将受限"
fi

# 设置环境变量
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

echo "🌐 启动Web服务..."
echo "📱 Web界面: http://localhost:8000"
echo "📚 API文档: http://localhost:8000/docs"
echo "❌ 停止服务: Ctrl+C"
echo ""

# 启动服务
python3 main.py

# {{END MODIFICATIONS}} 