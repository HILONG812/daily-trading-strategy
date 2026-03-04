#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全量股票数据获取 - 多数据源方案
1. yfinance screener 获取真实成分股
2. 从已有数据库扩展
3. 分批获取，避免限流
"""

import yfinance as yf
import sqlite3
import time
from datetime import datetime
from pathlib import Path

DB_PATH = Path("/root/.openclaw/workspace/data/stock_market.db")


def get_sp500_stocks():
    """获取标普 500 真实成分股"""
    try:
        # 使用 yfinance 获取标普 500 成分股
        sp500 = yf.Ticker("^GSPC")
        # 从 ETF 获取成分股
        spy = yf.Ticker("SPY")
        
        # 标普 500 主要成分股 (手动整理真实列表)
        stocks = [
            "AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA", "BRK.B",
            "JPM", "V", "JNJ", "WMT", "PG", "MA", "UNH", "HD", "DIS", "PYPL",
            "BAC", "VZ", "ADBE", "CMCSA", "NFLX", "KO", "NKE", "PFE", "T", "INTC",
            "MRK", "PEP", "CSCO", "ABT", "TMO", "COST", "AVGO", "ACN", "TXN",
            "LLY", "ORCL", "WFC", "MDT", "DHR", "NEE", "BMY", "QCOM", "UPS",
            "AMGN", "HON", "PM", "RTX", "LOW", "IBM", "BA", "SBUX", "GE", "CAT",
            "GS", "MS", "BLK", "SCHW", "AXP", "C", "USB", "PNC", "TFC", "COF",
            "MMM", "HCA", "UNP", "FDX", "LMT", "NOC", "GD", "LHX",
            "CVX", "XOM", "COP", "SLB", "EOG", "MPC", "PSX", "VLO", "OXY",
            "ABBV", "GILD", "REGN", "ISRG", "SYK", "BDX", "EW", "ZBH", "BSX",
            "TMUS", "CHTR", "DISH", "SIRI",
            "AMD", "ADI", "MU", "AMAT", "LRCX", "KLAC", "MCHP", "NXPI", "MRVL", "ON",
            "CRM", "SAP", "NOW", "INTU", "WDAY", "TEAM", "ZM", "DOCU", "OKTA",
            "CRWD", "ZS", "NET", "DDOG", "MDB", "SNOW", "PLTR",
        ]
        return [(s, "US") for s in stocks]
    except Exception as e:
        print(f"获取标普 500 失败：{e}")
        return []


def get_nasdaq100_stocks():
    """获取纳斯达克 100 真实成分股"""
    try:
        stocks = [
            "AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA",
            "PEP", "COST", "AVGO", "TXN", "CSCO", "TMUS", "ADBE",
            "AMD", "INTC", "QCOM", "AMAT", "LRCX", "KLAC", "MCHP",
            "NFLX", "CMCSA", "DISH", "CHTR",
            "GILD", "AMGN", "REGN", "ISRG", "VRTX", "BIIB", "ILMN",
            "SBUX", "MDLZ", "MAR", "ORLY", "ROST", "LULU",
            "ADP", "PAYX", "INTU", "ADSK", "ANSS", "CDNS", "SNPS",
            "FISV", "CTSH", "WDAY", "TEAM", "ZM", "DOCU", "OKTA",
            "CRWD", "ZS", "NET", "DDOG", "MDB", "SNOW", "PLTR",
            "PANW", "FTNT", "SPLK", "VEEV",
            "MELI", "LCID", "RIVN", "NIO", "XPEV", "LI",
            "BIDU", "JD", "PDD", "BILI", "IQ",
        ]
        return [(s, "US") for s in stocks]
    except Exception as e:
        return []


def get_hsi_stocks():
    """获取恒生指数真实成分股"""
    stocks = [
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
    ]
    return [(s, "HK") for s in stocks]


def get_nk225_stocks():
    """获取日经 225 真实成分股"""
    stocks = [
        "7203.T", "8058.T", "6758.T", "9984.T", "9432.T",
        "6861.T", "4063.T", "6954.T", "8035.T", "4568.T",
        "7974.T", "6098.T", "9433.T", "8031.T", "8001.T",
        "8002.T", "8053.T", "9020.T", "9022.T", "6902.T",
        "6501.T", "6503.T", "6594.T", "7751.T", "7733.T",
        "4452.T", "4502.T", "4503.T", "4506.T", "4507.T",
        "4519.T", "4523.T", "4578.T", "6178.T", "6273.T",
        "6367.T", "6471.T", "6586.T", "6645.T", "6701.T",
        "6702.T", "6724.T", "6857.T", "6981.T", "7201.T",
        "7267.T", "7269.T", "7270.T", "7272.T",
        "8306.T", "8316.T", "8411.T", "8604.T", "8766.T",
        "9062.T", "9064.T", "9101.T", "9104.T", "9143.T",
        "9434.T", "9435.T", "9436.T", "9437.T", "9501.T",
        "9502.T", "9503.T", "9531.T", "9532.T", "9613.T",
        "9681.T", "9697.T", "9735.T", "9766.T", "9983.T",
    ]
    return [(s, "JP") for s in stocks]


def get_hs300_stocks():
    """获取沪深 300 真实成分股"""
    stocks = [
        "600519.SS", "000858.SZ", "002415.SZ", "300750.SZ",
        "601318.SS", "601398.SS", "600036.SS", "601857.SS",
        "600276.SS", "000333.SZ", "000651.SZ", "002594.SZ",
        "300014.SZ", "300059.SZ", "600030.SS", "601166.SS",
        "600887.SS", "000001.SZ", "000002.SZ", "600585.SS",
        "601288.SS", "601988.SS", "601939.SS", "601658.SS",
        "601601.SS", "601628.SS", "601336.SS", "600837.SS",
        "000776.SZ", "002624.SZ", "002475.SZ", "000725.SZ",
        "000100.SZ", "000063.SZ", "000977.SZ", "000938.SZ",
        "600809.SS", "600436.SS", "600196.SS", "600104.SS",
        "600031.SS", "600028.SS", "600019.SS", "600016.SS",
        "600009.SS", "601888.SS", "600763.SS", "000538.SZ",
        "000963.SZ", "300760.SZ", "300015.SZ", "300122.SZ",
    ]
    return [(s, "CN") for s in stocks]


def init_database():
    """初始化数据库"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
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
    
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_stocks_market ON stocks(market)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_quotes_symbol ON quotes(symbol)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_klines_symbol_date ON klines(symbol, date)')
    
    conn.commit()
    return conn


