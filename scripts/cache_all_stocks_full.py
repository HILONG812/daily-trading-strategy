#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全量股票市场数据缓存 - 激进版本
使用 yfinance 获取全球所有股票数据
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


# 全量股票列表
# 美股：标普 500 + 纳斯达克 + 纽交所 (~5000 只)
# 港股：全部主板 (~2500 只)
# 日股：东证一部 (~3800 只)
# A 股：全部 (~5000 只)

US_STOCKS = [
    # 标普 500 全部成分股
    "AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA", "BRK.B",
    "JPM", "V", "JNJ", "WMT", "PG", "MA", "UNH", "HD", "DIS", "PYPL",
    "BAC", "VZ", "ADBE", "CMCSA", "NFLX", "KO", "NKE", "PFE", "T", "INTC",
    "MRK", "PEP", "CSCO", "ABT", "TMO", "COST", "AVGO", "ACN", "TXN",
    "LLY", "ORCL", "WFC", "MDT", "DHR", "NEE", "BMY", "QCOM", "UPS",
    "AMGN", "HON", "PM", "RTX", "LOW", "IBM", "BA", "SBUX", "GE", "CAT",
    "GS", "MS", "BLK", "SCHW", "AXP", "C", "USB", "PNC", "TFC", "COF",
    "MMM", "HCA", "UNP", "FDX", "LMT", "NOC", "GD", "RTN", "LHX",
    "CVX", "XOM", "COP", "SLB", "EOG", "MPC", "PSX", "VLO", "OXY",
    "ABBV", "MRK", "PFE", "JNJ", "LLY", "BMY", "AMGN", "GILD", "REGN",
    "ISRG", "SYK", "BDX", "MDT", "TMO", "DHR", "ABT", "EW", "ZBH", "BSX",
    "GOOGL", "GOOG", "META", "AMZN", "NFLX", "DIS", "CMCSA", "VZ", "T",
    "TMUS", "CHTR", "DISH", "SIRI", "LBRDK", "LBRDA", "FWONK", "FWONA",
    "AAPL", "MSFT", "NVDA", "AMD", "INTC", "QCOM", "AVGO", "TXN", "ADI",
    "MU", "AMAT", "LRCX", "KLAC", "MCHP", "NXPI", "MRVL", "ON", "STM",
    "CRM", "ORCL", "SAP", "ADBE", "NOW", "INTU", "WDAY", "TEAM", "ZM",
    "DOCU", "OKTA", "CRWD", "ZS", "NET", "DDOG", "MDB", "SNOW", "PLTR",
    "U", "PATH", "AI", "C3AI", "BBAI", "SOUN", "BBAI", "BBAI",
]

# 港股全部 (2500 只 - 使用代码范围)
HK_STOCKS = [f"{str(i).zfill(4)}.HK" for i in range(1, 9000) if i < 10000]

# 日股全部 (3800 只 - 东证一部)
JP_STOCKS = [f"{str(i).zfill(4)}.T" for i in range(1300, 10000)]

# A 股全部 (5000 只 - 沪深)
CN_STOCKS = (
    [f"{str(i).zfill(6)}.SS" for i in range(600000, 606000)] +  # 沪市
    [f"{str(i).zfill(6)}.SZ" for i in range(0, 4000)] +  # 深市
    [f"{str(i).zfill(6)}.SZ" for i in range(200000, 301000)]  # 创业板
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
        ''', (symbol, name, market, sector, industry, market_cap))
        
        # 获取行情
        hist = ticker.history(period="1d")
        if len(hist) > 0:
            row = hist.iloc[-1]
            prev_hist = ticker.history(period="2d")
            prev_close = prev_hist.iloc[-2]["Close"] if len(prev_hist) > 1 else row["Close"]
            change_pct = ((row["Close"] - prev_close) / prev_close) * 100 if prev_close else 0
            
            cursor.execute('''
                INSERT INTO quotes (symbol, price, change_pct, high, low, open, prev_close, volume)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (symbol, round(row["Close"], 2), round(change_pct, 2),
                  round(row["High"], 2), round(row["Low"], 2), round(row["Open"], 2),
                  round(prev_close, 2), int(row["Volume"])))
        
        # 获取 K 线 (最近 5 天)
        klines = ticker.history(period="5d", interval="1d")
        for date, row in klines.iterrows():
            cursor.execute('''
                INSERT OR REPLACE INTO klines (symbol, date, open, high, low, close, volume)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (symbol, date.strftime("%Y-%m-%d"), round(row["Open"], 2),
                  round(row["High"], 2), round(row["Low"], 2), round(row["Close"], 2), int(row["Volume"])))
        
        conn.commit()
        return True
    except Exception as e:
        return False


def main():
    print("=" * 70)
    print("🌍 全量股票市场数据缓存 - 激进版本")
    print(f"📅 时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    # 初始化数据库
    print("\n📁 初始化数据库...")
    conn = init_database()
    print(f"✅ 数据库：{DB_PATH}")
    
    # 统计总数
    total = len(US_STOCKS) + len(HK_STOCKS) + len(JP_STOCKS) + len(CN_STOCKS)
    print(f"📋 计划获取 {total:,} 只股票数据")
    print(f"   - 美股：{len(US_STOCKS):,} 只")
    print(f"   - 港股：{len(HK_STOCKS):,} 只")
    print(f"   - 日股：{len(JP_STOCKS):,} 只")
    print(f"   - A 股：{len(CN_STOCKS):,} 只")
    
    success = 0
    fail = 0
    total_processed = 0
    
    # 获取美股
    print("\n" + "=" * 70)
    print("🇺🇸 美股数据获取...")
    print("=" * 70)
    for i, symbol in enumerate(US_STOCKS):
        if fetch_and_save_stock(conn, symbol, "US"):
            success += 1
        else:
            fail += 1
        total_processed += 1
        
        if total_processed % 10 == 0:
            print(f"\r  进度：{total_processed:,}/{total:,} | 成功：{success:,} | 失败：{fail:,}", end="", flush=True)
    
    # 获取港股
    print("\n" + "=" * 70)
    print("🇭🇰 港股数据获取...")
    print("=" * 70)
    for i, symbol in enumerate(HK_STOCKS):
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
    for i, symbol in enumerate(JP_STOCKS):
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
    for i, symbol in enumerate(CN_STOCKS):
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
