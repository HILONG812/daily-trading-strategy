#!/usr/bin/env python3
"""
模拟交易执行脚本
ASML + SIL 买入订单
"""

import json
from datetime import datetime

# 订单详情
orders = {
    "timestamp": datetime.now().isoformat(),
    "type": "BUY",
    "status": "EXECUTED",
    "trades": [
        {
            "symbol": "ASML",
            "name": "ASML Holding NV",
            "action": "BUY",
            "shares": 5,
            "price": 950.00,
            "total": 4750.00,
            "allocation": "5%",
            "reason": "EUV 光刻机龙头，台积电加订"
        },
        {
            "symbol": "SIL",
            "name": "Global X Silver Miners ETF",
            "action": "BUY",
            "shares": 227,
            "price": 22.00,
            "total": 4994.00,
            "allocation": "5%",
            "reason": "白银避险 + 工业需求"
        }
    ],
    "summary": {
        "total_invested": 9744.00,
        "cash_before": 11665.00,
        "cash_after": 1921.00,
        "position_change": "88% → 97%"
    }
}

# 保存交易记录
with open('/root/.openclaw/workspace/executed_trades.json', 'w', encoding='utf-8') as f:
    json.dump(orders, f, indent=2, ensure_ascii=False)

print("✅ 模拟交易已执行！")
print("="*60)
print(f"ASML: 5 股 × $950 = ${orders['trades'][0]['total']:,.2f}")
print(f"SIL:  227 股 × $22 = ${orders['trades'][1]['total']:,.2f}")
print("="*60)
print(f"总投入：${orders['summary']['total_invested']:,.2f}")
print(f"现金：${orders['summary']['cash_before']:,.2f} → ${orders['summary']['cash_after']:,.2f}")
print("="*60)
print(f"📄 记录：/root/.openclaw/workspace/executed_trades.json")
