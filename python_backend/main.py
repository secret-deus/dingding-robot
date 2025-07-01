"""
钉钉机器人 + LLM + MCP 集成系统
FastAPI 主应用入口
"""

import os
import asyncio
from contextlib import asynccontextmanager
from typing import Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from loguru import logger
from dotenv import load_dotenv
import uvicorn
import json
from pathlib import Path
import logging

from src.mcp.client import MCPClient
from src.mcp.types import MCPClientConfig, LLMConfig
from src.llm.processor import EnhancedLLMProcessor
from src.dingtalk.bot import DingTalkBot

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv()

# 全局变量
mcp_client: Optional[MCPClient] = None
llm_processor: Optional[EnhancedLLMProcessor] = None
dingtalk_bot: Optional[DingTalkBot] = None

# 配置存储
config_file = "config.json"
default_config = {
    "llm": {
        "provider": "openai",
        "model": "gpt-3.5-turbo",
        "api_key": "",
        "temperature": 0.7,
        "max_tokens": 2000,
        "timeout": 30
    },
    "dingtalk": {
        "webhook_url": "",
        "secret": "",
        "enable_signature": True,
        "max_message_length": 4000,
        "enable_markdown": True,
        "enable_ai": True
    },
    "mcp": {
        "tools": []
    }
}

def load_config() -> Dict[str, Any]:
    """加载配置"""
    try:
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        logger.warning(f"加载配置失败: {e}")
    return default_config.copy()

def save_config(config: Dict[str, Any]) -> bool:
    """保存配置"""
    try:
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        logger.error(f"保存配置失败: {e}")
        return False

class WebhookRequest(BaseModel):
    """Webhook 请求结构"""
    msgId: str
    msgtype: str
    text: dict
    chatbotUserId: str
    conversationId: str
    atUsers: Optional[list] = None
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


class TestRequest(BaseModel):
    """测试请求结构"""
    tool_name: str
    parameters: dict


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化
    await initialize_services()
    logger.info("🚀 服务启动完成")
    
    yield
    
    # 关闭时清理
    await cleanup_services()
    logger.info("🛑 服务关闭完成")


app = FastAPI(
    title="钉钉K8s运维机器人",
    description="集成LLM和MCP工具链的智能运维助手",
    version="1.0.0",
    lifespan=lifespan
)

# 跨域配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件
app.mount("/static", StaticFiles(directory="static"), name="static")


async def initialize_services():
    """初始化所有服务"""
    global mcp_client, llm_processor, dingtalk_bot
    
    try:
        # 1. 初始化 MCP 客户端
        mcp_config = MCPClientConfig(
            timeout=30000,
            retry_attempts=3,
            max_concurrent_calls=5,
            enable_cache=True
        )
        mcp_client = MCPClient(mcp_config)
        await mcp_client.connect()
        logger.info("✅ MCP 客户端初始化成功")
        
        # 2. 初始化 LLM 处理器
        llm_config = LLMConfig(
            provider="openai",
            model=os.getenv("LLM_MODEL", "gpt-3.5-turbo"),
            api_key=os.getenv("LLM_API_KEY", ""),
            base_url=os.getenv("LLM_BASE_URL"),
            temperature=0.7,
            max_tokens=2000
        )
        
        if not llm_config.api_key:
            logger.warning("⚠️ LLM API Key 未配置，将使用模拟模式")
        
        llm_processor = EnhancedLLMProcessor(llm_config, mcp_client)
        logger.info("✅ LLM 处理器初始化成功")
        
        # 3. 初始化钉钉机器人
        dingtalk_webhook = os.getenv("DINGTALK_WEBHOOK_URL", "")
        dingtalk_secret = os.getenv("DINGTALK_SECRET")
        
        dingtalk_bot = DingTalkBot(
            webhook_url=dingtalk_webhook,
            secret=dingtalk_secret,
            llm_processor=llm_processor
        )
        logger.info("✅ 钉钉机器人初始化成功")
        
    except Exception as e:
        logger.error(f"❌ 服务初始化失败: {e}")
        raise


