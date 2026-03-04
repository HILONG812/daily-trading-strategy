# 🌍 全球股市数据缓存系统

## 📁 目录结构

```
data/market_cache/
├── realtime_{symbol}.json    # 实时行情缓存 (5 分钟过期)
├── kline_{symbol}.csv        # K 线历史数据 (增量追加)
├── daily_{symbol}.json       # 日线数据 (24 小时过期)
├── holdings_summary.json     # 持仓汇总
└── market_data_full.json     # 完整分析数据
```

## 🔄 缓存协议

遵循 Gemini 推荐的标准流程：

1. **检查缓存** → 优先读取本地文件
2. **验证有效期** → 实时数据 5 分钟，日线 24 小时
3. **按需更新** → 仅缓存失效时调用 API
4. **增量存储** → K 线数据追加模式，只下载缺失日期
5. **输出确认** → 返回"数据来自 [本地缓存/实时下载]"

## 📊 覆盖市场

| 市场 | 股票 | 数据源 |
|------|------|--------|
| 🇺🇸 美股 | NVDA, AAPL, TSLA, ASML, SIL | yfinance / NASDAQ |
| 🇭🇰 港股 | 0700, 9988, 9863, 2402 | 东方财富 API |
| 🇯🇵 日股 | 7203.T, 8058.T | yfinance |
| 🇨🇳 A 股 | 688339 | 东方财富 API |

## 🛠️ 使用方法

### 1. 获取所有持仓数据

```bash
cd /root/.openclaw/workspace
python3 scripts/cache_protocol_v3.py
```

### 2. 强制刷新（忽略缓存）

```bash
python3 scripts/cache_protocol_v3.py --force
```

### 3. 分析持仓

```bash
python3 scripts/analyze_from_cache.py
```

## 📈 分析功能

`analyze_from_cache.py` 提供：

- ✅ RSI 超买/超卖检测
- ✅ MA20 均线状态
- ✅ 盈亏分析
- ✅ 交易信号生成 (买入/卖出/持有)
- ✅ 置信度评分
- ✅ 全球市场状态
- ✅ 仓位评估

## 🎯 交易信号规则

| 条件 | 信号 | 操作 |
|------|------|------|
| RSI < 20 + 站上 MA20 | 🟢 强烈买入 | 加仓 |
| RSI < 30 + 站上 MA20 | 🟢 买入 | 加仓 |
| RSI > 70 | 🔴 超买 | 减仓/止盈 |
| 盈亏 < -8% | 🔴 止损 | 立即卖出 |
| 盈亏 > +20% | 🟡 止盈 | 减半仓 |
| 其他 | ⚪ 持有观望 | 保持 |

## 📝 示例输出

```
📦 数据来源：[本地缓存] NVDA (0:02:15)
🌐 数据来源：[实时下载] 0700

📊 数据汇总
总计：12 只股票
来自缓存：8
实时下载：4
```

## ⏰ 自动更新

Cron 任务已配置：

```bash
# 每 5 分钟更新实时数据
*/5 * * * * python3 /root/.openclaw/workspace/scripts/cache_protocol_v3.py

# 每小时分析一次
0 * * * * python3 /root/.openclaw/workspace/scripts/analyze_from_cache.py
```

## 🚀 优势

1. **突破对话限制** - 数据存在文件里，不占用上下文
2. **节省 Token** - 只关注增量信息
3. **支持多图表对比** - 直接读取多个缓存文件
4. **离线可用** - 缓存失效前无需网络
5. **增量更新** - 只下载缺失数据，节省流量

## 📁 相关文件

- `scripts/cache_protocol_v3.py` - 缓存系统主程序
- `scripts/analyze_from_cache.py` - 数据分析程序
- `scripts/global_market_cache.py` - 多数据源获取 (备用)
- `data/market_cache/` - 缓存数据目录

---

最后更新：2026-03-04 13:55
