# 钉钉机器人 MCP K8s 集成系统

基于现有钉钉机器人LLM集成架构，扩展支持MCP工具调用能力，特别是k8s-client工具来操作阿里云ACK集群，实现通过快捷指令触发的智能化运维工作流。

## 🏗️ 架构设计

```
快捷指令 → 钉钉机器人 → LLM引擎 → MCP工具链 → K8s集群
    ↓         ↓         ↓         ↓         ↓
  指令解析   消息处理   智能推理   工具调用   集群操作
```

## ✨ 核心特性

- 🔧 **MCP协议集成** - 支持标准MCP工具调用
- ⚡ **快捷指令处理** - 智能参数提取和命令执行
- 🧠 **LLM智能推理** - 基于上下文的工具选择
- 🔒 **多层安全控制** - RBAC权限管理和操作审计
- 📊 **可视化结果展示** - 友好的运维结果格式化
- 🌐 **多集群管理** - 支持阿里云ACK集群接入

## 🚀 快速开始

### 1. 安装依赖

```bash
npm install
```

### 2. 配置环境

```bash
cp .env.example .env
# 编辑 .env 文件，配置必要的参数
```

### 3. 构建项目

```bash
npm run build
```

### 4. 运行演示

```bash
npm run dev
```

## 📖 核心组件

### MCP 客户端 (MCPClient)

负责与MCP服务器通信，管理工具注册和调用：

```typescript
import { MCPClient } from './src/services/mcp/MCPClient';

const mcpClient = new MCPClient({
  timeout: 30000,
  retryAttempts: 3,
  enableCache: true
});

await mcpClient.connect();
const tools = await mcpClient.listTools();
const result = await mcpClient.callTool('k8s-get-pods', { namespace: 'default' });
```

### 增强版 LLM 处理器 (EnhancedLLMProcessor)

集成MCP工具调用的智能LLM处理器：

```typescript
import { EnhancedLLMProcessor } from './src/services/llm/EnhancedLLMProcessor';

const processor = new EnhancedLLMProcessor(llmConfig, mcpClient);
await processor.initializeMCP();

// 智能工具调用
const result = await processor.processChatWithTools([
  { role: 'user', content: '请帮我查看default命名空间的pod状态' }
]);

// 快捷指令
const shortcutResult = await processor.processShortcutCommand('查看pod');
```

## 🔧 支持的工具

### Kubernetes 工具

- **k8s-get-pods** - 获取 Pod 列表
  ```json
  {
    "namespace": "default",
    "labelSelector": "app=nginx"
  }
  ```

- **k8s-scale-deployment** - 扩缩容部署
  ```json
  {
    "name": "nginx-deployment",
    "replicas": 5,
    "namespace": "default"
  }
  ```

### 快捷指令映射

- `查看pod` → `k8s-get-pods`
- `扩容` → `k8s-scale-deployment`
- `缩容` → `k8s-scale-deployment`

## 📊 使用示例

### 1. 直接工具调用

```typescript
// 查看 Pod 状态
const pods = await mcpClient.callTool('k8s-get-pods', {
  namespace: 'production',
  labelSelector: 'app=web'
});

console.log(`找到 ${pods.items.length} 个 Pod`);
```

### 2. LLM 智能调用

```typescript
const messages = [
  { 
    role: 'user', 
    content: '帮我把生产环境的web应用扩容到10个副本' 
  }
];

const result = await processor.processChatWithTools(messages);
console.log(result.content); // LLM的智能响应
```

### 3. 快捷指令执行

```typescript
// 通过快捷指令查看 Pod
const result = await processor.processShortcutCommand('查看pod', {
  namespace: 'staging'
});

console.log(result.content);
```

## 🔒 安全控制

- **权限验证** - 基于用户角色的工具访问控制
- **操作审计** - 记录所有工具调用历史
- **参数验证** - 严格的输入参数校验
- **错误处理** - 完善的异常处理和回滚机制

## 📈 监控统计

系统提供详细的运行统计：

```typescript
const stats = mcpClient.getStats();
console.log(`总调用次数: ${stats.totalCalls}`);
console.log(`成功率: ${(stats.successfulCalls / stats.totalCalls * 100).toFixed(1)}%`);
console.log(`平均执行时间: ${stats.averageExecutionTime}ms`);
```

## 🔄 扩展开发

### 添加新工具

1. 在 `MCPClient` 中注册新工具
2. 在 `EnhancedLLMProcessor` 中添加工具描述
3. 实现工具的执行逻辑

### 添加快捷指令

在 `parseShortcutCommand` 方法中添加新的指令映射：

```typescript
const shortcuts = {
  '查看服务': { tool: 'k8s-get-services' },
  '重启应用': { tool: 'k8s-restart-deployment' }
};
```

## 🛠️ 开发指南

### 项目结构

```
src/
├── types/mcp.ts              # MCP 类型定义
├── services/
│   ├── mcp/MCPClient.ts      # MCP 客户端
│   └── llm/                  # LLM 处理器
│       ├── BaseLLMProcessor.ts
│       └── EnhancedLLMProcessor.ts
└── examples/
    └── mcp-demo.ts           # 使用示例
```

### 类型系统

项目使用 TypeScript 提供完整的类型安全：

- `MCPTool` - MCP 工具定义
- `MCPToolCall` - 工具调用请求
- `MCPToolResult` - 工具调用结果
- `ProcessResult` - LLM 处理结果

## 📋 任务状态

✅ **已完成：MCP客户端集成模块开发**
- MCP 协议客户端实现
- 工具注册和调用管理
- 增强版 LLM 处理器
- 完整的示例应用

## 🔗 相关文档

- [钉钉机器人API文档](./project_document/dingtalk-bot-api-documentation.md)
- [MCP协议规范](https://modelcontextprotocol.io/)
- [Kubernetes API参考](https://kubernetes.io/docs/reference/)

## 📄 License

本项目基于 MIT License 发布，详见 [LICENSE](LICENSE) 文件。

## 📞 支持

如有问题，请：
1. 查看示例代码：`src/examples/mcp-demo.ts`
2. 检查类型定义：`src/types/mcp.ts`
3. 参考现有实现进行扩展

---