async def cleanup_services():
    """清理服务"""
    global mcp_client
    
    if mcp_client:
        await mcp_client.disconnect()


@app.get("/", response_class=HTMLResponse)
async def index():
    """返回主页"""
    return FileResponse("static/index.html")


@app.get("/api/status")
async def get_status():
    """获取系统状态"""
    try:
        status = {
            "healthy": True,
            "mcp_client": mcp_client is not None and hasattr(mcp_client, 'is_initialized') and mcp_client.is_initialized,
            "llm_processor": llm_processor is not None,
            "dingtalk_bot": dingtalk_bot is not None,
            "tools_count": len(mcp_client.available_tools) if mcp_client and hasattr(mcp_client, 'available_tools') else 0,
            "timestamp": asyncio.get_event_loop().time()
        }
        
        # 检查各组件健康状态
        if mcp_client and hasattr(mcp_client, 'is_initialized') and not mcp_client.is_initialized:
            status["healthy"] = False
            
        return status
    except Exception as e:
        logger.error(f"获取系统状态失败: {e}")
        return {
            "healthy": False,
            "error": str(e),
            "mcp_client": False,
            "llm_processor": False,
            "dingtalk_bot": False,
            "tools_count": 0
        }


@app.get("/api/tools")
async def get_tools():
    """获取可用工具列表"""
    try:
        if not mcp_client or not hasattr(mcp_client, 'available_tools'):
            return {"tools": []}
            
        tools = []
        for tool_name, tool_info in mcp_client.available_tools.items():
            tools.append({
                "name": tool_name,
                "description": tool_info.get("description", ""),
                "parameters": tool_info.get("inputSchema", {}),
                "last_used": tool_info.get("last_used"),
                "usage_count": tool_info.get("usage_count", 0)
            })
            
        return {"tools": tools}
    except Exception as e:
        logger.error(f"获取工具列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取工具列表失败: {e}")


@app.post("/api/tools/test")
async def test_tool(request: Dict[str, Any]):
    """测试工具"""
    try:
        tool_name = request.get("tool_name")
        parameters = request.get("parameters", {})
        
        if not tool_name:
            raise HTTPException(status_code=400, detail="缺少工具名称")
            
        if not mcp_client:
            raise HTTPException(status_code=500, detail="MCP客户端未初始化")
            
        # 调用工具
        result = await mcp_client.call_tool(tool_name, parameters)
        return {"success": True, "result": result}
        
    except Exception as e:
        logger.error(f"工具测试失败: {e}")
        raise HTTPException(status_code=500, detail=f"工具测试失败: {e}")


@app.get("/api/config/{config_type}")
async def get_config(config_type: str):
    """获取配置"""
    try:
        config = load_config()
        if config_type not in config:
            raise HTTPException(status_code=404, detail=f"配置类型 {config_type} 不存在")
        return config[config_type]
    except Exception as e:
        logger.error(f"获取配置失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取配置失败: {e}")


@app.post("/api/config/{config_type}")
async def update_config(config_type: str, new_config: Dict[str, Any]):
    """更新配置"""
    try:
        config = load_config()
        if config_type not in config:
            raise HTTPException(status_code=404, detail=f"配置类型 {config_type} 不存在")
            
        config[config_type].update(new_config)
        
        if not save_config(config):
            raise HTTPException(status_code=500, detail="保存配置失败")
            
        # 如果是LLM配置更新，重新初始化LLM处理器
        if config_type == "llm":
            await reinitialize_llm_processor(config["llm"])
            
        # 如果是钉钉配置更新，重新初始化钉钉机器人
        if config_type == "dingtalk":
            await reinitialize_dingtalk_bot(config["dingtalk"])
            
        return {"success": True, "message": "配置更新成功"}
        
    except Exception as e:
        logger.error(f"更新配置失败: {e}")
        raise HTTPException(status_code=500, detail=f"更新配置失败: {e}")


