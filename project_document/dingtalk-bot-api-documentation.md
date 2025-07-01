# 钉钉机器人与LLM大模型集成系统 API 文档

**项目**: 钉钉智能机器人系统  
**版本**: v1.0.0  
**生成时间**: 2025-07-01 11:36:57 +08:00  
**API基础URL**: `https://your-domain.com/api`

## 目录

1. [系统概述](#系统概述)
2. [认证机制](#认证机制)
3. [钉钉机器人接口](#钉钉机器人接口)
4. [LLM调用接口](#llm调用接口)
5. [会话管理接口](#会话管理接口)
6. [系统管理接口](#系统管理接口)
7. [错误码说明](#错误码说明)
8. [SDK使用示例](#sdk使用示例)

## 系统概述

### 系统架构
本系统采用分层架构设计，支持钉钉机器人与多种大语言模型（LLM）的集成，提供智能对话服务。

**核心功能**:
- 钉钉机器人消息接收与响应
- 多种LLM模型统一调用（OpenAI、智谱AI、通义千问等）
- 会话上下文管理
- 消息预处理与后处理
- 安全认证与监控

### 技术栈
- **后端**: Node.js + TypeScript + Express.js
- **数据库**: MySQL + Redis
- **消息队列**: Redis
- **部署**: Docker + Kubernetes

## 认证机制

### API Key 认证
所有API调用需要在请求头中包含API密钥：

```http
Authorization: Bearer your-api-key-here
Content-Type: application/json
```

### 钉钉签名验证
钉钉Webhook请求采用HMAC-SHA256签名验证：

```javascript
// 签名计算方式
const signature = crypto
  .createHmac('sha256', secret)
  .update(timestamp + '\n' + nonce)
  .digest('base64');
```

## 钉钉机器人接口

### 1. 接收钉钉消息回调

**接口地址**: `POST /dingtalk/webhook`

**请求参数**:
```json
{
  "conversationType": "2",
  "atUsers": [
    {
      "dingtalkId": "user123",
      "staffId": "staff456"
    }
  ],
  "chatbotUserId": "bot789",
  "msgId": "msg001",
  "text": {
    "content": "你好，请帮我分析一下这个问题"
  },
  "msgtype": "text",
  "createAt": 1625097417000,
  "conversationId": "chat001",
  "isAdmin": false,
  "chatbotCorpId": "corp123",
  "isInAtList": true,
  "sessionWebhook": "https://oapi.dingtalk.com/robot/sendBySession",
  "createTime": 1625097417000,
  "senderNick": "张三",
  "isFromAdmin": false,
  "sessionWebhookExpiredTime": 1625183817000,
  "senderCorpId": "corp123",
  "senderStaffId": "staff456"
}
```

**响应格式**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "msgtype": "text",
    "text": {
      "content": "我是智能助手，很高兴为您服务！您想了解什么问题呢？"
    }
  }
}
```

### 2. 主动发送消息

**接口地址**: `POST /dingtalk/send`

**请求参数**:
```json
{
  "sessionWebhook": "https://oapi.dingtalk.com/robot/sendBySession",
  "msgtype": "text",
  "text": {
    "content": "这是一条主动推送的消息"
  },
  "at": {
    "atUserIds": ["user123"],
    "isAtAll": false
  }
}
```

**响应格式**:
```json
{
  "code": 200,
  "message": "消息发送成功",
  "data": {
    "messageId": "msg_12345",
    "timestamp": 1625097417000
  }
}
```

## LLM调用接口

### 1. 统一聊天接口

**接口地址**: `POST /chat/completions`

**请求参数**:
```json
{
  "model": "gpt-4",
  "messages": [
    {
      "role": "system",
      "content": "你是一个智能助手，请用中文回答用户问题。"
    },
    {
      "role": "user", 
      "content": "请介绍一下人工智能的发展历程"
    }
  ],
  "temperature": 0.7,
  "max_tokens": 2000,
  "stream": false,
  "user": "user_123"
}
```

**支持的模型列表**:
- `gpt-4`: OpenAI GPT-4
- `gpt-3.5-turbo`: OpenAI GPT-3.5 Turbo
- `glm-4`: 智谱AI GLM-4
- `qwen-turbo`: 阿里云通义千问
- `claude-3-sonnet`: Anthropic Claude-3

**响应格式**:
```json
{
  "id": "chatcmpl-123",
  "object": "chat.completion",
  "created": 1625097417,
  "model": "gpt-4",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "人工智能（AI）的发展历程可以分为以下几个重要阶段..."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 50,
    "completion_tokens": 200,
    "total_tokens": 250
  }
}
```

### 2. 流式聊天接口

**接口地址**: `POST /chat/completions` (设置 `stream: true`)

**响应格式** (Server-Sent Events):
```
data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1625097417,"model":"gpt-4","choices":[{"index":0,"delta":{"role":"assistant"},"finish_reason":null}]}

data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1625097417,"model":"gpt-4","choices":[{"index":0,"delta":{"content":"人工"},"finish_reason":null}]}

data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1625097417,"model":"gpt-4","choices":[{"index":0,"delta":{"content":"智能"},"finish_reason":null}]}

data: [DONE]
```

### 3. 获取支持的模型列表

**接口地址**: `GET /models`

**响应格式**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "models": [
      {
        "id": "gpt-4",
        "name": "GPT-4",
        "provider": "openai",
        "description": "OpenAI最先进的语言模型",
        "max_tokens": 8192,
        "input_price": 0.03,
        "output_price": 0.06,
        "currency": "USD",
        "available": true
      },
      {
        "id": "glm-4",
        "name": "ChatGLM-4",
        "provider": "zhipu",
        "description": "智谱AI自研大语言模型",
        "max_tokens": 8192,
        "input_price": 0.1,
        "output_price": 0.1,
        "currency": "CNY",
        "available": true
      }
    ]
  }
}
```

## 会话管理接口

### 1. 创建会话

**接口地址**: `POST /conversations`

**请求参数**:
```json
{
  "userId": "user_123",
  "title": "关于AI的讨论",
  "model": "gpt-4",
  "systemPrompt": "你是一个专业的AI助手",
  "maxTokens": 4000,
  "temperature": 0.7
}
```

**响应格式**:
```json
{
  "code": 200,
  "message": "会话创建成功",
  "data": {
    "conversationId": "conv_123456",
    "userId": "user_123",
    "title": "关于AI的讨论",
    "model": "gpt-4",
    "systemPrompt": "你是一个专业的AI助手",
    "createdAt": "2025-07-01T11:36:57+08:00",
    "updatedAt": "2025-07-01T11:36:57+08:00",
    "messageCount": 0,
    "tokenUsage": 0
  }
}
```

### 2. 获取会话列表

**接口地址**: `GET /conversations`

**查询参数**:
- `userId`: 用户ID
- `page`: 页码 (默认: 1)
- `limit`: 每页数量 (默认: 20)
- `search`: 搜索关键词

**响应格式**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "conversations": [
      {
        "conversationId": "conv_123456",
        "title": "关于AI的讨论",
        "model": "gpt-4",
        "createdAt": "2025-07-01T11:36:57+08:00",
        "updatedAt": "2025-07-01T11:36:57+08:00",
        "messageCount": 5,
        "tokenUsage": 1250
      }
    ],
    "pagination": {
      "total": 1,
      "page": 1,
      "limit": 20,
      "totalPages": 1
    }
  }
}
```

### 3. 获取会话消息

**接口地址**: `GET /conversations/{conversationId}/messages`

**响应格式**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "conversationId": "conv_123456",
    "messages": [
      {
        "messageId": "msg_001",
        "role": "user",
        "content": "你好",
        "timestamp": "2025-07-01T11:36:57+08:00",
        "tokens": 2
      },
      {
        "messageId": "msg_002",
        "role": "assistant",
        "content": "你好！我是智能助手，有什么可以帮助您的吗？",
        "timestamp": "2025-07-01T11:36:58+08:00",
        "tokens": 15
      }
    ],
    "totalTokens": 17
  }
}
```

