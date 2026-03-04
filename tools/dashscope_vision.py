"""
DashScope 视觉识别工具
支持图片理解、OCR、图表分析
"""

import dashscope
from dashscope import MultiModalConversation

def analyze_image(image_path, api_key, prompt="请分析这张图片的内容"):
    """
    分析图片内容
    
    参数:
        image_path: 图片文件路径
        api_key: DashScope API Key
        prompt: 分析问题
    
    返回:
        分析结果文本
    """
    try:
        dashscope.api_key = api_key
        
        # 构建请求
        messages = [{
            'role': 'user',
            'content': [
                {'image': image_path},
                {'text': prompt}
            ]
        }]
        
        # 调用 qwen-vl-max 模型
        response = MultiModalConversation.call(
            model='qwen-vl-max',
            messages=messages
        )
        
        if response.status_code == 200:
            return {
                'success': True,
                'text': response.output.choices[0].message.content[0]['text']
            }
        else:
            return {
                'success': False,
                'error': f"API 错误：{response.code} - {response.message}"
            }
            
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


# 测试示例
if __name__ == "__main__":
    import os
    api_key = os.getenv('DASHSCOPE_API_KEY', 'YOUR_API_KEY')
    
    test_image = '/root/.openclaw/media/inbound/test.jpg'
    result = analyze_image(test_image, api_key, "这张图片里有什么股票信息？")
    
    if result['success']:
        print(result['text'])
    else:
        print(f"识别失败：{result['error']}")