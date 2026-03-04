#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基于缓存数据的市场分析系统
不依赖实时 API，使用本地缓存数据进行分析
"""

import json
from pathlib import Path
from datetime import datetime

CACHE_FILE = Path("/root/.openclaw/workspace/data/market_cache/market_data_full.json")

def load_cache():
    with open(CACHE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def calculate_rsi_from_klines(klines, period=14):
    """从 K 线计算 RSI"""
    if len(klines) < period + 1:
        return None
    closes = [k["close"] for k in klines[-period-1:]]
    deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]
    gains = [d if d > 0 else 0 for d in deltas]
    losses = [-d if d < 0 else 0 for d in deltas]
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period
    if avg_loss == 0:
        return 100
    rs = avg_gain / avg_loss
    return round(100 - (100 / (1 + rs)), 2)

def calculate_ma(klines, period):
    """计算移动平均线"""
    if len(klines) < period:
        return None
    closes = [k["close"] for k in klines[-period:]]
    return round(sum(closes) / period, 2)

def analyze_stock(position, klines=None):
    """分析单只股票"""
    result = {
        "symbol": position["code"],
        "name": position["name"],
        "market": position["market"],
        "price": position["price"],
        "cost": position["cost"],
        "pnl_pct": position["pnl_pct"],
        "rsi": position.get("rsi", 0),
        "ma20_status": position.get("ma20_status", "未知"),
        "signals": [],
        "action": "持有",
        "confidence": 50,
    }
    
    # 计算 K 线指标
    if klines and len(klines) >= 5:
        rsi_calc = calculate_rsi_from_klines(klines, 14)
        ma20 = calculate_ma(klines, 5)  # 简化用 5 日线
        result["rsi_calculated"] = rsi_calc
        result["ma5"] = ma20
        
        # 最新收盘价
        latest_close = klines[-1]["close"]
        result["price_kline"] = latest_close
    
    # 交易信号
    signals = []
    confidence = 50
    
    # RSI 信号
    rsi = result["rsi"]
    if rsi < 20:
        signals.append("RSI 超卖 (<20)")
        confidence += 20
    elif rsi < 30:
        signals.append("RSI 接近超卖 (20-30)")
        confidence += 10
    elif rsi > 70:
        signals.append("RSI 超买 (>70)")
        confidence -= 20
    elif rsi > 60:
        signals.append("RSI 偏高 (60-70)")
        confidence -= 10
    
    # 均线信号
    if result["ma20_status"] == "站上":
        signals.append("股价站上 MA20")
        confidence += 15
    else:
        signals.append("股价跌破 MA20")
        confidence -= 15
    
    # 盈亏信号
    pnl = result["pnl_pct"]
    if pnl < -8:
        signals.append("触及止损线 (-8%)")
        confidence += 30
    elif pnl < -5:
        signals.append("亏损 -5%~-8% 警戒区")
        confidence += 10
    elif pnl > 20:
        signals.append("盈利 +20% 以上")
        confidence += 15
    
    result["signals"] = signals
    result["confidence"] = min(100, max(0, confidence))
    
    # 决策
    if pnl < -8:
        result["action"] = "止损卖出"
    elif rsi < 30 and result["ma20_status"] == "站上":
        result["action"] = "加仓买入"
    elif rsi > 70:
        result["action"] = "减仓/止盈"
    elif pnl > 20:
        result["action"] = "减半仓止盈"
    else:
        result["action"] = "持有观望"
    
    return result

def main():
    print("=" * 70)
    print("📊 全球股市数据分析系统 (基于缓存)")
    print(f"📅 数据时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 70)
    
    cache = load_cache()
    
    positions = cache.get("positions", [])
    kline_cache = cache.get("kline_cache", {})
    
    print(f"\n📈 分析 {len(positions)} 只持仓股票...\n")
    
    analyses = []
    for pos in positions:
        symbol = pos["code"]
        klines = kline_cache.get(symbol.replace(".HK", "").replace(".T", "").replace(".SH", ""))
        analysis = analyze_stock(pos, klines)
        analyses.append(analysis)
        
        # 打印摘要
        status_icon = "✅" if analysis["pnl_pct"] >= 0 else "❌"
        print(f"{status_icon} {analysis['market']} {analysis['symbol']} {analysis['name']}")
        print(f"   价格：¥{analysis['price']} | 盈亏：{analysis['pnl_pct']:.2f}%")
        print(f"   RSI: {analysis['rsi']} | MA20: {analysis['ma20_status']}")
        print(f"   信号：{', '.join(analysis['signals']) if analysis['signals'] else '无'}")
        print(f"   建议：{analysis['action']} (置信度：{analysis['confidence']}%)")
        print()
    
    # 汇总
    print("=" * 70)
    print("📋 交易建议汇总")
    print("=" * 70)
    
    buy_signals = [a for a in analyses if a["action"] == "加仓买入"]
    sell_signals = [a for a in analyses if a["action"] == "止损卖出"]
    hold_signals = [a for a in analyses if a["action"] == "持有观望"]
    reduce_signals = [a for a in analyses if "减仓" in a["action"] or "止盈" in a["action"]]
    
    if buy_signals:
        print("\n🟢 买入机会:")
        for a in buy_signals:
            print(f"   {a['symbol']}: {', '.join(a['signals'])}")
    
    if sell_signals:
        print("\n🔴 止损卖出:")
        for a in sell_signals:
            print(f"   {a['symbol']}: {', '.join(a['signals'])}")
    
    if reduce_signals:
        print("\n🟡 减仓/止盈:")
        for a in reduce_signals:
            print(f"   {a['symbol']}: {', '.join(a['signals'])}")
    
    if hold_signals:
        print("\n⚪ 持有观望:")
        for a in hold_signals:
            print(f"   {a['symbol']}: {', '.join(a['signals'])}")
    
    # 市场状态
    print("\n" + "=" * 70)
    print("🌍 全球市场状态")
    print("=" * 70)
    
    indices = cache.get("indices", {})
    for symbol, data in indices.items():
        icon = "🟢" if data["change_pct"] >= 0 else "🔴"
        print(f"{icon} {symbol}: {data['price']} ({data['change_pct']:.2f}%)")
    
    # 账户状态
    print("\n" + "=" * 70)
    print("💰 账户状态")
    print("=" * 70)
    
    initial = cache.get("initial", 100000)
    cash = cache.get("cash", 0)
    total_value = cache.get("total_value", 0)
    total_pnl = cache.get("total_pnl", 0)
    total_pnl_pct = cache.get("total_pnl_pct", 0)
    
    position_pct = total_value / (initial) * 100
    cash_pct = cash / (initial) * 100
    
    print(f"初始资金：${initial:,}")
    print(f"当前持仓：${total_value:,} ({position_pct:.1f}%)")
    print(f"现金储备：${cash:,} ({cash_pct:.1f}%)")
    print(f"总盈亏：${total_pnl:,.0f} ({total_pnl_pct:.2f}%)")
    
    # 仓位评估
    if position_pct > 90:
        print(f"\n⚠️  仓位过高 ({position_pct:.1f}%)，建议反弹减仓至 80% 以下")
    elif position_pct > 80:
        print(f"\n🟡 仓位偏高 ({position_pct:.1f}%)，注意风险控制")
    elif position_pct > 60:
        print(f"\n✅ 仓位合理 ({position_pct:.1f}%)")
    else:
        print(f"\n🟢 仓位偏低 ({position_pct:.1f}%)，可逢低加仓")
    
    # 最后更新
    print("\n" + "=" * 70)
    print(f"📁 数据来源：{CACHE_FILE}")
    print(f"⏰ 分析时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

if __name__ == "__main__":
    main()
