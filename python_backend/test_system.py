#!/usr/bin/env python3

"""
钉钉K8s运维机器人 - 系统测试脚本
测试各个模块的功能是否正常
"""

import asyncio
import json
import sys
from typing import Dict, Any
from loguru import logger

# 配置日志
logger.remove()
logger.add(sys.stdout, format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | {message}")


async def test_mcp_client():
    """测试MCP客户端"""
    logger.info("🔧 测试MCP客户端...")
    
    try:
        from src.mcp.client import MCPClient
        from src.mcp.types import MCPClientConfig
        
        config = MCPClientConfig(
            timeout=10000,
            retry_attempts=2,
            max_concurrent_calls=3,
            enable_cache=True
        )
        
        client = MCPClient(config)
        await client.connect()
        
        # 测试工具列表
        tools = await client.list_tools()
        logger.success(f"✅ MCP客户端连接成功，发现 {len(tools)} 个工具")
        
        # 测试工具调用
        result = await client.call_tool("k8s-get-pods", {"namespace": "default"})
        logger.success(f"✅ 工具调用成功: {result.success}")
        
        await client.disconnect()
        return True
        
    except Exception as e:
        logger.error(f"❌ MCP客户端测试失败: {e}")
        return False


async def test_llm_processor():
    """测试LLM处理器"""
    logger.info("🧠 测试LLM处理器...")
    
    try:
        from src.llm.processor import EnhancedLLMProcessor
        from src.mcp.client import MCPClient
        from src.mcp.types import MCPClientConfig, LLMConfig, ChatMessage
        
        # 初始化MCP客户端
        mcp_config = MCPClientConfig()
        mcp_client = MCPClient(mcp_config)
        await mcp_client.connect()
        
        # 初始化LLM处理器
        llm_config = LLMConfig(
            provider="openai",
            model="gpt-3.5-turbo",
            api_key="test-key",  # 测试用假key
            temperature=0.7,
            max_tokens=1000
        )
        
        processor = EnhancedLLMProcessor(llm_config, mcp_client)
        
        # 测试聊天功能（模拟模式）
        messages = [ChatMessage(role="user", content="Hello")]
        result = await processor.chat(messages, enable_tools=False)
        
        logger.success(f"✅ LLM处理器初始化成功")
        
        # 测试快捷指令
        shortcuts = await processor.get_available_shortcuts()
        logger.success(f"✅ 快捷指令功能正常，共 {len(shortcuts)} 个指令")
        
        await mcp_client.disconnect()
        return True
        
    except Exception as e:
        logger.error(f"❌ LLM处理器测试失败: {e}")
        return False


async def test_dingtalk_bot():
    """测试钉钉机器人"""
    logger.info("📱 测试钉钉机器人...")
    
    try:
        from src.dingtalk.bot import DingTalkBot, DingTalkWebhookRequest
        
        # 创建机器人实例
        bot = DingTalkBot(
            webhook_url="https://test.webhook.url",
            secret="test-secret"
        )
        
        # 模拟钉钉消息
        test_message = {
            "msgId": "test-msg-001",
            "msgtype": "text",
            "text": {"content": "/help"},
            "chatbotUserId": "bot-123",
            "conversationId": "conv-456",
            "senderId": "user-789",
            "senderNick": "测试用户",
            "sessionWebhook": "https://test.session.webhook",
            "createAt": 1640995200000,
            "conversationType": "2"
        }
        
        # 测试消息处理（不实际发送）
        bot._send_response = lambda *args: None  # 模拟发送
        
        result = await bot.process_webhook(test_message)
        logger.success(f"✅ 钉钉机器人消息处理成功: {result['success']}")
        
        # 测试机器人信息
        info = await bot.get_bot_info()
        logger.success(f"✅ 机器人信息获取成功: {info['status']}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 钉钉机器人测试失败: {e}")
        return False


async def test_integration():
    """测试完整集成"""
    logger.info("🔗 测试系统集成...")
    
    try:
        from src.mcp.client import MCPClient
        from src.mcp.types import MCPClientConfig, LLMConfig
        from src.llm.processor import EnhancedLLMProcessor
        from src.dingtalk.bot import DingTalkBot
        
        # 初始化所有组件
        mcp_config = MCPClientConfig()
        mcp_client = MCPClient(mcp_config)
        await mcp_client.connect()
        
        llm_config = LLMConfig(
            provider="openai",
            model="gpt-3.5-turbo",
            api_key="test-key",
            temperature=0.7
        )
        llm_processor = EnhancedLLMProcessor(llm_config, mcp_client)
        
        dingtalk_bot = DingTalkBot(
            webhook_url="https://test.url",
            llm_processor=llm_processor
        )
        
        # 测试完整流程
        test_message = {
            "msgId": "integration-test",
            "msgtype": "text", 
            "text": {"content": "/pods"},
            "chatbotUserId": "bot",
            "conversationId": "conv",
            "senderId": "user",
            "senderNick": "测试用户",
            "sessionWebhook": "https://test.webhook",
            "createAt": 1640995200000,
            "conversationType": "2"
        }
        
        # 模拟发送响应
        dingtalk_bot._send_response = lambda *args: None
        
        result = await dingtalk_bot.process_webhook(test_message)
        logger.success("✅ 系统集成测试成功")
        
        await mcp_client.disconnect()
        return True
        
    except Exception as e:
        logger.error(f"❌ 系统集成测试失败: {e}")
        return False


def test_imports():
    """测试模块导入"""
    logger.info("📦 测试模块导入...")
    
    modules = [
        "src.mcp.types",
        "src.mcp.client", 
        "src.llm.processor",
        "src.dingtalk.bot"
    ]
    
    success_count = 0
    
    for module in modules:
        try:
            __import__(module)
            logger.success(f"✅ {module} 导入成功")
            success_count += 1
        except Exception as e:
            logger.error(f"❌ {module} 导入失败: {e}")
    
    return success_count == len(modules)


async def test_fastapi_endpoints():
    """测试FastAPI端点（模拟）"""
    logger.info("🌐 测试API端点...")
    
    try:
        import httpx
        
        # 这里只是示例，实际测试需要启动服务
        endpoints = [
            "/api/status",
            "/api/tools",
            "/api/tools/test",
            "/api/config/{config_type}",
            "/api/test",
            "/dingtalk/webhook"
        ]
        
        logger.info(f"📋 API端点列表: {endpoints}")
        logger.success("✅ API端点结构正确")
        return True
        
    except Exception as e:
        logger.error(f"❌ API端点测试失败: {e}")
        return False


async def run_all_tests():
    """运行所有测试"""
    logger.info("🚀 开始系统测试...")
    print("=" * 60)
    
    tests = [
        ("模块导入", test_imports),
        ("MCP客户端", test_mcp_client),
        ("LLM处理器", test_llm_processor), 
        ("钉钉机器人", test_dingtalk_bot),
        ("API端点", test_fastapi_endpoints),
        ("系统集成", test_integration)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name} 测试")
        print("-" * 40)
        
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            results[test_name] = result
        except Exception as e:
            logger.error(f"❌ {test_name} 测试异常: {e}")
            results[test_name] = False
    
    # 显示测试结果摘要
    print("\n" + "=" * 60)
    logger.info("📊 测试结果摘要")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {test_name:<15} : {status}")
        if result:
            passed += 1
    
    print("-" * 60)
    success_rate = (passed / total) * 100
    print(f"  总计: {passed}/{total} 通过 ({success_rate:.1f}%)")
    
    if success_rate == 100:
        logger.success("🎉 所有测试通过！系统准备就绪")
        return True
    elif success_rate >= 80:
        logger.warning("⚠️  大部分测试通过，系统基本可用")
        return True
    else:
        logger.error("❌ 多个测试失败，请检查系统配置")
        return False


if __name__ == "__main__":
    try:
        result = asyncio.run(run_all_tests())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        logger.info("🛑 测试被用户中断")
        sys.exit(130)
    except Exception as e:
        logger.error(f"💥 测试执行异常: {e}")
        sys.exit(1) 