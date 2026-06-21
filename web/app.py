"""
Web UI - 简单的图形界面
"""

from flask import Flask, render_template, request, jsonify, send_file
import os
import sys
import time
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

# 配置
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)


@app.route('/')
def index():
    """主页"""
    return render_template('index.html',
                         templates=TEMPLATES,
                         models=MODEL_CONFIGS)


@app.route('/api/parse', methods=['POST'])
def api_parse():
    """解析 prompt"""
    data = request.json
    text = data.get('text', '')
    mode = data.get('mode', 'image')
    
    try:
        if mode == 'video':
            video_kw = get_video_keywords()
            prompt = build_video_prompt(text)
            return jsonify({'success': True, 'prompt': prompt})
        elif mode == '3d':
            prompt = build_3d_prompt(text)
            return jsonify({'success': True, 'prompt': prompt})
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


@app.route('/output/<filename>')
def serve_output(filename):
    """提供生成的图片"""
    return send_file(os.path.join(OUTPUT_DIR, filename))


if __name__ == '__main__':
    print("=" * 50)
    print("  CPU Image Gen Web UI")
    print("  访问 http://localhost:5000")
    print("=" * 50)
    app.run(debug=True, host='0.0.0.0', port=5000)
