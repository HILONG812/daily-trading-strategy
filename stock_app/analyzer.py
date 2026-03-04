#!/usr/bin/env python3
"""
股票分析师 v5 - 机会理由驱动
基于巴菲特/芒格/达利欧投资理念
"""

import json
import os
import time
from datetime import datetime
from typing import List, Dict
import yfinance as yf
import pandas as pd
import numpy as np

CONFIG_FILE = '/root/.openclaw/workspace/stock_app/config.json'
CACHE_FILE = '/root/.openclaw/workspace/stock_app/cache.json'

def load_config():
    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)

def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

def load_cache():
    try:
        with open(CACHE_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_cache(cache):
    with open(CACHE_FILE, 'w') as f:
        json.dump(cache, f)

def get_cache(key, max_age=600):
    cache = load_cache()
    if key in cache and time.time() - cache[key]['time'] < max_age:
        return cache[key]['value']
    return None

def set_cache(key, value):
    cache = load_cache()
    cache[key] = {'value': value, 'time': time.time()}
    save_cache(cache)

# ============ 监控管理 ============

def add_stock(ticker: str, market: str = 'US', reason: str = '') -> Dict:
    config = load_config()
    ticker = ticker.upper().strip()
    
    suffix = {'US': '', 'JP': '.T', 'HK': '.HK', 'CN': '.SS'}.get(market, '')
    full_ticker = ticker + suffix if suffix and not ticker.endswith(suffix) else ticker
    
    for s in config['monitored_stocks']:
        if s['ticker'] == ticker:
            return {'success': False, 'message': f'{ticker} 已监控'}
    
    try:
        stock = yf.Ticker(full_ticker)
        info = stock.info
        name = info.get('shortName', info.get('longName', ticker))
    except:
        name = ticker
    
    config['monitored_stocks'].append({
        'ticker': ticker, 'full_ticker': full_ticker,
        'market': market, 'name': name, 'reason': reason,
        'added_at': datetime.now().strftime('%Y-%m-%d')
    })
    save_config(config)
    return {'success': True, 'message': f'已添加 {ticker}'}

def remove_stock(ticker: str) -> Dict:
    config = load_config()
    ticker = ticker.upper().strip()
    before = len(config['monitored_stocks'])
    config['monitored_stocks'] = [s for s in config['monitored_stocks'] if s['ticker'] != ticker]
    if len(config['monitored_stocks']) < before:
        save_config(config)
        return {'success': True, 'message': f'已移除 {ticker}'}
    return {'success': False, 'message': f'{ticker} 不在列表'}

def get_monitored_stocks() -> List[Dict]:
    return load_config()['monitored_stocks']

# ============ 巴菲特价值分析 ============

def analyze_value(ticker: str) -> Dict:
    """巴菲特视角：护城河 + 估值"""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # 护城河指标
        roe = info.get('returnOnEquity', 0)  # ROE > 15% 优秀
        profit_margin = info.get('profitMargins', 0)  # 利润率
        pe = info.get('trailingPE', 0)  # 市盈率
        pb = info.get('priceToBookValue', 0)  # 市净率
        debt_to_equity = info.get('debtToEquity', 0)  # 负债率
        
        # 成长性
        revenue_growth = info.get('revenueGrowth', 0)  # 营收增长
        earnings_growth = info.get('earningsGrowth', 0)  # 盈利增长
        
        # 市场规模
        market_cap = info.get('marketCap', 0)
        
        # 护城河评估
        moat_score = 0
        moat_reasons = []
        
        if roe and roe > 0.15:
            moat_score += 2
            moat_reasons.append(f"ROE {roe*100:.1f}% 优秀")
        
        if profit_margin and profit_margin > 0.2:
            moat_score += 1
            moat_reasons.append(f"利润率 {profit_margin*100:.1f}%")
        
        if market_cap and market_cap > 1e11:  # >1000亿
            moat_score += 1
            moat_reasons.append(f"市值 ${market_cap/1e9:.0f}B 大公司")
        
        # 估值评估
        value_score = 0
        value_reasons = []
        
        if pe and 0 < pe < 20:
            value_score += 2
            value_reasons.append(f"PE {pe:.1f} 偏低")
        elif pe and pe < 0:
            value_reasons.append("⚠️ 亏损")
        
        if pb and 0 < pb < 3:
            value_score += 1
            value_reasons.append(f"PB {pb:.1f}")
        
        if debt_to_equity and debt_to_equity < 50:
            value_score += 1
            value_reasons.append("负债健康")
        
        # 成长评估
        growth_score = 0
        growth_reasons = []
        
        if revenue_growth and revenue_growth > 0.1:
            growth_score += 2
            growth_reasons.append(f"营收增长 {revenue_growth*100:.0f}%")
        
        return {
            'moat_score': moat_score, 'moat_reasons': moat_reasons,
            'value_score': value_score, 'value_reasons': value_reasons,
            'growth_score': growth_score, 'growth_reasons': growth_reasons,
            'roe': roe, 'pe': pe, 'market_cap': market_cap
        }
    except Exception as e:
        return {'error': str(e)}

# ============ 芒格逆向分析 ============

def analyze_contrarian(ticker: str) -> Dict:
    """芒格视角：逆向 + 误判检查"""
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period='1y')
        
        if hist.empty:
            return {'error': '无数据'}
        
        current = hist['Close'].iloc[-1]
        
        # 52周位置 (接近低点=机会)
        high_1y = hist['High'].max()
        low_1y = hist['Low'].min()
        position = (current - low_1y) / (high_1y - low_1y) * 100
        
        # 近期表现 (近期跌=机会)
        change_1m = ((current - hist['Close'].iloc[-22]) / hist['Close'].iloc[-22]) * 100 if len(hist) > 22 else 0
        change_3m = ((current - hist['Close'].iloc[-65]) / hist['Close'].iloc[-65]) * 100 if len(hist) > 65 else 0
        
        # RSI超卖
        delta = hist['Close'].diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        rsi_val = rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else 50
        
        # 芒格逆向信号
        signals = []
        
        if position < 20:
            signals.append(("💎", f"接近1年最低价({position:.0f}%)", "芒格:别人恐惧"))
        elif position < 40:
            signals.append(("📉", f"处于1年低位({position:.0f}%)", "低估区域"))
        
        if rsi_val < 30:
            signals.append(("⚡", f"RSI={rsi_val:.0f}超卖", "反弹概率高"))
        elif rsi_val < 40:
            signals.append(("👀", f"RSI={rsi_val:.0f}接近超卖", "关注机会"))
        
        if change_3m < -20:
            signals.append(("🔻", f"3个月跌{abs(change_3m):.0f}%", "超跌反弹"))
        
        # 负面信号 (误判检查)
        warnings = []
        if position > 80:
            warnings.append("⚠️ 接近1年最高，注意回调")
        if rsi_val > 70:
            warnings.append("⚠️ RSI超买")
        
        return {
            'position': position,
            'rsi': rsi_val,
            'change_1m': change_1m,
            'change_3m': change_3m,
            'signals': signals,
            'warnings': warnings
        }
    except Exception as e:
        return {'error': str(e)}

