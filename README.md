# 🤖 AI 模拟交易系统

> 10 万美金虚拟账户 | 实时数据追踪 | 全球市场覆盖

[![Deploy to GitHub Pages](https://github.com/HILONG812/daily-trading-strategy/actions/workflows/deploy.yml/badge.svg)](https://github.com/HILONG812/daily-trading-strategy/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 📈 实时预览

访问：https://HILONG812.github.io/daily-trading-strategy/

## 🎯 项目特色

- ✅ **实时股价**: 集成 Yahoo Finance API，5 分钟自动刷新
- ✅ **多市场支持**: 美股、港股、日股全覆盖
- ✅ **技术指标**: RSI、MA 等自动计算
- ✅ **盈亏追踪**: 实时计算持仓盈亏
- ✅ **响应式设计**: 手机/平板/电脑完美适配
- ✅ **离线可用**: 本地 JSON 数据存储

## 💼 当前持仓

| 市场 | 股票 | 代码 | 数量 | 成本价 | 现价 | 盈亏 |
|------|------|------|------|--------|------|------|
| 🇺🇸 美股 | 英伟达 | NVDA | 40 | $182.48 | 实时 | 实时 |
| 🇺🇸 美股 | 苹果 | AAPL | 25 | $264.72 | 实时 | 实时 |
| 🇺🇸 美股 | 特斯拉 | TSLA | 15 | $403.32 | 实时 | 实时 |
| 🇭🇰 港股 | 腾讯 | 0700.HK | 40 | HK$513.5 | 实时 | 实时 |
| 🇭🇰 港股 | 阿里 | 9988.HK | 80 | HK$135.1 | 实时 | 实时 |
| 🇯🇵 日股 | 丰田 | 7203.T | 10 | ¥3,702 | 实时 | 实时 |

**账户总额**: $100,000 | **已投资**: $88,335 | **现金**: $11,665

## 🚀 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/HILONG812/daily-trading-strategy.git
cd daily-trading-strategy
```

### 2. 安装依赖

```bash
pip install yfinance
```

### 3. 获取实时数据

```bash
python scripts/fetch_stock_data.py
```

### 4. 打开网页

```bash
# 直接在浏览器打开
open trading.html

# 或使用本地服务器
python -m http.server 8000
# 访问 http://localhost:8000/trading.html
```

## 📁 项目结构

```
daily-trading-strategy/
├── trading.html              # 主页面 (实时数据版)
├── trading_v2.html           # 增强版 (图表 + 实时刷新)
├── trades.json               # 交易数据
├── trading_log.md            # 交易日志
├── scripts/
│   └── fetch_stock_data.py   # 数据获取脚本
├── docs/
│   ├── index.html            # GitHub Pages 主页
│   ├── DEPLOYMENT.md         # 部署指南
│   └── ENGINEERING_STATUS.md # 工程状态
└── README.md                 # 本文件
```

## 🛠️ 功能模块

### 1. 实时股价获取

使用 `yfinance` 库从 Yahoo Finance 获取实时股价：

```python
import yfinance as yf

ticker = yf.Ticker('NVDA')
data = ticker.history(period='1d')
current_price = data['Close'].iloc[-1]
```

### 2. 技术指标计算

自动计算 RSI、移动平均线等指标：

- **RSI (相对强弱指数)**: 判断超买/超卖
- **MA (移动平均)**: 5 日/10 日/20 日均线
- **布林带**: 波动率分析

### 3. 自动刷新

网页每 5 分钟自动刷新数据：

```javascript
setInterval(refreshData, 300000); // 5 分钟
```

### 4. 图表展示

使用 Chart.js 展示净值走势：

```javascript
const chart = new Chart(ctx, {
    type: 'line',
    data: { ... },
    options: { ... }
});
```

## 📊 交易策略

### 选股逻辑

1. **基本面分析**: 护城河、现金流、估值
2. **技术面分析**: RSI、MA、支撑/阻力
3. **新闻面分析**: GNews API 实时新闻

### 买入信号

- ✅ RSI < 30 (超卖)
- ✅ 股价接近支撑位
- ✅ 正面新闻催化
- ✅ 估值低于历史平均

### 卖出信号

- ❌ RSI > 70 (超买)
- ❌ 跌破关键支撑
- ❌ 负面新闻冲击
- ❌ 达到目标价位

## 🔧 开发指南

### 添加新股票

1. 在 `trading.html` 的 `positions` 数组添加：

```javascript
{ market: '美股', code: 'MSFT', name: '微软', qty: 20, cost: 420.00, currency: 'USD' }
```

2. 在 `trades.json` 添加对应交易记录

3. 运行 `fetch_stock_data.py` 更新数据

### 修改刷新频率

```javascript
// trading.html
const CONFIG = {
    refreshInterval: 300000, // 毫秒 (5 分钟)
};
```

### 自定义图表

```javascript
// 修改 Chart.js 配置
navChart.config.data.datasets[0].borderColor = '#7ee787';
navChart.update();
```

## 📝 更新日志

### v2.0 (2026-03-03)
- ✅ 添加实时股价更新
- ✅ 集成 Yahoo Finance API
- ✅ 添加 Chart.js 图表
- ✅ 自动刷新功能 (5 分钟)
- ✅ 盈亏实时计算

### v1.0 (2026-03-02)
- ✅ 基础交易页面
- ✅ 持仓展示
- ✅ 交易记录
- ✅ 响应式设计

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE)

## 📞 联系

- GitHub: [@HILONG812](https://github.com/HILONG812)
- 项目地址：https://github.com/HILONG812/daily-trading-strategy

---

**免责声明**: 本项目为模拟交易，不构成投资建议。投资有风险，入市需谨慎。
