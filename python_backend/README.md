# 🤖 钉钉K8s运维机器人 (Python版本)

基于Python + FastAPI + MCP工具链的智能钉钉运维机器人，支持自然语言操作Kubernetes集群。具有Web配置界面。

## ✨ 核心特性

- 🚀 **快捷指令**: 支持 `/pods`、`/logs`、`/scale` 等快捷命令
- 🧠 **智能对话**: 集成LLM，支持自然语言描述运维需求
- 🔧 **MCP工具链**: 基于Model Context Protocol的可扩展工具系统
- ☁️ **K8s集成**: 原生支持Kubernetes集群操作
- 📱 **钉钉集成**: 无缝集成钉钉群聊和机器人
- 🔒 **安全控制**: 支持权限验证和操作审计
- 💻 **Web配置界面**: 直观的前端配置页面，支持实时配置管理

## 🏗️ 系统架构

```
钉钉用户
    ↓ (快捷指令/自然语言)
钉钉群聊机器人
    ↓ (Webhook)
FastAPI 后端服务
    ↓ (消息处理)
LLM处理器 (OpenAI/智谱/千问)
    ↓ (工具调用)
MCP客户端
    ↓ (K8s操作)
Kubernetes集群
```

## 📁 项目结构

```
python_backend/
├── main.py                 # FastAPI主应用
├── requirements.txt        # Python依赖
├── config.env.example     # 环境变量示例
├── start.sh               # 启动脚本
├── src/
│   ├── mcp/              # MCP客户端模块
│   │   ├── types.py      # 类型定义
│   │   └── client.py     # MCP客户端实现
│   ├── llm/              # LLM处理模块
│   │   └── processor.py  # LLM处理器
│   └── dingtalk/         # 钉钉集成模块
│       └── bot.py        # 钉钉机器人处理器
└── logs/                 # 日志目录
```

## 🚀 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone <your-repo>
cd python_backend

# 确保Python 3.8+
python3 --version

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
# 复制配置模板
cp config.env.example .env

# 编辑配置文件
nano .env
```

必要的配置项：

```bash
# LLM配置
LLM_API_KEY=your_openai_api_key_here
LLM_MODEL=gpt-3.5-turbo

# 钉钉机器人配置
DINGTALK_WEBHOOK_URL=https://oapi.dingtalk.com/robot/send?access_token=xxx
DINGTALK_SECRET=your_secret_here

# 服务端口
PORT=8000
```

### 3. 启动服务

```bash
# 使用启动脚本（推荐）
chmod +x start.sh
./start.sh

# 或直接启动
python main.py
```

### 4. 访问Web界面

打开浏览器访问：`http://localhost:8000`

## 📱 钉钉机器人配置

### 1. 创建钉钉机器人

1. 在钉钉群聊中选择 "群设置" → "智能群助手"
2. 添加 "自定义机器人"
3. 设置机器人名称（如："K8s运维助手"）
4. 复制Webhook地址和安全设置

### 2. 配置Webhook

将钉钉提供的Webhook URL和Secret配置到 `.env` 文件：

```bash
DINGTALK_WEBHOOK_URL=https://oapi.dingtalk.com/robot/send?access_token=your_token
DINGTALK_SECRET=your_secret
```

### 3. 设置外网访问

如果部署在内网，需要使用内网穿透工具：

```bash
# 使用ngrok (示例)
ngrok http 8000

# 将生成的外网地址设为钉钉机器人的Webhook URL
# 格式：https://xxxx.ngrok.io/webhook
```

## 🎯 使用说明

### 快捷指令

在钉钉群聊中直接发送以下指令：

```bash
# 查看Pod列表
/pods

# 查看特定命名空间的Pods
/pods production

# 查看Pod日志
/logs nginx-deployment-xxx

# 扩缩容Deployment
/scale nginx-deployment 3

# 检查集群状态
/status

# 显示帮助
/help
```

### 智能对话

@机器人 + 自然语言描述：

```bash
@K8s运维助手 帮我查看集群中有哪些异常的Pod

@K8s运维助手 nginx应用的副本数太少了，帮我扩容到5个

@K8s运维助手 production命名空间下的服务状态如何？
```

## 📱 Web配置界面

### 功能模块

1. **🔍 仪表板**
   - 系统状态监控
   - 组件健康检查
   - 快速测试功能

2. **🧠 LLM配置**
   - 支持多种AI提供商 (OpenAI, Azure, 智谱AI)
   - 模型参数调整
   - 实时配置测试

