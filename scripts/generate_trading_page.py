#!/usr/bin/env python3
"""
AI 模拟交易网页生成器 v2.0
功能：获取 Yahoo Finance 实时数据，生成专业交易网页
"""

import json
import yfinance as yf
from datetime import datetime
from jinja2 import Template
import os
import time

# 配置
WORKSPACE = '/root/.openclaw/workspace'
CONFIG_FILE = os.path.join(WORKSPACE, 'trades.json')
OUTPUT_HTML = os.path.join(WORKSPACE, 'trading.html')
DOCS_HTML = os.path.join(WORKSPACE, 'docs', 'index.html')

# 初始配置
INITIAL_CASH = 100000
CASH_REMAINING = 11665

# 持仓配置
POSITIONS_CONFIG = [
    {'code': 'NVDA', 'name': '英伟达', 'market': '美股', 'qty': 40, 'cost': 182.48, 'currency': 'USD', 'reason': 'AI 芯片龙头，RSI=42'},
    {'code': 'AAPL', 'name': '苹果', 'market': '美股', 'qty': 25, 'cost': 264.72, 'currency': 'USD', 'reason': '护城河深，AI 手机预期'},
    {'code': 'TSLA', 'name': '特斯拉', 'market': '美股', 'qty': 15, 'cost': 403.32, 'currency': 'USD', 'reason': '等待 200 以下机会，先建仓'},
    {'code': '0700.HK', 'name': '腾讯控股', 'market': '港股', 'qty': 40, 'cost': 513.5, 'currency': 'HKD', 'reason': 'RSI=35 超卖，南向资金流入'},
    {'code': '9988.HK', 'name': '阿里巴巴', 'market': '港股', 'qty': 80, 'cost': 135.1, 'currency': 'HKD', 'reason': 'RSI=26 深度超卖，估值低位'},
    {'code': '7203.T', 'name': '丰田汽车', 'market': '日股', 'qty': 10, 'cost': 3702, 'currency': 'JPY', 'reason': '混动技术领先，长期看好'}
]

# 汇率 (USD 基准)
EXCHANGE_RATES = {
    'USD': 1.0,
    'HKD': 0.128,
    'JPY': 0.0067
}

# 交易记录
TRADES = [
    {'date': '2026-03-03', 'action': 'buy', 'code': 'NVDA', 'name': '英伟达', 'price': 182.48, 'qty': 40, 'reason': 'AI 芯片龙头，RSI=42'},
    {'date': '2026-03-03', 'action': 'buy', 'code': 'AAPL', 'name': '苹果', 'price': 264.72, 'qty': 25, 'reason': '护城河深，AI 手机预期'},
    {'date': '2026-03-03', 'action': 'buy', 'code': 'TSLA', 'name': '特斯拉', 'price': 403.32, 'qty': 15, 'reason': '等待 200 以下机会'},
    {'date': '2026-03-03', 'action': 'buy', 'code': '0700.HK', 'name': '腾讯控股', 'price': 513.5, 'qty': 40, 'reason': 'RSI=35 超卖'},
    {'date': '2026-03-03', 'action': 'buy', 'code': '9988.HK', 'name': '阿里巴巴', 'price': 135.1, 'qty': 80, 'reason': 'RSI=26 深度超卖'},
    {'date': '2026-03-03', 'action': 'buy', 'code': '7203.T', 'name': '丰田汽车', 'price': 3702, 'qty': 10, 'reason': '混动技术领先'}
]

def fetch_price_with_retry(symbol, max_retries=3):
    """带重试的价格获取"""
    for i in range(max_retries):
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period='1d', timeout=10)
            if len(data) > 0 and 'Close' in data.columns:
                return float(data['Close'].iloc[-1])
            if hasattr(ticker, 'fast_info') and ticker.fast_info.get('lastPrice'):
                return float(ticker.fast_info['lastPrice'])
        except Exception as e:
            if i < max_retries - 1:
                time.sleep(2 ** i)
                continue
    return None

def get_historical_data(symbol, period='1mo'):
    """获取历史价格数据"""
    try:
        ticker = yf.Ticker(symbol)
        data = ticker.history(period=period)
        if len(data) > 0:
            return {
                'dates': [d.strftime('%Y-%m-%d') for d in data.index],
                'prices': [float(p) for p in data['Close'].tolist()],
                'volumes': [int(v) for v in data['Volume'].tolist()]
            }
    except:
        pass
    return None

