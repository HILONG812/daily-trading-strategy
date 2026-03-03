#!/bin/bash
# BrowserWing 启动脚本

LOG_FILE="/tmp/browserwing.log"
PID_FILE="/tmp/browserwing.pid"

# 检查是否已在运行
if [ -f "$PID_FILE" ]; then
    PID=$(cat $PID_FILE)
    if ps -p $PID > /dev/null; then
        echo "BrowserWing 已在运行 (PID: $PID)"
        exit 0
    fi
fi

# 启动服务
echo "启动 BrowserWing..."
nohup browserwing --port 8080 > $LOG_FILE 2>&1 &
PID=$!

# 保存 PID
echo $PID > $PID_FILE

# 等待启动
sleep 3

# 检查是否成功
if curl -s http://localhost:8080/api/health > /dev/null; then
    echo "✅ BrowserWing 启动成功!"
    echo "📍 PID: $PID"
    echo "🌐 访问：http://localhost:8080"
    echo "📋 日志：$LOG_FILE"
else
    echo "❌ 启动失败，查看日志：$LOG_FILE"
fi