### 4. 删除会话

**接口地址**: `DELETE /conversations/{conversationId}`

**响应格式**:
```json
{
  "code": 200,
  "message": "会话删除成功",
  "data": null
}
```

## 系统管理接口

### 1. 健康检查

**接口地址**: `GET /health`

**响应格式**:
```json
{
  "status": "healthy",
  "timestamp": "2025-07-01T11:36:57+08:00",
  "version": "1.0.0",
  "services": {
    "database": "healthy",
    "redis": "healthy",
    "llm_providers": {
      "openai": "healthy",
      "zhipu": "healthy",
      "dashscope": "healthy"
    }
  },
  "uptime": 86400
}
```

### 2. 系统统计

**接口地址**: `GET /stats`

**响应格式**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "totalUsers": 1000,
    "totalConversations": 5000,
    "totalMessages": 50000,
    "todayMessages": 500,
    "totalTokens": 1000000,
    "todayTokens": 10000,
    "modelUsage": {
      "gpt-4": 40,
      "gpt-3.5-turbo": 35,
      "glm-4": 15,
      "qwen-turbo": 10
    }
  }
}
```

### 3. 配置管理

**接口地址**: `GET /config` 和 `PUT /config`

**GET响应格式**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "maxTokensPerRequest": 4000,
    "defaultModel": "gpt-3.5-turbo",
    "rateLimitPerMinute": 60,
    "enableStreamResponse": true,
    "enableLogging": true,
    "logLevel": "info"
  }
}
```

**PUT请求参数**:
```json
{
  "maxTokensPerRequest": 8000,
  "defaultModel": "gpt-4",
  "rateLimitPerMinute": 100
}
```

## 错误码说明

### HTTP状态码
- `200`: 请求成功
- `400`: 请求参数错误
- `401`: 认证失败
- `403`: 权限不足
- `404`: 资源不存在
- `429`: 请求频率超限
- `500`: 服务器内部错误
- `503`: 服务暂时不可用

