"""
腾讯 OCR API 工具
用于图片文字识别（OCR）
"""

import base64
import json
from tencentcloud.common import credential
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
from tencentcloud.ocr.v20181119 import ocr_client, models

def ocr_image(image_path, secret_id, secret_key):
    """
    识别图片中的文字
    
    参数:
        image_path: 图片文件路径
        secret_id: 腾讯云 SecretId
        secret_key: 腾讯云 SecretKey
    
    返回:
        识别结果字典
    """
    try:
        # 读取图片并转 base64
        with open(image_path, 'rb') as f:
            image_base64 = base64.b64encode(f.read()).decode('utf-8')
        
        # 创建认证对象
        cred = credential.Credential(secret_id, secret_key)
        
        # 创建 OCR 客户端
        client = ocr_client.OcrClient(cred, "ap-guangzhou")
        
        # 创建请求
        req = models.GeneralBasicOCRRequest()
        params = {
            "ImageBase64": image_base64,
            "LanguageType": "zh"  # 中文识别
        }
        req.from_json_string(json.dumps(params))
        
        # 发送请求
        response = client.GeneralBasicOCR(req)
        
        # 解析结果
        result = {
            'success': True,
            'text_detections': []
        }
        
        for item in response.TextDetections:
            result['text_detections'].append({
                'text': item.DetectedText,
                'confidence': item.Confidence,
                'polygon': item.Polygon
            })
        
        return result
        
    except TencentCloudSDKException as err:
        return {
            'success': False,
            'error': str(err)
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


# 测试示例
if __name__ == "__main__":
    # 从环境变量或配置文件读取密钥
    import os
    secret_id = os.getenv('TENCENT_SECRET_ID', 'YOUR_SECRET_ID')
    secret_key = os.getenv('TENCENT_SECRET_KEY', 'YOUR_SECRET_KEY')
    
    # 测试图片
    test_image = '/root/.openclaw/media/inbound/test.jpg'
    
    result = ocr_image(test_image, secret_id, secret_key)
    print(json.dumps(result, indent=2, ensure_ascii=False))