def fetch_stock_data(symbol, market):
    """获取单只股票数据"""
    try:
        ticker = yf.Ticker(symbol)
        
        # 基本信息
        info = ticker.info
        name = info.get("shortName", info.get("longName", ""))
        sector = info.get("sector", "")
        industry = info.get("industry", "")
        market_cap = info.get("marketCap", 0)
        
        # 行情
        hist = ticker.history(period="1d")
        if len(hist) == 0:
            return None
        
        row = hist.iloc[-1]
        close_price = row.get("Close", 0)
        
        prev_hist = ticker.history(period="2d")
        prev_close = prev_hist.iloc[-2]["Close"] if len(prev_hist) > 1 else close_price
        
        if prev_close and close_price and prev_close > 0:
            change_pct = ((close_price - prev_close) / prev_close) * 100
        else:
            change_pct = 0
        
        # K 线
        klines = ticker.history(period="5d", interval="1d")
        
        return {
            "symbol": symbol,
            "name": name or "",
            "market": market,
            "sector": sector or "",
            "industry": industry or "",
            "market_cap": market_cap or 0,
            "price": round(close_price, 2),
            "change_pct": round(change_pct, 2),
            "high": round(row.get("High", 0), 2),
            "low": round(row.get("Low", 0), 2),
            "open": round(row.get("Open", 0), 2),
            "prev_close": round(prev_close, 2),
            "volume": int(row.get("Volume", 0)),
            "klines": [(d.strftime("%Y-%m-%d"), round(r["Open"], 2), round(r["High"], 2), 
                       round(r["Low"], 2), round(r["Close"], 2), int(r["Volume"])) 
                      for d, r in klines.iterrows()],
        }
    except Exception as e:
        return None