# ============ 综合分析 ============

def analyze_opportunity(ticker: str) -> Dict:
    """综合分析 - 机会理由"""
    cache_key = f'opp_{ticker}'
    cached = get_cache(cache_key)
    if cached:
        return cached
    
    try:
        # 基础信息
        stock = yf.Ticker(ticker)
        try:
            info = stock.info
            name = info.get('shortName', info.get('longName', ticker))
        except:
            name = ticker
        
        hist = stock.history(period='3mo')
        if hist.empty:
            return {'error': '无数据'}
        
        price = hist['Close'].iloc[-1]
        prev = hist['Close'].iloc[-2] if len(hist) > 1 else price
        change = ((price - prev) / prev) * 100
        
        # 巴菲特分析
        value = analyze_value(ticker)
        # 芒格分析
        contrarian = analyze_contrarian(ticker)
        
        # 生成机会理由
        reasons = []
        buy_reasons = []
        
        # 从价值分析获取理由
        if 'error' not in value:
            buy_reasons.extend(value.get('moat_reasons', []))
            buy_reasons.extend(value.get('value_reasons', []))
            buy_reasons.extend(value.get('growth_reasons', []))
        
        # 从逆向分析获取理由
        if 'error' not in contrarian:
            for emoji, sig, reason in contrarian.get('signals', []):
                reasons.append(f"{emoji} {sig}")
                if "超卖" in sig or "最低" in sig or "超跌" in sig:
                    buy_reasons.append(reason)
        
        # 综合建议
        if contrarian.get('rsi', 50) < 30:
            action = "🔥 强烈关注"
            summary = f"RSI超卖({contrarian['rsi']:.0f})，可能是反弹起点"
        elif contrarian.get('position', 50) < 20:
            action = "👀 关注"
            summary = "接近1年最低，逆向投资机会"
        elif value.get('value_score', 0) >= 3:
            action = "👍 价值显现"
            summary = "估值便宜，具备吸引力"
        elif value.get('moat_score', 0) >= 3:
            action = "🛡️ 护城河强"
            summary = "公司护城河深厚"
        else:
            action = "⏸️ 等待"
            summary = "等待更好时机"
        
        result = {
            'ticker': ticker,
            'name': name,
            'price': price,
            'change': change,
            'action': action,
            'summary': summary,
            'reasons': reasons[:3],  # 最多3条
            'buy_reasons': buy_reasons[:4],  # 买入理由
            'warnings': contrarian.get('warnings', []),
            'value': value,
            'contrarian': contrarian
        }
        
        set_cache(cache_key, result)
        return result
        
    except Exception as e:
        return {'error': str(e)}

