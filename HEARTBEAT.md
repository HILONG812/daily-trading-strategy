# HEARTBEAT.md

# 市场策略师定时任务

## 自动更新
- 每天 08:00（早盘前）：拉新闻→分析→更新网页
- 每天 20:00（盘后）：拉新闻→分析→更新网页

## 执行流程
1. 用 GNews API 拉最新财经新闻
2. AI分析新闻，给出交易策略
3. 更新 GitHub Pages 网页
4. 推送更新通知到飞书

## 手动触发
用户说"更新"时也执行上述流程

## 记录
- lastMorningRun: 2026-03-04 08:00 ✅ (实际执行：16:26 北京时间)
- lastEveningRun: 2026-03-04 00:00 ✅
- nextEveningRun: 2026-03-04 20:00

## ✅ Cron 已配置（2026-03-03 22:40）
```
0 8 * * * /usr/bin/python3 /root/.openclaw/workspace/scripts/market_report_cron.py
0 20 * * * /usr/bin/python3 /root/.openclaw/workspace/scripts/market_report_cron.py
```
**明天 08:00 自动执行，不会再忘记！**