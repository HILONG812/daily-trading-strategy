#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基于真实股票列表的数据缓存 - 使用 447 只核心股票
"""

import yfinance as yf
import sqlite3
import json
from datetime import datetime
from pathlib import Path

DB_PATH = Path("/root/.openclaw/workspace/data/stock_market.db")
STOCK_LIST_DIR = Path("/root/.openclaw/workspace/data/stock_lists")


# 加载所有股票列表
def load_all_stocks():
    """从 JSON 文件加载所有股票"""
    all_stocks = []
    
    for json_file in STOCK_LIST_DIR.glob("*.json"):
        if json_file.name == "all_stocks_summary.json":
            continue
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                market = data.get("market", "")
                for symbol in data.get("stocks", []):
                    all_stocks.append((symbol, market))
        except Exception as e:
            print(f"加载 {json_file} 失败：{e}")
    
    # 去重
    seen = set()
    unique_stocks = []
    for symbol, market in all_stocks:
        if symbol not in seen:
            seen.add(symbol)
            unique_stocks.append((symbol, market))
    
    return unique_stocks


def init_database():
    """初始化数据库"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 创建表
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
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
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
            UNIQUE(symbol, date)
        )
    ''')
    
    # 索引
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_stocks_market ON stocks(market)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_quotes_symbol ON quotes(symbol)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_klines_symbol_date ON klines(symbol, date)')
    
    conn.commit()
    return conn


def fetch_and_save(conn, symbol, market):
    """获取并保存单只股票数据"""
    try:
        ticker = yf.Ticker(symbol)
        
        # 基本信息
        info = ticker.info
        name = info.get("shortName", info.get("longName", ""))
        sector = info.get("sector", "")
        industry = info.get("industry", "")
        market_cap = info.get("marketCap", 0)
        
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO stocks (symbol, name, market, sector, industry, market_cap, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (symbol, name if name else "", market, sector if sector else "", industry if industry else "", market_cap if market_cap else 0))
        
        # 行情
        hist = ticker.history(period="1d")
        if len(hist) > 0:
            row = hist.iloc[-1]
            prev_hist = ticker.history(period="2d")
            prev_close = prev_hist.iloc[-2]["Close"] if len(prev_hist) > 1 else row.get("Close", 0)
            close_price = row.get("Close", 0)
            
            if prev_close and close_price and prev_close > 0:
                change_pct = ((close_price - prev_close) / prev_close) * 100
            else:
                change_pct = 0
            
            cursor.execute('''
                INSERT INTO quotes (symbol, price, change_pct, high, low, open, prev_close, volume)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (symbol, round(close_price, 2), round(change_pct, 2),
                  round(row.get("High", 0), 2), round(row.get("Low", 0), 2),
                  round(row.get("Open", 0), 2), round(prev_close, 2), int(row.get("Volume", 0))))
        
        # K 线 (5 天)
        klines = ticker.history(period="5d", interval="1d")
        kline_count = 0
        for date, row in klines.iterrows():
            cursor.execute('''
                INSERT OR REPLACE INTO klines (symbol, date, open, high, low, close, volume)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (symbol, date.strftime("%Y-%m-%d"), round(row.get("Open", 0), 2),
                  round(row.get("High", 0), 2), round(row.get("Low", 0), 2),
                  round(row.get("Close", 0), 2), int(row.get("Volume", 0))))
            kline_count += 1
        
        conn.commit()
        return True, kline_count
    except Exception as e:
        return False, 0


def main():
    print("=" * 70)
    print("📊 基于真实股票列表的数据缓存")
    print(f"⏰ 时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    # 加载股票列表
    print("\n📋 加载股票列表...")
    stocks = load_all_stocks()
    print(f"✅ 加载 {len(stocks)} 只唯一股票")
    
    # 初始化数据库
    print("\n📁 初始化数据库...")
    conn = init_database()
    
    # 按市场分组
    by_market = {}
    for symbol, market in stocks:
        if market not in by_market:
            by_market[market] = []
        by_market[market].append(symbol)
    
    print(f"📊 市场分布:")
    for market, syms in by_market.items():
        print(f"   {market}: {len(syms)} 只")
    
    # 获取数据
    total = len(stocks)
    success = 0
    fail = 0
    total_klines = 0
    
    print("\n" + "=" * 70)
    print("🔄 开始获取数据...")
    print("=" * 70)
    
    for i, (symbol, market) in enumerate(stocks):
        ok, kline_count = fetch_and_save(conn, symbol, market)
        if ok:
            success += 1
            total_klines += kline_count
        else:
            fail += 1
        
        total_processed = success + fail
        
        # 进度汇报
        if total_processed % 50 == 0 or total_processed == total:
            pct = (total_processed / total) * 100
            print(f"\r  进度：{total_processed:,}/{total:,} ({pct:.1f}%) | 成功：{success:,} | 失败：{fail:,} | K 线：{total_klines:,}条", end="", flush=True)
    
    print("\n")
    
    # 最终统计
    print("=" * 70)
    print("📊 最终统计")
    print("=" * 70)
    
    cursor = conn.cursor()
    cursor.execute("SELECT market, COUNT(*) FROM stocks GROUP BY market")
    market_counts = dict(cursor.fetchall())
    for market, count in market_counts.items():
        print(f"  {market}: {count} 只股票")
    
    cursor.execute("SELECT COUNT(*) FROM quotes")
    quote_count = cursor.fetchone()[0]
    print(f"  行情记录：{quote_count} 条")
    
    cursor.execute("SELECT COUNT(*) FROM klines")
    kline_count = cursor.fetchone()[0]
    print(f"  K 线记录：{kline_count} 条")
    
    conn.close()
    
    print("\n" + "=" * 70)
    print(f"✅ 缓存完成!")
    print(f"   总计：{total} 只")
    print(f"   成功：{success} 只 ({success/total*100:.1f}%)")
    print(f"   失败：{fail} 只")
    print(f"   K 线：{total_klines} 条")
    print("=" * 70)


if __name__ == "__main__":
    main()
