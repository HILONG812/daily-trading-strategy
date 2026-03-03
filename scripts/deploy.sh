#!/bin/bash
# GitHub Pages 部署脚本

cd /root/.openclaw/workspace

# 复制最新网页到 GitHub 目录
cp docs/index.html trading.html

echo "✅ 网页已更新：trading.html"
echo "📄 下次推送时请使用:"
echo "   git add trading.html"
echo "   git commit -m '📊 更新研报'"
echo "   git push origin main"
