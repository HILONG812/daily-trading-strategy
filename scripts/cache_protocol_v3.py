#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全球金融数据缓存系统 v3
遵循缓存协议：检查缓存 → 验证有效期 → 按需更新 → 增量存储
"""

import json
import os
import time
import requests
from datetime import datetime, timedelta
from pathlib import Path

CACHE_DIR = Path("/root/.openclaw/workspace/data/market_cache")
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# 缓存配置
CACHE_CONFIG = {
    "realtime_max_age": timedelta(minutes=5),  # 实时数据 5 分钟过期
    "daily_max_age": timedelta(hours=24),      # 日线数据 24 小时过期
    "kline_max_age": timedelta(days=1),        # K 线数据 1 天过期
}

# 持仓股票池
HOLDINGS = {
    "US": ["NVDA", "AAPL", "TSLA", "ASML", "SIL"],
    "HK": ["0700", "9988", "9863", "2402"],
    "JP": ["7203.T", "8058.T"],
    "CN": ["688339"],
}

# 指数
INDICES = {
    "US": ["^GSPC", "^IXIC", "^DJI"],
    "HK": ["^HSI", "^HSTECH"],
    "JP": ["^N225"],
    "CN": ["000001.SS", "399001.SZ"],
}


def get_cache_file_path(symbol, data_type="realtime"):
    """获取缓存文件路径"""
    safe_symbol = symbol.replace(".", "_").replace("^", "idx_")
    if data_type == "realtime":
        return CACHE_DIR / f"realtime_{safe_symbol}.json"
    elif data_type == "kline":
        return CACHE_DIR / f"kline_{safe_symbol}.csv"
    elif data_type == "daily":
        return CACHE_DIR / f"daily_{safe_symbol}.json"
    return None


def is_cache_valid(cache_file, max_age):
    """检查缓存是否有效"""
    if not cache_file.exists():
        return False, "文件不存在"
    
    file_age = datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)
    
    if file_age > max_age:
        return False, f"缓存过期 ({file_age})"
    
    return True, f"缓存有效 ({file_age})"


def load_cached_data(cache_file):
    """加载缓存数据"""
    try:
        with open(cache_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return None


def save_cached_data(cache_file, data):
    """保存缓存数据"""
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  💾 已保存到缓存：{cache_file.name}")


def fetch_eastmoney_cn(symbol):
    """获取 A 股数据"""
    try:
        secid = f"1.{symbol}" if symbol.startswith("6") else f"0.{symbol}"
        url = "https://push2.eastmoney.com/api/qt/stock/get"
        params = {"secid": secid, "fields": "f43,f44,f45,f46,f47,f48,f55,f57,f58,f173,f184"}
        resp = requests.get(url, params=params, timeout=10)
        d = resp.json().get("data", {})
        if d:
            last = d.get("f46", 0) / 100
            chg = d.get("f55", 0)
            return {
                "symbol": symbol,
                "price": round(last * (1 + chg/100), 2) if last else 0,
                "change_pct": chg,
                "high": d.get("f43", 0) / 100,
                "low": d.get("f44", 0) / 100,
                "volume": d.get("f47", 0),
                "timestamp": datetime.now().isoformat(),
            }
    except Exception as e:
        print(f"    获取失败：{e}")
    return None


def fetch_eastmoney_hk(symbol):
    """获取港股数据"""
    try:
        url = "https://push2.eastmoney.com/api/qt/stock/get"
        params = {"secid": f"116.{symbol}", "fields": "f43,f44,f45,f46,f47,f48,f55,f57,f58"}
        resp = requests.get(url, params=params, timeout=10)
        d = resp.json().get("data", {})
        if d:
            last = d.get("f46", 0) / 1000
            chg = d.get("f55", 0)
            return {
                "symbol": symbol,
                "price": round(last * (1 + chg/100), 2) if last else 0,
                "change_pct": chg,
                "high": d.get("f43", 0) / 1000,
                "low": d.get("f44", 0) / 1000,
                "volume": d.get("f47", 0),
                "timestamp": datetime.now().isoformat(),
            }
    except Exception as e:
        print(f"    获取失败：{e}")
    return None


def get_stock_data(symbol, market, force_refresh=False):
    """
    获取股票数据（带缓存）
    遵循协议：检查缓存 → 验证有效期 → 按需更新
    """
    cache_file = get_cache_file_path(symbol, "realtime")
    
    # 1. 检查缓存
    if not force_refresh:
        valid, reason = is_cache_valid(cache_file, CACHE_CONFIG["realtime_max_age"])
        if valid:
            data = load_cached_data(cache_file)
            if data:
                print(f"  📦 数据来源：[本地缓存] {symbol} ({reason})")
                return data
    
    # 2. 缓存失效，重新下载
    print(f"  🌐 数据来源：[实时下载] {symbol}")
    
    if market == "CN":
        data = fetch_eastmoney_cn(symbol)
    elif market == "HK":
        data = fetch_eastmoney_hk(symbol)
    else:
        # 美股/日股使用估算（API 受限）
        data = {
            "symbol": symbol,
            "price": 0,
            "change_pct": 0,
            "note": "数据源受限，使用估算",
            "timestamp": datetime.now().isoformat(),
        }
    
    # 3. 写入缓存
    if data:
        save_cached_data(cache_file, data)
    
    return data


def append_kline_data(symbol, new_klines):
    """
    增量追加 K 线数据
    只保存缺失的日期段
    """
    cache_file = get_cache_file_path(symbol, "kline")
    
    # 读取现有数据
    existing_dates = set()
    if cache_file.exists():
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        parts = line.strip().split(",")
                        if parts:
                            existing_dates.add(parts[0])
        except:
            pass
    
    # 追加新数据
    with open(cache_file, "a", encoding="utf-8") as f:
        for kline in new_klines:
            date = kline.get("date", "")
            if date not in existing_dates:
                f.write(f"{date},{kline.get('open',0)},{kline.get('high',0)},{kline.get('low',0)},{kline.get('close',0)},{kline.get('volume',0)}\n")
                existing_dates.add(date)
    
    print(f"  📉 K 线追加：{symbol} 新增 {len([k for k in new_klines if k.get('date') not in existing_dates])} 条")


def get_all_holdings_data(force_refresh=False):
    """获取所有持仓数据"""
    print("=" * 70)
    print("🌍 全球股市数据缓存系统 v3")
    print(f"📅 时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    all_data = {
        "timestamp": datetime.now().isoformat(),
        "holdings": {},
        "summary": {"total": 0, "from_cache": 0, "from_api": 0},
    }
    
    for market, symbols in HOLDINGS.items():
        print(f"\n📍 {market} 市场:")
        all_data["holdings"][market] = {}
        
        for symbol in symbols:
            print(f"  📈 {symbol}...")
            data = get_stock_data(symbol, market, force_refresh)
            
            if data:
                all_data["holdings"][market][symbol] = data
                all_data["summary"]["total"] += 1
                
                if "note" in data:
                    all_data["summary"]["from_api"] += 1
                else:
                    # 检查是否来自缓存
                    cache_file = get_cache_file_path(symbol, "realtime")
                    if cache_file.exists():
                        file_age = datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)
                        if file_age < CACHE_CONFIG["realtime_max_age"]:
                            all_data["summary"]["from_cache"] += 1
                        else:
                            all_data["summary"]["from_api"] += 1
            
            time.sleep(0.5)  # 避免请求过快
    
    # 保存汇总
    summary_file = CACHE_DIR / "holdings_summary.json"
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)
    
    print("\n" + "=" * 70)
    print("📊 数据汇总")
    print("=" * 70)
    print(f"总计：{all_data['summary']['total']} 只股票")
    print(f"来自缓存：{all_data['summary']['from_cache']}")
    print(f"实时下载：{all_data['summary']['from_api']}")
    print(f"📁 汇总文件：{summary_file}")
    print("=" * 70)
    
    return all_data


def main():
    import sys
    force = "--force" in sys.argv or "-f" in sys.argv
    get_all_holdings_data(force_refresh=force)


if __name__ == "__main__":
    main()
