#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全量股票市场数据缓存 - 真正的全量版本
使用 yfinance screener 获取所有美股 + 港股 + 日股 + A 股
"""

import yfinance as yf
import sqlite3
import json
import time
from datetime import datetime
from pathlib import Path

DB_PATH = Path("/root/.openclaw/workspace/data/stock_market.db")
CACHE_DIR = Path("/root/.openclaw/workspace/data/market_cache")
CACHE_DIR.mkdir(parents=True, exist_ok=True)


def get_us_stocks():
    """获取所有美股 (纳斯达克 + 纽交所 + 美交所)"""
    # 使用 yfinance screener 获取美股列表
    try:
        # 纳斯达克
        nasdaq = yf.EquityQuery('exchange', ['NMS'])
        # 纽交所
        nyse = yf.EquityQuery('exchange', ['NYQ'])
        # 美交所
        amex = yf.EquityQuery('exchange', ['ASE'])
        
        # 获取所有股票
        all_us = []
        for query in [nasdaq, nyse, amex]:
            try:
                symbols = yf.Screener(query=query, count=10000)
                all_us.extend([s.symbol for s in symbols])
            except:
                pass
        
        return list(set(all_us))
    except Exception as e:
        print(f"获取美股列表失败：{e}")
        # 备用方案：使用代码范围生成
        return [f"{chr(i)}{chr(j)}{chr(k)}" for i in range(65, 91) for j in range(65, 91) for k in range(65, 91)][:8000]


def get_hk_stocks():
    """获取所有港股 (0001-9999)"""
    return [f"{str(i).zfill(4)}.HK" for i in range(1, 10000)]


def get_jp_stocks():
    """获取所有日股 (东证一部 + 二部 + 创业板)"""
    # 东证一部 (1300-9999)
    # 东证二部 (1300-9999)
    # 创业板 (3000-9999)
    return [f"{str(i).zfill(4)}.T" for i in range(1300, 10000)]


def get_cn_stocks():
    """获取所有 A 股 (沪深 + 创业板 + 科创板)"""
    # 沪市主板 (600000-605999)
    # 沪市科创板 (688000-688999)
    # 深市主板 (000001-002999)
    # 深市创业板 (300000-301999)
    return (
        [f"{str(i).zfill(6)}.SS" for i in range(600000, 606000)] +
        [f"{str(i).zfill(6)}.SS" for i in range(688000, 689000)] +
        [f"{str(i).zfill(6)}.SZ" for i in range(1, 3000)] +
        [f"{str(i).zfill(6)}.SZ" for i in range(200000, 302000)]
    )


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


def fetch_and_save_stock(conn, symbol, market):
    """获取并保存单只股票数据"""
    try:
        ticker = yf.Ticker(symbol)
        
        # 获取基本信息
        info = ticker.info
        name = info.get("shortName", info.get("longName", ""))
        sector = info.get("sector", "")
        industry = info.get("industry", "")
        market_cap = info.get("marketCap", 0)
        
        # 保存股票信息
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO stocks (symbol, name, market, sector, industry, market_cap, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (symbol, name if name else "", market, sector if sector else "", industry if industry else "", market_cap if market_cap else 0))
        
        # 获取行情
        hist = ticker.history(period="1d")
        if len(hist) > 0 and len(hist.iloc[-1]) > 0:
            row = hist.iloc[-1]
            prev_hist = ticker.history(period="2d")
            prev_close = prev_hist.iloc[-2]["Close"] if len(prev_hist) > 1 else row.get("Close", row.get("Open", 0))
            close_price = row.get("Close", row.get("Open", 0))
            if prev_close and close_price:
                change_pct = ((close_price - prev_close) / prev_close) * 100
            else:
                change_pct = 0
            
            cursor.execute('''
                INSERT INTO quotes (symbol, price, change_pct, high, low, open, prev_close, volume)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (symbol, round(close_price, 2), round(change_pct, 2),
                  round(row.get("High", 0), 2), round(row.get("Low", 0), 2),
                  round(row.get("Open", 0), 2), round(prev_close, 2), int(row.get("Volume", 0))))
        
        # 获取 K 线 (最近 5 天)
        klines = ticker.history(period="5d", interval="1d")
        for date, row in klines.iterrows():
            if len(row) > 0:
                cursor.execute('''
                    INSERT OR REPLACE INTO klines (symbol, date, open, high, low, close, volume)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (symbol, date.strftime("%Y-%m-%d"), round(row.get("Open", 0), 2),
                      round(row.get("High", 0), 2), round(row.get("Low", 0), 2),
                      round(row.get("Close", 0), 2), int(row.get("Volume", 0))))
        
        conn.commit()
        return True
    except Exception as e:
        return False


def main():
    print("=" * 70)
    print("🌍 全量股票市场数据缓存 - 真正的全量版本")
    print(f"📅 时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    # 初始化数据库
    print("\n📁 初始化数据库...")
    conn = init_database()
    print(f"✅ 数据库：{DB_PATH}")
    
    # 获取股票列表
    print("\n📋 获取股票列表...")
    us_stocks = get_us_stocks()
    hk_stocks = get_hk_stocks()
    jp_stocks = get_jp_stocks()
    cn_stocks = get_cn_stocks()
    
    total = len(us_stocks) + len(hk_stocks) + len(jp_stocks) + len(cn_stocks)
    print(f"✅ 总计：{total:,} 只股票")
    print(f"   - 🇺🇸 美股：{len(us_stocks):,} 只")
    print(f"   - 🇭🇰 港股：{len(hk_stocks):,} 只")
    print(f"   - 🇯🇵 日股：{len(jp_stocks):,} 只")
    print(f"   - 🇨🇳 A 股：{len(cn_stocks):,} 只")
    
    success = 0
    fail = 0
    total_processed = 0
    
    # 获取美股
    print("\n" + "=" * 70)
    print("🇺🇸 美股数据获取...")
    print("=" * 70)
    for i, symbol in enumerate(us_stocks):
        if fetch_and_save_stock(conn, symbol, "US"):
            success += 1
        else:
            fail += 1
        total_processed += 1
        
        if total_processed % 50 == 0:
            print(f"\r  进度：{total_processed:,}/{total:,} | 成功：{success:,} | 失败：{fail:,}", end="", flush=True)
    
    # 获取港股
    print("\n" + "=" * 70)
    print("🇭🇰 港股数据获取...")
    print("=" * 70)
    for i, symbol in enumerate(hk_stocks):
        if fetch_and_save_stock(conn, symbol, "HK"):
            success += 1
        else:
            fail += 1
        total_processed += 1
        
        if total_processed % 100 == 0:
            print(f"\r  进度：{total_processed:,}/{total:,} | 成功：{success:,} | 失败：{fail:,}", end="", flush=True)
    
    # 获取日股
    print("\n" + "=" * 70)
    print("🇯🇵 日股数据获取...")
    print("=" * 70)
    for i, symbol in enumerate(jp_stocks):
        if fetch_and_save_stock(conn, symbol, "JP"):
            success += 1
        else:
            fail += 1
        total_processed += 1
        
        if total_processed % 100 == 0:
            print(f"\r  进度：{total_processed:,}/{total:,} | 成功：{success:,} | 失败：{fail:,}", end="", flush=True)
    
    # 获取 A 股
    print("\n" + "=" * 70)
    print("🇨🇳 A 股数据获取...")
    print("=" * 70)
    for i, symbol in enumerate(cn_stocks):
        if fetch_and_save_stock(conn, symbol, "CN"):
            success += 1
        else:
            fail += 1
        total_processed += 1
        
        if total_processed % 100 == 0:
            print(f"\r  进度：{total_processed:,}/{total:,} | 成功：{success:,} | 失败：{fail:,}", end="", flush=True)
    
    # 最终统计
    print("\n" + "=" * 70)
    print("📊 最终统计")
    print("=" * 70)
    cursor = conn.cursor()
    cursor.execute("SELECT market, COUNT(*) FROM stocks GROUP BY market")
    market_counts = dict(cursor.fetchall())
    for market, count in market_counts.items():
        print(f"  {market}: {count:,} 只股票")
    
    cursor.execute("SELECT COUNT(*) FROM quotes")
    quote_count = cursor.fetchone()[0]
    print(f"  行情记录：{quote_count:,} 条")
    
    cursor.execute("SELECT COUNT(*) FROM klines")
    kline_count = cursor.fetchone()[0]
    print(f"  K 线记录：{kline_count:,} 条")
    
    conn.close()
    print("\n" + "=" * 70)
    print(f"✅ 全量数据缓存完成!")
    print(f"   总计：{total_processed:,} 只")
    print(f"   成功：{success:,} 只")
    print(f"   失败：{fail:,} 只")
    print(f"   成功率：{success/total_processed*100:.1f}%")
    print("=" * 70)


if __name__ == "__main__":
    main()
