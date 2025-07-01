"""
LLM 处理器 - Python版本
支持多种 LLM 提供商，集成 MCP 工具调用功能
"""

import json
import time
from typing import Dict, List, Optional, Any
from loguru import logger
import openai
from tenacity import retry, stop_after_attempt, wait_exponential

from ..mcp.types import (
    LLMConfig, ChatMessage, ProcessResult, FunctionCall, FunctionCallResult,
    MCPException
)
from ..mcp.client import MCPClient


class EnhancedLLMProcessor:
    """增强版 LLM 处理器，支持 MCP 工具调用"""
    
    def __init__(self, llm_config: LLMConfig, mcp_client: MCPClient):
        self.config = llm_config
        self.mcp_client = mcp_client
        self.client = self._initialize_client()
        
    def _initialize_client(self):
        """初始化 LLM 客户端"""
        if self.config.provider == "openai":
            return openai.OpenAI(
                api_key=self.config.api_key,
                base_url=self.config.base_url
            )
        else:
            # 支持其他提供商
            raise NotImplementedError(f"Provider {self.config.provider} not implemented yet")
    
    async def chat(
        self,
        messages: List[ChatMessage],
        enable_tools: bool = False
    ) -> ProcessResult:
        """普通聊天处理"""
        try:
            if enable_tools and self.mcp_client.status.value == "connected":
                return await self._chat_with_tools(messages)
            else:
                return await self._chat_without_tools(messages)
        except Exception as e:
            logger.error(f"LLM 处理失败: {e}")
            raise MCPException("LLM_PROCESSING_FAILED", "LLM processing failed", str(e))
    
    async def chat_with_shortcuts(
        self,
        shortcut: str,
        content: str,
        context: Optional[Dict[str, Any]] = None
    ) -> ProcessResult:
        """快捷指令处理"""
        shortcut_prompts = {
            "/pods": "请获取Kubernetes集群中的Pod列表，并以易读的格式展示",
            "/logs": "请获取指定Pod的最新日志",
            "/scale": "请扩缩容指定的Deployment",
            "/status": "请检查集群状态和健康情况",
            "/help": "显示所有可用的快捷指令"
        }
        
        prompt = shortcut_prompts.get(shortcut)
        if not prompt:
            return ProcessResult(
                content=f"未知的快捷指令: {shortcut}\n\n可用指令:\n" + 
                       "\n".join(f"- {k}: {v}" for k, v in shortcut_prompts.items())
            )
        
        # 构建消息
        messages = [
            ChatMessage(role="system", content="你是一个专业的Kubernetes运维助手，擅长使用K8s工具来管理集群。"),
            ChatMessage(role="user", content=f"{prompt}\n\n用户补充信息: {content}")
        ]
        
        return await self.chat(messages, enable_tools=True)
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=60))
    async def _chat_without_tools(self, messages: List[ChatMessage]) -> ProcessResult:
        """不使用工具的聊天"""
        openai_messages = self._convert_messages_to_openai(messages)
        
        response = await self.client.chat.completions.acreate(
            model=self.config.model,
            messages=openai_messages,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens
        )
        
        return ProcessResult(
            content=response.choices[0].message.content,
            usage=response.usage.model_dump() if response.usage else None
        )
    
    async def _chat_with_tools(self, messages: List[ChatMessage]) -> ProcessResult:
        """使用工具的聊天"""
        # 获取可用工具
        tools = await self.mcp_client.list_tools()
        if not tools:
            return await self._chat_without_tools(messages)
        
        # 转换工具为 OpenAI 格式
        openai_tools = self._convert_tools_to_openai(tools)
        openai_messages = self._convert_messages_to_openai(messages)
        
        # 调用 LLM
        response = await self.client.chat.completions.acreate(
            model=self.config.model,
            messages=openai_messages,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            tools=openai_tools,
            tool_choice="auto"
        )
        
        message = response.choices[0].message
        
        # 如果没有工具调用，直接返回
        if not message.tool_calls:
            return ProcessResult(
                content=message.content,
                usage=response.usage.model_dump() if response.usage else None
            )
        
        # 执行工具调用
        function_results = []
        for tool_call in message.tool_calls:
            try:
                # 解析参数
                parameters = json.loads(tool_call.function.arguments)
                
                # 调用 MCP 工具
                result = await self.mcp_client.call_tool(
                    tool_call.function.name,
                    parameters
                )
                
                function_results.append(FunctionCallResult(
                    function_call=FunctionCall(
                        name=tool_call.function.name,
                        arguments=tool_call.function.arguments
                    ),
                    result=result
                ))
                
                # 将工具结果添加到消息历史
                openai_messages.append({
                    "role": "assistant",
                    "content": message.content,
                    "tool_calls": [{
                        "id": tool_call.id,
                        "type": "function",
                        "function": {
                            "name": tool_call.function.name,
                            "arguments": tool_call.function.arguments
                        }
                    }]
                })
                
                openai_messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result, ensure_ascii=False, indent=2)
                })
                
            except Exception as e:
                logger.error(f"工具调用失败 {tool_call.function.name}: {e}")
                function_results.append(FunctionCallResult(
                    function_call=FunctionCall(
                        name=tool_call.function.name,
                        arguments=tool_call.function.arguments
                    ),
                    error=str(e)
                ))
        
        # 如果有工具调用结果，再次调用 LLM 生成最终回复
        if function_results:
            final_response = await self.client.chat.completions.acreate(
                model=self.config.model,
                messages=openai_messages,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens
            )
            
            final_content = self._format_response_with_tools(
                final_response.choices[0].message.content,
                function_results
            )
            
            return ProcessResult(
                content=final_content,
                function_calls=function_results,
                usage=final_response.usage.model_dump() if final_response.usage else None
            )
        
        return ProcessResult(
            content=message.content or "执行完成",
            function_calls=function_results,
            usage=response.usage.model_dump() if response.usage else None
        )
    
    def _convert_messages_to_openai(self, messages: List[ChatMessage]) -> List[Dict[str, Any]]:
        """转换消息格式为 OpenAI 格式"""
        result = []
        for msg in messages:
            openai_msg = {
                "role": msg.role,
                "content": msg.content
            }
            
            if msg.tool_call_id:
                openai_msg["tool_call_id"] = msg.tool_call_id
                
            if msg.function_call:
                openai_msg["function_call"] = {
                    "name": msg.function_call.name,
                    "arguments": msg.function_call.arguments
                }
            
            result.append(openai_msg)
        
        return result
    
    def _convert_tools_to_openai(self, tools) -> List[Dict[str, Any]]:
        """转换 MCP 工具为 OpenAI 工具格式"""
        result = []
        for tool in tools:
            result.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.input_schema
                }
            })
        return result
    
    def _format_response_with_tools(
        self,
        content: str,
        function_results: List[FunctionCallResult]
    ) -> str:
        """格式化包含工具调用结果的响应"""
        if not function_results:
            return content
        
        formatted_content = content + "\n\n**工具调用详情:**\n"
        
        for i, result in enumerate(function_results, 1):
            formatted_content += f"\n**{i}. {result.function_call.name}**\n"
            
            if result.error:
                formatted_content += f"❌ 执行失败: {result.error}\n"
            else:
                formatted_content += f"✅ 执行成功\n"
                # 简化结果显示
                if isinstance(result.result, dict):
                    if "items" in result.result:
                        formatted_content += f"📊 返回 {len(result.result['items'])} 项结果\n"
                    else:
                        formatted_content += f"📋 结果: {json.dumps(result.result, ensure_ascii=False, indent=2)[:200]}...\n"
                else:
                    formatted_content += f"📋 结果: {str(result.result)[:200]}...\n"
        
        return formatted_content
    
    async def get_available_shortcuts(self) -> Dict[str, str]:
        """获取可用的快捷指令"""
        shortcuts = {
            "/pods": "查看Pod列表",
            "/logs": "查看Pod日志",
            "/scale": "扩缩容Deployment", 
            "/status": "检查集群状态",
            "/help": "显示帮助信息"
        }
        
        # 如果 MCP 客户端连接，添加工具相关的快捷指令
        if self.mcp_client.status.value == "connected":
            tools = await self.mcp_client.list_tools()
            for tool in tools:
                shortcuts[f"/tool-{tool.name}"] = f"直接调用工具: {tool.description}"
        
        return shortcuts
    
    def format_tool_result(self, result: Any) -> str:
        """格式化工具调用结果为用户友好的文本"""
        if isinstance(result, dict):
            if "items" in result and isinstance(result["items"], list):
                # K8s 资源列表格式
                items = result["items"]
                if not items:
                    return "📭 未找到任何资源"
                
                formatted = f"📦 找到 {len(items)} 个资源:\n\n"
                for item in items[:10]:  # 限制显示数量
                    metadata = item.get("metadata", {})
                    status = item.get("status", {})
                    formatted += f"• **{metadata.get('name', 'Unknown')}**\n"
                    formatted += f"  命名空间: {metadata.get('namespace', 'default')}\n"
                    formatted += f"  状态: {status.get('phase', 'Unknown')}\n\n"
                
                if len(items) > 10:
                    formatted += f"... 还有 {len(items) - 10} 个资源\n"
                
                return formatted
            
            elif "pod_name" in result and "content" in result:
                # 日志格式
                return f"📋 **{result['pod_name']}** 日志:\n\n```\n{result['content']}\n```"
            
            elif "deployment_name" in result:
                # 扩缩容结果格式
                return f"🔄 扩缩容完成:\n" + \
                       f"• 部署名称: {result['deployment_name']}\n" + \
                       f"• 命名空间: {result.get('namespace', 'default')}\n" + \
                       f"• 副本数: {result.get('previous_replicas', 0)} → {result.get('target_replicas', 0)}\n" + \
                       f"• 状态: {'✅ 成功' if result.get('success') else '❌ 失败'}"
            
            else:
                # 通用字典格式
                return f"📄 结果:\n```json\n{json.dumps(result, ensure_ascii=False, indent=2)}\n```"
        
        elif isinstance(result, list):
            return f"📋 列表结果 ({len(result)} 项):\n" + \
                   "\n".join(f"• {item}" for item in result[:10])
        
        else:
            return f"�� 结果: {str(result)}" 