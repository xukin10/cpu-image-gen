"""
基础示例 - 使用 CPU Image Gen 生成图片
"""

import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src import parse_input, build_prompt, generate_image


def example_basic():
    """基础示例：一句话生成图片"""
    print("=" * 50)
    print("  基础示例：一句话生成图片")
    print("=" * 50)
    
    text = "赛博朋克城市夜景，雨天霓虹灯"
    print(f"\n输入: {text}")
    
    parsed = parse_input(text, ask_clarification=False)
    prompt = build_prompt(parsed)
    print(f"生成的 prompt: {prompt}")
    
    # 生成图片（取消注释下面的代码来实际生成）
    # generate_image(prompt, raw_input=text)


def example_cultural():
    """文化实体示例"""
    print("\n" + "=" * 50)
    print("  文化实体示例")
    print("=" * 50)
    
    test_cases = [
        "中国龙 在云端",
        "西方龙 在洞穴",
        "日本九尾狐 神社",
        "樱花 日落",
    ]
    
    for text in test_cases:
        parsed = parse_input(text, ask_clarification=False)
        prompt = build_prompt(parsed)
        print(f"\n输入: {text}")
        print(f"输出: {prompt}")


def example_template():
    """模板示例"""
    print("\n" + "=" * 50)
    print("  模板示例")
    print("=" * 50)
    
    from src import TEMPLATES, generate_prompt_from_template
    
    templates_to_test = ["portrait", "landscape", "anime"]
    
    for tpl_key in templates_to_test:
        if tpl_key in TEMPLATES:
            template = TEMPLATES[tpl_key]
            prompt = generate_prompt_from_template(template, "a beautiful scene")
            print(f"\n模板: {template['label']}")
            print(f"输出: {prompt}")


if __name__ == "__main__":
    example_basic()
    example_cultural()
    example_template()
    
    print("\n" + "=" * 50)
    print("  示例完成！")
    print("  取消注释 generate_image() 来实际生成图片")
    print("=" * 50)