3. **🛠️ MCP工具管理**
   - 工具列表查看
   - 工具参数配置
   - 工具测试执行

4. **💬 钉钉机器人配置**
   - Webhook URL设置
   - 签名密钥配置
   - 消息格式设置

5. **🧪 工具测试**
   - 交互式工具测试
   - 参数验证
   - 结果展示

### 界面特色

- **响应式设计** - 支持桌面和移动设备
- **实时反馈** - 配置更改即时生效
- **状态监控** - 组件运行状态一目了然
- **现代UI** - 基于现代设计原则的用户界面

## 🔧 API接口

### 核心接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/` | GET | 服务状态 |
| `/webhook` | POST | 钉钉Webhook处理 |
| `/status` | GET | 系统状态检查 |
| `/tools` | GET | 可用工具列表 |
| `/test` | POST | 工具调用测试 |
| `/chat` | POST | 聊天功能测试 |
| `/shortcuts` | GET | 快捷指令列表 |

### 测试工具调用

```bash
curl -X POST "http://localhost:8000/test" \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "k8s-get-pods",
    "parameters": {"namespace": "default"}
  }'
```

### 测试聊天功能

```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "帮我查看集群中的Pod状态",
    "enable_tools": true
  }'
```

### 系统状态
```http
GET /api/status
```

### 工具管理
```http
GET /api/tools
POST /api/tools/test
```

### 配置管理
```http
GET /api/config/{config_type}
POST /api/config/{config_type}
```

### 消息测试
```http
POST /api/test
```

### 钉钉Webhook
```http
POST /dingtalk/webhook
```

## 🔍 故障排查

### 常见问题

1. **MCP客户端连接失败**
   ```bash
   # 检查服务状态
   curl http://localhost:8000/status
   
   # 查看日志
   tail -f logs/app.log
   ```

2. **LLM调用失败**
   ```bash
   # 验证API Key配置
   echo $LLM_API_KEY
   
   # 测试API连通性
   curl -X POST "http://localhost:8000/chat" \
     -H "Content-Type: application/json" \
     -d '{"message": "hello", "enable_tools": false}'
   ```

3. **钉钉消息无响应**
   ```bash
   # 检查Webhook配置
   echo $DINGTALK_WEBHOOK_URL
   
   # 查看Webhook日志
   grep "webhook" logs/app.log
   ```

4. **K8s连接问题**
   ```bash
   # 检查kubeconfig
   kubectl cluster-info
   ```

### 日志查看

```bash
# 实时查看日志
tail -f logs/app.log

# 查看错误日志
grep "ERROR" logs/app.log

# 查看工具调用日志
grep "tool_call" logs/app.log
```

## 🔒 安全配置

### 环境变量保护

```bash
# 设置文件权限
chmod 600 .env

# 排除敏感文件
echo ".env" >> .gitignore
echo "logs/" >> .gitignore
```

### 钉钉签名验证

在生产环境中，建议启用钉钉签名验证：

```bash
# 在.env中配置Secret
DINGTALK_SECRET=your_secret_here
```

### K8s权限控制

```bash
# 使用受限的RBAC角色
KUBECONFIG_PATH=/path/to/limited/kubeconfig
```

## 📈 性能优化

### 缓存配置

MCP客户端支持结果缓存，可在配置中调整：

```python
mcp_config = MCPClientConfig(
    enable_cache=True,
    cache_timeout=300000,  # 5分钟
    max_concurrent_calls=5
)
```

### 并发控制

```python
# 调整并发数限制
max_concurrent_calls=10  # 根据服务器性能调整
```

## 🔄 集成Node.js版本

如果您已有Node.js版本的实现，可以通过以下方式集成：

### 方案1: 微服务架构

```bash
# Python服务作为主服务
python_backend:8000

# Node.js服务作为MCP工具提供者
nodejs_mcp_service:3000
```

### 方案2: 混合调用

```python
import subprocess

# 在Python中调用Node.js脚本
result = subprocess.run(['node', 'mcp-tool.js'], capture_output=True)
```

## 🤝 贡献指南

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交变更 (`git commit -m 'Add some AmazingFeature'`)
4. 推送分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 技术支持

- 📧 Email: support@example.com
- 💬 钉钉群: xxxxx
- 🐛 Issue: [GitHub Issues](https://github.com/your-repo/issues)

---

**⭐ 如果这个项目对您有帮助，请给个Star！** 