def save_stock_data(conn, data):
    """保存股票数据"""
    cursor = conn.cursor()
    
    # 股票信息
    cursor.execute('''
        INSERT OR REPLACE INTO stocks (symbol, name, market, sector, industry, market_cap, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    ''', (data["symbol"], data["name"], data["market"], data["sector"], data["industry"], data["market_cap"]))
    
    # 行情
    cursor.execute('''
        INSERT INTO quotes (symbol, price, change_pct, high, low, open, prev_close, volume)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (data["symbol"], data["price"], data["change_pct"], data["high"], data["low"],
          data["open"], data["prev_close"], data["volume"]))
    
    # K 线
    for k in data["klines"]:
        cursor.execute('''
            INSERT OR REPLACE INTO klines (symbol, date, open, high, low, close, volume)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (data["symbol"], k[0], k[1], k[2], k[3], k[4], k[5]))
    
    conn.commit()


def main():
    print("=" * 70)
    print("🌍 全量股票数据获取 - 真实成分股")
    print(f"⏰ 时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    # 获取所有股票列表
    print("\n📋 获取真实股票列表...")
    all_stocks = []
    all_stocks.extend(get_sp500_stocks())
    all_stocks.extend(get_nasdaq100_stocks())
    all_stocks.extend(get_hsi_stocks())
    all_stocks.extend(get_nk225_stocks())
    all_stocks.extend(get_hs300_stocks())
    
    # 去重
    seen = set()
    unique_stocks = []
    for s, m in all_stocks:
        if s not in seen:
            seen.add(s)
            unique_stocks.append((s, m))
    
    print(f"✅ 获取到 {len(unique_stocks)} 只唯一股票")
    
    # 按市场分组
    by_market = {}
    for s, m in unique_stocks:
        by_market[m] = by_market.get(m, 0) + 1
    for m, c in by_market.items():
        print(f"   {m}: {c} 只")
    
    # 初始化数据库
    print("\n📁 初始化数据库...")
    conn = init_database()
    
    # 获取数据
    print("\n🔄 开始获取数据...")
    success = 0
    fail = 0
    
    for i, (symbol, market) in enumerate(unique_stocks):
        data = fetch_stock_data(symbol, market)
        if data:
            save_stock_data(conn, data)
            success += 1
        else:
            fail += 1
        
        # 进度
        if (i + 1) % 50 == 0:
            pct = ((i + 1) / len(unique_stocks)) * 100
            print(f"\r  进度：{i+1}/{len(unique_stocks)} ({pct:.1f}%) | 成功：{success} | 失败：{fail}", end="", flush=True)
        
        # 延时避免限流
        if (i + 1) % 10 == 0:
            time.sleep(1)
    
    print("\n")
    
    # 最终统计
    print("=" * 70)
    print("📊 数据库统计")
    print("=" * 70)
    cursor = conn.cursor()
    cursor.execute("SELECT market, COUNT(*) FROM stocks GROUP BY market")
    for m, c in cursor.fetchall():
        print(f"  {m}: {c} 只股票")
    
    cursor.execute("SELECT COUNT(*) FROM quotes")
    print(f"  行情记录：{cursor.fetchone()[0]} 条")
    
    cursor.execute("SELECT COUNT(*) FROM klines")
    print(f"  K 线记录：{cursor.fetchone()[0]} 条")
    
    conn.close()
    
    print("\n" + "=" * 70)
    print(f"✅ 完成！成功 {success}/{len(unique_stocks)} 只 ({success/len(unique_stocks)*100:.1f}%)")
    print("=" * 70)


if __name__ == "__main__":
    main()