### 业务错误码
```json
{
  "code": 40001,
  "message": "API密钥无效",
  "data": null,
  "timestamp": "2025-07-01T11:36:57+08:00",
  "requestId": "req_123456"
}
```

**常见错误码**:
- `40001`: API密钥无效
- `40002`: 签名验证失败
- `40003`: 参数格式错误
- `40004`: 模型不支持
- `40005`: Token超出限制
- `42901`: 请求频率超限
- `50001`: LLM服务调用失败
- `50002`: 数据库连接异常
- `50003`: 缓存服务异常

## SDK使用示例

### Node.js SDK

```javascript
const { DingTalkBotClient } = require('dingtalk-bot-sdk');

// 初始化客户端
const client = new DingTalkBotClient({
  baseURL: 'https://your-domain.com/api',
  apiKey: 'your-api-key'
});

// 调用LLM
async function chatWithLLM() {
  const response = await client.chat.completions.create({
    model: 'gpt-4',
    messages: [
      { role: 'user', content: '你好' }
    ]
  });
  
  console.log(response.choices[0].message.content);
}

// 创建会话
async function createConversation() {
  const conversation = await client.conversations.create({
    userId: 'user_123',
    title: '新的对话',
    model: 'gpt-4'
  });
  
  return conversation.conversationId;
}
```

### Python SDK

```python
from dingtalk_bot_sdk import DingTalkBotClient

# 初始化客户端
client = DingTalkBotClient(
    base_url='https://your-domain.com/api',
    api_key='your-api-key'
)

# 调用LLM
def chat_with_llm():
    response = client.chat.completions.create(
        model='gpt-4',
        messages=[
            {'role': 'user', 'content': '你好'}
        ]
    )
    
    return response.choices[0].message.content

# 流式调用
def stream_chat():
    stream = client.chat.completions.create(
        model='gpt-4',
        messages=[{'role': 'user', 'content': '写一篇关于AI的文章'}],
        stream=True
    )
    
    for chunk in stream:
        if chunk.choices[0].delta.content:
            print(chunk.choices[0].delta.content, end='')
```

### cURL 示例

```bash
# 调用LLM接口
curl -X POST https://your-domain.com/api/chat/completions \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4",
    "messages": [
      {"role": "user", "content": "你好"}
    ]
  }'

# 获取模型列表
curl -X GET https://your-domain.com/api/models \
  -H "Authorization: Bearer your-api-key"

# 健康检查
curl -X GET https://your-domain.com/api/health
```

## 部署说明

### Docker 部署

```dockerfile
# Dockerfile示例
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
EXPOSE 3000
CMD ["npm", "start"]
```

```yaml
# docker-compose.yml
version: '3.8'
services:
  dingtalk-bot:
    build: .
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=production
      - DATABASE_URL=mysql://user:pass@db:3306/dingtalk_bot
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis
      
  db:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: rootpassword
      MYSQL_DATABASE: dingtalk_bot
    volumes:
      - mysql_data:/var/lib/mysql
      
  redis:
    image: redis:7-alpine
    
volumes:
  mysql_data:
```

### 环境变量配置

```bash
# .env
NODE_ENV=production
PORT=3000

# 数据库配置
DATABASE_URL=mysql://username:password@localhost:3306/dingtalk_bot
REDIS_URL=redis://localhost:6379

# 钉钉配置
DINGTALK_APP_KEY=your_app_key
DINGTALK_APP_SECRET=your_app_secret
DINGTALK_WEBHOOK_SECRET=your_webhook_secret

# LLM API配置
OPENAI_API_KEY=your_openai_key
OPENAI_BASE_URL=https://api.openai.com/v1
ZHIPU_API_KEY=your_zhipu_key
DASHSCOPE_API_KEY=your_dashscope_key

# 安全配置
JWT_SECRET=your_jwt_secret
API_RATE_LIMIT=100
MAX_TOKENS_PER_REQUEST=4000
```

## 常见问题FAQ

### Q: 如何获取钉钉机器人的配置信息？
A: 登录钉钉开放平台(https://open-dev.dingtalk.com/)，创建企业内部应用或机器人应用，获取AppKey、AppSecret和Webhook地址。

### Q: 支持哪些LLM模型？
A: 目前支持OpenAI (GPT-3.5/GPT-4)、智谱AI (GLM-4)、阿里云通义千问、Anthropic Claude等主流模型。

### Q: 如何实现流式响应？
A: 在调用`/chat/completions`接口时，设置`stream: true`参数，服务器将返回Server-Sent Events格式的流式数据。

### Q: 如何控制对话的上下文长度？
A: 系统会自动管理上下文窗口，当对话长度超过模型限制时，会智能截断早期消息，保留最近的对话内容。

### Q: 如何监控系统性能？
A: 可以通过`/health`和`/stats`接口监控系统状态，建议配置Prometheus + Grafana进行可视化监控。

---

**文档更新时间**: 2025-07-01 11:36:57 +08:00  
**技术支持**: 如有问题请联系开发团队或查看GitHub Issues 