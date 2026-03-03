# 腾讯 OCR API 配置

## API 信息
- 服务商：腾讯云 OCR
- 接口：通用文字识别（高精度版）
- 文档：https://cloud.tencent.com/document/product/866

## 认证信息
需要在 TOOLS.md 或环境变量中配置：
- TENCENT_SECRET_ID
- TENCENT_SECRET_KEY

## 使用方式

### Python 调用示例
```python
import requests
import base64
import hmac
import hashlib
import time

def tencent_ocr(image_path, secret_id, secret_key):
    # 读取图片并转 base64
    with open(image_path, 'rb') as f:
        image_base64 = base64.b64encode(f.read()).decode('utf-8')
    
    # 构建请求
    endpoint = "ocr.tencentcloudapi.com"
    action = "GeneralBasicOCR"
    version = "2018-11-19"
    region = "ap-guangzhou"
    
    # 简化版（实际需要用 TC3-HMAC-SHA256 签名）
    url = f"https://{endpoint}"
    headers = {
        "Content-Type": "application/json",
        "X-TC-Action": action,
        "X-TC-Version": version,
        "X-TC-Region": region,
    }
    
    payload = {
        "ImageBase64": image_base64,
        "LanguageType": "zh"  # 中文识别
    }
    
    response = requests.post(url, json=payload, headers=headers)
    return response.json()
```

## 免费额度
- 每月 1000 次免费调用
- 超出后：0.005 元/次

## 支持功能
- 中文 OCR（简体/繁体）
- 英文 OCR
- 数字识别
- 表格识别
- 手写体识别

---

更新时间：2026-03-03 19:38