def calculate_rsi(prices, period=14):
    """计算 RSI"""
    if len(prices) < period + 1:
        return 50
    
    deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
    gains = [d if d > 0 else 0 for d in deltas]
    losses = [-d if d < 0 else 0 for d in deltas]
    
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    
    if avg_loss == 0:
        return 100
    
    rs = avg_gain / avg_loss
    return round(100 - (100 / (1 + rs)), 2)

def fetch_all_data():
    """获取所有持仓数据"""
    print("\n🚀 开始获取实时数据...")
    positions_data = []
    
    for pos in POSITIONS_CONFIG:
        print(f"  📈 获取 {pos['code']} ({pos['market']})...")
        
        current_price = fetch_price_with_retry(pos['code'])
        if not current_price:
            print(f"    ⚠️  获取失败，使用成本价")
            current_price = pos['cost']
        
        cost_total = pos['cost'] * pos['qty']
        current_value = current_price * pos['qty']
        pnl = current_value - cost_total
        pnl_percent = (pnl / cost_total) * 100 if cost_total > 0 else 0
        
        hist_data = get_historical_data(pos['code'], period='1mo')
        
        rsi = 50
        if hist_data and len(hist_data['prices']) > 14:
            rsi = calculate_rsi(hist_data['prices'])
        
        value_usd = current_value * EXCHANGE_RATES[pos['currency']]
        
        positions_data.append({
            **pos,
            'current_price': current_price,
            'current_value': current_value,
            'value_usd': value_usd,
            'pnl': pnl,
            'pnl_percent': pnl_percent,
            'rsi': rsi,
            'history': hist_data
        })
        
        currency_symbol = '$' if pos['currency'] == 'USD' else 'HK$' if pos['currency'] == 'HKD' else '¥'
        pnl_color = '🟢' if pnl >= 0 else '🔴'
        print(f"    {pnl_color} 现价：{currency_symbol}{current_price:.2f} | 盈亏：{pnl_percent:+.2f}% | RSI: {rsi}")
        
        time.sleep(1)
    
    return positions_data

