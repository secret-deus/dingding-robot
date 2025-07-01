"""
钉钉机器人集成模块 - Python版本
处理钉钉消息，集成 LLM 和 MCP 工具链
"""

import json
import hashlib
import hmac
import base64
from typing import Dict, List, Optional, Any
from datetime import datetime
from loguru import logger
import httpx
from pydantic import BaseModel

from ..llm.processor import EnhancedLLMProcessor
from ..mcp.types import ChatMessage, MCPException


class DingTalkMessage(BaseModel):
    """钉钉消息结构"""
    msgtype: str
    text: Optional[Dict[str, str]] = None
    markdown: Optional[Dict[str, str]] = None
    at: Optional[Dict[str, List[str]]] = None


class DingTalkWebhookRequest(BaseModel):
    """钉钉Webhook请求结构"""
    msgId: str
    msgtype: str
    text: Dict[str, str]
    chatbotUserId: str
    conversationId: str
    atUsers: Optional[List[Dict[str, str]]] = None
    conversationType: str
    conversationTitle: Optional[str] = None
    senderId: str
    senderNick: str
    senderCorpId: Optional[str] = None
    sessionWebhook: str
    createAt: int
    senderStaffId: Optional[str] = None
    isAdmin: Optional[bool] = None
    robotCode: Optional[str] = None


