#!/usr/bin/env python3
"""
Stock Analyst v5 - 机会理由驱动界面
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import sys
sys.path.insert(0, '/root/.openclaw/workspace/stock_app')
from analyzer import (add_stock, remove_stock, get_monitored_stocks, 
                    analyze_opportunity, get_opportunities, get_news)

st.set_page_config(page_title="Stock Analyst", page_icon="📈", layout="wide")

# CSS - 移动端优先 + 理由驱动
st.markdown("""
<style>
    .stApp { background: #000; color: #fff; }
    
    /* 顶部 */
    .header { background: linear-gradient(90deg, #1a1a2e, #16213e); padding: 16px; position: sticky; top: 0; z-index: 100; }
    .header-title { font-size: 22px; font-weight: 700; background: linear-gradient(90deg, #00ff88, #00ccff); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    
    /* 机会卡片 */
    .opp-card { background: #1a1a2e; border-radius: 12px; padding: 16px; margin-bottom: 16px; border: 1px solid #333; }
    
    /* 标题区 */
    .opp-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
    .opp-name { font-size: 18px; font-weight: 600; }
    .opp-code { font-size: 12px; color: #888; }
    .opp-action { font-size: 16px; font-weight: 700; padding: 4px 12px; border-radius: 8px; }
    .action-hot { background: #ff4444; color: #fff; }
    .action-watch { background: #ffaa00; color: #000; }
    .action-value { background: #00ff88; color: #000; }
    .action-wait { background: #666; color: #fff; }
    
    /* 摘要 */
    .opp-summary { font-size: 15px; color: #ccc; margin-bottom: 12px; line-height: 1.5; }
    
    /* 理由列表 */
    .reasons-box { background: #0d1117; border-radius: 8px; padding: 12px; }
    .reason-item { padding: 6px 0; border-bottom: 1px solid #222; font-size: 14px; }
    .reason-item:last-child { border-bottom: none; }
    .reason-bullet { color: #00ff88; margin-right: 8px; }
    
    /* 警告 */
    .warning-item { color: #ff4444; font-size: 13px; padding: 4px 0; }
    
    /* 价格 */
    .price-row { display: flex; gap: 16px; margin-top: 12px; padding-top: 12px; border-top: 1px solid #333; }
    .price-item { text-align: center; }
    .price-label { font-size: 11px; color: #666; }
    .price-value { font-size: 16px; font-weight: 600; }
    
    /* 摘要统计 */
    .summary-row { display: flex; justify-content: space-around; background: #1a1a2e; border-radius: 12px; padding: 16px; margin-bottom: 16px; }
    .sum-item { text-align: center; }
    .sum-num { font-size: 24px; font-weight: 700; }
    .sum-label { font-size: 11px; color: #888; }
    
    /* 输入 */
    .stTextInput input { background: #252540 !important; border: 1px solid #333 !important; color: #fff !important; border-radius: 8px !important; }
    .stButton button { background: linear-gradient(90deg, #00ff88, #00ccff) !important; color: #000 !important; border: none !important; border-radius: 8px !important; width: 100%; }
    
    /* 标签 */
    .stTabs [data-baseweb="tab-list"] { background: #1a1a2e; gap: 4px; padding: 8px; }
    .stTabs [data-baseweb="tab"] { background: transparent; color: #666; border-radius: 8px; }
    .stTabs [aria-selected="true"] { background: #00ff88 !important; color: #000 !important; }
    
    /* 新闻 */
    .news-item { padding: 10px 0; border-bottom: 1px solid #333; }
    .news-title { font-size: 14px; }
    .news-source { font-size: 11px; color: #666; }
</style>
""", unsafe_allow_html=True)

# 顶部
st.markdown(f'''
<div class="header">
    <div style="display:flex; justify-content:space-between; align-items:center;">
        <div class="header-title">📈 Stock Analyst</div>
        <div style="color:#888; font-size:12px;">{datetime.now().strftime('%m-%d %H:%M')}</div>
    </div>
</div>
''', unsafe_allow_html=True)

# 侧边栏
with st.sidebar:
    st.markdown('<div class="sidebar-title">⚡ 操作</div>', unsafe_allow_html=True)
    with st.expander("➕ 添加", expanded=True):
        c1, c2 = st.columns(2)
        tk = c1.text_input("代码", placeholder="AAPL", key="add")
        mk = c2.selectbox("市场", ["US", "HK", "CN", "JP"], format_func=lambda x: {"US":"🇺🇸","HK":"🇭🇰","CN":"🇨🇳","JP":"🇯🇵"}[x])
        if st.button("添加"):
            if tk:
                add_stock(tk, mk, '')
                st.success("已添加")
                st.rerun()
    with st.expander("➖ 移除"):
        stocks = get_monitored_stocks()
        if stocks:
            rm = st.selectbox("选", [s['ticker'] for s in stocks])
            if st.button("移除"):
                remove_stock(rm)
                st.rerun()

# 主界面
tab1, tab2, tab3 = st.tabs(["🔥 机会", "📋 监控", "📰 资讯"])

# ============ Tab 1: 机会 ============
with tab1:
    with st.spinner("分析中..."):
        opp = get_opportunities()
    
    # 统计
    st.markdown(f'''
    <div class="summary-row">
        <div class="sum-item"><div class="sum-num" style="color:#fff;">{len(get_monitored_stocks())}</div><div class="sum-label">监控</div></div>
        <div class="sum-item"><div class="sum-num" style="color:#ff4444;">{len(opp['hot'])}</div><div class="sum-label">强烈</div></div>
        <div class="sum-item"><div class="sum-num" style="color:#ffaa00;">{len(opp['watch'])}</div><div class="sum-label">关注</div></div>
        <div class="sum-item"><div class="sum-num" style="color:#666;">{len(opp['neutral'])}</div><div class="sum-label">等待</div></div>
    </div>
    ''', unsafe_allow_html=True)
    
    # 机会列表
    all_opp = opp['hot'] + opp['watch'] + opp['neutral']
    
    for o in all_opp:
        # 动作样式
        action_cls = 'action-hot' if '🔥' in o.get('action','') else 'action-watch' if '👀' in o.get('action','') else 'action-value' if '👍' in o.get('action','') else 'action-wait'
        
        # 涨跌颜色
        change_color = '#00ff88' if o.get('change',0) >= 0 else '#ff4444'
        
        st.markdown(f'''
        <div class="opp-card">
            <div class="opp-header">
                <div>
                    <div class="opp-name">{o.get('name', o['ticker'])[:15]}</div>
                    <div class="opp-code">{o['ticker']}</div>
                </div>
                <span class="opp-action {action_cls}">{o.get('action', '⏸️ 等待')}</span>
            </div>
            
            <div class="opp-summary">{o.get('summary', '')}</div>
            
            <div class="reasons-box">
                <div style="color:#666; font-size:12px; margin-bottom:8px;">📋 买入理由</div>
                {''.join([f'<div class="reason-item"><span class="reason-bullet">✓</span>{r}</div>' for r in o.get('buy_reasons', [])[:3]]) if o.get('buy_reasons') else '<div class="reason-item">暂无</div>'}
            </div>
            
            {''.join([f'<div class="warning-item">⚠️ {w}</div>' for w in o.get('warnings', [])]) if o.get('warnings') else ''}
            
            <div class="price-row">
                <div class="price-item">
                    <div class="price-label">价格</div>
                    <div class="price-value">${o.get('price', 0):.2f}</div>
                </div>
                <div class="price-item">
                    <div class="price-label">今日</div>
                    <div class="price-value" style="color:{change_color};">{o.get('change', 0):+.2f}%</div>
                </div>
                <div class="price-item">
                    <div class="price-label">位置</div>
                    <div class="price-value">{o.get('contrarian',{}).get('position', 50):.0f}%</div>
                </div>
            </div>
        </div>
        ''', unsafe_allow_html=True)

# ============ Tab 2: 监控列表 ============
with tab2:
    st.markdown("### 全部监控")
    results = [analyze_opportunity(s['full_ticker']) for s in get_monitored_stocks()]
    results = [r for r in results if 'error' not in r]
    
    if results:
        data = [{'代码': r['ticker'], '动作': r.get('action', ''), '理由': r.get('summary', '')[:30]} for r in results]
        st.dataframe(pd.DataFrame(data), use_container_width=True, hide_index=True)

# ============ Tab 3: 资讯 ============
with tab3:
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**美股**")
        news = get_news([s['ticker'] for s in get_monitored_stocks() if s['market']=='US'][:3] or ['AAPL'])
        for n in news:
            st.markdown(f'<div class="news-item"><div class="news-title">{n.get("title","")}</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown("**A股**")
        st.markdown('<div class="news-item"><div class="news-title">暂无新闻源</div></div>', unsafe_allow_html=True)

st.markdown("---")
st.caption("📈 Stock Analyst v5 | 基于巴菲特·芒格·达利欧理念")

if __name__ == '__main__':
    st.run()