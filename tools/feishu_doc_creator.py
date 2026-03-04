"""
飞书文档创建工具
使用完整 API 创建多 block 文档，支持正常字体
"""

import requests
import json
import os

# 飞书 API 配置
BASE_URL = "https://open.feishu.cn/open-apis"

def get_access_token():
    """获取飞书 access token"""
    # 需要从环境变量或配置文件读取 app_id 和 app_secret
    app_id = os.getenv("FEISHU_APP_ID", "")
    app_secret = os.getenv("FEISHU_APP_SECRET", "")
    
    if not app_id or not app_secret:
        print("⚠️ 未配置 FEISHU_APP_ID 和 FEISHU_APP_SECRET")
        return None
    
    url = f"{BASE_URL}/auth/v3/tenant_access_token/internal"
    payload = {
        "app_id": app_id,
        "app_secret": app_secret
    }
    
    response = requests.post(url, json=payload)
    result = response.json()
    
    if result.get("code") == 0:
        return result.get("tenant_access_token")
    else:
        print(f"获取 token 失败：{result}")
        return None


def create_document(title, access_token):
    """创建空文档"""
    url = f"{BASE_URL}/docx/v1/documents"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    payload = {
        "title": title
    }
    
    response = requests.post(url, headers=headers, json=payload)
    result = response.json()
    
    if result.get("code") == 0:
        doc_token = result["data"]["document"]["token"]
        print(f"✅ 创建文档成功：{doc_token}")
        return doc_token
    else:
        print(f"❌ 创建文档失败：{result}")
        return None


def create_text_block(doc_token, text, access_token, style="normal"):
    """创建文本块"""
    url = f"{BASE_URL}/docx/v1/documents/{doc_token}/blocks"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    # 字体样式映射
    style_map = {
        "normal": {"font_size": 11, "bold": False},  # 五号字
        "heading1": {"font_size": 22, "bold": True},  # 一号字
        "heading2": {"font_size": 18, "bold": True},  # 二号字
        "heading3": {"font_size": 16, "bold": True},  # 三号字
    }
    
    font_config = style_map.get(style, style_map["normal"])
    
    payload = {
        "parent_id": doc_token,
        "block_type": 1,  # 文本块
        "text": {
            "elements": [
                {
                    "text_run": {
                        "content": text,
                        "text_element_style": {
                            "font_size": font_config["font_size"],
                            "bold": font_config["bold"]
                        }
                    }
                }
            ]
        }
    }
    
    response = requests.post(url, headers=headers, json=payload)
    result = response.json()
    
    if result.get("code") == 0:
        block_id = result["data"]["block"]["block_id"]
        return block_id
    else:
        print(f"❌ 创建块失败：{text[:50]}... - {result}")
        return None


def create_divider_block(doc_token, access_token):
    """创建分割线"""
    url = f"{BASE_URL}/docx/v1/documents/{doc_token}/blocks"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "parent_id": doc_token,
        "block_type": 7  # 分割线
    }
    
    response = requests.post(url, headers=headers, json=payload)
    result = response.json()
    
    if result.get("code") == 0:
        return result["data"]["block"]["block_id"]
    else:
        print(f"❌ 创建分割线失败：{result}")
        return None


def build_document_from_md(doc_token, md_content, access_token):
    """从 markdown 内容构建文档"""
    lines = md_content.split("\n")
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # 判断行类型
        if line.startswith("# "):
            # 一级标题
            create_text_block(doc_token, line[2:], access_token, "heading1")
        elif line.startswith("## "):
            # 二级标题
            create_text_block(doc_token, line[3:], access_token, "heading2")
        elif line.startswith("### "):
            # 三级标题
            create_text_block(doc_token, line[4:], access_token, "heading3")
        elif line.startswith("---"):
            # 分割线
            create_divider_block(doc_token, access_token)
        else:
            # 普通文本
            create_text_block(doc_token, line, access_token, "normal")
    
    print(f"✅ 文档构建完成")


if __name__ == "__main__":
    # 示例：创建文档
    token = get_access_token()
    if token:
        doc_token = create_document("测试文档", token)
        if doc_token:
            # 添加内容
            create_text_block(doc_token, "这是标题", token, "heading1")
            create_text_block(doc_token, "这是正文内容，使用正常字体（五号字）", token, "normal")
            create_divider_block(doc_token, token)
            create_text_block(doc_token, "分割线下面的内容", token, "normal")
            
            print(f"文档链接：https://feishu.cn/docx/{doc_token}")
