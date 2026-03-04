#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任务 4: 创建股票池 - 滚动增减，实时监控
"""

import json
import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path("/root/.openclaw/workspace/data/stock_market.db")
POOL_FILE = Path("/root/.openclaw/workspace/data/stock_pool.json")


def create_stock_pool():
    """创建股票池"""
    pool = {
        "created_time": datetime.now().isoformat(),
        "last_updated": datetime.now().isoformat(),
        "watchlist": [],      # 观察池
        "buy_candidates": [], # 买入候选
        "hold": [],           # 持有
        "sell_candidates": [],# 卖出候选
        "blacklist": [],      # 黑名单
    }
    return pool


def update_pool(pool):
    """更新股票池时间戳"""
    pool["last_updated"] = datetime.now().isoformat()
    return pool


def main():
    print("=" * 70)
    print("🏊 任务 4: 创建股票池")
    print(f"⏰ 时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    # 创建股票池
    pool = create_stock_pool()
    
    # 从数据库读取已有股票
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 读取所有股票
    cursor.execute("SELECT symbol, name, market FROM stocks")
    rows = cursor.fetchall()
    
    for row in rows:
        symbol, name, market = row
        pool["watchlist"].append({
            "symbol": symbol,
            "name": name or "",
            "market": market,
            "added_time": datetime.now().isoformat(),
            "status": "watching",
        })
    
    conn.close()
    
    # 更新池
    pool = update_pool(pool)
    
    # 保存
    with open(POOL_FILE, "w", encoding="utf-8") as f:
        json.dump(pool, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 股票池创建完成!")
    print(f"📊 观察池：{len(pool['watchlist'])} 只")
    print(f"📄 文件：{POOL_FILE}")
    print("=" * 70)


if __name__ == "__main__":
    main()
