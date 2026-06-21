"""
API 服务 - 供前端调用
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import sys
import base64
from io import BytesIO

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.prompt_builder import (
    parse_input, build_prompt, generate_image,
    TEMPLATES, MODEL_CONFIGS, get_video_keywords, get_3d_keywords,
    build_video_prompt, build_3d_prompt
)

app = Flask(__name__)
CORS(app)  # 允许跨域

# 配置
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)


@app.route('/api/parse', methods=['POST'])
def api_parse():
    """解析 prompt"""
    data = request.json
    text = data.get('text', '')
    mode = data.get('mode', 'image')
    
    try:
        if mode == 'video':
            prompt = build_video_prompt(text)
        elif mode == '3d':
            prompt = build_3d_prompt(text)
        else:
            parsed = parse_input(text, ask_clarification=False)
            prompt = build_prompt(parsed)
        
        return jsonify({'success': True, 'prompt': prompt})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/generate', methods=['POST'])
def api_generate():
    """生成图片"""
    data = request.json
    prompt = data.get('prompt', '')
    model = data.get('model', 'stabilityai/sdxl-turbo')
    steps = data.get('steps', 4)
    size = data.get('size', 512)
    
    try:
        output_path = generate_image(
            prompt=prompt,
            steps=steps,
            width=size,
            height=size,
            model_name=model
        )
        
        if output_path:
            # 读取图片并转换为 base64
            with open(output_path, 'rb') as f:
                img_base64 = base64.b64encode(f.read()).decode('utf-8')
            
            return jsonify({
                'success': True,
                'image': img_base64,
                'path': output_path
            })
        else:
            return jsonify({'success': False, 'error': '生成失败'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/templates')
def api_templates():
    """获取模板列表"""
    template_list = []
    for key, template in TEMPLATES.items():
        template_list.append({
            'key': key,
            'label': template['label'],
            'category': template.get('category', '其他')
        })
    return jsonify({'templates': template_list})


@app.route('/api/models')
def api_models():
    """获取模型列表"""
    model_list = []
    for key, config in MODEL_CONFIGS.items():
        model_list.append({
            'key': key,
            'name': config['name'],
            'settings': config.get('recommended_settings', {})
        })
    return jsonify({'models': model_list})


@app.route('/api/upscale', methods=['POST'])
def api_upscale():
    """放大图片"""
    data = request.json
    image_path = data.get('image_path', '')
    scale = data.get('scale', 2)
    method = data.get('method', 'bicubic')
    
    try:
        from src.adapters.upscaler import upscaler
        
        if not os.path.exists(image_path):
            return jsonify({'success': False, 'error': '图片文件不存在'})
        
        output_path = upscaler.upscale(
            image_path=image_path,
            scale=scale,
            method=method
        )
        
        if output_path:
            # 读取图片并转换为 base64
            with open(output_path, 'rb') as f:
                img_base64 = base64.b64encode(f.read()).decode('utf-8')
            
            return jsonify({
                'success': True,
                'image': img_base64,
                'path': output_path,
                'scale': scale
            })
        else:
            return jsonify({'success': False, 'error': '放大失败'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/styles')
def api_styles():
    """获取可用风格列表"""
    from src.adapters.style_transfer import style_transfer
    return jsonify({'styles': style_transfer.get_available_styles()})


@app.route('/api/style', methods=['POST'])
def api_style():
    """风格迁移"""
    data = request.json
    image_path = data.get('image_path', '')
    style = data.get('style', 'oil_painting')
    intensity = data.get('intensity', 1.0)
    
    try:
        from src.adapters.style_transfer import style_transfer
        
        if not os.path.exists(image_path):
            return jsonify({'success': False, 'error': '图片文件不存在'})
        
        output_path = style_transfer.transfer(
            image_path=image_path,
            style=style,
            intensity=intensity
        )
        
        if output_path:
            # 读取图片并转换为 base64
            with open(output_path, 'rb') as f:
                img_base64 = base64.b64encode(f.read()).decode('utf-8')
            
            return jsonify({
                'success': True,
                'image': img_base64,
                'path': output_path,
                'style': style
            })
        else:
            return jsonify({'success': False, 'error': '风格迁移失败'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


if __name__ == '__main__':
    print("=" * 50)
    print("  CPU Image Gen API Server")
    print("  访问 http://localhost:8000")
    print("=" * 50)
    app.run(debug=True, host='0.0.0.0', port=8000)
