#!/usr/bin/env python3
"""
市场策略师 - 定时任务脚本
每天 08:00（盘前）和 20:00（盘后）自动执行
"""

import requests
import json
from datetime import datetime
import os

# 配置
FEISHU_WEBHOOK = "https://open.feishu.cn/open-apis/bot/v2/hook/6e6bf0cc-dd8d-46b2-b12b-55ea498840e0"
GNEWS_API_KEY = "460c85c665a0d32b478a0804cd8b7c69"
WORKSPACE = "/root/.openclaw/workspace"

def send_feishu(title, content):
    """发送飞书消息（必须包含"老板"关键词）"""
    payload = {
        "msg_type": "text",
        "content": {
            "text": f"老板 {title}\n\n{content}"
        }
    }
    
    response = requests.post(FEISHU_WEBHOOK, json=payload)
    return response.json()

def get_market_news():
    """获取最新财经新闻"""
    url = f"https://gnews.io/api/v4/top-headlines?category=business&lang=en&country=us&max=5&apikey={GNEWS_API_KEY}"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        articles = data.get('articles', [])[:5]
        
        news_summary = []
        for article in articles:
            news_summary.append(f"- {article['title']}")
        
        return "\n".join(news_summary)
    except Exception as e:
        return f"新闻获取失败：{e}"

def generate_morning_report():
    """生成盘前研报"""
    news = get_market_news()
    
    report = f"""
📅 盘前研报 {datetime.now().strftime('%Y-%m-%d %H:%M')}

最新新闻：
{news}

持仓监控：
- 美股：NVDA AAPL TSLA
- 港股：腾讯 阿里 零跑
- 日股：丰田 三菱

操作建议：
1. 检查仓位是否超标（单只≤20%）
2. 关注超卖股票（RSI<30）
3. 地缘政治风险预警

详细报告：https://hilong812.github.io/daily-trading-strategy/trading.html
"""
    return report

def generate_evening_report():
    """生成盘后研报"""
    news = get_market_news()
    
    report = f"""
📊 盘后复盘 {datetime.now().strftime('%Y-%m-%d %H:%M')}

最新新闻：
{news}

今日复盘：
- 检查持仓表现
- 更新交易记录
- 计算 P&L

明日计划：
- 关注财报发布
- 技术指标更新
- 仓位调整

详细报告：https://hilong812.github.io/daily-trading-strategy/trading.html
"""
    return report

def main():
    """主函数"""
    hour = datetime.now().hour
    
    if hour < 12:
        # 上午：盘前报告
        print("🌅 生成盘前研报...")
        report = generate_morning_report()
        result = send_feishu("盘前研报已更新", report)
        print(f"✅ 盘前报告已发送：{result}")
    else:
        # 下午/晚上：盘后报告
        print("🌆 生成盘后研报...")
        report = generate_evening_report()
        result = send_feishu("盘后复盘已更新", report)
        print(f"✅ 盘后报告已发送：{result}")

if __name__ == "__main__":
    main()
