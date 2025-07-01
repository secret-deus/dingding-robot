"""
MCP (Model Context Protocol) 类型定义 - Python版本
"""

from typing import Dict, List, Optional, Any, Union, Literal
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class MCPConnectionStatus(str, Enum):
    """MCP连接状态"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"


class MCPTool(BaseModel):
    """MCP工具定义"""
    name: str = Field(..., description="工具名称")
    description: str = Field(..., description="工具描述")
    input_schema: Dict[str, Any] = Field(..., description="输入参数schema")
    category: Optional[str] = Field(None, description="工具分类")
    version: Optional[str] = Field(None, description="工具版本")
    provider: Optional[str] = Field(None, description="工具提供者")


class MCPToolCall(BaseModel):
    """MCP工具调用请求"""
    id: str = Field(..., description="调用ID")
    name: str = Field(..., description="工具名称")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="调用参数")
    context: Optional[Dict[str, Any]] = Field(None, description="调用上下文")


class MCPError(BaseModel):
    """MCP错误信息"""
    code: str = Field(..., description="错误代码")
    message: str = Field(..., description="错误消息")
    details: Optional[Any] = Field(None, description="错误详情")


class MCPToolResult(BaseModel):
    """MCP工具调用结果"""
    id: str = Field(..., description="调用ID")
    tool_name: str = Field(..., description="工具名称")
    success: bool = Field(..., description="是否成功")
    result: Optional[Any] = Field(None, description="调用结果")
    error: Optional[MCPError] = Field(None, description="错误信息")
    execution_time: float = Field(..., description="执行时间(ms)")
    timestamp: datetime = Field(default_factory=datetime.now, description="执行时间戳")


class MCPClientConfig(BaseModel):
    """MCP客户端配置"""
    timeout: int = Field(default=30000, description="超时时间(ms)")
    retry_attempts: int = Field(default=3, description="重试次数")
    retry_delay: int = Field(default=1000, description="重试延迟(ms)")
    max_concurrent_calls: int = Field(default=5, description="最大并发调用数")
    enable_cache: bool = Field(default=True, description="是否启用缓存")
    cache_timeout: int = Field(default=300000, description="缓存超时时间(ms)")


class MCPStats(BaseModel):
    """MCP统计信息"""
    total_calls: int = Field(default=0, description="总调用次数")
    successful_calls: int = Field(default=0, description="成功调用次数")
    failed_calls: int = Field(default=0, description="失败调用次数")
    average_execution_time: float = Field(default=0, description="平均执行时间")
    cache_hit_rate: float = Field(default=0, description="缓存命中率")
    active_tools: int = Field(default=0, description="活跃工具数")


class FunctionCall(BaseModel):
    """LLM函数调用"""
    name: str = Field(..., description="函数名称")
    arguments: str = Field(..., description="函数参数(JSON字符串)")


class FunctionCallResult(BaseModel):
    """LLM函数调用结果"""
    function_call: FunctionCall = Field(..., description="函数调用信息")
    result: Optional[Any] = Field(None, description="调用结果")
    error: Optional[str] = Field(None, description="错误信息")


class ChatMessage(BaseModel):
    """聊天消息"""
    role: Literal["system", "user", "assistant", "tool"] = Field(..., description="消息角色")
    content: str = Field(..., description="消息内容")
    tool_call_id: Optional[str] = Field(None, description="工具调用ID")
    function_call: Optional[FunctionCall] = Field(None, description="函数调用")


class ProcessResult(BaseModel):
    """LLM处理结果"""
    content: str = Field(..., description="响应内容")
    function_calls: Optional[List[FunctionCallResult]] = Field(None, description="函数调用结果")
    conversation_id: Optional[str] = Field(None, description="会话ID")
    usage: Optional[Dict[str, int]] = Field(None, description="Token使用情况")


class LLMConfig(BaseModel):
    """LLM配置"""
    provider: Literal["openai", "zhipu", "qwen"] = Field(..., description="LLM提供商")
    model: str = Field(..., description="模型名称")
    api_key: str = Field(..., description="API密钥")
    base_url: Optional[str] = Field(None, description="API基础URL")
    temperature: float = Field(default=0.7, description="温度参数")
    max_tokens: int = Field(default=2000, description="最大Token数")


class MCPException(Exception):
    """MCP异常类"""
    
    def __init__(self, code: str, message: str, details: Any = None, tool_name: Optional[str] = None):
        self.code = code
        self.message = message
        self.details = details
        self.tool_name = tool_name
        super().__init__(f"{code}: {message}") 