# ============ 批量分析 ============

def analyze_all() -> List[Dict]:
    results = []
    for s in get_monitored_stocks():
        r = analyze_opportunity(s['full_ticker'])
        if 'error' not in r:
            r['market'] = s['market']
            results.append(r)
    return results

def get_opportunities() -> Dict:
    all_stocks = analyze_all()
    
    # 排序：强关注 > 关注 > 价值 > 护城河 > 等待
    priority = {'🔥 强烈关注': 0, '👀 关注': 1, '👍 价值显现': 2, '🛡️ 护城河强': 3, '⏸️ 等待': 4}
    all_stocks.sort(key=lambda x: priority.get(x.get('action', '⏸️ 等待'), 4))
    
    hot = [s for s in all_stocks if '🔥' in s.get('action', '')]
    watch = [s for s in all_stocks if '👀' in s.get('action', '') or '👍' in s.get('action', '')]
    others = [s for s in all_stocks if s not in hot and s not in watch]
    
    return {
        'hot': hot,
        'watch': watch,
        'neutral': others,
        'summary': f"监控 {len(all_stocks)} 只 | 🔥 {len(hot)} | 👀 {len(watch)} | ⏸️ {len(others)}"
    }

def get_news(tickers: List[str]) -> List[Dict]:
    news = []
    for t in tickers[:3]:
        try:
            stock = yf.Ticker(t)
            items = stock.news
            if items:
                for item in items[:1]:
                    news.append({'title': item.get('title', '')[:60], 'ticker': t})
        except:
            pass
    return news

if __name__ == '__main__':
    r = analyze_opportunity('0700.HK')
    print(f"腾讯: {r.get('action')}")
    print(f"理由: {r.get('summary')}")
    print(f"分析: {r.get('buy_reasons', [])[:2]}")