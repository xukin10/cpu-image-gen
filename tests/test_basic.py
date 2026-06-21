"""
基础测试 - 验证模块导入和基本功能
"""

import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_imports():
    """测试模块导入"""
    try:
        from src import parse_input, build_prompt
        from src import TEMPLATES, TEMPLATE_CATEGORIES
        from src import CULTURAL_ENTITIES, ENTITY_KEYWORDS
        from src import MODEL_CONFIGS
        print("✓ 所有模块导入成功")
        return True
    except ImportError as e:
        print(f"✗ 导入失败: {e}")
        return False


def test_parse_input():
    """测试输入解析"""
    from src import parse_input, build_prompt
    
    test_cases = [
        "赛博朋克城市夜景",
        "中国龙 在云端",
        "樱花 日落",
    ]
    
    print("\n测试输入解析：")
    for text in test_cases:
        parsed = parse_input(text, ask_clarification=False)
        prompt = build_prompt(parsed)
        print(f"  {text} → {prompt[:50]}...")
    
    print("✓ 输入解析测试通过")
    return True


def test_templates():
    """测试模板系统"""
    from src import TEMPLATES, generate_prompt_from_template
    
    print(f"\n✓ 模板系统：{len(TEMPLATES)} 个模板可用")
    return True


def test_cultural_entities():
    """测试文化实体"""
    from src import CULTURAL_ENTITIES
    
    print(f"✓ 文化实体：{len(CULTURAL_ENTITIES)} 个实体可用")
    return True


def test_model_configs():
    """测试模型配置"""
    from src import MODEL_CONFIGS
    
    print(f"✓ 模型配置：{len(MODEL_CONFIGS)} 个模型可用")
    return True


if __name__ == "__main__":
    print("=" * 50)
    print("  CPU Image Gen 测试")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_parse_input,
        test_templates,
        test_cultural_entities,
        test_model_configs,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"✗ {test.__name__} 失败: {e}")
            failed += 1
    
    print("\n" + "=" * 50)
    print(f"  测试结果: {passed} 通过, {failed} 失败")
    print("=" * 50)
