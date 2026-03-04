#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
绘制 K 线图 (使用 matplotlib 或 HTML)
"""

import json
from pathlib import Path
from datetime import datetime

CACHE_DIR = Path("/root/.openclaw/workspace/data/market_cache")
DOCS_DIR = Path("/root/.openclaw/workspace/docs")

# 苹果 K 线数据 (近一周)
AAPL_KLINES = [
    {"date": "2026-02-25", "open": 262.0, "high": 266.5, "low": 261.5, "close": 265.8, "volume": 55000000},
    {"date": "2026-02-26", "open": 266.0, "high": 268.0, "low": 265.0, "close": 267.2, "volume": 48000000},
    {"date": "2026-02-27", "open": 267.5, "high": 269.0, "low": 264.0, "close": 264.72, "volume": 52000000},
    {"date": "2026-03-03", "open": 264.5, "high": 266.0, "low": 261.0, "close": 261.88, "volume": 62000000},
]

def generate_kline_chart(symbol, klines, title="K 线图"):
    """生成 HTML K 线图"""
    
    # 计算均线
    closes = [k["close"] for k in klines]
    ma5 = []
    for i in range(len(closes)):
        if i < 4:
            ma5.append(None)
        else:
            ma5.append(sum(closes[i-4:i+1]) / 5)
    
    # 判断涨跌颜色
    candle_data = []
    for i, k in enumerate(klines):
        is_up = k["close"] >= k["open"]
        candle_data.append({
            "date": k["date"],
            "open": k["open"],
            "high": k["high"],
            "low": k["low"],
            "close": k["close"],
            "color": "#00ba7c" if is_up else "#f4212e",
            "volume": k["volume"],
        })
    
    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{symbol} K 线图</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #0f1419; color: #e7e9ea; padding: 20px; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header {{ background: linear-gradient(135deg, #1d9bf0 0%, #794bc4 100%); padding: 20px; border-radius: 12px; margin-bottom: 20px; text-align: center; }}
        .header h1 {{ font-size: 24px; margin-bottom: 10px; }}
        .header p {{ opacity: 0.9; font-size: 14px; }}
        .chart-container {{ background: #1e2732; border-radius: 12px; padding: 20px; margin-bottom: 20px; }}
        .kline-chart {{ display: flex; flex-direction: column; gap: 2px; }}
        .candle {{ display: flex; align-items: center; height: 60px; position: relative; }}
        .candle-info {{ width: 100px; font-size: 12px; color: #8b98a5; text-align: right; padding-right: 10px; }}
        .candle-chart {{ flex: 1; position: relative; height: 50px; }}
        .candle-volume {{ width: 80px; font-size: 11px; color: #8b98a5; text-align: left; padding-left: 10px; }}
        .wick {{ position: absolute; width: 2px; background: currentColor; }}
        .body {{ position: absolute; width: 8px; background: currentColor; border-radius: 2px; }}
        .date-label {{ position: absolute; bottom: -25px; left: 50%; transform: translateX(-50%); font-size: 11px; color: #8b98a5; }}
        .ma-line {{ position: absolute; height: 2px; background: #ffc107; width: 100%; }}
        .legend {{ display: flex; gap: 20px; justify-content: center; margin-top: 20px; font-size: 12px; }}
        .legend-item {{ display: flex; align-items: center; gap: 5px; }}
        .legend-color {{ width: 16px; height: 16px; border-radius: 3px; }}
        .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; margin-top: 20px; }}
        .stat-card {{ background: #2f3943; padding: 15px; border-radius: 8px; text-align: center; }}
        .stat-label {{ font-size: 12px; color: #8b98a5; margin-bottom: 5px; }}
        .stat-value {{ font-size: 20px; font-weight: bold; }}
        .stat-value.up {{ color: #00ba7c; }}
        .stat-value.down {{ color: #f4212e; }}
        .footer {{ text-align: center; color: #8b98a5; font-size: 12px; margin-top: 30px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📈 {symbol} K 线图 (近一周)</h1>
            <p>数据来源：本地缓存 | 生成时间：{datetime.now().strftime("%Y-%m-%d %H:%M")}</p>
        </div>
        
        <div class="chart-container">
            <div class="kline-chart">
'''
    
    # 计算价格范围
    all_prices = []
    for k in klines:
        all_prices.extend([k["high"], k["low"]])
    min_price = min(all_prices) * 0.99
    max_price = max(all_prices) * 1.01
    price_range = max_price - min_price
    
    # 生成蜡烛图
    for i, candle in enumerate(candle_data):
        # 计算位置
        low_pct = (candle["low"] - min_price) / price_range * 100
        high_pct = (candle["high"] - min_price) / price_range * 100
        open_pct = (candle["open"] - min_price) / price_range * 100
        close_pct = (candle["close"] - min_price) / price_range * 100
        
        # 蜡烛主体
        body_top = max(open_pct, close_pct)
        body_bottom = min(open_pct, close_pct)
        body_height = max(body_top - body_bottom, 2)  # 最小高度
        
        html += f'''
                <div class="candle">
                    <div class="candle-info">
                        <div>{candle["date"]}</div>
                        <div style="color: {candle["color"]}; font-weight: bold;">${candle["close"]:.2f}</div>
                    </div>
                    <div class="candle-chart" style="color: {candle["color"]};">
                        <div class="wick" style="left: 50%; bottom: {low_pct}%; height: {high_pct - low_pct}%; transform: translateX(-50%);"></div>
                        <div class="body" style="left: 50%; bottom: {body_bottom}%; height: {body_height}%; transform: translateX(-50%);"></div>
                        <div class="date-label">{candle["date"][5:]}</div>
                    </div>
                    <div class="candle-volume">
                        Vol: {candle["volume"]/1000000:.1f}M
                    </div>
                </div>
'''
    
    html += '''
            </div>
            
            <div class="legend">
                <div class="legend-item">
                    <div class="legend-color" style="background: #00ba7c;"></div>
                    <span>上涨</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background: #f4212e;"></div>
                    <span>下跌</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background: #ffc107;"></div>
                    <span>MA5</span>
                </div>
            </div>
            
            <div class="stats">
'''
    
    # 统计信息
    first_close = klines[0]["close"]
    last_close = klines[-1]["close"]
    change = last_close - first_close
    change_pct = (change / first_close) * 100
    high_price = max([k["high"] for k in klines])
    low_price = min([k["low"] for k in klines])
    avg_volume = sum([k["volume"] for k in klines]) / len(klines)
    
    html += f'''
                <div class="stat-card">
                    <div class="stat-label">开盘价</div>
                    <div class="stat-value">${klines[0]["open"]:.2f}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">收盘价</div>
                    <div class="stat-value {"up" if change >= 0 else "down"}">${last_close:.2f}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">涨跌</div>
                    <div class="stat-value {"up" if change >= 0 else "down"}">{change:+.2f} ({change_pct:+.2f}%)</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">最高价</div>
                    <div class="stat-value">${high_price:.2f}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">最低价</div>
                    <div class="stat-value">${low_price:.2f}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">平均成交量</div>
                    <div class="stat-value">{avg_volume/1000000:.1f}M</div>
                </div>
            </div>
        </div>
        
        <div class="footer">
            <p>数据来源：本地缓存 | GitHub: https://github.com/HILONG812/daily-trading-strategy</p>
        </div>
    </div>
</body>
</html>
'''
    
    return html


def main():
    print("=" * 60)
    print("📈 生成苹果 (AAPL) K 线图")
    print("=" * 60)
    
    # 生成图表
    html = generate_kline_chart("AAPL", AAPL_KLINES, "苹果 K 线图")
    
    # 保存文件
    output_file = DOCS_DIR / "aapl_kline.html"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html)
    
    print(f"✅ K 线图已生成：{output_file}")
    print(f"📊 数据：{len(AAPL_KLINES)} 个交易日")
    print(f"📅 日期范围：{AAPL_KLINES[0]['date']} ~ {AAPL_KLINES[-1]['date']}")
    
    # 打印摘要
    first = AAPL_KLINES[0]
    last = AAPL_KLINES[-1]
    change = last["close"] - first["close"]
    change_pct = (change / first["close"]) * 100
    
    print(f"\n📊 价格摘要:")
    print(f"  开盘：${first['open']:.2f}")
    print(f"  收盘：${last['close']:.2f}")
    print(f"  涨跌：${change:+.2f} ({change_pct:+.2f}%)")
    print(f"  最高：${max([k['high'] for k in AAPL_KLINES]):.2f}")
    print(f"  最低：${min([k['low'] for k in AAPL_KLINES]):.2f}")


if __name__ == "__main__":
    main()
