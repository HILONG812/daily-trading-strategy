#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全量股票市场数据缓存系统
覆盖：港股 (2500+)、美股 (5000+)、A 股 (5000+)、日股 (3800+)
使用 SQLite 数据库存储
"""

import sqlite3
import json
import time
import requests
from datetime import datetime
from pathlib import Path

DB_PATH = Path("/root/.openclaw/workspace/data/stock_market.db")
CACHE_DIR = Path("/root/.openclaw/workspace/data/market_cache")
CACHE_DIR.mkdir(parents=True, exist_ok=True)


def init_database():
    """初始化 SQLite 数据库"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 股票基本信息表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stocks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT UNIQUE NOT NULL,
            name TEXT,
            market TEXT NOT NULL,
            sector TEXT,
            industry TEXT,
            market_cap REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 实时行情表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS quotes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            price REAL,
            change_pct REAL,
            high REAL,
            low REAL,
            open REAL,
            prev_close REAL,
            volume INTEGER,
            turnover REAL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (symbol) REFERENCES stocks(symbol)
        )
    ''')
    
    # K 线历史表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS klines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            date DATE NOT NULL,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            volume INTEGER,
            UNIQUE(symbol, date),
            FOREIGN KEY (symbol) REFERENCES stocks(symbol)
        )
    ''')
    
    # 创建索引
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_stocks_market ON stocks(market)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_quotes_symbol ON quotes(symbol)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_klines_symbol_date ON klines(symbol, date)')
    
    conn.commit()
    return conn


def fetch_hk_stock_list():
    """获取港股股票列表 (东方财富 API)"""
    try:
        # 获取港股主板股票
        url = "https://push2.eastmoney.com/api/qt/clist/get"
        params = {
            "pn": 1,
            "pz": 500,
            "po": "1",
            "np": "1",
            "ut": "bd1d9ddb04089700cf9c27f6f7426281",
            "fltt": "2",
            "invt": "2",
            "fid": "f3",
            "fs": "m:116 t:3,m:116 t:4,m:116 t:1,m:116 t:2",
            "fields": "f12,f14,f152,f136,f150,f137,f124,f128"
        }
        resp = requests.get(url, params=params, timeout=30)
        data = resp.json()
        
        stocks = []
        if data.get("data") and data["data"].get("diff"):
            for item in data["data"]["diff"]:
                stocks.append({
                    "symbol": item.get("f12", ""),
                    "name": item.get("f14", ""),
                    "market": "HK",
                    "sector": "",
                    "industry": "",
                    "market_cap": item.get("f152", 0),
                })
        
        return stocks
    except Exception as e:
        print(f"❌ 获取港股列表失败：{e}")
        return []


def fetch_hk_quote(symbol):
    """获取港股实时行情"""
    try:
        url = "https://push2.eastmoney.com/api/qt/stock/get"
        params = {
            "secid": f"116.{symbol}",
            "fields": "f43,f44,f45,f46,f47,f48,f55,f57,f58"
        }
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
                "open": d.get("f45", 0) / 1000,
                "prev_close": last,
                "volume": d.get("f47", 0),
                "turnover": d.get("f48", 0) / 10000,
            }
    except Exception as e:
        pass
    return None


def save_stock(conn, stock):
    """保存股票基本信息"""
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT OR REPLACE INTO stocks (symbol, name, market, sector, industry, market_cap, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (stock["symbol"], stock["name"], stock["market"], 
              stock.get("sector", ""), stock.get("industry", ""), stock.get("market_cap", 0)))
        conn.commit()
        return True
    except Exception as e:
        print(f"  保存股票失败：{e}")
        return False


def save_quote(conn, quote):
    """保存实时行情"""
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO quotes (symbol, price, change_pct, high, low, open, prev_close, volume, turnover)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (quote["symbol"], quote["price"], quote["change_pct"],
              quote.get("high", 0), quote.get("low", 0), quote.get("open", 0),
              quote.get("prev_close", 0), quote.get("volume", 0), quote.get("turnover", 0)))
        conn.commit()
        return True
    except Exception as e:
        print(f"  保存行情失败：{e}")
        return False


def cache_hk_stocks(conn, limit=None):
    """缓存港股数据"""
    print("\n" + "=" * 70)
    print("🇭🇰 开始缓存港股数据...")
    print("=" * 70)
    
    # 获取股票列表
    print("📋 获取港股列表...")
    stocks = fetch_hk_stock_list()
    
    if not stocks:
        print("❌ 获取港股列表失败")
        return
    
    print(f"✅ 获取到 {len(stocks)} 只港股")
    
    if limit:
        stocks = stocks[:limit]
        print(f"📌 限制缓存前 {limit} 只")
    
    # 缓存股票信息和行情
    success_count = 0
    fail_count = 0
    
    for i, stock in enumerate(stocks):
        symbol = stock["symbol"]
        name = stock["name"]
        
        if i % 100 == 0:
            print(f"  进度：{i}/{len(stocks)} ({i/len(stocks)*100:.1f}%)")
        
        # 保存股票信息
        if not save_stock(conn, stock):
            fail_count += 1
            continue
        
        # 获取行情
        quote = fetch_hk_quote(symbol)
        if quote:
            save_quote(conn, quote)
            success_count += 1
        else:
            fail_count += 1
        
        # 避免 API 限流
        time.sleep(0.1)
    
    print(f"\n✅ 港股缓存完成!")
    print(f"  成功：{success_count} 只")
    print(f"  失败：{fail_count} 只")


def get_stats(conn):
    """获取数据库统计"""
    cursor = conn.cursor()
    
    cursor.execute("SELECT market, COUNT(*) FROM stocks GROUP BY market")
    market_counts = dict(cursor.fetchall())
    
    cursor.execute("SELECT COUNT(*) FROM quotes")
    quote_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM klines")
    kline_count = cursor.fetchone()[0]
    
    return {
        "stocks": market_counts,
        "quotes": quote_count,
        "klines": kline_count,
    }


def main():
    print("=" * 70)
    print("🌍 全量股票市场数据缓存系统")
    print(f"📅 时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    # 初始化数据库
    print("\n📁 初始化数据库...")
    conn = init_database()
    print(f"✅ 数据库：{DB_PATH}")
    
    # 缓存港股
    cache_hk_stocks(conn, limit=500)  # 先缓存 500 只测试
    
    # 统计
    print("\n" + "=" * 70)
    print("📊 数据库统计")
    print("=" * 70)
    stats = get_stats(conn)
    for market, count in stats["stocks"].items():
        print(f"  {market}: {count} 只股票")
    print(f"  行情记录：{stats['quotes']} 条")
    print(f"  K 线记录：{stats['klines']} 条")
    
    conn.close()
    print("\n" + "=" * 70)
    print("✅ 完成!")
    print("=" * 70)


if __name__ == "__main__":
    main()
