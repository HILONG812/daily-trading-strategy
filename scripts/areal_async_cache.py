#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AReaL 改进应用 - 异步数据获取 + 三层缓存
基于 AReaL 论文的异步 RL 系统思想
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
import sqlite3

CACHE_DIR = Path("/root/.openclaw/workspace/data/market_cache")
DB_PATH = Path("/root/.openclaw/workspace/data/stock_market.db")
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# 三层缓存配置
CACHE_L1_MAX_AGE = timedelta(minutes=5)   # L1 内存缓存 5 分钟
CACHE_L2_MAX_AGE = timedelta(hours=24)    # L2 文件缓存 24 小时
CACHE_L3_MAX_AGE = timedelta(days=30)     # L3 数据库缓存 30 天

# 持仓股票
HOLDINGS = {
    "HK": ["0700", "9988", "9863", "2402"],
    "US": ["NVDA", "AAPL", "TSLA", "ASML", "SIL"],
    "JP": ["7203.T", "8058.T"],
    "CN": ["688339"],
}

# L1 内存缓存
l1_cache = {}
l1_timestamps = {}


async def fetch_stock_quote(session, symbol, market):
    """异步获取单只股票行情"""
    try:
        if market == "HK":
            url = f"http://push2.eastmoney.com/api/qt/stock/get?secid=116.{symbol}&fields=f43,f44,f45,f46,f47,f48,f55"
        elif market == "CN":
            secid = f"1.{symbol}" if symbol.startswith("6") else f"0.{symbol}"
            url = f"http://push2.eastmoney.com/api/qt/stock/get?secid={secid}&fields=f43,f44,f45,f46,f47,f48,f55"
        else:
            return None
        
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
            data = await resp.json()
            d = data.get("data", {})
            if d:
                last = d.get("f46", 0) / (1000 if market == "HK" else 100)
                chg = d.get("f55", 0)
                return {
                    "symbol": symbol,
                    "market": market,
                    "price": round(last * (1 + chg/100), 2) if last else 0,
                    "change_pct": chg,
                    "high": d.get("f43", 0) / (1000 if market == "HK" else 100),
                    "low": d.get("f44", 0) / (1000 if market == "HK" else 100),
                    "volume": d.get("f47", 0),
                    "timestamp": datetime.now().isoformat(),
                }
    except Exception as e:
        pass
    return None


async def fetch_all_holdings():
    """异步获取所有持仓数据 (AReaL 异步思想)"""
    async with aiohttp.ClientSession() as session:
        tasks = []
        for market, symbols in HOLDINGS.items():
            for symbol in symbols:
                tasks.append(fetch_stock_quote(session, symbol, market))
        
        # 异步并发获取，不等待最慢的
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 过滤有效结果
        valid_results = [r for r in results if isinstance(r, dict)]
        return valid_results


def get_l1_cache(symbol):
    """获取 L1 内存缓存"""
    if symbol in l1_cache:
        age = datetime.now() - l1_timestamps.get(symbol, datetime.now())
        if age < CACHE_L1_MAX_AGE:
            return l1_cache[symbol], "L1"
    return None, None


def get_l2_cache(symbol):
    """获取 L2 文件缓存"""
    cache_file = CACHE_DIR / f"quote_{symbol}.json"
    if cache_file.exists():
        try:
            age = datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)
            if age < CACHE_L2_MAX_AGE:
                with open(cache_file, "r") as f:
                    return json.load(f), "L2"
        except:
            pass
    return None, None


def get_l3_cache(conn, symbol):
    """获取 L3 数据库缓存"""
    cursor = conn.cursor()
    cursor.execute(
        "SELECT symbol, price, change_pct, high, low, volume, timestamp FROM quotes WHERE symbol=? ORDER BY timestamp DESC LIMIT 1",
        (symbol,)
    )
    row = cursor.fetchone()
    if row:
        try:
            ts = datetime.fromisoformat(row[6])
            age = datetime.now() - ts
            if age < CACHE_L3_MAX_AGE:
                return {
                    "symbol": row[0],
                    "price": row[1],
                    "change_pct": row[2],
                    "high": row[3],
                    "low": row[4],
                    "volume": row[5],
                    "timestamp": row[6],
                }, "L3"
        except:
            pass
    return None, None


def save_to_l1(symbol, data):
    """保存到 L1 缓存"""
    l1_cache[symbol] = data
    l1_timestamps[symbol] = datetime.now()


def save_to_l2(symbol, data):
    """保存到 L2 缓存"""
    cache_file = CACHE_DIR / f"quote_{symbol}.json"
    with open(cache_file, "w") as f:
        json.dump(data, f, indent=2)


def save_to_l3(conn, data):
    """保存到 L3 数据库"""
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO quotes (symbol, price, change_pct, high, low, volume) VALUES (?, ?, ?, ?, ?, ?)",
            (data["symbol"], data["price"], data["change_pct"], data["high"], data["low"], data["volume"])
        )
        conn.commit()
    except Exception as e:
        pass


async def get_stock_data(symbol, market, conn):
    """
    获取股票数据 - 三层缓存策略
    L1 > L2 > L3 > API
    """
    # 1. 检查 L1 缓存
    data, source = get_l1_cache(symbol)
    if data:
        return data, source
    
    # 2. 检查 L2 缓存
    data, source = get_l2_cache(symbol)
    if data:
        save_to_l1(symbol, data)  # 提升到 L1
        return data, source
    
    # 3. 检查 L3 缓存
    data, source = get_l3_cache(conn, symbol)
    if data:
        save_to_l1(symbol, data)
        save_to_l2(symbol, data)  # 提升到 L2
        return data, source
    
    # 4. API 获取 (异步)
    return None, "API"


async def main():
    print("=" * 70)
    print("🚀 AReaL 改进应用 - 异步数据获取 + 三层缓存")
    print(f"⏰ 时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    # 连接数据库
    conn = sqlite3.connect(DB_PATH)
    
    # 异步获取所有持仓数据
    print("\n📡 异步获取持仓数据...")
    start = time.time()
    
    results = await fetch_all_holdings()
    
    elapsed = time.time() - start
    print(f"✅ 获取完成：{len(results)} 只股票，耗时 {elapsed:.2f}秒")
    
    # 保存到缓存
    print("\n💾 保存到三层缓存...")
    for data in results:
        symbol = data["symbol"]
        save_to_l1(symbol, data)
        save_to_l2(symbol, data)
        save_to_l3(conn, data)
        print(f"  ✅ {symbol}: ${data['price']} ({data['change_pct']}%)")
    
    # 统计
    print(f"\n📊 缓存统计:")
    print(f"  L1 内存缓存：{len(l1_cache)} 只")
    print(f"  L2 文件缓存：{len(list(CACHE_DIR.glob('quote_*.json')))} 只")
    
    conn.close()
    
    print("\n" + "=" * 70)
    print("✅ AReaL 改进应用完成!")
    print("=" * 70)
    
    return results


if __name__ == "__main__":
    asyncio.run(main())
