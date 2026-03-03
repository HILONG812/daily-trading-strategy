#!/bin/bash
# 自动部署到 GitHub Pages (需要 Token)

GITHUB_TOKEN="${GITHUB_TOKEN:-}"  # 从环境变量读取
REPO="HILONG812/daily-trading-strategy"
BRANCH="main"

cd /root/.openclaw/workspace

# 复制最新网页
cp docs/index.html trading.html

# Git 操作
git config user.email "hilong812@gmail.com"
git config user.name "HILONG812"

git add trading.html docs/index.html
git commit -m "📊 自动部署：四维研报 $(date +%Y-%m-%d)"

if [ -n "$GITHUB_TOKEN" ]; then
    git remote set-url origin https://$GITHUB_TOKEN@github.com/$REPO.git
    git push origin $BRANCH
    echo "✅ 推送成功"
else
    echo "⚠️ GITHUB_TOKEN 未设置，无法推送"
    echo "请在飞书回复 Token 或手动执行:"
    echo "  export GITHUB_TOKEN=your_token"
    echo "  ./scripts/auto-deploy.sh"
fi
