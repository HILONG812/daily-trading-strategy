"""
CosyVoice 语音合成工具
阿里云 DashScope TTS
"""

import os
import dashscope
from dashscope.audio.tts_v2 import SpeechSynthesizer, ResultCallback, AudioFormat

class TTSCallback(ResultCallback):
    def __init__(self, output_file='output.mp3'):
        self.output_file = output_file
        self.file = None
    
    def on_open(self):
        self.file = open(self.output_file, 'wb')
        print('✅ 连接建立')
    
    def on_data(self, data: bytes):
        self.file.write(data)
    
    def on_complete(self):
        print('✅ 语音合成完成')
        self.file.close()
    
    def on_error(self, message):
        print(f'❌ 错误：{message}')
    
    def on_close(self):
        print('🔒 连接关闭')

def synthesize_speech(text, api_key, output_file='output.mp3', model='cosyvoice-v3-flash', voice='longanyang'):
    """
    语音合成
    
    参数:
        text: 待合成文本
        api_key: DashScope API Key
        output_file: 输出文件路径
        model: 模型名称
        voice: 音色名称
    
    返回:
        成功返回文件路径，失败返回错误信息
    """
    try:
        dashscope.api_key = api_key
        dashscope.base_websocket_api_url = 'wss://dashscope.aliyuncs.com/api-ws/v1/inference'
        
        callback = TTSCallback(output_file)
        
        synthesizer = SpeechSynthesizer(
            model=model,
            voice=voice,
            callback=callback,
        )
        
        synthesizer.call(text)
        
        return {'success': True, 'file': output_file}
        
    except Exception as e:
        return {'success': False, 'error': str(e)}

# 测试
if __name__ == '__main__':
    api_key = os.getenv('DASHSCOPE_API_KEY', 'sk-xxx')
    result = synthesize_speech('你好，这是语音合成测试', api_key)
    print(result)