#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用 yfinance 获取全球股票市场数据
覆盖：美股/港股/A 股/日股 主要成分股
"""

import yfinance as yf
import sqlite3
import json
from datetime import datetime
from pathlib import Path

DB_PATH = Path("/root/.openclaw/workspace/data/stock_market.db")
CACHE_DIR = Path("/root/.openclaw/workspace/data/market_cache")
CACHE_DIR.mkdir(parents=True, exist_ok=True)


# 主要市场指数成分股 (精简版)
MARKET_STOCKS = {
    "US": [
        # 科技巨头
        "AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA", "BRK.B",
        # 标普 500 主要成分
        "JPM", "V", "JNJ", "WMT", "PG", "MA", "UNH", "HD", "DIS", "PYPL",
        "BAC", "VZ", "ADBE", "CMCSA", "NFLX", "KO", "NKE", "PFE", "T", "INTC",
        "MRK", "PEP", "CSCO", "ABT", "TMO", "COST", "AVGO", "ACN", "TXN",
        "LLY", "ORCL", "WFC", "MDT", "DHR", "NEE", "BMY", "QCOM", "UPS",
        "AMGN", "HON", "PM", "RTX", "LOW", "IBM", "BA", "SBUX", "GE", "CAT",
    ],
    "HK": [
        # 恒生指数成分股
        "0700.HK", "9988.HK", "9618.HK", "9863.HK", "2402.HK",
        "0005.HK", "0001.HK", "0002.HK", "0003.HK", "0006.HK",
        "0011.HK", "0012.HK", "0016.HK", "0017.HK", "0019.HK",
        "0027.HK", "0066.HK", "0083.HK", "0088.HK", "0101.HK",
        "0144.HK", "0175.HK", "0267.HK", "0288.HK", "0293.HK",
        "0386.HK", "0388.HK", "0390.HK", "0392.HK", "0489.HK",
        "0688.HK", "0762.HK", "0823.HK", "0857.HK", "0883.HK",
        "0939.HK", "0941.HK", "0968.HK", "0992.HK", "1038.HK",
        "1044.HK", "1088.HK", "1093.HK", "1109.HK", "1113.HK",
        "1177.HK", "1299.HK", "1398.HK", "1876.HK", "1997.HK",
        "2018.HK", "2269.HK", "2313.HK", "2318.HK", "2382.HK",
        "2388.HK", "2628.HK", "3690.HK", "3968.HK", "3988.HK",
    ],
    "JP": [
        # 日经 225 主要成分
        "7203.T", "8058.T", "6758.T", "9984.T", "9432.T",
        "6861.T", "4063.T", "6954.T", "8035.T", "4568.T",
        "7974.T", "6098.T", "9433.T", "8031.T", "8001.T",
        "8002.T", "8053.T", "9020.T", "9022.T", "6902.T",
    ],
    "CN": [
        # 沪深 300 主要成分
        "600519.SS", "000858.SZ", "002415.SZ", "300750.SZ",
        "601318.SS", "601398.SS", "600036.SS", "601857.SS",
        "600276.SS", "000333.SZ", "000651.SZ", "002594.SZ",
        "300014.SZ", "300059.SZ", "600030.SS", "601166.SS",
        "600887.SS", "000001.SZ", "000002.SZ", "600585.SS",
    ],
}


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


def fetch_stock_info(symbol):
    """获取股票基本信息"""
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        return {
            "symbol": symbol,
            "name": info.get("shortName", info.get("longName", "")),
            "sector": info.get("sector", ""),
            "industry": info.get("industry", ""),
            "market_cap": info.get("marketCap", 0),
        }
    except Exception as e:
        return None


def fetch_stock_quote(symbol):
    """获取实时行情"""
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="1d")
        
        if len(hist) > 0:
            row = hist.iloc[-1]
            prev_hist = ticker.history(period="2d")
            prev_close = prev_hist.iloc[-2]["Close"] if len(prev_hist) > 1 else row["Close"]
            
            change_pct = ((row["Close"] - prev_close) / prev_close) * 100 if prev_close else 0
            
            return {
                "symbol": symbol,
                "price": round(row["Close"], 2),
                "change_pct": round(change_pct, 2),
                "high": round(row["High"], 2),
                "low": round(row["Low"], 2),
                "open": round(row["Open"], 2),
                "prev_close": round(prev_close, 2),
                "volume": int(row["Volume"]),
            }
    except Exception as e:
        pass
    return None


def fetch_kline_data(symbol, period="5d", interval="1d"):
    """获取 K 线历史数据"""
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=period, interval=interval)
        
        klines = []
        for date, row in hist.iterrows():
            klines.append({
                "date": date.strftime("%Y-%m-%d"),
                "open": round(row["Open"], 2),
                "high": round(row["High"], 2),
                "low": round(row["Low"], 2),
                "close": round(row["Close"], 2),
                "volume": int(row["Volume"]),
            })
        return klines
    except Exception as e:
        return []


def save_stock(conn, stock, market):
    """保存股票基本信息"""
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT OR REPLACE INTO stocks (symbol, name, market, sector, industry, market_cap, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (stock["symbol"], stock["name"], market, 
              stock.get("sector", ""), stock.get("industry", ""), stock.get("market_cap", 0)))
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
        except:
            pass
    conn.commit()
    return count


def main():
    print("=" * 70)
    print("🌍 yfinance 全球股票市场数据缓存")
    print(f"📅 时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    # 初始化数据库
    print("\n📁 初始化数据库...")
    conn = init_database()
    print(f"✅ 数据库：{DB_PATH}")
    
    total_stocks = sum(len(stocks) for stocks in MARKET_STOCKS.values())
    print(f"📋 计划获取 {total_stocks} 只股票数据")
    
    # 按市场获取
    for market, symbols in MARKET_STOCKS.items():
        print(f"\n{'='*70}")
        print(f"🇭🇰 {market} 市场 ({len(symbols)} 只)")
        print(f"{'='*70}")
        
        success_count = 0
        for i, symbol in enumerate(symbols):
            print(f"\r  进度：{i+1}/{len(symbols)} | 成功：{success_count}", end="", flush=True)
            
            # 获取基本信息
            info = fetch_stock_info(symbol)
            if info:
                save_stock(conn, info, market)
            
            # 获取行情
            quote = fetch_stock_quote(symbol)
            if quote:
                save_quote(conn, quote)
                success_count += 1
            
            # 获取 K 线 (最近 5 天)
            klines = fetch_kline_data(symbol, period="5d")
            if klines:
                save_klines(conn, symbol, klines)
        
        print(f"\n  ✅ {market} 完成：{success_count}/{len(symbols)}")
    
    # 统计
    print("\n" + "=" * 70)
    print("📊 数据库统计")
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
    print("✅ yfinance 数据缓存完成!")
    print("=" * 70)


if __name__ == "__main__":
    main()