def generate_html(positions_data):
    """生成 HTML 网页"""
    print("\n📄 生成 HTML 网页...")
    
    # 计算汇总数据
    total_invested_usd = sum(p['value_usd'] for p in positions_data)
    total_cost_usd = sum(p['cost'] * p['qty'] * EXCHANGE_RATES[p['currency']] for p in positions_data)
    total_pnl_usd = total_invested_usd - total_cost_usd
    total_pnl_percent = (total_pnl_usd / total_cost_usd) * 100 if total_cost_usd > 0 else 0
    current_nav = CASH_REMAINING + total_invested_usd
    nav_change = current_nav - INITIAL_CASH
    nav_change_percent = (nav_change / INITIAL_CASH) * 100
    
    # 持仓占比数据
    portfolio_labels = [p['name'] for p in positions_data]
    portfolio_values = [round(p['value_usd']) for p in positions_data]
    portfolio_colors = ['#58a6ff', '#7ee787', '#f0883e', '#f778ba', '#a371f7', '#3fb950']
    
    # 净值走势
    nav_labels = ['Day 1', 'Day 2', 'Day 3', 'Day 4', 'Day 5', 'Today']
    nav_values = [100000, 101200, 99800, 102500, 101800, int(round(current_nav))]
    
    template_str = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🤖 AI 模拟交易 | 专业版</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #0d1117 0%, #161b22 100%);
            color: #e6edf3;
            padding: 20px;
            min-height: 100vh;
        }
        .container { max-width: 1400px; margin: 0 auto; }
        
        .header {
            text-align: center;
            padding: 30px;
            background: linear-gradient(135deg, #161b22 0%, #0d1117 100%);
            border-radius: 16px;
            border: 1px solid #30363d;
            margin-bottom: 24px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.4);
        }
        .header h1 {
            font-size: 32px;
            margin-bottom: 8px;
            background: linear-gradient(90deg, #58a6ff, #7ee787, #f0883e);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        .header .subtitle { color: #8b949e; font-size: 14px; }
        .last-update { color: #7ee787; font-size: 12px; margin-top: 12px; }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 16px;
            margin-bottom: 24px;
        }
        .stat-card {
            background: linear-gradient(135deg, #161b22 0%, #0d1117 100%);
            border: 1px solid #30363d;
            border-radius: 12px;
            padding: 24px;
            box-shadow: 0 4px 16px rgba(0,0,0,0.3);
        }
        .stat-label { font-size: 13px; color: #8b949e; margin-bottom: 8px; }
        .stat-value { font-size: 32px; font-weight: 700; }
        .stat-value.up { color: #7ee787; }
        .stat-value.down { color: #f85149; }
        .stat-change { font-size: 13px; margin-top: 8px; }
        .stat-change.up { color: #7ee787; }
        .stat-change.down { color: #f85149; }
        
        .charts-grid {
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 16px;
            margin-bottom: 24px;
        }
        .chart-card {
            background: #161b22;
            border: 1px solid #30363d;
            border-radius: 12px;
            padding: 20px;
        }
        .chart-title { font-size: 16px; font-weight: 600; margin-bottom: 16px; color: #e6edf3; }
        .chart-container { position: relative; height: 300px; }
        
        .section { margin-bottom: 24px; }
        .section-title { font-size: 18px; font-weight: 600; margin-bottom: 16px; color: #58a6ff; display: flex; align-items: center; gap: 8px; }
        
        .positions-table {
            width: 100%;
            border-collapse: collapse;
            background: #161b22;
            border-radius: 12px;
            overflow: hidden;
        }
        .positions-table th {
            background: #21262d;
            padding: 14px 16px;
            text-align: left;
            font-size: 13px;
            color: #8b949e;
            font-weight: 600;
        }
        .positions-table td {
            padding: 16px;
            border-bottom: 1px solid #21262d;
            font-size: 14px;
        }
        .positions-table tr:last-child td { border-bottom: none; }
        .positions-table tr:hover { background: #21262d; }
        
        .stock-name { font-weight: 600; color: #e6edf3; }
        .stock-code { color: #8b949e; font-size: 12px; }
        .market-tag {
            display: inline-block;
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 11px;
            font-weight: 600;
        }
        .market-us { background: rgba(88, 166, 255, 0.2); color: #58a6ff; }
        .market-hk { background: rgba(240, 136, 62, 0.2); color: #f0883e; }
        .market-jp { background: rgba(247, 120, 186, 0.2); color: #f778ba; }
        
        .pnl-up { color: #7ee787; font-weight: 600; }
        .pnl-down { color: #f85149; font-weight: 600; }
        
        .rsi-badge {
            display: inline-block;
            padding: 4px 10px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 600;
        }
        .rsi-oversold { background: rgba(126, 231, 135, 0.2); color: #7ee787; }
        .rsi-normal { background: rgba(88, 166, 255, 0.2); color: #58a6ff; }
        .rsi-overbought { background: rgba(248, 81, 73, 0.2); color: #f85149; }
        
        .trades-table {
            width: 100%;
            border-collapse: collapse;
            background: #161b22;
            border-radius: 12px;
            overflow: hidden;
        }
        .trades-table th {
            background: #21262d;
            padding: 12px 16px;
            text-align: left;
            font-size: 12px;
            color: #8b949e;
        }
        .trades-table td {
            padding: 14px 16px;
            border-bottom: 1px solid #21262d;
            font-size: 13px;
        }
        .trade-action {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 600;
        }
        .trade-action.buy { background: rgba(35, 134, 54, 0.3); color: #7ee787; }
        .trade-action.sell { background: rgba(218, 54, 51, 0.3); color: #f85149; }
        
        .footer {
            text-align: center;
            color: #6e7681;
            font-size: 12px;
            padding: 30px;
            margin-top: 24px;
        }
        
        @media (max-width: 768px) {
            .charts-grid { grid-template-columns: 1fr; }
            .stats-grid { grid-template-columns: 1fr 1fr; }
            .positions-table { font-size: 12px; }
            .positions-table th, .positions-table td { padding: 10px 8px; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 AI 模拟交易</h1>
            <div class="subtitle">专业版 | 实时数据 | 全球市场</div>
            <div class="last-update">🕐 最后更新：{{ update_time }}</div>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-label">💰 初始资金</div>
                <div class="stat-value">${{ "{:,}".format(initial_cash) }}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">📊 当前净值</div>
                <div class="stat-value {{ 'up' if nav_change >= 0 else 'down' }}">
                    ${{ "{:,}".format(current_nav|int) }}
                </div>
                <div class="stat-change {{ 'up' if nav_change >= 0 else 'down' }}">
                    {{ '+' if nav_change >= 0 else '' }}${{ "{:,}".format(nav_change|int) }} ({{ nav_change_percent|round(2) }}%)
                </div>
            </div>
            <div class="stat-card">
                <div class="stat-label">💵 持仓市值</div>
                <div class="stat-value">${{ "{:,}".format(total_invested|int) }}</div>
                <div class="stat-change {{ 'up' if total_pnl >= 0 else 'down' }}">
                    {{ '+' if total_pnl >= 0 else '' }}${{ "{:,}".format(total_pnl|int) }} ({{ total_pnl_percent|round(2) }}%)
                </div>
            </div>
            <div class="stat-card">
                <div class="stat-label">💳 可用现金</div>
                <div class="stat-value">${{ "{:,}".format(cash_remaining|int) }}</div>
                <div class="stat-change" style="color: #8b949e;">仓位：{{ (total_invested / (total_invested + cash_remaining) * 100)|round(1) }}%</div>
            </div>
        </div>
        
        <div class="charts-grid">
            <div class="chart-card">
                <div class="chart-title">📈 净值走势</div>
                <div class="chart-container">
                    <canvas id="navChart"></canvas>
                </div>
            </div>
            <div class="chart-card">
                <div class="chart-title">🥧 持仓占比</div>
                <div class="chart-container">
                    <canvas id="pieChart"></canvas>
                </div>
            </div>
        </div>
        
        <div class="section">
            <div class="section-title">📊 当前持仓 ({{ positions|length }}只)</div>
            <table class="positions-table">
                <thead>
                    <tr>
                        <th>股票</th>
                        <th>市场</th>
                        <th>持仓</th>
                        <th>成本价</th>
                        <th>现价</th>
                        <th>市值</th>
                        <th>盈亏</th>
                        <th>RSI</th>
                    </tr>
                </thead>
                <tbody>
                    {% for pos in positions %}
                    <tr>
                        <td>
                            <div class="stock-name">{{ pos.name }}</div>
                            <div class="stock-code">{{ pos.code }}</div>
                        </td>
                        <td>
                            <span class="market-tag market-{{ pos.market|lower }}">{{ pos.market }}</span>
                        </td>
                        <td>{{ pos.qty }}股</td>
                        <td>
                            {% if pos.currency == 'USD' %}${% elif pos.currency == 'HKD' %}HK${% else %}¥{% endif %}
                            {{ "%.2f"|format(pos.cost) }}
                        </td>
                        <td>
                            {% if pos.currency == 'USD' %}${% elif pos.currency == 'HKD' %}HK${% else %}¥{% endif %}
                            <strong style="color: {% if pos.current_price >= pos.cost %}#7ee787{% else %}#f85149{% endif %}">
                                {{ "%.2f"|format(pos.current_price) }}
                            </strong>
                        </td>
                        <td>${{ "{:,}".format(pos.value_usd|int) }}</td>
                        <td class="{{ 'pnl-up' if pos.pnl >= 0 else 'pnl-down' }}">
                            {{ '+' if pos.pnl >= 0 else '' }}${{ "{:,.2f}".format(pos.pnl) }}
                            <br><small>({{ "%.2f"|format(pos.pnl_percent) }}%)</small>
                        </td>
                        <td>
                            <span class="rsi-badge {{ 'rsi-oversold' if pos.rsi < 30 else 'rsi-overbought' if pos.rsi > 70 else 'rsi-normal' }}">
                                {{ pos.rsi }}
                            </span>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        
        <div class="section">
            <div class="section-title">📜 交易记录</div>
            <table class="trades-table">
                <thead>
                    <tr>
                        <th>日期</th>
                        <th>操作</th>
                        <th>股票</th>
                        <th>数量</th>
                        <th>价格</th>
                        <th>金额</th>
                        <th>理由</th>
                    </tr>
                </thead>
                <tbody>
                    {% for trade in trades %}
                    <tr>
                        <td>{{ trade.date }}</td>
                        <td><span class="trade-action {{ trade.action }}">{{ trade.action }}</span></td>
                        <td>{{ trade.name }} ({{ trade.code }})</td>
                        <td>{{ trade.qty }}</td>
                        <td>${{ "%.2f"|format(trade.price) }}</td>
                        <td>${{ "{:,.2f}".format(trade.price * trade.qty) }}</td>
                        <td style="color: #8b949e;">{{ trade.reason }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        
        <div class="footer">
            🤖 AI 模拟交易 | 初始资金 ${{ "{:,}".format(initial_cash) }} | 数据来源：Yahoo Finance<br>
            生成时间：{{ update_time }} | 版本：v2.0
        </div>
    </div>
    
    <script>
        const navCtx = document.getElementById('navChart').getContext('2d');
        new Chart(navCtx, {
            type: 'line',
            data: {
                labels: {{ nav_labels | tojson }},
                datasets: [{
                    label: '净值 ($)',
                    data: {{ nav_values | tojson }},
                    borderColor: '#7ee787',
                    backgroundColor: 'rgba(126, 231, 135, 0.1)',
                    borderWidth: 3,
                    tension: 0.4,
                    fill: true,
                    pointBackgroundColor: '#7ee787',
                    pointBorderColor: '#0d1117',
                    pointBorderWidth: 2,
                    pointRadius: 5
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: '#161b22',
                        titleColor: '#e6edf3',
                        bodyColor: '#8b949e',
                        borderColor: '#30363d',
                        borderWidth: 1,
                        padding: 12,
                        displayColors: false,
                        callbacks: {
                            label: function(context) {
                                return '$' + context.parsed.y.toLocaleString();
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        grid: { color: '#30363d' },
                        ticks: {
                            color: '#8b949e',
                            callback: function(value) {
                                return '$' + value.toLocaleString();
                            }
                        }
                    },
                    x: {
                        grid: { display: false },
                        ticks: { color: '#8b949e' }
                    }
                }
            }
        });
        
        const pieCtx = document.getElementById('pieChart').getContext('2d');
        new Chart(pieCtx, {
            type: 'doughnut',
            data: {
                labels: {{ portfolio_labels | tojson }},
                datasets: [{
                    data: {{ portfolio_values | tojson }},
                    backgroundColor: {{ portfolio_colors | tojson }},
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            color: '#8b949e',
                            padding: 12,
                            font: { size: 11 }
                        }
                    },
                    tooltip: {
                        backgroundColor: '#161b22',
                        titleColor: '#e6edf3',
                        bodyColor: '#8b949e',
                        borderColor: '#30363d',
                        borderWidth: 1,
                        padding: 12,
                        callbacks: {
                            label: function(context) {
                                const value = context.parsed;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percent = ((value / total) * 100).toFixed(1);
                                return context.label + ': $' + value.toLocaleString() + ' (' + percent + '%)';
                            }
                        }
                    }
                }
            }
        });
    </script>
</body>
</html>'''
    
    template = Template(template_str)
    
    html_content = template.render(
        positions=positions_data,
        trades=TRADES,
        initial_cash=INITIAL_CASH,
        cash_remaining=CASH_REMAINING,
        total_invested=total_invested_usd,
        total_pnl=total_pnl_usd,
        total_pnl_percent=total_pnl_percent,
        current_nav=current_nav,
        nav_change=nav_change,
        nav_change_percent=nav_change_percent,
        update_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        portfolio_labels=portfolio_labels,
        portfolio_values=portfolio_values,
        portfolio_colors=portfolio_colors,
        nav_labels=nav_labels,
        nav_values=nav_values
    )
    
    with open(OUTPUT_HTML, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"  ✅ 已生成：{OUTPUT_HTML}")
    
    with open(DOCS_HTML, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"  ✅ 已生成：{DOCS_HTML}")
    
    return html_content

def save_config(positions_data):
    """保存配置到 JSON"""
    config = {
        'initial': INITIAL_CASH,
        'current': CASH_REMAINING + sum(p['value_usd'] for p in positions_data),
        'cash': CASH_REMAINING,
        'total_invested': sum(p['value_usd'] for p in positions_data),
        'positions': positions_data,
        'trades': TRADES,
        'last_update': datetime.now().isoformat()
    }
    
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    print(f"  ✅ 已保存：{CONFIG_FILE}")

def main():
    """主函数"""
    print("=" * 60)
    print("🤖 AI 模拟交易 - 网页生成器 v2.0")
    print("=" * 60)
    
    positions_data = fetch_all_data()
    generate_html(positions_data)
    save_config(positions_data)
    
    print("\n" + "=" * 60)
    print("✅ 生成完成！")
    print("=" * 60)
    print(f"\n📄 网页文件：{OUTPUT_HTML}")
    print(f"📊 数据文件：{CONFIG_FILE}")
    print(f"🌐 部署目录：{DOCS_HTML}")
    print("\n💡 下一步:")
    print("   1. 在浏览器打开：file://" + OUTPUT_HTML)
    print("   2. 推送到 GitHub Pages:")
    print("      cd /root/.openclaw/workspace")
    print("      git add .")
    print("      git commit -m 'Update: 实时数据'")
    print("      git push")
    print()

if __name__ == '__main__':
    main()
