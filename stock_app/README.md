# 📈 Stock Analyzer

多市场股票分析工具，支持美股、日股、港股、A股。

![Python](https://img.shields.io/badge/Python-3.11+-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-1.54+-red)
![License](https://img.shields.io/badge/License-MIT-green)

## 🛠 技术栈

| 组件 | 技术 | 说明 |
|------|------|------|
| 数据源 | yfinance | 美/日/港股数据 |
| 数据源 | AkShare | A股深度数据 |
| 前端 | Streamlit | 交互式Web界面 |
| 图表 | Plotly | K线图、技术指标 |

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 运行应用

```bash
streamlit run app.py
```

### 3. 访问

打开浏览器访问: http://localhost:8501

## 📊 支持的市场

| 市场 | 代码示例 | 备注 |
|------|----------|------|
| 美股 | AAPL, MSFT, GOOGL | 需安装 yfinance |
| 日股 | 7203.T, 9984.T | 丰田、软银 |
| 港股 | 0700.HK, 9988.HK | 腾讯、阿里 |
| A股 | 000001.SS, 600519.SS | 上证、茅台 (需 .SS/.SZ 后缀) |

## 📈 功能特性

- ✅ 实时股价查询
- ✅ K线图 + 成交量
- ✅ 移动平均线 (MA20, MA50, MA200)
- ✅ 52周高低点
- ✅ 市值、PE、EPS等财务指标
- ✅ A股 AkShare 深度数据

## 🌐 部署

### 本地运行
```bash
streamlit run app.py --server.port 8501
```

### 服务器部署
```bash
# 后台运行
nohup streamlit run app.py --server.port 8501 --server.address 0.0.0.0 &
```

## 📝 股票代码说明

- **美股**: 直接输入代码 (如 `AAPL`)
- **日股**: 加 `.T` 后缀 (如 `7203.T`)
- **港股**: 加 `.HK` 后缀 (如 `0700.HK`)
- **A股**: 
  - 上海: 加 `.SS` (如 `600519.SS`)
  - 深圳: 加 `.SZ` (如 `000001.SZ`)

## 📄 License

MIT License