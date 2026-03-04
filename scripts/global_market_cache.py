#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全球股市数据缓存系统
覆盖：美股、港股、日股、A 股
数据源：东方财富 API、yfinance、AKShare
"""

import json
import os
import time
import requests
from datetime import datetime
from pathlib import Path

# 缓存目录
CACHE_DIR = Path("/root/.openclaw/workspace/data/market_cache")
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# 持仓股票池
PORTFOLIO = {
    "US": [
        {"symbol": "NVDA", "name": "英伟达"},
        {"symbol": "AAPL", "name": "苹果"},
        {"symbol": "TSLA", "name": "特斯拉"},
        {"symbol": "ASML", "name": "ASML"},
        {"symbol": "SIL", "name": "白银 ETF"},
    ],
    "HK": [
        {"symbol": "0700", "name": "腾讯控股"},
        {"symbol": "9988", "name": "阿里巴巴"},
        {"symbol": "9863", "name": "零跑汽车"},
        {"symbol": "2402", "name": "亿华通"},
    ],
    "JP": [
        {"symbol": "7203.T", "name": "丰田"},
        {"symbol": "8058.T", "name": "三菱商事"},
    ],
    "CN": [
        {"symbol": "688339", "name": "亿华通-U"},
        {"symbol": "000660", "name": "SK 海力士"},
    ],
}

# 主要指数
INDICES = {
    "US": ["^GSPC", "^IXIC", "^DJI"],  # 标普、纳指、道指
    "HK": ["^HSI", "^HSTECH"],  # 恒指、恒生科技
    "JP": ["^N225"],  # 日经 225
    "CN": ["000001.SS", "399001.SZ"],  # 上证、深证
}


def fetch_cn_stock(symbol):
    """获取 A 股数据 (东方财富 API)"""
    try:
        secid = f"1.{symbol}" if symbol.startswith("6") else f"0.{symbol}"
        url = f"https://push2.eastmoney.com/api/qt/stock/get"
        params = {
            "secid": secid,
            "fields": "f43,f44,f45,f46,f47,f48,f55,f57,f58,f173,f184,f185"
        }
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()
        if data.get("data"):
            d = data["data"]
            last_close = d.get("f46", 0) / 100
            change_pct = d.get("f55", 0)
            current = last_close * (1 + change_pct / 100) if last_close else 0
            return {
                "symbol": d.get("f57", symbol),
                "name": d.get("f58", ""),
                "price": round(current, 2),
                "change_pct": round(change_pct, 2),
                "high": d.get("f43", 0) / 100,
                "low": d.get("f44", 0) / 100,
                "open": d.get("f45", 0) / 100,
                "prev_close": last_close,
                "volume": d.get("f47", 0),
                "turnover": d.get("f48", 0) / 10000,
                "pe": d.get("f173"),
                "pb": d.get("f184"),
                "ps": d.get("f185"),
                "timestamp": datetime.now().isoformat(),
            }
    except Exception as e:
        print(f"  ❌ {symbol}: {e}")
    return None


def fetch_hk_stock(symbol):
    """获取港股数据 (东方财富 API)"""
    try:
        url = f"https://push2.eastmoney.com/api/qt/stock/get"
        params = {
            "secid": f"116.{symbol}",
            "fields": "f43,f44,f45,f46,f47,f48,f55,f57,f58,f173,f184"
        }
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()
        if data.get("data"):
            d = data["data"]
            last_close = d.get("f46", 0) / 1000
            change_pct = d.get("f55", 0)
            current = last_close * (1 + change_pct / 100) if last_close else 0
            return {
                "symbol": symbol,
                "name": d.get("f58", ""),
                "price": round(current, 2),
                "change_pct": round(change_pct, 2),
                "high": d.get("f43", 0) / 1000,
                "low": d.get("f44", 0) / 1000,
                "open": d.get("f45", 0) / 1000,
                "prev_close": last_close,
                "volume": d.get("f47", 0),
                "turnover": d.get("f48", 0) / 10000,
                "pe": d.get("f173"),
                "pb": d.get("f184"),
                "timestamp": datetime.now().isoformat(),
            }
    except Exception as e:
        print(f"  ❌ {symbol}: {e}")
    return None


def fetch_us_stock(symbol):
    """获取美股数据 (yfinance)"""
    import yfinance as yf
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        hist = ticker.history(period="1d")
        if len(hist) > 0:
            current = hist["Close"].iloc[-1]
            prev_close = hist["Close"].iloc[-2] if len(hist) > 1 else current
            change = ((current - prev_close) / prev_close) * 100
            return {
                "symbol": symbol,
                "name": info.get("shortName", info.get("longName", "")),
                "price": round(current, 2),
                "change_pct": round(change, 2),
                "high": round(hist["High"].iloc[-1], 2),
                "low": round(hist["Low"].iloc[-1], 2),
                "open": round(hist["Open"].iloc[-1], 2),
                "prev_close": round(prev_close, 2),
                "volume": int(hist["Volume"].iloc[-1]),
                "market_cap": info.get("marketCap"),
                "pe": info.get("trailingPE"),
                "pb": info.get("priceToBook"),
                "timestamp": datetime.now().isoformat(),
            }
    except Exception as e:
        print(f"  ❌ {symbol}: {e}")
    return None


def fetch_jp_stock(symbol):
    """获取日股数据 (yfinance)"""
    import yfinance as yf
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="1d")
        info = ticker.info
        if len(hist) > 0:
            current = hist["Close"].iloc[-1]
            prev_close = hist["Close"].iloc[-2] if len(hist) > 1 else current
            change = ((current - prev_close) / prev_close) * 100
            return {
                "symbol": symbol,
                "name": info.get("shortName", info.get("longName", "")),
                "price": round(current, 2),
                "change_pct": round(change, 2),
                "high": round(hist["High"].iloc[-1], 2),
                "low": round(hist["Low"].iloc[-1], 2),
                "open": round(hist["Open"].iloc[-1], 2),
                "prev_close": round(prev_close, 2),
                "volume": int(hist["Volume"].iloc[-1]),
                "timestamp": datetime.now().isoformat(),
            }
    except Exception as e:
        print(f"  ❌ {symbol}: {e}")
    return None


def fetch_index_data(market, symbol):
    """获取指数数据"""
    import yfinance as yf
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="1d")
        if len(hist) > 0:
            current = hist["Close"].iloc[-1]
            prev_close = hist["Close"].iloc[-2] if len(hist) > 1 else current
            change = ((current - prev_close) / prev_close) * 100
            return {
                "symbol": symbol,
                "price": round(current, 2),
                "change_pct": round(change, 2),
                "timestamp": datetime.now().isoformat(),
            }
    except Exception as e:
        print(f"  ❌ {symbol}: {e}")
    return None


def fetch_kline_data(symbol, market, period="6mo"):
    """获取 K 线历史数据"""
    import yfinance as yf
    try:
        if market == "CN":
            # A 股使用 AKShare
            import akshare as ak
            secid = symbol
            df = ak.stock_zh_a_hist(symbol=secid, period="daily", adjust="qfq")
            if len(df) > 0:
                klines = []
                for _, row in df.tail(100).iterrows():
                    klines.append({
                        "date": str(row.get("日期", "")),
                        "open": float(row.get("开盘", 0)),
                        "high": float(row.get("最高", 0)),
                        "low": float(row.get("最低", 0)),
                        "close": float(row.get("收盘", 0)),
                        "volume": int(row.get("成交量", 0)),
                    })
                return {"symbol": symbol, "klines": klines}
        else:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period)
            if len(hist) > 0:
                klines = []
                for date, row in hist.tail(100).iterrows():
                    klines.append({
                        "date": str(date.date()),
                        "open": round(row["Open"], 2),
                        "high": round(row["High"], 2),
                        "low": round(row["Low"], 2),
                        "close": round(row["Close"], 2),
                        "volume": int(row["Volume"]),
                    })
                return {"symbol": symbol, "klines": klines}
    except Exception as e:
        print(f"  ❌ {symbol} K 线：{e}")
    return None


def calculate_rsi(prices, period=14):
    """计算 RSI"""
    if len(prices) < period + 1:
        return None
    delta = [prices[i] - prices[i-1] for i in range(1, len(prices))]
    gains = [d if d > 0 else 0 for d in delta]
    losses = [-d if d < 0 else 0 for d in delta]
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    if avg_loss == 0:
        return 100
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return round(rsi, 2)


def calculate_ma(prices, period):
    """计算移动平均线"""
    if len(prices) < period:
        return None
    return round(sum(prices[-period:]) / period, 2)


def main():
    print("=" * 60)
    print("🌍 全球股市数据缓存系统")
    print(f"📅 时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    cache = {
        "timestamp": datetime.now().isoformat(),
        "markets": {},
        "portfolio": {},
        "indices": {},
    }
    
    # 1. 获取 A 股数据
    print("\n🇨🇳 获取 A 股数据...")
    cn_stocks = {}
    for stock in PORTFOLIO["CN"]:
        print(f"  📈 {stock['symbol']} {stock['name']}")
        data = fetch_cn_stock(stock["symbol"])
        if data:
            cn_stocks[stock["symbol"]] = data
        time.sleep(0.5)
    cache["markets"]["CN"] = cn_stocks
    
    # 2. 获取港股数据
    print("\n🇭🇰 获取港股数据...")
    hk_stocks = {}
    for stock in PORTFOLIO["HK"]:
        print(f"  📈 {stock['symbol']} {stock['name']}")
        data = fetch_hk_stock(stock["symbol"])
        if data:
            hk_stocks[stock["symbol"]] = data
        time.sleep(0.5)
    cache["markets"]["HK"] = hk_stocks
    
    # 3. 获取美股数据
    print("\n🇺🇸 获取美股数据...")
    us_stocks = {}
    for stock in PORTFOLIO["US"]:
        print(f"  📈 {stock['symbol']} {stock['name']}")
        data = fetch_us_stock(stock["symbol"])
        if data:
            us_stocks[stock["symbol"]] = data
        time.sleep(1)  # 避免 yfinance 限流
    cache["markets"]["US"] = us_stocks
    
    # 4. 获取日股数据
    print("\n🇯🇵 获取日股数据...")
    jp_stocks = {}
    for stock in PORTFOLIO["JP"]:
        print(f"  📈 {stock['symbol']} {stock['name']}")
        data = fetch_jp_stock(stock["symbol"])
        if data:
            jp_stocks[stock["symbol"]] = data
        time.sleep(1)
    cache["markets"]["JP"] = jp_stocks
    
    # 5. 获取指数数据
    print("\n📊 获取指数数据...")
    for market, symbols in INDICES.items():
        print(f"  {market}:")
        for symbol in symbols:
            print(f"    📊 {symbol}")
            data = fetch_index_data(market, symbol)
            if data:
                cache["indices"][symbol] = data
            time.sleep(0.5)
    
    # 6. 计算技术指标
    print("\n📐 计算技术指标...")
    for market, stocks in cache["markets"].items():
        for symbol, data in stocks.items():
            if data and "price" in data:
                # 简单 RSI 估算 (基于近期涨跌幅)
                change = data.get("change_pct", 0)
                if change < -5:
                    rsi = 20 + change  # 大跌 RSI 低
                elif change > 5:
                    rsi = 80 + change  # 大涨 RSI 高
                else:
                    rsi = 50 + change * 2
                data["rsi_estimate"] = round(rsi, 2)
    
    # 7. 保存到文件
    output_file = CACHE_DIR / f"market_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)
    
    # 更新 latest.json
    latest_file = CACHE_DIR / "latest.json"
    with open(latest_file, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)
    
    # 8. 获取 K 线历史数据
    print("\n📉 获取 K 线历史数据...")
    kline_cache = {"timestamp": datetime.now().isoformat(), "klines": {}}
    
    for market, stocks in cache["markets"].items():
        for symbol, data in stocks.items():
            print(f"  📉 {market} {symbol}")
            if market == "CN":
                kline_data = fetch_kline_data(symbol, "CN")
            else:
                full_symbol = symbol
                if market == "HK":
                    full_symbol = f"{symbol}.HK"
                elif market == "JP":
                    full_symbol = symbol  # 已经是 .T 结尾
                kline_data = fetch_kline_data(full_symbol, market)
            
            if kline_data:
                kline_cache["klines"][f"{market}_{symbol}"] = kline_data
            time.sleep(0.5)
    
    kline_file = CACHE_DIR / f"kline_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(kline_file, "w", encoding="utf-8") as f:
        json.dump(kline_cache, f, ensure_ascii=False, indent=2)
    
    # 更新 kline_latest.json
    kline_latest = CACHE_DIR / "kline_latest.json"
    with open(kline_latest, "w", encoding="utf-8") as f:
        json.dump(kline_cache, f, ensure_ascii=False, indent=2)
    
    print("\n" + "=" * 60)
    print("✅ 数据缓存完成!")
    print(f"📁 实时数据：{output_file}")
    print(f"📁 K 线数据：{kline_file}")
    print(f"📁 Latest: {CACHE_DIR / 'latest.json'}")
    print("=" * 60)
    
    # 打印摘要
    print("\n📊 数据摘要:")
    for market, stocks in cache["markets"].items():
        print(f"\n  {market}:")
        for symbol, data in stocks.items():
            if data:
                price = data.get("price", "N/A")
                change = data.get("change_pct", "N/A")
                rsi = data.get("rsi_estimate", "N/A")
                print(f"    {symbol}: ¥{price} ({change}%) RSI≈{rsi}")


if __name__ == "__main__":
    main()