@app.post("/api/test")
async def test_message(request: Dict[str, Any]):
    """测试消息处理"""
    try:
        message = request.get("message", "")
        if not message:
            raise HTTPException(status_code=400, detail="消息不能为空")
            
        if not llm_processor:
            raise HTTPException(status_code=500, detail="LLM处理器未初始化")
            
        # 处理消息
        response = await llm_processor.process_message(message)
        return {"success": True, "response": response}
        
    except Exception as e:
        logger.error(f"消息测试失败: {e}")
        raise HTTPException(status_code=500, detail=f"消息测试失败: {e}")


@app.post("/dingtalk/webhook")
async def dingtalk_webhook(request: Request):
    """钉钉Webhook处理"""
    try:
        if not dingtalk_bot:
            raise HTTPException(status_code=500, detail="钉钉机器人未初始化")
            
        # 获取请求数据
        body = await request.body()
        headers = dict(request.headers)
        
        # 处理钉钉消息
        response = await dingtalk_bot.handle_webhook(body, headers)
        return response
        
    except Exception as e:
        logger.error(f"钉钉Webhook处理失败: {e}")
        raise HTTPException(status_code=500, detail=f"处理失败: {e}")


async def reinitialize_llm_processor(llm_config: Dict[str, Any]):
    """重新初始化LLM处理器"""
    global llm_processor
    try:
        llm_processor = EnhancedLLMProcessor(
            api_key=llm_config.get("api_key"),
            model=llm_config.get("model", "gpt-3.5-turbo"),
            mcp_client=mcp_client
        )
        logger.info("LLM处理器重新初始化成功")
    except Exception as e:
        logger.error(f"LLM处理器重新初始化失败: {e}")


async def reinitialize_dingtalk_bot(dingtalk_config: Dict[str, Any]):
    """重新初始化钉钉机器人"""
    global dingtalk_bot
    try:
        if dingtalk_config.get("webhook_url"):
            dingtalk_bot = DingTalkBot(
                webhook_url=dingtalk_config["webhook_url"],
                secret=dingtalk_config.get("secret"),
                llm_processor=llm_processor
            )
            logger.info("钉钉机器人重新初始化成功")
        else:
            dingtalk_bot = None
            logger.warning("钉钉Webhook URL未配置，跳过初始化")
    except Exception as e:
        logger.error(f"钉钉机器人重新初始化失败: {e}")


@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    global mcp_client, llm_processor, dingtalk_bot
    
    logger.info("正在启动钉钉K8s运维机器人...")
    
    try:
        # 加载配置
        config = load_config()
        
        # 初始化MCP客户端
        mcp_client = MCPClient()
        await mcp_client.initialize()
        logger.info("MCP客户端初始化成功")
        
        # 初始化LLM处理器
        llm_config = config.get("llm", {})
        if llm_config.get("api_key"):
            llm_processor = EnhancedLLMProcessor(
                api_key=llm_config["api_key"],
                model=llm_config.get("model", "gpt-3.5-turbo"),
                mcp_client=mcp_client
            )
            logger.info("LLM处理器初始化成功")
        else:
            logger.warning("LLM API Key未配置，跳过LLM处理器初始化")
            
        # 初始化钉钉机器人
        dingtalk_config = config.get("dingtalk", {})
        if dingtalk_config.get("webhook_url"):
            dingtalk_bot = DingTalkBot(
                webhook_url=dingtalk_config["webhook_url"],
                secret=dingtalk_config.get("secret"),
                llm_processor=llm_processor
            )
            logger.info("钉钉机器人初始化成功")
        else:
            logger.warning("钉钉Webhook URL未配置，跳过钉钉机器人初始化")
            
        logger.info("系统启动完成！")
        
    except Exception as e:
        logger.error(f"系统启动失败: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    logger.info("正在关闭系统...")
    
    if mcp_client:
        await mcp_client.cleanup()
        
    logger.info("系统已关闭")


if __name__ == "__main__":
    # 配置日志
    logger.add(
        "logs/app.log",
        rotation="1 day",
        retention="7 days",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
    )
    
    # 启动服务
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        reload=os.getenv("DEBUG", "false").lower() == "true",
        log_level="info"
    ) 