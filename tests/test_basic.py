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


def test_empty_input():
    """测试空输入"""
    from src import parse_input, build_prompt
    
    parsed = parse_input("", ask_clarification=False)
    prompt = build_prompt(parsed)
    
    assert prompt, "空输入应该生成默认 prompt"
    print("✓ 空输入测试通过")
    return True


def test_cultural_context():
    """测试文化上下文检测"""
    from src import parse_input
    
    # 测试中文文化上下文
    parsed = parse_input("中国龙", ask_clarification=False)
    assert parsed.get("cultural_context") == "chinese", "应该检测到中文文化上下文"
    
    # 测试日本文化上下文
    parsed = parse_input("日本武士刀", ask_clarification=False)
    assert parsed.get("cultural_context") == "japanese", "应该检测到日本文化上下文"
    
    # 测试西方文化上下文
    parsed = parse_input("西方骑士", ask_clarification=False)
    assert parsed.get("cultural_context") == "western", "应该检测到西方文化上下文"
    
    print("✓ 文化上下文测试通过")
    return True


def test_templates():
    """测试模板系统"""
    from src import TEMPLATES, generate_prompt_from_template
    
    print(f"\n✓ 模板系统：{len(TEMPLATES)} 个模板可用")
    
    # 测试模板生成
    if "portrait" in TEMPLATES:
        template = TEMPLATES["portrait"]
        prompt = generate_prompt_from_template(template, "a young woman")
        assert "portrait" in prompt.lower(), "模板应该包含 portrait"
        print("✓ 模板生成测试通过")
    
    return True


def test_cultural_entities():
    """测试文化实体"""
    from src import CULTURAL_ENTITIES, parse_input, build_prompt
    
    print(f"✓ 文化实体：{len(CULTURAL_ENTITIES)} 个实体可用")
    
    # 测试文化实体解析
    parsed = parse_input("中国龙 在云端", ask_clarification=False)
    assert parsed.get("resolved_entities"), "应该解析到文化实体"
    
    prompt = build_prompt(parsed)
    assert "Chinese dragon" in prompt, "应该包含 Chinese dragon"
    
    print("✓ 文化实体解析测试通过")
    return True


def test_model_configs():
    """测试模型配置"""
    from src import MODEL_CONFIGS, get_model_config
    
    print(f"✓ 模型配置：{len(MODEL_CONFIGS)} 个模型可用")
    
    # 测试获取模型配置
    config = get_model_config("stabilityai/sdxl-turbo")
    assert config, "应该返回模型配置"
    assert "recommended_settings" in config, "配置应该包含 recommended_settings"
    
    print("✓ 模型配置测试通过")
    return True


def test_multimodal():
    """测试多模态功能"""
    from src import build_video_prompt, build_3d_prompt, get_video_keywords, get_3d_keywords
    
    # 测试视频 prompt
    video_kw = get_video_keywords()
    assert video_kw, "应该有视频关键词"
    
    prompt = build_video_prompt("a dragon flying", motion="flying")
    assert "flying" in prompt, "应该包含动作"
    
    # 测试 3D prompt
    spatial_kw = get_3d_keywords()
    assert spatial_kw, "应该有 3D 关键词"
    
    prompt = build_3d_prompt("a sword", material="metallic material")
    assert "metallic" in prompt, "应该包含材质"
    
    print("✓ 多模态功能测试通过")
    return True


def test_prompt_length_control():
    """测试 prompt 长度控制"""
    from src.prompt_builder import CONFIG, _count_words, _trim_prompt
    from src import parse_input, build_prompt

    max_words = CONFIG.get("max_prompt_words", 45)

    # 测试 _count_words
    assert _count_words("a, b, c") == 3, "计数应正确"
    assert _count_words("") == 0, "空字符串返回 0"

    # 测试 _trim_prompt
    long_prompt = ", ".join([f"word{i}" for i in range(60)])
    trimmed = _trim_prompt(long_prompt, max_words)
    assert _count_words(trimmed) <= max_words, f"截断后应不超过 {max_words} 段"

    # 测试典型场景：复杂输入不应超过限制
    test_cases = [
        "赛博朋克城市夜景 霓虹灯 雨天 俯视 电影感 史诗 神秘",
        "中国龙 在云端 水墨 清晨 雾 逆光 精细 壮观",
        "战士 恶龙 战斗 中世纪城堡 史诗氛围 广角 逆光 高清",
    ]
    for text in test_cases:
        parsed = parse_input(text, ask_clarification=False)
        prompt = build_prompt(parsed)
        word_count = _count_words(prompt)
        assert word_count <= max_words, \
            f"Prompt ({word_count}段) 超过限制 ({max_words}段): {text}"
        assert prompt, "Prompt 不应为空"

    print(f"✓ Prompt 长度控制测试通过 (限制 {max_words} 段)")
    return True


def test_error_handling():
    """测试错误处理"""
    from src.prompt_builder import safe_load_json, _count_words
    
    # 测试文件不存在
    try:
        safe_load_json("nonexistent.json")
        print("✗ 应该抛出 FileNotFoundError")
        return False
    except FileNotFoundError:
        pass
    
    # 测试 JSON 格式错误
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write("invalid json")
        temp_path = f.name
    
    try:
        safe_load_json(temp_path)
        print("✗ 应该抛出 ValueError")
        return False
    except ValueError:
        pass
    finally:
        os.unlink(temp_path)
    
    print("✓ 错误处理测试通过")
    return True


if __name__ == "__main__":
    print("=" * 50)
    print("  CPU Image Gen 测试")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_parse_input,
        test_empty_input,
        test_cultural_context,
        test_templates,
        test_cultural_entities,
        test_model_configs,
        test_multimodal,
        test_prompt_length_control,
        test_error_handling,
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