class DingTalkBot:
    """钉钉机器人处理器"""
    
    def __init__(
        self, 
        webhook_url: str,
        secret: Optional[str] = None,
        llm_processor: Optional[EnhancedLLMProcessor] = None
    ):
        self.webhook_url = webhook_url
        self.secret = secret
        self.llm_processor = llm_processor
        
    async def process_webhook(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理钉钉Webhook请求"""
        try:
            # 解析请求
            webhook_request = DingTalkWebhookRequest(**request_data)
            logger.info(f"收到钉钉消息: {webhook_request.text.get('content', '')}")
            
            # 处理消息
            response_content = await self._process_message(webhook_request)
            
            # 构建响应
            response = await self._build_response(webhook_request, response_content)
            
            # 发送响应
            await self._send_response(webhook_request.sessionWebhook, response)
            
            return {"success": True, "message": "消息处理成功"}
            
        except Exception as e:
            logger.error(f"处理钉钉消息失败: {e}")
            return {"success": False, "error": str(e)}
    
    async def _process_message(self, request: DingTalkWebhookRequest) -> str:
        """处理消息内容"""
        content = request.text.get("content", "").strip()
        
        if not content:
            return "请发送有效的消息内容"
        
        # 检查是否为快捷指令
        if content.startswith("/"):
            return await self._process_shortcut_command(content, request)
        
        # 检查是否需要AI处理
        if self._should_process_with_ai(content, request):
            return await self._process_with_llm(content, request)
        
        # 默认响应
        return self._get_default_response(content)
    
    async def _process_shortcut_command(
        self, 
        content: str, 
        request: DingTalkWebhookRequest
    ) -> str:
        """处理快捷指令"""
        if not self.llm_processor:
            return "❌ LLM处理器未配置，无法执行快捷指令"
        
        parts = content.split(" ", 1)
        shortcut = parts[0]
        additional_content = parts[1] if len(parts) > 1 else ""
        
        try:
            context = {
                "user_id": request.senderId,
                "user_name": request.senderNick,
                "conversation_id": request.conversationId
            }
            
            result = await self.llm_processor.chat_with_shortcuts(
                shortcut, additional_content, context
            )
            
            return result.content
            
        except MCPException as e:
            logger.error(f"快捷指令处理失败: {e}")
            return f"❌ 指令执行失败: {e.message}"
        except Exception as e:
            logger.error(f"快捷指令处理异常: {e}")
            return f"❌ 指令执行异常: {str(e)}"
    
    async def _process_with_llm(
        self, 
        content: str, 
        request: DingTalkWebhookRequest
    ) -> str:
        """使用LLM处理消息"""
        if not self.llm_processor:
            return "❌ LLM处理器未配置"
        
        try:
            messages = [
                ChatMessage(
                    role="system",
                    content="你是一个专业的Kubernetes运维助手，可以帮助用户管理和监控K8s集群。"
                ),
                ChatMessage(
                    role="user", 
                    content=content
                )
            ]
            
            # 启用工具调用
            result = await self.llm_processor.chat(messages, enable_tools=True)
            return result.content
            
        except MCPException as e:
            logger.error(f"LLM处理失败: {e}")
            return f"❌ AI处理失败: {e.message}"
        except Exception as e:
            logger.error(f"LLM处理异常: {e}")
            return f"❌ AI处理异常: {str(e)}"
    
    def _should_process_with_ai(
        self, 
        content: str, 
        request: DingTalkWebhookRequest
    ) -> bool:
        """判断是否需要AI处理"""
        # 被@的情况
        if request.atUsers and any(user.get("dingtalkId") == request.chatbotUserId for user in request.atUsers):
            return True
        
        # 包含关键词的情况
        keywords = ["帮助", "查看", "监控", "集群", "pod", "deployment", "日志", "状态", "扩缩容"]
        return any(keyword in content.lower() for keyword in keywords)
    
    def _get_default_response(self, content: str) -> str:
        """获取默认响应"""
        if "help" in content.lower() or "帮助" in content:
            return self._get_help_message()
        
        return f"收到消息: {content}\n\n💡 使用快捷指令或@我来获取AI助手服务！"
    
    def _get_help_message(self) -> str:
        """获取帮助信息"""
        return """🤖 **钉钉K8s运维机器人**

**🚀 快捷指令:**
• `/pods` - 查看Pod列表
• `/logs <pod名称>` - 查看Pod日志  
• `/scale <deployment> <副本数>` - 扩缩容
• `/status` - 集群状态检查
• `/help` - 显示此帮助

**💬 智能对话:**
• @我 + 问题：智能回答K8s相关问题
• 支持自然语言描述运维需求

**📋 示例:**
• `/pods default` - 查看default命名空间的pods
• `/logs nginx-pod` - 查看nginx-pod的日志  
• `@机器人 帮我查看集群中有哪些异常的pod` - 智能分析
"""
    
    async def _build_response(
        self, 
        request: DingTalkWebhookRequest, 
        content: str
    ) -> DingTalkMessage:
        """构建响应消息"""
        # 限制消息长度
        if len(content) > 4000:
            content = content[:3900] + "\n\n... (内容过长，已截断)"
        
        # Markdown格式支持
        if self._is_markdown_content(content):
            return DingTalkMessage(
                msgtype="markdown",
                markdown={
                    "title": "K8s运维助手",
                    "text": content
                }
            )
        else:
            return DingTalkMessage(
                msgtype="text",
                text={"content": content}
            )
    
    def _is_markdown_content(self, content: str) -> bool:
        """检查内容是否包含Markdown格式"""
        markdown_indicators = ["**", "```", "###", "•", "📦", "✅", "❌"]
        return any(indicator in content for indicator in markdown_indicators)
    
    async def _send_response(self, session_webhook: str, message: DingTalkMessage) -> None:
        """发送响应消息"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    session_webhook,
                    json=message.model_dump(exclude_none=True),
                    headers={"Content-Type": "application/json"},
                    timeout=30
                )
                
                if response.status_code == 200:
                    logger.info("钉钉消息发送成功")
                else:
                    logger.error(f"钉钉消息发送失败: {response.status_code} - {response.text}")
                    
        except Exception as e:
            logger.error(f"发送钉钉消息异常: {e}")
    
    def verify_signature(self, timestamp: str, signature: str) -> bool:
        """验证钉钉签名"""
        if not self.secret:
            return True  # 如果没有配置secret，跳过验证
        
        try:
            string_to_sign = f"{timestamp}\n{self.secret}"
            hmac_code = hmac.new(
                self.secret.encode("utf-8"),
                string_to_sign.encode("utf-8"),
                digestmod=hashlib.sha256
            ).digest()
            sign = base64.b64encode(hmac_code).decode("utf-8")
            return sign == signature
        except Exception as e:
            logger.error(f"签名验证失败: {e}")
            return False
    
    async def send_proactive_message(
        self, 
        webhook_url: str, 
        content: str, 
        at_users: Optional[List[str]] = None
    ) -> bool:
        """主动发送消息"""
        try:
            message_data = {
                "msgtype": "text",
                "text": {"content": content}
            }
            
            if at_users:
                message_data["at"] = {
                    "atMobiles": at_users,
                    "isAtAll": False
                }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    webhook_url,
                    json=message_data,
                    headers={"Content-Type": "application/json"},
                    timeout=30
                )
                
                if response.status_code == 200:
                    logger.info("主动消息发送成功")
                    return True
                else:
                    logger.error(f"主动消息发送失败: {response.status_code} - {response.text}")
                    return False
                    
        except Exception as e:
            logger.error(f"发送主动消息异常: {e}")
            return False
    
    async def get_bot_info(self) -> Dict[str, Any]:
        """获取机器人信息"""
        if self.llm_processor and self.llm_processor.mcp_client:
            tools = await self.llm_processor.mcp_client.list_tools()
            stats = self.llm_processor.mcp_client.get_stats()
            shortcuts = await self.llm_processor.get_available_shortcuts()
            
            return {
                "status": "active",
                "mcp_status": self.llm_processor.mcp_client.status.value,
                "available_tools": len(tools),
                "available_shortcuts": list(shortcuts.keys()),
                "stats": stats.model_dump()
            }
        else:
            return {
                "status": "basic",
                "mcp_status": "not_configured",
                "available_tools": 0,
                "available_shortcuts": ["/help"],
                "stats": {}
            } 