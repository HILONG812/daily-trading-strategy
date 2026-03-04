#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全球股市数据缓存系统 v2
多数据源轮换 + 网页抓取备用
"""

import json
import os
import time
import requests
from datetime import datetime
from pathlib import Path

CACHE_DIR = Path("/root/.openclaw/workspace/data/market_cache")
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# 持仓股票池
HOLDINGS = [
    # 美股
    {"market": "US", "symbol": "NVDA", "name": "英伟达", "src_symbol": "NVDA"},
    {"market": "US", "symbol": "AAPL", "name": "苹果", "src_symbol": "AAPL"},
    {"market": "US", "symbol": "TSLA", "name": "特斯拉", "src_symbol": "TSLA"},
    {"market": "US", "symbol": "ASML", "name": "ASML", "src_symbol": "ASML"},
    {"market": "US", "symbol": "SIL", "name": "白银 ETF", "src_symbol": "SIL"},
    # 港股
    {"market": "HK", "symbol": "0700", "name": "腾讯", "src_symbol": "00700"},
    {"market": "HK", "symbol": "9988", "name": "阿里", "src_symbol": "09988"},
    {"market": "HK", "symbol": "9863", "name": "零跑", "src_symbol": "09863"},
    {"market": "HK", "symbol": "2402", "name": "亿华通", "src_symbol": "02402"},
    # 日股
    {"market": "JP", "symbol": "7203", "name": "丰田", "src_symbol": "7203"},
    {"market": "JP", "symbol": "8058", "name": "三菱商事", "src_symbol": "8058"},
    # A 股
    {"market": "CN", "symbol": "688339", "name": "亿华通-U", "src_symbol": "688339"},
]

def fetch_from_eastmoney_cn(symbol):
    """东方财富 A 股"""
    try:
        secid = f"1.{symbol}" if symbol.startswith("6") else f"0.{symbol}"
        url = "https://push2.eastmoney.com/api/qt/stock/get"
        params = {"secid": secid, "fields": "f43,f44,f45,f46,f55,f57,f58"}
        resp = requests.get(url, params=params, timeout=8)
        d = resp.json().get("data", {})
        if d:
            last = d.get("f46", 0) / 100
            chg = d.get("f55", 0)
            return {
                "price": round(last * (1 + chg/100), 2) if last else 0,
                "change_pct": chg,
                "high": d.get("f43", 0) / 100,
                "low": d.get("f44", 0) / 100,
                "volume": d.get("f47", 0),
            }
    except Exception as e:
        print(f"    Eastmoney CN fail: {e}")
    return None

def fetch_from_eastmoney_hk(symbol):
    """东方财富港股"""
    try:
        url = "https://push2.eastmoney.com/api/qt/stock/get"
        params = {"secid": f"116.{symbol}", "fields": "f43,f44,f45,f46,f55,f57,f58"}
        resp = requests.get(url, params=params, timeout=8)
        d = resp.json().get("data", {})
        if d:
            last = d.get("f46", 0) / 1000
            chg = d.get("f55", 0)
            return {
                "price": round(last * (1 + chg/100), 2) if last else 0,
                "change_pct": chg,
                "high": d.get("f43", 0) / 1000,
                "low": d.get("f44", 0) / 1000,
                "volume": d.get("f47", 0),
            }
    except Exception as e:
        print(f"    Eastmoney HK fail: {e}")
    return None

def fetch_from_sina(symbol, market):
    """新浪财经"""
    try:
        if market == "US":
            url = f"https://quote.sina.cn/quotes/api/jsonp.php/vars={symbol}/USMarketService.getUSStockQuotes?symbol={symbol}"
        elif market == "HK":
            url = f"https://quote.sina.cn/quotes/api/jsonp.php/vars={symbol}/HKMarketService.getHKStockQuotes?symbol={symbol}"
        resp = requests.get(url, timeout=8)
        # 解析 JSONP
        text = resp.text
        if "=" in text:
            text = text.split("=", 1)[1]
        data = json.loads(text.strip().strip(";"))
        if data and isinstance(data, list) and len(data) > 0:
            d = data[0]
            return {
                "price": float(d.get("price", 0)),
                "change_pct": float(d.get("change_pct", 0)),
                "high": float(d.get("high", 0)),
                "low": float(d.get("low", 0)),
                "open": float(d.get("open", 0)),
                "prev_close": float(d.get("prev_close", 0)),
            }
    except Exception as e:
        print(f"    Sina fail: {e}")
    return None

def fetch_from_nasdaq(symbol):
    """NASDAQ 官网 API"""
    try:
        url = f"https://api.nasdaq.com/api/quote/{symbol}"
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, headers=headers, timeout=8)
        data = resp.json()
        if data.get("data"):
            quote = data["data"].get("quote", {})
            return {
                "price": float(quote.get("last", 0)),
                "change_pct": float(quote.get("changePercent", 0)),
                "high": float(quote.get("high", 0)),
                "low": float(quote.get("low", 0)),
                "open": float(quote.get("open", 0)),
            }
    except Exception as e:
        print(f"    NASDAQ fail: {e}")
    return None

def calculate_rsi(change_pct):
    """简单 RSI 估算"""
    if change_pct < -8:
        return 15
    elif change_pct < -5:
        return 25
    elif change_pct < -2:
        return 35
    elif change_pct < 0:
        return 45
    elif change_pct < 2:
        return 55
    elif change_pct < 5:
        return 65
    elif change_pct < 8:
        return 75
    else:
        return 85

def main():
    print("=" * 60)
    print("🌍 全球股市数据缓存系统 v2")
    print(f"📅 时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    cache = {
        "timestamp": datetime.now().isoformat(),
        "holdings": [],
        "summary": {},
    }
    
    for i, stock in enumerate(HOLDINGS):
        market = stock["market"]
        symbol = stock["symbol"]
        name = stock["name"]
        src_symbol = stock["src_symbol"]
        
        print(f"\n[{i+1}/{len(HOLDINGS)}] {market} {symbol} {name}")
        
        data = None
        
        # 尝试多个数据源
        if market == "CN":
            print("  尝试 Eastmoney CN...")
            data = fetch_from_eastmoney_cn(src_symbol)
            time.sleep(1)
        
        elif market == "HK":
            print("  尝试 Eastmoney HK...")
            data = fetch_from_eastmoney_hk(src_symbol)
            time.sleep(1)
            
            if not data:
                print("  尝试 Sina HK...")
                data = fetch_from_sina(src_symbol, "HK")
                time.sleep(1)
        
        elif market == "US":
            print("  尝试 NASDAQ...")
            data = fetch_from_nasdaq(src_symbol)
            time.sleep(1)
            
            if not data:
                print("  尝试 Sina US...")
                data = fetch_from_sina(src_symbol, "US")
                time.sleep(1)
        
        elif market == "JP":
            # 日股较难获取，先跳过或用估算
            print("  日股数据源受限，使用估算...")
            data = {"price": 0, "change_pct": 0, "note": "日股数据待更新"}
            time.sleep(0.5)
        
        if data:
            result = {
                "market": market,
                "symbol": symbol,
                "name": name,
                "price": data.get("price", 0),
                "change_pct": data.get("change_pct", 0),
                "high": data.get("high", 0),
                "low": data.get("low", 0),
                "open": data.get("open", 0),
                "prev_close": data.get("prev_close", 0),
                "volume": data.get("volume", 0),
                "rsi_estimate": calculate_rsi(data.get("change_pct", 0)),
                "timestamp": datetime.now().isoformat(),
            }
            cache["holdings"].append(result)
            print(f"  ✅ {result['price']} ({result['change_pct']}%) RSI≈{result['rsi_estimate']}")
        else:
            print(f"  ❌ 所有数据源失败")
            cache["holdings"].append({
                "market": market,
                "symbol": symbol,
                "name": name,
                "error": "数据获取失败",
                "timestamp": datetime.now().isoformat(),
            })
        
        # 每 5 个股票休息久一点
        if (i + 1) % 5 == 0:
            print("  ⏸️  休息 3 秒...")
            time.sleep(3)
    
    # 计算摘要
    total_holdings = len([h for h in cache["holdings"] if "price" in h and h["price"] > 0])
    failed_holdings = len([h for h in cache["holdings"] if "error" in h])
    avg_change = sum([h.get("change_pct", 0) for h in cache["holdings"] if "change_pct" in h]) / max(total_holdings, 1)
    
    cache["summary"] = {
        "total": len(HOLDINGS),
        "success": total_holdings,
        "failed": failed_holdings,
        "avg_change_pct": round(avg_change, 2),
    }
    
    # 保存
    output_file = CACHE_DIR / f"holdings_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)
    
    latest_file = CACHE_DIR / "holdings_latest.json"
    with open(latest_file, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)
    
    print("\n" + "=" * 60)
    print("✅ 缓存完成!")
    print(f"📁 文件：{output_file}")
    print(f"📊 成功：{total_holdings}/{len(HOLDINGS)}")
    print(f"📊 失败：{failed_holdings}")
    print("=" * 60)
    
    # 打印摘要
    print("\n📊 持仓摘要:")
    for h in cache["holdings"]:
        if "price" in h and h["price"] > 0:
            print(f"  {h['market']} {h['symbol']}: ¥{h['price']} ({h['change_pct']}%) RSI≈{h['rsi_estimate']}")
        else:
            print(f"  {h['market']} {h['symbol']}: ❌ {h.get('error', '无数据')}")

if __name__ == "__main__":
    main()
