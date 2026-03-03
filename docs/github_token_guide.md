# GitHub Token 配置指南

## 为什么需要 Token

GitHub 从 2021 年起不再支持密码推送，必须使用 Personal Access Token。

---

## 创建 Token 步骤

### 1. 访问 Token 页面
https://github.com/settings/tokens

### 2. 选择 Token 类型
点击 **"Generate new token (classic)"**

### 3. 填写信息
- **Note**: `OpenClaw Server`
- **Expiration**: `No expiration` (或自定义)

### 4. 选择权限 (Scopes)
勾选以下权限:
- ✅ `repo` (完整仓库权限)
- ✅ `workflow` (GitHub Actions)

### 5. 生成 Token
点击 **"Generate token"**

### 6. 复制 Token
格式：`ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

⚠️ **重要**: Token 只显示一次，立即复制保存！

---

## 配置 Token

### 方法 A: 环境变量 (推荐)
```bash
export GITHUB_TOKEN="ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

### 方法 B: 写入配置文件
```bash
echo 'export GITHUB_TOKEN="ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"' >> ~/.bashrc
source ~/.bashrc
```

### 方法 C: 直接给 AI
在飞书回复 Token，我会立即使用并销毁记录

---

## 验证 Token
```bash
curl -H "Authorization: token YOUR_TOKEN" https://api.github.com/user
```

成功返回用户信息即表示 Token 有效。

---

## 安全提醒

1. Token = 密码，不要分享给他人
2. 建议设置过期时间 (90 天)
3. 定期轮换 Token
4. 泄露后立即撤销

---

更新时间：2026-03-04
