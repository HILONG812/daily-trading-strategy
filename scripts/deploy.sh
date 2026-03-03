#!/bin/bash
# GitHub Pages 部署脚本

set -e

WORKSPACE="/root/.openclaw/workspace"
REPO_URL="https://github.com/HILONG812/daily-trading-strategy.git"

cd "$WORKSPACE"

echo "🚀 开始部署到 GitHub Pages..."

# 检查 Git 配置
if ! git remote get-url origin &>/dev/null; then
    echo "⚠️  未配置 Git remote，正在添加..."
    git remote add origin "$REPO_URL" || true
fi

# 检查是否有 GitHub CLI
if command -v gh &>/dev/null; then
    echo "✅ 检测到 GitHub CLI"
    if ! gh auth status &>/dev/null; then
        echo "⚠️  未登录 GitHub，请运行：gh auth login"
        exit 1
    fi
fi

# 添加文件
echo "📦 添加文件..."
git add trading.html trades.json docs/ README.md scripts/

# 检查是否有更改
if git diff --cached --quiet; then
    echo "✅ 没有更改需要提交"
else
    # 提交
    echo "💾 提交更改..."
    git commit -m "Update: $(date +'%Y-%m-%d %H:%M') - 自动更新实时数据"
    
    # 推送
    echo "📤 推送到 GitHub..."
    git push -u origin main || git push origin main
fi

echo ""
echo "✅ 部署完成！"
echo "🌐 访问：https://HILONG812.github.io/daily-trading-strategy/"
echo ""
