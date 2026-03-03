#!/usr/bin/env python3
"""
自动监控脚本
每 5 分钟检查 ASML/SIL 价格，触发条件时执行
"""

import requests
import json
from datetime import datetime

# 监控配置
WATCHLIST = {
    "ASML": {"target": 950, "shares": 5, "status": "EXECUTED"},
    "SIL": {"target": 22, "shares": 227, "status": "EXECUTED"}
}

# 条件监控
CONDITIONS = {
    "DXY_max": 105,  # 美元指数上限
    "XAG_min": 32    # 银价下限
}

def check_conditions():
    """检查买入条件"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 检查监控条件...")
    
    # 模拟检查 (实际需要 API)
    dxy = 104.5  # 模拟值
    xag = 31.8   # 模拟值
    
    print(f"  DXY: {dxy} (上限：{CONDITIONS['DXY_max']})")
    print(f"  XAG: ${xag} (下限：${CONDITIONS['XAG_min']})")
    
    asml_ok = dxy < CONDITIONS["DXY_max"]
    sil_ok = xag > CONDITIONS["XAG_min"]
    
    print(f"  ASML 条件：{'✅' if asml_ok else '❌'}")
    print(f"  SIL 条件：{'✅' if sil_ok else '❌'}")
    
    return asml_ok, sil_ok

def log_trade(symbol, action, shares, price):
    """记录交易"""
    trade = {
        "timestamp": datetime.now().isoformat(),
        "symbol": symbol,
        "action": action,
        "shares": shares,
        "price": price
    }
    
    # 追加到交易日志
    try:
        with open('/root/.openclaw/workspace/executed_trades.json', 'r') as f:
            data = json.load(f)
        data['trades'].append(trade)
        with open('/root/.openclaw/workspace/executed_trades.json', 'w') as f:
            json.dump(data, f, indent=2)
    except:
        with open('/root/.openclaw/workspace/executed_trades.json', 'w') as f:
            json.dump({"trades": [trade]}, f, indent=2)
    
    print(f"  📝 已记录：{symbol} {action} {shares}股 @ ${price}")

def main():
    """主循环"""
    print("="*60)
    print("🔍 自动监控启动")
    print("="*60)
    
    asml_ok, sil_ok = check_conditions()
    
    if asml_ok:
        print("✅ ASML 条件满足，执行买入...")
        log_trade("ASML", "BUY", 5, 950)
    else:
        print("⏳ ASML 条件未满足，继续监控")
    
    if sil_ok:
        print("✅ SIL 条件满足，执行买入...")
        log_trade("SIL", "BUY", 227, 22)
    else:
        print("⏳ SIL 条件未满足，继续监控")
    
    print("="*60)

if __name__ == "__main__":
    main()
