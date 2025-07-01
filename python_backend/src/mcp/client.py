"""
MCP 客户端 - Python版本
负责与 MCP 服务器通信，管理工具注册和调用
"""

import asyncio
import random
import json
import time
import hashlib
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from loguru import logger

from .types import (
    MCPTool, MCPToolCall, MCPToolResult, MCPClientConfig,
    MCPConnectionStatus, MCPStats, MCPException
)


class MCPClient:
    """MCP 客户端实现"""
    
    def __init__(self, config: MCPClientConfig):
        self.config = config
        self.status = MCPConnectionStatus.DISCONNECTED
        self.tools: Dict[str, MCPTool] = {}
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.stats = MCPStats()
        self._semaphore = asyncio.Semaphore(config.max_concurrent_calls)
        
    async def connect(self) -> None:
        """连接到 MCP 服务器"""
        try:
            self.status = MCPConnectionStatus.CONNECTING
            logger.info("正在连接 MCP 服务器...")
            
            # 模拟连接过程
            await self._initialize_mcp_connection()
            await self._discover_tools()
            
            self.status = MCPConnectionStatus.CONNECTED
            logger.info("MCP 客户端连接成功")
            
        except Exception as e:
            self.status = MCPConnectionStatus.ERROR
            logger.error(f"MCP 连接失败: {e}")
            raise MCPException("CONNECTION_FAILED", "Failed to connect to MCP server", str(e))
    
    async def disconnect(self) -> None:
        """断开连接"""
        self.status = MCPConnectionStatus.DISCONNECTED
        self.tools.clear()
        self.cache.clear()
        logger.info("MCP 客户端已断开连接")
    
    async def list_tools(self) -> List[MCPTool]:
        """获取所有可用工具"""
        if self.status != MCPConnectionStatus.CONNECTED:
            raise MCPException("NOT_CONNECTED", "MCP client is not connected")
        return list(self.tools.values())
    
    def get_tool(self, name: str) -> Optional[MCPTool]:
        """获取特定工具信息"""
        return self.tools.get(name)
    
    async def call_tool(
        self, 
        name: str, 
        parameters: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Any:
        """调用 MCP 工具"""
        async with self._semaphore:
            start_time = time.time()
            call_id = self._generate_call_id()
            
            try:
                # 验证工具存在性
                tool = self.tools.get(name)
                if not tool:
                    raise MCPException("TOOL_NOT_FOUND", f"Tool '{name}' not found", tool_name=name)
                
                # 验证参数
                self._validate_parameters(tool, parameters)
                
                # 检查缓存
                if self.config.enable_cache:
                    cached_result = self._get_cached_result(name, parameters)
                    if cached_result:
                        self._update_stats(True, (time.time() - start_time) * 1000, True)
                        return cached_result
                
                # 创建工具调用对象
                tool_call = MCPToolCall(
                    id=call_id,
                    name=name,
                    parameters=parameters,
                    context=context
                )
                
                # 执行工具调用
                result = await self._execute_tool_call(tool_call)
                
                # 缓存结果
                if self.config.enable_cache and result.success:
                    self._cache_result(name, parameters, result.result)
                
                execution_time = (time.time() - start_time) * 1000
                self._update_stats(result.success, execution_time, False)
                
                if not result.success:
                    raise MCPException(
                        "EXECUTION_FAILED", 
                        result.error.message if result.error else "Tool execution failed",
                        result.error.details if result.error else None,
                        name
                    )
                
                return result.result
                
            except MCPException:
                raise
            except Exception as e:
                execution_time = (time.time() - start_time) * 1000
                self._update_stats(False, execution_time, False)
                raise MCPException("EXECUTION_FAILED", "Tool execution failed", str(e), name)
    
    async def call_tools_batch(
        self, 
        calls: List[Dict[str, Any]]
    ) -> List[MCPToolResult]:
        """批量调用工具"""
        tasks = []
        for call in calls:
            task = self._call_tool_safe(call["name"], call["parameters"])
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        formatted_results = []
        for i, result in enumerate(results):
            call = calls[i]
            call_id = self._generate_call_id()
            
            if isinstance(result, Exception):
                formatted_results.append(MCPToolResult(
                    id=call_id,
                    tool_name=call["name"],
                    success=False,
                    error={
                        "code": "EXECUTION_ERROR",
                        "message": str(result),
                        "details": None
                    },
                    execution_time=0,
                    timestamp=datetime.now()
                ))
            else:
                formatted_results.append(MCPToolResult(
                    id=call_id,
                    tool_name=call["name"],
                    success=True,
                    result=result,
                    execution_time=0,
                    timestamp=datetime.now()
                ))
        
        return formatted_results
    
    def get_stats(self) -> MCPStats:
        """获取统计信息"""
        return self.stats.model_copy()
    
    def reset_stats(self) -> None:
        """重置统计信息"""
        self.stats = MCPStats(active_tools=len(self.tools))
    
    # 私有方法
    
    async def _initialize_mcp_connection(self) -> None:
        """初始化 MCP 连接"""
        # 模拟连接延迟
        await asyncio.sleep(0.1)
    
    async def _discover_tools(self) -> None:
        """发现可用工具"""
        # 模拟工具发现过程，注册 K8s 相关工具
        mock_tools = [
            MCPTool(
                name="k8s-get-pods",
                description="获取 Kubernetes Pod 列表",
                input_schema={
                    "type": "object",
                    "properties": {
                        "namespace": {"type": "string", "description": "命名空间"},
                        "label_selector": {"type": "string", "description": "标签选择器"}
                    }
                },
                category="kubernetes"
            ),
            MCPTool(
                name="k8s-scale-deployment",
                description="扩缩容 Kubernetes Deployment",
                input_schema={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "部署名称"},
                        "replicas": {"type": "number", "description": "副本数"},
                        "namespace": {"type": "string", "description": "命名空间"}
                    },
                    "required": ["name", "replicas"]
                },
                category="kubernetes"
            ),
            MCPTool(
                name="k8s-get-logs",
                description="获取 Pod 日志",
                input_schema={
                    "type": "object",
                    "properties": {
                        "pod_name": {"type": "string", "description": "Pod名称"},
                        "namespace": {"type": "string", "description": "命名空间"},
                        "lines": {"type": "number", "description": "行数"}
                    },
                    "required": ["pod_name"]
                },
                category="kubernetes"
            ),
            MCPTool(
                name="k8s-describe-pod",
                description="查看 Pod 详细信息",
                input_schema={
                    "type": "object",
                    "properties": {
                        "pod_name": {"type": "string", "description": "Pod名称"},
                        "namespace": {"type": "string", "description": "命名空间"}
                    },
                    "required": ["pod_name"]
                },
                category="kubernetes"
            )
        ]
        
        for tool in mock_tools:
            self.tools[tool.name] = tool
        
        self.stats.active_tools = len(self.tools)
        logger.info(f"发现 {len(self.tools)} 个可用工具")
    
    def _validate_parameters(self, tool: MCPTool, parameters: Dict[str, Any]) -> None:
        """验证参数"""
        required = tool.input_schema.get("required", [])
        for param in required:
            if param not in parameters:
                raise MCPException(
                    "INVALID_PARAMETERS", 
                    f"Missing required parameter: {param}",
                    tool_name=tool.name
                )
    
    def _get_cached_result(self, name: str, parameters: Dict[str, Any]) -> Optional[Any]:
        """获取缓存结果"""
        cache_key = self._generate_cache_key(name, parameters)
        cached = self.cache.get(cache_key)
        
        if cached and cached["expire_at"] > datetime.now():
            cached["hit_count"] += 1
            return cached["result"]
        
        if cached:
            del self.cache[cache_key]
        
        return None
    
    def _cache_result(self, name: str, parameters: Dict[str, Any], result: Any) -> None:
        """缓存结果"""
        cache_key = self._generate_cache_key(name, parameters)
        expire_at = datetime.now() + timedelta(milliseconds=self.config.cache_timeout)
        
        self.cache[cache_key] = {
            "result": result,
            "expire_at": expire_at,
            "hit_count": 0
        }
    
    async def _execute_tool_call(self, call: MCPToolCall) -> MCPToolResult:
        """执行工具调用"""
        start_time = time.time()
        
        try:
            # 模拟工具执行
            result = await self._simulate_tool_execution(call)
            
            return MCPToolResult(
                id=call.id,
                tool_name=call.name,
                success=True,
                result=result,
                execution_time=(time.time() - start_time) * 1000,
                timestamp=datetime.now()
            )
        except Exception as e:
            return MCPToolResult(
                id=call.id,
                tool_name=call.name,
                success=False,
                error={
                    "code": "EXECUTION_ERROR",
                    "message": str(e),
                    "details": None
                },
                execution_time=(time.time() - start_time) * 1000,
                timestamp=datetime.now()
            )
    
    async def _simulate_tool_execution(self, call: MCPToolCall) -> Any:
        """模拟工具执行"""
        # 添加随机延迟以模拟真实执行
        await asyncio.sleep(0.2 + 0.3 * random.random())
        
        if call.name == "k8s-get-pods":
            return {
                "items": [
                    {
                        "metadata": {
                            "name": "nginx-deployment-1",
                            "namespace": call.parameters.get("namespace", "default")
                        },
                        "status": {"phase": "Running"},
                        "spec": {"containers": [{"name": "nginx", "image": "nginx:1.20"}]}
                    },
                    {
                        "metadata": {
                            "name": "redis-deployment-1", 
                            "namespace": call.parameters.get("namespace", "default")
                        },
                        "status": {"phase": "Running"},
                        "spec": {"containers": [{"name": "redis", "image": "redis:6.2"}]}
                    }
                ]
            }
        
        elif call.name == "k8s-scale-deployment":
            return {
                "deployment_name": call.parameters["name"],
                "namespace": call.parameters.get("namespace", "default"),
                "previous_replicas": 2,
                "target_replicas": call.parameters["replicas"],
                "current_replicas": call.parameters["replicas"],
                "success": True
            }
        
        elif call.name == "k8s-get-logs":
            return {
                "pod_name": call.parameters["pod_name"],
                "namespace": call.parameters.get("namespace", "default"),
                "content": f"""[{datetime.now().isoformat()}] INFO: Application started successfully
[{datetime.now().isoformat()}] INFO: Listening on port 8080
[{datetime.now().isoformat()}] INFO: Health check passed""",
                "lines": call.parameters.get("lines", 100)
            }
        
        elif call.name == "k8s-describe-pod":
            return {
                "pod_name": call.parameters["pod_name"],
                "namespace": call.parameters.get("namespace", "default"),
                "status": "Running",
                "node": "worker-node-1",
                "ip": "10.244.1.10",
                "containers": [
                    {"name": "main", "image": "nginx:1.20", "status": "Running"}
                ],
                "events": [
                    {"type": "Normal", "reason": "Scheduled", "message": "Successfully assigned pod to node"},
                    {"type": "Normal", "reason": "Pulled", "message": "Container image pulled successfully"}
                ]
            }
        
        else:
            raise Exception(f"Unknown tool: {call.name}")
    
    async def _call_tool_safe(self, name: str, parameters: Dict[str, Any]) -> Any:
        """安全的工具调用（用于批量调用）"""
        try:
            return await self.call_tool(name, parameters)
        except Exception as e:
            raise e
    
    def _generate_call_id(self) -> str:
        """生成调用ID"""
        return f"call_{int(time.time() * 1000)}_{hash(time.time()) % 10000:04d}"
    
    def _generate_cache_key(self, name: str, parameters: Dict[str, Any]) -> str:
        """生成缓存键"""
        param_str = json.dumps(parameters, sort_keys=True)
        return f"{name}:{hashlib.md5(param_str.encode()).hexdigest()}"
    
    def _update_stats(self, success: bool, execution_time: float, from_cache: bool) -> None:
        """更新统计信息"""
        self.stats.total_calls += 1
        
        if success:
            self.stats.successful_calls += 1
        else:
            self.stats.failed_calls += 1
        
        # 更新平均执行时间
        total_time = self.stats.average_execution_time * (self.stats.total_calls - 1) + execution_time
        self.stats.average_execution_time = total_time / self.stats.total_calls
        
        # 更新缓存命中率
        if from_cache:
            cache_hits = round(self.stats.cache_hit_rate * (self.stats.total_calls - 1))
            self.stats.cache_hit_rate = (cache_hits + 1) / self.stats.total_calls
        else:
            cache_hits = round(self.stats.cache_hit_rate * (self.stats.total_calls - 1))
            self.stats.cache_hit_rate = cache_hits / self.stats.total_calls 