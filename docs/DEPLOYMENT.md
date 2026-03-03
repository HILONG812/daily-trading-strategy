# 部署到 GitHub Pages

## 前提条件

1. GitHub 账号
2. 创建仓库：`daily-trading-strategy`
3. 安装 GitHub CLI (可选)

## 方法一：使用 Git 命令 (推荐)

### 1. 配置 Git 用户信息

```bash
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

### 2. 添加远程仓库

```bash
cd /root/.openclaw/workspace
git remote add origin https://github.com/YOUR_USERNAME/daily-trading-strategy.git
```

### 3. 推送代码

```bash
git add trading.html docs/
git commit -m "Initial commit: AI 模拟交易网页"
git branch -M main
git push -u origin main
```

### 4. 启用 GitHub Pages

1. 访问：https://github.com/YOUR_USERNAME/daily-trading-strategy/settings/pages
2. Source: Deploy from a branch
3. Branch: main
4. Folder: /docs
5. 点击 Save

### 5. 访问网页

部署完成后，访问：
```
https://YOUR_USERNAME.github.io/daily-trading-strategy/
```

## 方法二：使用 GitHub CLI

### 1. 安装 GitHub CLI

```bash
# Ubuntu/Debian
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
sudo apt update
sudo apt install gh -y

# 验证安装
gh --version
```

### 2. 登录 GitHub

```bash
gh auth login
```

### 3. 创建仓库并推送

```bash
cd /root/.openclaw/workspace

# 创建仓库
gh repo create daily-trading-strategy --public --source=. --remote=origin --push

# 或者推送到现有仓库
git push -u origin main
```

## 自动部署脚本

创建 `.github/workflows/deploy.yml`:

```yaml
name: Deploy to GitHub Pages

on:
  push:
    branches:
      - main
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

jobs:
  deploy:
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Pages
        uses: actions/configure-pages@v4

      - name: Upload artifact
        uses: actions/upload-pages-artifact@v3
        with:
          path: './docs'

      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v4
```

## 更新流程

### 手动更新

```bash
cd /root/.openclaw/workspace
git add .
git commit -m "Update: 添加实时数据功能"
git push
```

### 自动更新 (Cron)

创建定时任务，每天自动推送更新：

```bash
crontab -e

# 每天 09:00 自动更新
0 9 * * * cd /root/.openclaw/workspace && git pull && /usr/bin/python3 scripts/fetch_stock_data.py && git add . && git commit -m "Daily update: $(date +\%Y-\%m-\%d)" && git push
```

## 自定义域名 (可选)

1. 在仓库设置中添加 CNAME 文件
2. 内容：`your-domain.com`
3. 在 DNS 提供商处配置 CNAME 记录

## 故障排查

### 页面不显示

- 检查 GitHub Pages 是否启用
- 确认 `docs/index.html` 存在
- 查看 GitHub Actions 部署日志

### 数据不更新

- 检查 `fetch_stock_data.py` 是否正常运行
- 验证 Yahoo Finance API 是否可访问
- 查看 trades.json 最后更新时间

## 相关资源

- [GitHub Pages 文档](https://docs.github.com/en/pages)
- [GitHub CLI 文档](https://cli.github.com/)
- [yfinance 文档](https://pypi.org/project/yfinance/)
