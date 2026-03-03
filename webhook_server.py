"""
飞书 Webhook 异步处理服务器
支持幂等性检查和后台任务处理
"""

import asyncio
from fastapi import FastAPI, Request, BackgroundTasks, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
import time
import json

app = FastAPI(title="Feishu Webhook Server")

# 内存缓存：存储已处理的消息 ID（生产环境建议用 Redis）
processed_messages: Dict[str, dict] = {}

# 清理过期记录的任务
CLEANUP_INTERVAL = 3600  # 1 小时
MESSAGE_EXPIRY = 3600    # 消息记录过期时间


async def cleanup_old_messages():
    """定期清理过期的消息记录"""
    while True:
        await asyncio.sleep(CLEANUP_INTERVAL)
        current_time = time.time()
        expired_keys = [
            k for k, v in processed_messages.items()
            if current_time - v['timestamp'] > MESSAGE_EXPIRY
        ]
        for key in expired_keys:
            del processed_messages[key]
        print(f"清理了 {len(expired_keys)} 条过期消息记录")


async def create_feishu_document_task(message_id: str, user_id: str, content: Dict[str, Any]):
    """
    具体的耗时任务：生成飞书文档
    """
    print(f"[{message_id}] 开始为消息生成文档...")
    start_time = time.time()
    
    try:
        # 1. 调用大模型分析内容
        print(f"[{message_id}] 正在分析内容...")
        await asyncio.sleep(2)  # 模拟 LLM 调用
        
        # 2. 调用飞书 API 创建文档
        print(f"[{message_id}] 正在创建飞书文档...")
        await asyncio.sleep(2)  # 模拟飞书 API 调用
        
        # 3. 发送结果给用户
        print(f"[{message_id}] 正在发送结果...")
        await asyncio.sleep(1)  # 模拟发送消息
        
        elapsed = time.time() - start_time
        print(f"[{message_id}] 处理完成，耗时：{elapsed:.2f}秒")
        
        # 更新状态
        processed_messages[message_id]['status'] = 'completed'
        processed_messages[message_id]['result'] = 'success'
        
    except Exception as e:
        print(f"[{message_id}] 处理失败：{str(e)}")
        processed_messages[message_id]['status'] = 'failed'
        processed_messages[message_id]['error'] = str(e)


@app.on_event("startup")
async def startup_event():
    """启动时开始清理任务"""
    asyncio.create_task(cleanup_old_messages())
    print("🚀 Webhook 服务器启动完成")


@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {
        "status": "healthy",
        "processed_count": len(processed_messages),
        "timestamp": time.time()
    }


@app.get("/status/{message_id}")
async def get_message_status(message_id: str):
    """查询消息处理状态"""
    if message_id not in processed_messages:
        raise HTTPException(status_code=404, detail="消息未找到")
    
    return processed_messages[message_id]


@app.post("/webhook")
async def feishu_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    飞书 Webhook 入口
    支持幂等性检查和异步处理
    """
    try:
        data = await request.json()
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="无效的 JSON 格式")
    
    # 1. 提取飞书消息的唯一 ID
    # 优先使用 event_id（新版事件），回退到 message_id（旧版）
    msg_id = (
        data.get("header", {}).get("event_id") or
        data.get("event", {}).get("message", {}).get("message_id") or
        data.get("message_id")
    )
    
    if not msg_id:
        print("⚠️ 未找到消息 ID，使用请求时间戳代替")
        msg_id = f"manual_{int(time.time() * 1000)}"
    
    # 2. 幂等性检查：如果这个 ID 已经在处理中或已处理，直接返回
    current_time = time.time()
    if msg_id in processed_messages:
        existing = processed_messages[msg_id]
        elapsed = current_time - existing['timestamp']
        
        if existing['status'] == 'processing' and elapsed < 30:
            # 仍在处理中（30 秒内）
            print(f"⏳ 消息 {msg_id} 正在处理中，跳过")
            return {"code": 0, "msg": "already processing"}
        elif existing['status'] in ['completed', 'failed']:
            # 已完成或失败，但可以重试（超过 30 秒）
            if elapsed > 30:
                print(f"🔄 消息 {msg_id} 已处理完成，允许重试")
                # 更新状态为 processing
                processed_messages[msg_id]['status'] = 'processing'
                processed_messages[msg_id]['timestamp'] = current_time
            else:
                print(f"⏳ 消息 {msg_id} 刚处理完成，跳过重试")
                return {"code": 0, "msg": "already completed"}
    
    # 3. 记录该消息 ID
    processed_messages[msg_id] = {
        'timestamp': current_time,
        'status': 'processing',
        'user_id': data.get('user_id', 'unknown'),
        'content_preview': str(data.get('content', ''))[:100]
    }
    
    # 4. 提取用户 ID 和内容
    user_id = (
        data.get("event", {}).get("message", {}).get("sender", {}).get("user_id") or
        data.get("user_id", "unknown")
    )
    
    # 5. 利用 BackgroundTasks 立即返回响应给飞书
    background_tasks.add_task(
        create_feishu_document_task,
        msg_id,
        user_id,
        data
    )
    
    # 6. 立即告诉飞书：我收到了！
    print(f"✅ 消息 {msg_id} 已接收，开始后台处理")
    return {"code": 0, "msg": "success"}


@app.post("/webhook/test")
async def test_webhook():
    """测试 Webhook 接口"""
    return {
        "code": 0,
        "msg": "Webhook 正常工作",
        "timestamp": time.time()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
