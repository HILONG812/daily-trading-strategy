#!/usr/bin/env python3
"""
股票数据获取脚本
功能：从 Yahoo Finance 获取实时股价，更新 trades.json
"""

import json
import yfinance as yf
from datetime import datetime
import os

# 配置
WORKSPACE = '/root/.openclaw/workspace'
TRADES_FILE = os.path.join(WORKSPACE, 'trades.json')

# 持仓股票代码
POSITIONS = [
    {'code': 'NVDA', 'name': '英伟达', 'market': '美股', 'currency': 'USD'},
    {'code': 'AAPL', 'name': '苹果', 'market': '美股', 'currency': 'USD'},
    {'code': 'TSLA', 'name': '特斯拉', 'market': '美股', 'currency': 'USD'},
    {'code': '0700.HK', 'name': '腾讯', 'market': '港股', 'currency': 'HKD'},
    {'code': '9988.HK', 'name': '阿里', 'market': '港股', 'currency': 'HKD'},
    {'code': '7203.T', 'name': '丰田', 'market': '日股', 'currency': 'JPY'}
]

# 汇率 (简化，实际应从 API 获取)
EXCHANGE_RATES = {
    'USD': 1.0,
    'HKD': 0.128,
    'JPY': 0.0067
}

def fetch_stock_price(symbol):
    """获取股票实时价格"""
    try:
        ticker = yf.Ticker(symbol)
        # 获取最新价格
        data = ticker.history(period='1d')
        if len(data) > 0:
            current_price = data['Close'].iloc[-1]
            return float(current_price)
        else:
            # 尝试获取 fast_info
            return float(ticker.fast_info['lastPrice'])
    except Exception as e:
        print(f"❌ 获取 {symbol} 价格失败：{e}")
        return None

def calculate_rsi(prices, period=14):
    """计算 RSI 指标"""
    if len(prices) < period + 1:
        return 50  # 默认中性
    
    # 计算价格变化
    deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
    
    # 分离涨跌
    gains = [d if d > 0 else 0 for d in deltas]
    losses = [-d if d < 0 else 0 for d in deltas]
    
    # 计算平均涨跌
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    
    if avg_loss == 0:
        return 100
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    return round(rsi, 2)

def get_historical_prices(symbol, period='1mo'):
    """获取历史价格用于计算技术指标"""
    try:
        ticker = yf.Ticker(symbol)
        data = ticker.history(period=period)
        if len(data) > 0:
            return data['Close'].tolist()
        return []
    except:
        return []

def update_trades_json():
    """更新 trades.json 文件"""
    # 读取现有数据
    if os.path.exists(TRADES_FILE):
        with open(TRADES_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
    else:
        data = {
            'initial': 100000,
            'current': 100000,
            'cash': 11665.0,
            'total_invested': 88335.0,
            'positions': [],
            'trades': [],
            'total_cost': 88335.0
        }
    
    # 更新持仓价格
    updated_positions = []
    total_value = 0
    
    print("\n📊 获取实时股价...")
    for pos in POSITIONS:
        print(f"  正在获取 {pos['code']}...")
        current_price = fetch_stock_price(pos['code'])
        
        if current_price:
            # 查找原有持仓
            existing = next((p for p in data.get('positions', []) if p['code'] == pos['code']), None)
            qty = existing['qty'] if existing else 0
            cost = existing['cost'] if existing else 0
            
            # 计算盈亏
            if pos['currency'] == 'USD':
                value_usd = current_price * qty
            else:
                value_usd = current_price * qty * EXCHANGE_RATES[pos['currency']]
            
            total_value += value_usd
            
            # 获取 RSI
            prices = get_historical_prices(pos['code'])
            rsi = calculate_rsi(prices) if prices else 50
            
            updated_positions.append({
                'market': pos['market'],
                'code': pos['code'],
                'name': pos['name'],
                'price': current_price,
                'qty': qty,
                'cost': cost,
                'currency': pos['currency'],
                'rsi': rsi,
                'value_usd': value_usd
            })
            
            pnl = (current_price - cost) * qty
            pnl_percent = (pnl / (cost * qty)) * 100 if cost * qty > 0 else 0
            print(f"    ✓ {pos['code']}: ${current_price:.2f} | RSI={rsi} | 盈亏：{pnl_percent:+.2f}%")
        else:
            print(f"    ✗ {pos['code']}: 获取失败")
    
    # 更新数据
    data['positions'] = updated_positions
    data['current'] = data['cash'] + total_value
    data['last_update'] = datetime.now().isoformat()
    
    # 写入文件
    with open(TRADES_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 数据已更新：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   当前净值：${data['current']:,.2f}")
    print(f"   总盈亏：${data['current'] - data['initial']:,.2f}")
    
    return data

if __name__ == '__main__':
    update_trades_json()
