# 钉钉K8s运维机器人 - 项目概览

## 🎯 项目简介

这是一个基于Python + FastAPI的智能钉钉K8s运维机器人系统，集成了MCP工具链和Web配置界面，支持通过自然语言进行Kubernetes集群运维操作。

## 🏗️ 项目架构

```
钉钉群聊 → 机器人Webhook → LLM处理 → MCP工具调用 → K8s集群操作
                                ↓
                          Web配置界面 ← 用户配置管理
```

## 📁 项目结构

```
ding-robot/
├── python_backend/              # Python后端系统
│   ├── src/                     # 源代码目录
│   │   ├── mcp/                 # MCP客户端模块
│   │   ├── llm/                 # LLM处理器模块
│   │   └── dingtalk/            # 钉钉机器人模块
│   ├── static/                  # Web前端静态文件
│   │   ├── index.html           # 主页面
│   │   ├── css/styles.css       # 样式文件
│   │   └── js/app.js            # JavaScript逻辑
│   ├── main.py                  # FastAPI主应用
│   ├── requirements.txt         # Python依赖
│   ├── start.sh                 # 启动脚本
│   ├── test_system.py           # 系统测试
│   ├── config.env.example       # 配置示例
│   └── README.md                # 项目文档
├── INTEGRATION_GUIDE.md         # 集成指南
└── PROJECT_OVERVIEW.md          # 项目概览
```

## 🌟 核心功能

### 1. Web配置界面
- **仪表板** - 系统状态监控和快速测试
- **LLM配置** - AI模型参数配置和测试
- **MCP工具管理** - 工具列表查看和测试
- **钉钉配置** - 机器人Webhook和消息设置
- **实时配置** - 支持运行时配置更新

### 2. 智能对话系统
- **自然语言处理** - 基于LLM的智能理解
- **快捷指令** - 预定义的K8s操作指令
- **工具调用** - 自动选择合适的MCP工具
- **结果格式化** - 友好的消息回复格式

### 3. K8s集成
- **资源查询** - Pod、Service、Deployment状态
- **日志查看** - 实时Pod日志获取
- **扩缩容操作** - 应用副本数量调整
- **事件监控** - 集群事件实时监控

### 4. 钉钉集成
- **Webhook处理** - 消息接收和解析
- **签名验证** - 安全的消息验证
- **Markdown支持** - 丰富的消息格式
- **@机器人** - 群聊中的机器人触发

## 🚀 部署流程

### 1. 环境准备
```bash
cd python_backend/
pip install -r requirements.txt
```

### 2. 配置系统
```bash
cp config.env.example .env
# 编辑 .env 文件，配置API Key和Webhook
```

### 3. 启动服务
```bash
./start.sh
```

### 4. 访问界面
- **Web界面**: http://localhost:8000
- **API文档**: http://localhost:8000/docs

## 🔧 技术栈

### 后端技术
- **FastAPI** - 现代高性能Web框架
- **Python 3.8+** - 主要编程语言
- **asyncio** - 异步编程支持
- **Kubernetes Client** - K8s集群交互
- **OpenAI API** - LLM智能处理

### 前端技术
- **HTML5/CSS3** - 现代Web标准
- **JavaScript ES6+** - 交互逻辑
- **响应式设计** - 移动设备支持
- **Font Awesome** - 图标库

### 集成协议
- **MCP (Model Context Protocol)** - 工具通信协议
- **钉钉开放平台** - 机器人API
- **Kubernetes API** - 集群管理API

## 📊 系统监控

### 健康检查
- **组件状态** - MCP、LLM、钉钉机器人状态
- **连接检查** - K8s集群连接状态
- **工具统计** - 可用工具数量和使用情况

### 日志系统
- **结构化日志** - JSON格式日志输出
- **级别控制** - DEBUG/INFO/WARNING/ERROR
- **审计日志** - 操作记录和追踪

## 🔒 安全特性

### 访问控制
- **签名验证** - 钉钉消息安全验证
- **配置加密** - 敏感信息安全存储
- **权限控制** - 基于角色的访问限制

### 安全建议
- 定期更新API Key
- 启用钉钉签名验证
- 限制K8s集群访问权限
- 监控异常操作日志

## 🔄 维护指南

### 配置更新
- 通过Web界面实时更新配置
- 配置自动保存到 `config.json`
- 支持热重载，无需重启服务

### 系统更新
```bash
git pull origin main
pip install -r requirements.txt --upgrade
./start.sh
```

### 故障排查
1. 检查系统状态: `/api/status`
2. 查看日志文件: `logs/`
3. 测试组件功能: Web界面测试工具
4. 验证配置正确性: 配置页面

## 📈 性能优化

### 建议配置
- **并发处理** - 异步处理钉钉消息
- **缓存策略** - MCP工具结果缓存
- **连接池** - K8s API连接复用
- **资源限制** - 设置合理的内存和CPU限制

### 扩展建议
- 使用Redis缓存提升性能
- 部署多实例实现负载均衡
- 集成监控系统如Prometheus
- 使用消息队列处理高并发

## 🤝 贡献指南

欢迎提交Issue和Pull Request来改进项目：

1. Fork项目到个人仓库
2. 创建功能分支进行开发
3. 编写测试用例验证功能
4. 提交PR并描述改动内容

## 📄 许可证

本项目采用MIT许可证，详见[LICENSE](LICENSE)文件。

---

**让智能运维更简单！** 🎉 