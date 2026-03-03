# BrowserWing 浏览器自动化控制

## ✅ 已安装

**版本**: v1.0.0
**位置**: `/root/.nvm/versions/node/v22.22.0/bin/browserwing`

---

## 启动方式

### 后台运行
```bash
nohup browserwing --port 8080 > /tmp/browserwing.log 2>&1 &
```

### 访问界面
http://localhost:8080

---

## API 端点

| 端点 | 说明 |
|------|------|
| GET /api/health | 健康检查 |
| POST /api/browser/navigate | 导航到 URL |
| POST /api/browser/click | 点击元素 |
| POST /api/browser/type | 输入文本 |
| POST /api/browser/screenshot | 截图 |
| POST /api/browser/extract | 提取数据 |
| GET /api/browser/cookies | 获取 Cookie |
| POST /api/browser/cookies | 设置 Cookie |

---

## 集成到 OpenClaw

### 方式 1: HTTP API 调用
```python
import requests

# 导航
requests.post('http://localhost:8080/api/browser/navigate', json={
    'url': 'https://finance.yahoo.com'
})

# 截图
resp = requests.post('http://localhost:8080/api/browser/screenshot')
with open('screenshot.png', 'wb') as f:
    f.write(resp.content)
```

### 方式 2: MCP 协议
BrowserWing 支持 MCP 协议，可被 AI agent 直接调用

---

## 配置文件

位置：`~/.browserwing/config.toml`

```toml
[server]
host = "0.0.0.0"
port = "8080"

[browser]
bin_path = ""  # 自动检测 Chrome
user_data_dir = "./chrome_user_data"
```

---

## 使用场景

1. **财经新闻抓取**
   - 访问 Bloomberg/Reuters
   - 截图或提取内容

2. **股价数据获取**
   - Yahoo Finance
   - Google Finance

3. **GitHub 页面操作**
   - 自动更新 Pages
   - 提交代码

4. **社交媒体监控**
   - Twitter/X
   - 雪球

---

## 测试命令

```bash
# 启动服务
browserwing --port 8080 &

# 测试 API
curl http://localhost:8080/api/health

# 导航测试
curl -X POST http://localhost:8080/api/browser/navigate \
  -H "Content-Type: application/json" \
  -d '{"url":"https://www.google.com"}'

# 截图测试
curl -X POST http://localhost:8080/api/browser/screenshot \
  -o screenshot.png
```

---

更新时间：2026-03-03 23:56