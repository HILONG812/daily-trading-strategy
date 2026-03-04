#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用 AKShare 获取全球股票市场数据
支持：A 股/港股/美股/日股/期货/基金/债券 等
文档：https://akshare.akfamily.xyz/
"""

import akshare as ak
import json
import sqlite3
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


def fetch_all_a_stocks():
    """获取全部 A 股股票列表"""
    print("\n🇨🇳 获取 A 股股票列表...")
    try:
        # 获取 A 股列表
        stock_info = ak.stock_info_a_code_name()
        stocks = []
        for _, row in stock_info.iterrows():
            stocks.append({
                "symbol": row["code"],
                "name": row["name"],
                "market": "CN",
                "sector": "",
                "industry": "",
            })
        print(f"✅ 获取到 {len(stocks)} 只 A 股")
        return stocks
    except Exception as e:
        print(f"❌ 获取 A 股列表失败：{e}")
        return []


def fetch_hk_stock_list():
    """获取港股股票列表"""
    print("\n🇭🇰 获取港股股票列表...")
    try:
        # 获取港股列表
        stock_hk = ak.stock_hk_spot()
        stocks = []
        for _, row in stock_hk.iterrows():
            stocks.append({
                "symbol": str(row["代码"]),
                "name": str(row["名称"]),
                "market": "HK",
                "sector": "",
                "industry": "",
            })
        print(f"✅ 获取到 {len(stocks)} 只港股")
        return stocks
    except Exception as e:
        print(f"❌ 获取港股列表失败：{e}")
        return []


def fetch_us_stock_list():
    """获取美股股票列表"""
    print("\n🇺🇸 获取美股股票列表...")
    try:
        # 获取美股列表
        stock_us = ak.stock_us_spot()
        stocks = []
        for _, row in stock_us.iterrows():
            stocks.append({
                "symbol": str(row["ticker"]),
                "name": str(row["name"]),
                "market": "US",
                "sector": "",
                "industry": "",
            })
        print(f"✅ 获取到 {len(stocks)} 只美股")
        return stocks
    except Exception as e:
        print(f"❌ 获取美股列表失败：{e}")
        return []


def fetch_stock_quote(symbol, market):
    """获取单只股票实时行情"""
    try:
        if market == "CN":
            df = ak.stock_zh_a_spot_em()
            row = df[df["代码"] == symbol]
            if len(row) > 0:
                return {
                    "symbol": symbol,
                    "price": float(row["最新价"].values[0]),
                    "change_pct": float(row["涨跌幅"].values[0]),
                    "high": float(row["最高"].values[0]),
                    "low": float(row["最低"].values[0]),
                    "open": float(row["今开"].values[0]),
                    "prev_close": float(row["昨收"].values[0]),
                    "volume": int(float(row["成交量"].values[0]) * 100),
                }
        elif market == "HK":
            df = ak.stock_hk_spot()
            row = df[df["代码"] == symbol]
            if len(row) > 0:
                return {
                    "symbol": symbol,
                    "price": float(row["最新价"].values[0]),
                    "change_pct": float(row["涨跌幅"].values[0]),
                    "high": float(row["最高"].values[0]),
                    "low": float(row["最低"].values[0]),
                    "open": float(row["今开"].values[0]),
                    "prev_close": float(row["昨收"].values[0]),
                    "volume": int(float(row["成交量"].values[0])),
                }
        elif market == "US":
            df = ak.stock_us_spot()
            row = df[df["ticker"] == symbol]
            if len(row) > 0:
                return {
                    "symbol": symbol,
                    "price": float(row["最新价"].values[0]),
                    "change_pct": float(row["涨跌幅"].values[0]),
                    "high": float(row["最高"].values[0]),
                    "low": float(row["最低"].values[0]),
                    "open": float(row["今开"].values[0]),
                    "prev_close": float(row["昨收"].values[0]),
                    "volume": int(float(row["成交量"].values[0])),
                }
    except Exception as e:
        pass
    return None


def fetch_kline_data(symbol, market, period="daily", start_date="20260225", end_date="20260304"):
    """获取 K 线历史数据"""
    try:
        if market == "CN":
            df = ak.stock_zh_a_hist(symbol=symbol, period=period, start_date=start_date, end_date=end_date, adjust="")
        elif market == "HK":
            df = ak.stock_hk_hist(symbol=symbol, period=period, start_date=start_date, end_date=end_date, adjust="")
        elif market == "US":
            df = ak.stock_us_hist(symbol=symbol, period=period, start_date=start_date, end_date=end_date, adjust="")
        else:
            return []
        
        klines = []
        for _, row in df.iterrows():
            klines.append({
                "date": str(row["日期"]),
                "open": float(row["开盘"]),
                "high": float(row["最高"]),
                "low": float(row["最低"]),
                "close": float(row["收盘"]),
                "volume": int(float(row["成交量"]) * 100) if "成交量" in row.index else 0,
            })
        return klines
    except Exception as e:
        print(f"  获取 {symbol} K 线失败：{e}")
        return []


def save_stock(conn, stock):
    """保存股票基本信息"""
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT OR REPLACE INTO stocks (symbol, name, market, sector, industry, updated_at)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (stock["symbol"], stock["name"], stock["market"], 
              stock.get("sector", ""), stock.get("industry", "")))
        conn.commit()
        return True
    except Exception as e:
        return False


def save_quote(conn, quote):
    """保存实时行情"""
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO quotes (symbol, price, change_pct, high, low, open, prev_close, volume)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (quote["symbol"], quote["price"], quote["change_pct"],
              quote.get("high", 0), quote.get("low", 0), quote.get("open", 0),
              quote.get("prev_close", 0), quote.get("volume", 0)))
        conn.commit()
        return True
    except Exception as e:
        return False


def save_klines(conn, symbol, klines):
    """保存 K 线历史数据"""
    cursor = conn.cursor()
    count = 0
    for k in klines:
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO klines (symbol, date, open, high, low, close, volume)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (symbol, k["date"], k["open"], k["high"], k["low"], k["close"], k["volume"]))
            count += 1
        except Exception as e:
            pass
    conn.commit()
    return count


def main():
    print("=" * 70)
    print("🌍 AKShare 全量股票市场数据缓存")
    print(f"📅 时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    # 初始化数据库
    print("\n📁 初始化数据库...")
    conn = init_database()
    print(f"✅ 数据库：{DB_PATH}")
    
    # 1. 获取 A 股股票列表
    cn_stocks = fetch_all_a_stocks()
    for stock in cn_stocks[:100]:  # 先缓存 100 只测试
        save_stock(conn, stock)
    
    # 2. 获取港股股票列表
    hk_stocks = fetch_hk_stock_list()
    for stock in hk_stocks[:100]:  # 先缓存 100 只测试
        save_stock(conn, stock)
    
    # 3. 获取美股股票列表
    us_stocks = fetch_us_stock_list()
    for stock in us_stocks[:100]:  # 先缓存 100 只测试
        save_stock(conn, stock)
    
    # 统计
    cursor = conn.cursor()
    cursor.execute("SELECT market, COUNT(*) FROM stocks GROUP BY market")
    market_counts = dict(cursor.fetchall())
    
    print("\n" + "=" * 70)
    print("📊 数据库统计")
    print("=" * 70)
    for market, count in market_counts.items():
        print(f"  {market}: {count} 只股票")
    
    conn.close()
    print("\n" + "=" * 70)
    print("✅ AKShare 数据缓存完成!")
    print("=" * 70)


if __name__ == "__main__":
    main()
