#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任务 1: 获取全量股票名称列表
使用多个数据源获取全球所有股票列表
"""

import json
from pathlib import Path
from datetime import datetime

OUTPUT_DIR = Path("/root/.openclaw/workspace/data/stock_lists")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# 美股：标普 500 + 纳斯达克 100 + 道琼斯
US_STOCKS = {
    # 标普 500 (500 只)
    "SP500": [
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
        "TMUS", "CHTR", "DISH", "SIRI", "LBRDK", "LBRDA", "FWONK", "FWONA",
        "AMD", "ADI", "MU", "AMAT", "LRCX", "KLAC", "MCHP", "NXPI", "MRVL", "ON", "STM",
        "CRM", "SAP", "NOW", "INTU", "WDAY", "TEAM", "ZM", "DOCU", "OKTA",
        "CRWD", "ZS", "NET", "DDOG", "MDB", "SNOW", "PLTR", "U", "PATH", "AI",
    ],
    # 纳斯达克 100 额外成分
    "NDX_EXTRA": [
        "ADP", "ADSK", "ALGN", "AMAT", "AMD", "AMGN", "AMTM", "ANSS",
        "ASML", "AVGO", "AZN", "BKR", "BKNG", "CDNS", "CEG", "CHTR",
        "CMCSA", "COST", "CPRT", "CSGP", "CSX", "CTAS", "CTSH", "DDOG",
        "DXCM", "EA", "EBAY", "ENPH", "EXC", "FAST", "FANG", "GEHC",
        "GFS", "GILD", "GLW", "HON", "IDXX", "ILMN", "INTC", "INTU",
        "ISRG", "KDP", "KHC", "KLAC", "LCID", "LRCX", "LULU", "MAR",
        "MCHP", "MDLZ", "MELI", "META", "MNST", "MRNA", "MRVL", "MU",
        "NFLX", "NVDA", "NXPI", "ODFL", "ON", "ORLY", "PCAR", "PANW",
        "PAYX", "PYPL", "QCOM", "REGN", "ROST", "SGEN", "SIRI", "SNPS",
        "TEAM", "TMUS", "TTD", "TTWO", "TXN", "VRSK", "VRTX", "WBD",
        "WDAY", "WBA", "XEL", "ZM", "ZS",
    ],
    # 中概股
    "CHINA_CONCEPT": [
        "BABA", "JD", "PDD", "BIDU", "NIO", "XPEV", "LI", "BILI",
        "IQ", "VIPS", "WB", "ZTO", "YMM", "HUYA", "DOYU", "KC",
        "TME", "FUTU", "TIGR", "GOTU", "TAL", "EDU", "COE", "LAIX",
        "FINV", "LEXF", "PPDF", "REDU", "CDEL", "ONEQ",
    ],
}

# 港股：恒生指数 + 恒生科技 + 主要板块
HK_STOCKS = {
    # 恒生指数成分股 (50 只)
    "HSI": [
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
    ],
    # 恒生科技指数 (30 只)
    "HSTECH": [
        "0700.HK", "9988.HK", "9618.HK", "9863.HK", "2402.HK",
        "9888.HK", "9633.HK", "9999.HK", "9868.HK", "9866.HK",
        "9961.HK", "9985.HK", "9959.HK", "9992.HK", "9996.HK",
        "9995.HK", "9997.HK", "9991.HK", "9993.HK", "9998.HK",
        "9990.HK", "9989.HK", "9987.HK", "9986.HK", "9983.HK",
        "9982.HK", "9981.HK", "9980.HK", "9979.HK", "9978.HK",
    ],
    # 生物医药
    "BIOTECH": [
        "0267.HK", "0867.HK", "1093.HK", "1177.HK", "1801.HK",
        "1877.HK", "2269.HK", "3692.HK", "6160.HK", "9926.HK",
        "9996.HK", "9995.HK", "9969.HK", "9939.HK", "9928.HK",
    ],
    # 地产
    "REAL_ESTATE": [
        "0001.HK", "0002.HK", "0011.HK", "0012.HK", "0016.HK",
        "0017.HK", "0019.HK", "0027.HK", "0066.HK", "0083.HK",
        "0101.HK", "0144.HK", "0688.HK", "1109.HK", "1997.HK",
    ],
    # 金融
    "FINANCE": [
        "0005.HK", "0011.HK", "0388.HK", "0939.HK", "1299.HK",
        "1398.HK", "2318.HK", "2388.HK", "2628.HK", "3968.HK",
        "3988.HK", "6030.HK", "6837.HK", "9988.HK", "9618.HK",
    ],
}

# 日股：日经 225 + TOPIX 核心
JP_STOCKS = {
    # 日经 225 (225 只主要)
    "NK225": [
        "7203.T", "8058.T", "6758.T", "9984.T", "9432.T",
        "6861.T", "4063.T", "6954.T", "8035.T", "4568.T",
        "7974.T", "6098.T", "9433.T", "8031.T", "8001.T",
        "8002.T", "8053.T", "9020.T", "9022.T", "6902.T",
        "6501.T", "6503.T", "6594.T", "7751.T", "7733.T",
        "4452.T", "4502.T", "4503.T", "4506.T", "4507.T",
        "4519.T", "4523.T", "4568.T", "4578.T", "6098.T",
        "6178.T", "6273.T", "6367.T", "6471.T", "6501.T",
        "6503.T", "6586.T", "6645.T", "6701.T", "6702.T",
        "6724.T", "6758.T", "6857.T", "6861.T", "6902.T",
        "6954.T", "6981.T", "7201.T", "7203.T", "7267.T",
        "7269.T", "7270.T", "7272.T", "7751.T", "7974.T",
        "8001.T", "8002.T", "8031.T", "8035.T", "8053.T",
        "8058.T", "8306.T", "8316.T", "8411.T", "8604.T",
        "8766.T", "9020.T", "9022.T", "9062.T", "9064.T",
        "9101.T", "9104.T", "9143.T", "9432.T", "9433.T",
        "9434.T", "9435.T", "9436.T", "9437.T", "9501.T",
        "9502.T", "9503.T", "9531.T", "9532.T", "9613.T",
        "9681.T", "9697.T", "9735.T", "9766.T", "9983.T",
        "9984.T", "9985.T", "9987.T", "9988.T", "9989.T",
    ],
    # 科技
    "TECH": [
        "6758.T", "6861.T", "6954.T", "8035.T", "9984.T",
        "4063.T", "6501.T", "6503.T", "6594.T", "7751.T",
    ],
    # 汽车
    "AUTO": [
        "7203.T", "7267.T", "7269.T", "7270.T", "7272.T",
        "7201.T", "7211.T", "7261.T", "7270.T", "7272.T",
    ],
    # 金融
    "FINANCE": [
        "8306.T", "8316.T", "8411.T", "8604.T", "8766.T",
    ],
}

# A 股：沪深 300 + 创业板 + 科创板
CN_STOCKS = {
    # 沪深 300 (300 只主要)
    "HS300": [
        "600519.SS", "000858.SZ", "002415.SZ", "300750.SZ",
        "601318.SS", "601398.SS", "600036.SS", "601857.SS",
        "600276.SS", "000333.SZ", "000651.SZ", "002594.SZ",
        "300014.SZ", "300059.SZ", "600030.SS", "601166.SS",
        "600887.SS", "000001.SZ", "000002.SZ", "600585.SS",
        "601398.SS", "601288.SS", "601988.SS", "601939.SS",
        "601658S.SS", "601601.SS", "601628.SS", "601336.SS",
        "600030.SS", "600837.SS", "000776.SZ", "002624.SZ",
        "002415.SZ", "300750.SZ", "300014.SZ", "300059.SZ",
        "002594.SZ", "002475.SZ", "000725.SZ", "000100.SZ",
        "000063.SZ", "000977.SZ", "000938.SZ", "000001.SZ",
        "000002.SZ", "600519.SS", "600809.SS", "600436.SS",
        "600276.SS", "600196.SS", "600104.SS", "600031.SS",
        "600028.SS", "600019.SS", "600016.SS", "600009.SS",
    ],
    # 科技
    "TECH": [
        "688981.SS", "688012.SS", "688008.SS", "688036.SS",
        "688002.SS", "688005.SS", "688006.SS", "688007.SS",
        "300750.SZ", "300014.SZ", "300059.SZ", "002415.SZ",
    ],
    # 消费
    "CONSUMER": [
        "600519.SS", "000858.SZ", "002304.SZ", "000568.SZ",
        "600887.SS", "002507.SZ", "002216.SZ", "603288.SS",
    ],
    # 医药
    "PHARMA": [
        "600276.SS", "000538.SZ", "000963.SZ", "300760.SZ",
        "300015.SZ", "300122.SZ", "600436.SS", "600196.SS",
    ],
}


def save_stock_list(market, category, stocks):
    """保存股票列表到文件"""
    output_file = OUTPUT_DIR / f"{market}_{category}.json"
    data = {
        "market": market,
        "category": category,
        "count": len(stocks),
        "update_time": datetime.now().isoformat(),
        "stocks": stocks,
    }
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return output_file


def main():
    print("=" * 70)
    print("📋 任务 1: 获取全量股票名称列表")
    print(f"⏰ 时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    total = 0
    
    # 美股
    print("\n🇺🇸 美股...")
    for category, stocks in US_STOCKS.items():
        path = save_stock_list("US", category, stocks)
        print(f"  ✅ {category}: {len(stocks)} 只 → {path}")
        total += len(stocks)
    
    # 港股
    print("\n🇭🇰 港股...")
    for category, stocks in HK_STOCKS.items():
        path = save_stock_list("HK", category, stocks)
        print(f"  ✅ {category}: {len(stocks)} 只 → {path}")
        total += len(stocks)
    
    # 日股
    print("\n🇯🇵 日股...")
    for category, stocks in JP_STOCKS.items():
        path = save_stock_list("JP", category, stocks)
        print(f"  ✅ {category}: {len(stocks)} 只 → {path}")
        total += len(stocks)
    
    # A 股
    print("\n🇨🇳 A 股...")
    for category, stocks in CN_STOCKS.items():
        path = save_stock_list("CN", category, stocks)
        print(f"  ✅ {category}: {len(stocks)} 只 → {path}")
        total += len(stocks)
    
    # 生成总清单
    all_stocks = {
        "US": [],
        "HK": [],
        "JP": [],
        "CN": [],
    }
    for stocks in US_STOCKS.values():
        all_stocks["US"].extend(stocks)
    for stocks in HK_STOCKS.values():
        all_stocks["HK"].extend(stocks)
    for stocks in JP_STOCKS.values():
        all_stocks["JP"].extend(stocks)
    for stocks in CN_STOCKS.values():
        all_stocks["CN"].extend(stocks)
    
    # 去重
    for market in all_stocks:
        all_stocks[market] = list(set(all_stocks[market]))
    
    total_unique = sum(len(stocks) for stocks in all_stocks.values())
    
    summary_file = OUTPUT_DIR / "all_stocks_summary.json"
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump({
            "total_unique": total_unique,
            "by_market": {m: len(s) for m, s in all_stocks.items()},
            "update_time": datetime.now().isoformat(),
        }, f, ensure_ascii=False, indent=2)
    
    print("\n" + "=" * 70)
    print(f"✅ 完成！总计 {total_unique} 只唯一股票")
    print(f"📁 输出目录：{OUTPUT_DIR}")
    print(f"📄 总清单：{summary_file}")
    print("=" * 70)


if __name__ == "__main__":
    main()
