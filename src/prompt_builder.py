"""
CPU Image Gen - 自然语言 Prompt 架构
用自然语言描述需求，自动构建 AI 生图 prompt

支持：
- 中文自然语言输入
- 70 个文化实体（中国/日本/西方/希腊/北欧/埃及）
- 24 个场景模板
- 5 个模型适配（SDXL/SD3/Flux）
- 视频/3D prompt 生成
- 高级品质优化
"""

from diffusers import AutoPipelineForText2Image
import torch
import time
import os
import re
import json
import sys
import argparse
import logging
from typing import Dict, List, Optional, Tuple, Any
from tqdm import tqdm

# ============================================================
# 日志配置
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================
# 路径配置
# ============================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIGS_DIR = os.path.join(BASE_DIR, "configs")

# ============================================================
# 安全的文件加载
# ============================================================

def safe_load_json(file_path: str) -> Dict:
    """安全加载 JSON 文件，带有错误处理"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"配置文件不存在: {file_path}")
        raise FileNotFoundError(f"配置文件不存在: {file_path}。请确保项目结构完整。")
    except json.JSONDecodeError as e:
        logger.error(f"JSON 解析错误: {file_path} - {e}")
        raise ValueError(f"配置文件格式错误: {file_path}。请检查 JSON 格式。")
    except Exception as e:
        logger.error(f"加载配置文件失败: {file_path} - {e}")
        raise

# ============================================================
# 加载关键词映射表
# ============================================================

KEYWORDS_PATH = os.path.join(CONFIGS_DIR, "keywords.json")

def load_keywords() -> Dict:
    return safe_load_json(KEYWORDS_PATH)

KEYWORDS = load_keywords()

STYLE_MAP = KEYWORDS["style"]
TIME_MAP = KEYWORDS["time"]
PLACE_MAP = KEYWORDS["place"]
WEATHER_MAP = KEYWORDS["weather"]
LIGHT_MAP = KEYWORDS["light"]
VIEW_MAP = KEYWORDS["view"]
QUALITY_MAP = KEYWORDS["quality"]
ARTIST_MAP = KEYWORDS.get("artist", {})
MATERIAL_MAP = KEYWORDS.get("material", {})
MOOD_MAP = KEYWORDS.get("mood", {})
CN_TO_EN = KEYWORDS["subject_cn_to_en"]

ALL_MAPS = [STYLE_MAP, TIME_MAP, PLACE_MAP, WEATHER_MAP, LIGHT_MAP, VIEW_MAP, QUALITY_MAP, ARTIST_MAP, MATERIAL_MAP, MOOD_MAP]

# ============================================================
# 加载场景模板
# ============================================================

TEMPLATES_PATH = os.path.join(CONFIGS_DIR, "templates.json")

def load_templates() -> Dict:
    return safe_load_json(TEMPLATES_PATH)

TEMPLATES = load_templates()

TEMPLATE_CATEGORIES = {}
for key, template in TEMPLATES.items():
    cat = template.get("category", "其他")
    if cat not in TEMPLATE_CATEGORIES:
        TEMPLATE_CATEGORIES[cat] = []
    TEMPLATE_CATEGORIES[cat].append((key, template["label"]))

# ============================================================
# 加载文化实体库
# ============================================================

CULTURAL_PATH = os.path.join(CONFIGS_DIR, "cultural_entities.json")

def load_cultural_entities() -> Dict:
    return safe_load_json(CULTURAL_PATH)

CULTURAL_ENTITIES = load_cultural_entities()

CULTURAL_MARKERS = {
    "chinese": ["中国", "中式", "国风", "东方", "传统", "华夏", "汉"],
    "western": ["西方", "欧式", "西式", "西洋", "classic", "欧美"],
    "japanese": ["日本", "日式", "和风", "和", "东瀛"],
}

ENTITY_KEYWORDS = {
    "九尾狐": "nine_tailed_fox",
    "中国剑": "sword",
    "日本刀": "sword",
    "武士刀": "sword",
    "西洋剑": "sword",
    "中国铠甲": "armor",
    "日本铠甲": "armor",
    "西方铠甲": "armor",
    "中国盾": "shield",
    "西方盾": "shield",
    "中国法杖": "staff",
    "西方法杖": "staff",
    "天狗": "tengu",
    "饕餮": "taotie",
    "龙龟": "dragon_turtle",
    "穷奇": "qiongqi",
    "混沌": "hundun",
    "木乃伊": "mummy",
    "女巫": "witch",
    "巫师": "wizard",
    "海妖": "siren",
    "半人马": "centaur",
    "美杜莎": "medusa",
    "米诺陶": "minotaur",
    "狮鹫": "griffin",
    "巨人": "giant",
    "观音": "guanyin",
    "雅典娜": "athena",
    "洛基": "loki",
    "宙斯": "zeus",
    "阿波罗": "apollo",
    "阿瑞斯": "ares",
    "波塞冬": "poseidon",
    "哈迪斯": "hades",
    "托尔": "thor",
    "奥丁": "odin",
    "弗雷亚": "freya",
    "蚩尤": "chiyou",
    "盘古": "pangu",
    "女娲": "nuwa",
    "伏羲": "fuxi",
    "神农": "shennong",
    "美人鱼": "mermaid",
    "狼人": "werewolf",
    "吸血鬼": "vampire",
    "丧尸": "zombie",
    "机器人": "robot",
    "江南水乡": "jiangnan",
    "敦煌": "dunhuang",
    "京都": "kyoto",
    "奥林匹斯山": "olympus",
    "阿斯加德": "asgard",
    "地狱": "hell",
    "天堂": "heaven",
    "魔法森林": "enchanted_forest",
    "龙": "dragon",
    "凤凰": "phoenix",
    "独角兽": "unicorn",
    "精灵": "elf",
    "恶魔": "demon",
    "天使": "angel",
    "樱花": "sakura",
    "樱花树": "cherry_blossom_tree",
    "梅花": "plum_blossom",
    "菊花": "chrysanthemum",
    "莲花": "lotus",
    "竹": "bamboo",
    "松树": "pine",
    "柳树": "willow",
    "银杏": "ginkgo",
    "枫叶": "maple",
    "中国建筑": "chinese_architecture",
    "日本建筑": "japanese_architecture",
    "机甲": "mecha",
    "铠甲": "armor",
    "弓": "bow",
    "盾": "shield",
    "法杖": "staff",
    "城堡": "castle",
    "塔": "tower",
    "剑": "sword",
    "刀": "sword",
}

# ============================================================
# 加载五维词汇库
# ============================================================

VOCABULARY_PATH = os.path.join(CONFIGS_DIR, "vocabulary.json")

def load_vocabulary() -> Dict:
    return safe_load_json(VOCABULARY_PATH)

VOCABULARY = load_vocabulary()

# 五维关键词映射
NARRATIVE_MAP = VOCABULARY.get("categories", {}).get("narrative", {}).get("words", {})
APPEARANCE_MAP = VOCABULARY.get("categories", {}).get("appearance", {}).get("words", {})
ACTION_MAP = VOCABULARY.get("categories", {}).get("action", {}).get("words", {})
PHYSICS_MAP = VOCABULARY.get("categories", {}).get("physics", {}).get("words", {})
ENVIRONMENT_MAP = VOCABULARY.get("categories", {}).get("environment", {}).get("words", {})
LENS_MAP = VOCABULARY.get("categories", {}).get("lens", {}).get("words", {})
DOF_MAP = VOCABULARY.get("categories", {}).get("depth_of_field", {}).get("words", {})
ANGLE_MAP = VOCABULARY.get("categories", {}).get("angle", {}).get("words", {})
ASPECT_MAP = VOCABULARY.get("categories", {}).get("aspect_ratio", {}).get("words", {})
COLOR_MOOD_MAP = VOCABULARY.get("categories", {}).get("color_mood", {}).get("words", {})
ATMOSPHERE_MAP = VOCABULARY.get("categories", {}).get("atmosphere_effect", {}).get("words", {})

ALL_FIVE_DIM_MAPS = [NARRATIVE_MAP, APPEARANCE_MAP, ACTION_MAP, PHYSICS_MAP, 
                     ENVIRONMENT_MAP, LENS_MAP, DOF_MAP, ANGLE_MAP, ASPECT_MAP,
                     COLOR_MOOD_MAP, ATMOSPHERE_MAP]

MODEL_CONFIGS_PATH = os.path.join(CONFIGS_DIR, "model_configs.json")

def load_model_configs() -> Dict:
    return safe_load_json(MODEL_CONFIGS_PATH)

MODEL_CONFIGS = load_model_configs()

def get_model_config(model_name: str) -> Dict:
    return MODEL_CONFIGS.get(model_name, MODEL_CONFIGS.get("stabilityai/sdxl-turbo"))

def adapt_prompt_for_model(prompt: str, model_name: str) -> str:
    config = get_model_config(model_name)
    return prompt

# ============================================================
# 加载多模态配置
# ============================================================

MULTIMODAL_PATH = os.path.join(CONFIGS_DIR, "multimodal_configs.json")

def load_multimodal_configs() -> Dict:
    return safe_load_json(MULTIMODAL_PATH)

MULTIMODAL_CONFIGS = load_multimodal_configs()

def get_video_keywords() -> Dict:
    return MULTIMODAL_CONFIGS.get("video", {}).get("temporal_keywords", {})

def get_3d_keywords() -> Dict:
    return MULTIMODAL_CONFIGS.get("3d", {}).get("spatial_keywords", {})

def build_video_prompt(base_prompt: str, motion: str = None, camera: str = None, 
                       temporal: str = None, transition: str = None) -> str:
    parts = [base_prompt]
    if motion: parts.append(motion)
    if camera: parts.append(camera)
    if temporal: parts.append(temporal)
    if transition: parts.append(transition)
    return ", ".join(parts)

def build_3d_prompt(base_prompt: str, material: str = None, lighting: str = None,
                    view: str = None, render_style: str = None) -> str:
    parts = [base_prompt]
    if material: parts.append(material)
    if lighting: parts.append(lighting)
    if view: parts.append(view)
    if render_style: parts.append(render_style)
    return ", ".join(parts)

# ============================================================
# 加载配置
# ============================================================

CONFIG_PATH = os.path.join(CONFIGS_DIR, "config.json")

def load_config() -> Dict:
    return safe_load_json(CONFIG_PATH)

CONFIG = load_config()

# ============================================================
# 文化上下文检测与实体解析
# ============================================================

def detect_cultural_context(text: str) -> Optional[str]:
    for culture, markers in CULTURAL_MARKERS.items():
        if any(m in text for m in markers):
            return culture
    return None

def find_entities_in_text(text: str) -> List[Tuple[str, str]]:
    found = []
    matched_entities = set()
    for keyword, entity_key in ENTITY_KEYWORDS.items():
        if keyword in text:
            if entity_key in matched_entities:
                continue
            found = [(k, e) for k, e in found if e != entity_key]
            found.append((keyword, entity_key))
            matched_entities.add(entity_key)
    return found

def resolve_entity(entity_key: str, cultural_context: str = None) -> Optional[Dict]:
    entity = CULTURAL_ENTITIES.get(entity_key)
    if not entity:
        return None
    variants = entity.get("variants", {})
    if cultural_context and cultural_context in variants:
        return variants[cultural_context]
    if len(variants) == 1:
        return list(variants.values())[0]
    return {"all_variants": variants, "label": entity.get("label", entity_key)}

def ask_cultural_clarification(entity_label: str, variants: Dict) -> Optional[Dict]:
    print(f"\n>> 检测到「{entity_label}」，请问是哪种类型？")
    variant_list = list(variants.items())
    for i, (key, variant) in enumerate(variant_list, 1):
        desc = variant.get("name_en", key)
        print(f"  [{i}] {desc}")
    choice = input(">> 请选择 (数字，直接回车跳过): ").strip()
    if choice.isdigit() and 1 <= int(choice) <= len(variant_list):
        return variant_list[int(choice) - 1][1]
    return None

# ============================================================
# 生成历史记录
# ============================================================

HISTORY_PATH = os.path.join(BASE_DIR, "history.log")

def log_generation(raw_input: str, prompt: str, output_path: str, elapsed: float):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {elapsed:.1f}s | {raw_input} → {prompt} | {output_path}\n"
    with open(HISTORY_PATH, "a", encoding="utf-8") as f:
        f.write(log_entry)

# ============================================================
# 自然语言解析器
# ============================================================

def parse_input(text: str, ask_clarification: bool = True) -> Dict:
    """解析用户输入，提取各层关键词"""
    result = {
        "subject": "",
        "style": [],
        "time": [],
        "place": [],
        "weather": [],
        "light": [],
        "view": [],
        "quality": ["highly detailed"],
        "artist": [],
        "material": [],
        "mood": [],
        "raw": text,
        "cultural_context": None,
        "resolved_entities": [],
        # 五维关键词
        "narrative": [],
        "appearance": [],
        "action": [],
        "physics": [],
        "environment": [],
        "lens": [],
        "dof": [],
        "angle": [],
        "aspect": [],
        "color_mood": [],
        "atmosphere": [],
    }

    result["cultural_context"] = detect_cultural_context(text)

    found_entities = find_entities_in_text(text)
    for keyword, entity_key in found_entities:
        resolved = resolve_entity(entity_key, result["cultural_context"])
        if resolved:
            if "all_variants" in resolved:
                if ask_clarification:
                    clarified = ask_cultural_clarification(resolved["label"], resolved["all_variants"])
                    if clarified:
                        result["resolved_entities"].append(clarified)
                    else:
                        first_variant = list(resolved["all_variants"].values())[0]
                        result["resolved_entities"].append(first_variant)
                else:
                    first_variant = list(resolved["all_variants"].values())[0]
                    result["resolved_entities"].append(first_variant)
            else:
                result["resolved_entities"].append(resolved)

    for key, value in STYLE_MAP.items():
        if key in text: result["style"].append(value)
    for key, value in TIME_MAP.items():
        if key in text: result["time"].append(value)
    for key, value in PLACE_MAP.items():
        if key in text: result["place"].append(value)
    for key, value in WEATHER_MAP.items():
        if key in text: result["weather"].append(value)
    for key, value in LIGHT_MAP.items():
        if key in text: result["light"].append(value)
    for key, value in VIEW_MAP.items():
        if key in text: result["view"].append(value)
    for key, value in QUALITY_MAP.items():
        if key in text: result["quality"].append(value)
    for key, value in ARTIST_MAP.items():
        if key in text: result["artist"].append(value)
    for key, value in MATERIAL_MAP.items():
        if key in text: result["material"].append(value)
    for key, value in MOOD_MAP.items():
        if key in text: result["mood"].append(value)
    
    # 五维关键词解析
    for key, value in NARRATIVE_MAP.items():
        if key in text: result["narrative"].append(value)
    for key, value in APPEARANCE_MAP.items():
        if key in text: result["appearance"].append(value)
    for key, value in ACTION_MAP.items():
        if key in text: result["action"].append(value)
    for key, value in PHYSICS_MAP.items():
        if key in text: result["physics"].append(value)
    for key, value in ENVIRONMENT_MAP.items():
        if key in text: result["environment"].append(value)
    for key, value in LENS_MAP.items():
        if key in text: result["lens"].append(value)
    for key, value in DOF_MAP.items():
        if key in text: result["dof"].append(value)
    for key, value in ANGLE_MAP.items():
        if key in text: result["angle"].append(value)
    for key, value in ASPECT_MAP.items():
        if key in text: result["aspect"].append(value)
    for key, value in COLOR_MOOD_MAP.items():
        if key in text: result["color_mood"].append(value)
    for key, value in ATMOSPHERE_MAP.items():
        if key in text: result["atmosphere"].append(value)

    if not result.get("resolved_entities"):
        subject_raw = text
        # 第1步：先从原文中做 CN_TO_EN + PLACE 最长匹配（作为主体）
        en_parts = []
        # CN_TO_EN 多字词
        cn_keys = sorted(
            [k for k in CN_TO_EN.keys() if len(k) > 1 and k in subject_raw],
            key=len, reverse=True
        )
        remaining = subject_raw
        for cn in cn_keys:
            if cn in remaining:
                val = CN_TO_EN[cn]
                if val:
                    en_parts.append(val)
                remaining = remaining.replace(cn, " ", 1)
        # PLACE 多字词（补充地点信息）
        place_keys = sorted(
            [k for k in PLACE_MAP.keys() if len(k) > 1 and k in remaining],
            key=len, reverse=True
        )
        for pk in place_keys:
            if pk in remaining:
                remaining = remaining.replace(pk, " ", 1)
        # 单字 CN_TO_EN
        for part in remaining.split():
            if len(part) == 1 and part in CN_TO_EN:
                en_parts.append(CN_TO_EN[part])

        if en_parts:
            # 有主体词：用 CN_TO_EN 结果
            subject = " ".join(en_parts)
            # 剩下的部分再去匹配修饰词（以 remaining 而非 text 为准）
            mod_text = remaining
        else:
            # 无主体词：从剩余原文匹配修饰词再回退
            subject = ""
            mod_text = subject_raw
            # 清理标点虚词
            subject = re.sub(r'[,，、。!！?？\s]+', ' ', subject_raw).strip()
            subject = re.sub(r'[的了在是和与有下上中里外一个两只三匹些种张台件面条颗瓶杯碗盘把]', ' ', subject)
            subject = re.sub(r'\s+', ' ', subject).strip()
            if not subject.strip():
                subject = "a scene"

        # 第2步：用剩余文字匹配修饰词（时间/天气/光影/质量等）
        if en_parts:  # 一次匹配过的修饰词不再从原文重复提取
            for key, val in TIME_MAP.items():
                if key in mod_text and val not in result["time"]:
                    result["time"].append(val)
            for key, val in PLACE_MAP.items():
                if key in mod_text and val not in result["place"]:
                    result["place"].append(val)
            for key, val in WEATHER_MAP.items():
                if key in mod_text and val not in result["weather"]:
                    result["weather"].append(val)
            # 保留原有的全量匹配结果（已在上面提取过）

        result["subject"] = subject
    else:
        result["subject"] = ""
    return result

# ============================================================
# 物理逻辑验证与效果限制
# ============================================================

# 物理冲突规则
PHYSICS_CONFLICTS = {
    "游泳": ["干燥", "干的"],
    "水中": ["干燥", "干的"],
    "雨中": ["干燥", "阳光明媚"],
    "火中": ["湿润", "水"],
    "太空": ["重力", "站立"],
}

# 特效最大数量
MAX_EFFECTS = 3

def validate_physics(parsed: Dict) -> List[str]:
    """验证物理逻辑，返回警告列表"""
    warnings = []
    
    action = " ".join(parsed.get("action", []))
    physics = " ".join(parsed.get("physics", []))
    
    for action_key, conflicts in PHYSICS_CONFLICTS.items():
        if action_key in action:
            for conflict in conflicts:
                if conflict in physics:
                    warnings.append(f"物理冲突: {action_key} 与 {conflict} 不兼容")
    
    return warnings

def limit_effects(parsed: Dict) -> Dict:
    """限制特效数量，避免过度叠加"""
    if len(parsed.get("atmosphere", [])) > MAX_EFFECTS:
        parsed["atmosphere"] = parsed["atmosphere"][:MAX_EFFECTS]
        logger.info(f"特效数量限制为 {MAX_EFFECTS} 个")
    return parsed

# ============================================================
# 模板选择与生成
# ============================================================

def select_template() -> Tuple[Optional[str], Optional[Dict]]:
    print("\n" + "=" * 50)
    print("  选择场景模板")
    print("=" * 50)
    
    cat_list = list(TEMPLATE_CATEGORIES.keys())
    for i, cat in enumerate(cat_list, 1):
        templates = TEMPLATE_CATEGORIES[cat]
        print(f"  [{i}] {cat} ({len(templates)}个)")
    
    print()
    cat_choice = input(">> 选择分类 (数字，直接回车跳过): ").strip()
    
    if not cat_choice or not cat_choice.isdigit():
        return None, None
    
    cat_idx = int(cat_choice) - 1
    if cat_idx < 0 or cat_idx >= len(cat_list):
        return None, None
    
    selected_cat = cat_list[cat_idx]
    templates = TEMPLATE_CATEGORIES[selected_cat]
    
    print(f"\n  {selected_cat} 类模板：")
    for i, (key, label) in enumerate(templates, 1):
        print(f"  [{i}] {label}")
    
    print()
    tpl_choice = input(">> 选择模板 (数字): ").strip()
    
    if not tpl_choice or not tpl_choice.isdigit():
        return None, None
    
    tpl_idx = int(tpl_choice) - 1
    if tpl_idx < 0 or tpl_idx >= len(templates):
        return None, None
    
    tpl_key, tpl_label = templates[tpl_idx]
    return tpl_key, TEMPLATES[tpl_key]

def generate_prompt_from_template(template: Dict, user_input: str) -> str:
    base = template.get("base_prompt", "{subject}")
    quality = template.get("quality_additions", [])
    composition = template.get("composition", "")
    lighting = template.get("lighting", "")
    
    prompt = base.replace("{subject}", user_input)
    if quality: prompt += ", " + ", ".join(quality[:3])
    if composition: prompt += ", " + composition
    if lighting: prompt += ", " + lighting
    prompt += ", highly detailed, 8k"
    
    return prompt

# ============================================================
# Prompt 构建（高级品质优化）
# ============================================================

def _count_words(prompt: str) -> int:
    """计算 prompt 中的单词数（按逗号分隔的段数估算 tokens）"""
    return len([w.strip() for w in prompt.split(",") if w.strip()])


def _trim_prompt(prompt: str, max_words: int) -> str:
    """
    按优先级截断 prompt → 保证不超过 max_words 段。

    SDXL 注意力窗口 ≈ 75 tokens，每段平均 1.5 tokens，
    45 段 ≈ 67 tokens，留 10% 余量。

    截断策略：从后往前丢弃（后面的通常是 P4/P3 低优先级补充词），
    保持前面的 P1/P2 核心词完整。
    """
    parts = [w.strip() for w in prompt.split(",") if w.strip()]
    if len(parts) <= max_words:
        return prompt

    original_count = len(parts)
    trimmed = parts[:max_words]
    # 确保以完整逗号段结尾（不截断词组中间）
    result = ", ".join(trimmed)
    logger.info(f"Prompt 截断: {original_count} → {max_words} 段 "
                f"({original_count - max_words} 段低优先级词被丢弃)")
    return result


def build_prompt(parsed: Dict) -> str:
    # 验证物理逻辑
    physics_warnings = validate_physics(parsed)
    if physics_warnings:
        for warning in physics_warnings:
            logger.warning(warning)

    # 限制特效数量
    parsed = limit_effects(parsed)

    # 使用关系系统检查冲突
    from src.utils.relationship import relationship_manager
    all_words = []
    if parsed.get("style"): all_words.extend(parsed["style"])
    if parsed.get("subject"): all_words.append(parsed["subject"])
    if parsed.get("mood"): all_words.extend(parsed["mood"])

    conflicts = relationship_manager.check_conflicts(all_words)
    if conflicts:
        for w1, w2, rel in conflicts:
            logger.warning(f"词汇冲突: {w1} <-> {w2}")

    # 获取协同词汇
    synergies = relationship_manager.find_synergies(all_words)
    synergy_words = []
    for s in synergies:
        if isinstance(s, list):
            synergy_words.extend(s)
        elif isinstance(s, str):
            synergy_words.append(s)

    # 检查风格组合是否匹配预定义组合
    style_combos = relationship_manager.config.get("style_combinations", {})
    matched_combo = None
    combined_style_keywords = []
    for combo_name, combo_data in style_combos.items():
        combo_kw = set(combo_data.get("keywords", []))
        matches = combo_kw & set(all_words)
        if len(matches) >= 2:
            matched_combo = combo_data
            combined_style_keywords = combo_data.get("keywords", [])
            break

    # ============================================================
    # 分层构建：P1(不可丢) → P2(尽量保留) → P3(可压缩) → P4(先丢弃)
    # ============================================================
    p1_parts = []  # 风格首词、主体、光影、视角
    p2_parts = []  # 时间、地点、天气、质量
    p3_parts = []  # 五维扩展、额外风格、艺术家、材质、情绪
    p4_parts = []  # 关系协同、场景丰富度、色彩调色板、构图建议

    exclude_words = []

    # ---- P1: 风格首词 ----
    if parsed["style"]:
        p1_parts.append(parsed["style"][0])

    # ---- P1: 主体 ----
    if parsed.get("resolved_entities"):
        for entity in parsed["resolved_entities"]:
            if "name_en" in entity: p1_parts.append(entity["name_en"])
            if "morphology" in entity: p3_parts.extend(entity["morphology"][:2])
            if "elements" in entity: p3_parts.extend(entity["elements"][:2])
            if "atmosphere" in entity: p3_parts.append(entity["atmosphere"][0])
            if "exclude" in entity: exclude_words.extend(entity["exclude"])
    else:
        p1_parts.append(parsed["subject"])

    # ---- P1: 光影（默认或指定） ----
    if parsed["light"]:
        p1_parts.append(", ".join(parsed["light"]))
    elif parsed["subject"]:
        subject_lower = parsed["subject"].lower()
        if any(k in subject_lower for k in ["horror", "abandoned", "dark"]):
            p1_parts.append("dim light, deep shadows, atmospheric fog")
        elif any(k in subject_lower for k in ["water", "ocean", "lake"]):
            p1_parts.append("sunlight reflections, caustics, shimmering light")
        elif any(k in subject_lower for k in ["flower", "garden", "spring"]):
            p1_parts.append("soft diffused light, gentle shadows")
        elif any(k in subject_lower for k in ["city", "cyber", "neon"]):
            p1_parts.append("neon glow, colorful reflections, urban lighting")
        elif any(k in subject_lower for k in ["mountain", "landscape", "valley"]):
            p1_parts.append("natural lighting, golden hour, atmospheric perspective")
        else:
            p1_parts.append("dramatic lighting, volumetric light")

    # ---- P1: 视角（默认或指定） ----
    if parsed["view"]:
        p1_parts.append(parsed["view"][0])
    else:
        subject_lower = parsed["subject"].lower() if parsed["subject"] else ""
        if any(k in subject_lower for k in ["portrait", "face", "girl", "boy", "person"]):
            p1_parts.append("portrait composition, shallow depth of field")
        elif any(k in subject_lower for k in ["city", "building", "architecture", "skyline"]):
            p1_parts.append("wide angle, deep depth of field, architectural composition")
        elif any(k in subject_lower for k in ["dragon", "creature", "monster", "beast"]):
            p1_parts.append("dynamic angle, dramatic composition")
        elif any(k in subject_lower for k in ["flower", "plant", "nature", "macro"]):
            p1_parts.append("close-up, macro photography, bokeh background")
        elif any(k in subject_lower for k in ["landscape", "mountain", "valley", "forest"]):
            p1_parts.append("panoramic view, rule of thirds, atmospheric perspective")

    # ---- P2: 质量（紧接主体，确保不被截断） ----
    quality = list(parsed["quality"])
    subject_lower = parsed["subject"].lower() if parsed["subject"] else ""

    if any(k in subject_lower for k in ["portrait", "face", "girl", "boy", "person"]):
        if not any(e in "detailed face" for e in exclude_words):
            quality.append("detailed face, detailed eyes, skin texture")
    elif any(k in subject_lower for k in ["dragon", "creature", "monster"]):
        if not any(e in "detailed scales" for e in exclude_words):
            quality.append("detailed scales, intricate details, realistic textures")
    elif any(k in subject_lower for k in ["city", "building", "architecture"]):
        quality.append("detailed architecture, sharp lines, intricate details")
    elif any(k in subject_lower for k in ["flower", "plant", "nature"]):
        if not any(e in "single flower" for e in exclude_words):
            quality.append("detailed petals, vibrant colors, natural textures")
    elif any(k in subject_lower for k in ["landscape", "mountain", "forest", "valley"]):
        quality.append("vast landscape, atmospheric depth, natural beauty")

    if len(quality) < 4: quality.append("sharp focus")
    if len(quality) < 5: quality.append("8k resolution")
    if len(quality) < 6: quality.append("highly detailed")
    p2_parts.extend(quality[:5])  # 上限 5 个质量词

    # ---- P2: 时间 ----
    if parsed["time"]:
        p2_parts.append(parsed["time"][0])
    elif parsed.get("resolved_entities"):
        for entity in parsed["resolved_entities"]:
            if "scenes" in entity:
                p2_parts.append(entity["scenes"][0])
                break

    # ---- P2: 地点 ----
    if parsed["place"]:
        p2_parts.append(parsed["place"][0])
    elif parsed["subject"]:
        subject_lower = parsed["subject"].lower()
        if any(k in subject_lower for k in ["dragon", "phoenix", "bird"]):
            p2_parts.append("in the sky")
        elif any(k in subject_lower for k in ["fish", "whale", "coral"]):
            p2_parts.append("underwater")
        elif any(k in subject_lower for k in ["tree", "forest", "wolf"]):
            p2_parts.append("in a forest")

    # ---- P2: 天气 ----
    if parsed["weather"]:
        p2_parts.append(parsed["weather"][0])

    # ---- P3: 五维扩展 ----
    if parsed.get("narrative"): p3_parts.extend(parsed["narrative"][:2])
    if parsed.get("appearance"): p3_parts.extend(parsed["appearance"][:2])
    if parsed.get("action"): p3_parts.extend(parsed["action"][:2])
    if parsed.get("physics"): p3_parts.extend(parsed["physics"][:2])
    if parsed.get("environment"): p3_parts.extend(parsed["environment"][:2])
    if parsed.get("lens"): p3_parts.extend(parsed["lens"][:1])
    if parsed.get("dof"): p3_parts.extend(parsed["dof"][:1])
    if parsed.get("angle"): p3_parts.extend(parsed["angle"][:1])
    if parsed.get("aspect"): p3_parts.extend(parsed["aspect"][:1])
    if parsed.get("color_mood"): p3_parts.extend(parsed["color_mood"][:1])
    if parsed.get("atmosphere"): p3_parts.extend(parsed["atmosphere"][:1])

    # ---- P3: 额外风格、艺术家、材质、情绪 ----
    for s in parsed["style"][1:]:
        p3_parts.append(s)
    if parsed["artist"]: p3_parts.append(", ".join(parsed["artist"][:2]))
    if parsed["material"]: p3_parts.append(", ".join(parsed["material"][:2]))
    if parsed["mood"]: p3_parts.append(", ".join(parsed["mood"][:2]))

    # ---- P4: 关系协同词 ----
    if synergy_words: p4_parts.extend(synergy_words[:2])
    if combined_style_keywords: p4_parts.extend(combined_style_keywords[:2])

    # ---- P4: 构图建议 ----
    composition_suggestion = relationship_manager.suggest_composition(all_words)
    if composition_suggestion and composition_suggestion != ["rule_of_thirds"]:
        existing_comp = set(parsed.get("view", []))
        for comp in composition_suggestion[:1]:
            if comp not in existing_comp:
                p4_parts.append(comp)

    # ---- P4: 场景丰富度 ----
    if any(k in subject_lower for k in ["city", "urban", "street"]):
        p4_parts.extend(["busy streets", "atmospheric haze"])
    elif any(k in subject_lower for k in ["forest", "jungle", "woodland"]):
        p4_parts.extend(["dense foliage", "dappled light"])
    elif any(k in subject_lower for k in ["ocean", "sea", "underwater"]):
        p4_parts.extend(["light rays", "floating particles"])
    elif any(k in subject_lower for k in ["mountain", "peak", "cliff"]):
        p4_parts.extend(["misty valleys", "distant peaks"])
    elif any(k in subject_lower for k in ["castle", "palace", "fortress"]):
        p4_parts.extend(["stone textures", "ancient details"])

    # ---- P4: 色彩调色板 ----
    if parsed.get("cultural_context") == "chinese":
        p4_parts.extend(["rich reds", "golden accents"])
    elif parsed.get("cultural_context") == "japanese":
        p4_parts.extend(["subtle pastels", "natural tones"])
    elif parsed.get("cultural_context") == "western":
        p4_parts.extend(["vibrant colors", "dramatic contrasts"])

    # ============================================================
    # 按优先级拼接 + 长度控制
    # ============================================================
    max_words = CONFIG.get("max_prompt_words", 45)

    # P1→P2→P3→P4 顺序拼接，末尾自然先被丢弃
    all_parts = p1_parts + p2_parts + p3_parts + p4_parts
    prompt = ", ".join([p for p in all_parts if p and p.strip()])

    if exclude_words:
        for word in exclude_words:
            prompt = prompt.replace(word, "")

    # 去重
    words = [w.strip() for w in prompt.split(",")]
    seen = set()
    unique_words = []
    for word in words:
        word_lower = word.lower()
        if word_lower not in seen and word:
            seen.add(word_lower)
            unique_words.append(word)
    prompt = ", ".join(unique_words)

    prompt = re.sub(r',\s*,', ',', prompt)
    prompt = re.sub(r'^\s*,\s*', '', prompt)
    prompt = re.sub(r'\s*,\s*$', '', prompt)

    # 长度截断：末尾丢弃 P4→P3→P2（逐层）
    prompt = _trim_prompt(prompt, max_words)

    return prompt

# ============================================================
# 交互式问答流程
# ============================================================

def interactive_mode() -> str:
    print("\n" + "=" * 50)
    print("  精细模式 - 逐步构建你的 prompt")
    print("=" * 50)

    layers = {
        "主体": {"question": "你想画什么？（主体描述）", "key": "subject", "required": True},
        "风格": {"question": "什么风格？（如：赛博朋克、水墨、油画、动漫...）", "key": "style", "required": False},
        "时间": {"question": "什么时间？（如：夜晚、黄昏、黎明...）", "key": "time", "required": False},
        "地点": {"question": "在哪里？（如：城市、森林、海底...）", "key": "place", "required": False},
        "天气": {"question": "什么天气？（如：雨天、雪天、雾...）", "key": "weather", "required": False},
        "光线": {"question": "什么光线？（如：逆光、霓虹、月光...）", "key": "light", "required": False},
        "视角": {"question": "什么视角？（如：俯视、仰视、特写...）", "key": "view", "required": False},
    }

    answers = {}
    for name, config in layers.items():
        prompt_text = config["question"]
        if not config["required"]:
            prompt_text += " (直接回车跳过)"
        answer = input(f"\n>> {prompt_text}\n   ").strip()
        if answer or config["required"]:
            answers[config["key"]] = answer

    full_text = " ".join(answers.values())
    parsed = parse_input(full_text)

    if "subject" in answers: parsed["subject"] = answers["subject"]
    if "style" in answers and answers["style"]: parsed["style"] = [STYLE_MAP.get(answers["style"], answers["style"])]
    if "time" in answers and answers["time"]: parsed["time"] = [TIME_MAP.get(answers["time"], answers["time"])]
    if "place" in answers and answers["place"]: parsed["place"] = [PLACE_MAP.get(answers["place"], answers["place"])]
    if "weather" in answers and answers["weather"]: parsed["weather"] = [WEATHER_MAP.get(answers["weather"], answers["weather"])]
    if "light" in answers and answers["light"]: parsed["light"] = [LIGHT_MAP.get(answers["light"], answers["light"])]
    if "view" in answers and answers["view"]: parsed["view"] = [VIEW_MAP.get(answers["view"], answers["view"])]

    return build_prompt(parsed)

def quick_mode() -> str:
    print("\n" + "=" * 50)
    print("  快速模式 - 一句话描述你想要的图片")
    print("  示例：赛博朋克城市夜景，雨天霓虹灯")
    print("=" * 50)

    text = input("\n>> 你想要什么？\n   ").strip()
    if not text: text = "a beautiful scene"

    parsed = parse_input(text)
    return build_prompt(parsed)

# ============================================================
# 图片生成
# ============================================================

def generate_image(prompt: str, steps: int = None, width: int = None, height: int = None,
                   raw_input: str = None, model_name: str = None, negative_prompt: str = None) -> Optional[str]:
    current_model = model_name or CONFIG["model"]
    model_config = get_model_config(current_model)
    recommended = model_config.get("recommended_settings", {})
    
    steps = steps or recommended.get("steps", CONFIG["steps"])
    width = width or recommended.get("width", CONFIG["width"])
    height = height or recommended.get("height", CONFIG["height"])
    raw_input = raw_input or prompt

    # 根据模型类型处理 prompt
    if model_config.get("chinese_support", False):
        # 中文模型：直接使用中文 prompt
        prompt_to_use = raw_input
    else:
        # 其他模型：使用解析后的英文 prompt
        prompt_to_use = adapt_prompt_for_model(prompt, current_model)

    print(f"\n[Prompt] {prompt_to_use}")
    print(f"[Model] {model_config.get('name', current_model)}")
    if model_config.get("chinese_support", False):
        print("[语言] 中文原生支持")

    # 使用模型缓存
    from .utils.model_cache import model_cache
    
    try:
        print(f"正在加载模型...")
        pipe = model_cache.get_model(current_model)
        if pipe is None:
            print("错误：模型加载失败")
            return None
    except Exception as e:
        print(f"错误：模型加载失败 - {e}")
        return None

    try:
        print(f"开始生成图片...")
        t0 = time.time()

        image = pipe(
            prompt=prompt_to_use,
            negative_prompt=negative_prompt or CONFIG.get("negative_prompt", ""),
            num_inference_steps=steps,
            guidance_scale=CONFIG["guidance_scale"],
            width=width,
            height=height,
        ).images[0]

        elapsed = time.time() - t0
        print(f"生成完成，耗时 {elapsed:.1f}s")

        output_dir = os.path.join(BASE_DIR, CONFIG["output_dir"])
        os.makedirs(output_dir, exist_ok=True)

        timestamp = time.strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(output_dir, f"{timestamp}.png")
        image.save(output_path)
        print(f"图片已保存到: {output_path}")

        log_generation(raw_input, prompt, output_path, elapsed)

        if CONFIG.get("auto_open", False):
            try: os.startfile(output_path)
            except Exception as e:
                logger.warning(f"无法自动打开图片: {e}")

        return output_path

    except torch.cuda.OutOfMemoryError:
        logger.error("显存不足，尝试降低分辨率或步数")
        print("错误：显存不足，请尝试降低分辨率或步数")
        return None
    except Exception as e:
        logger.error(f"图片生成失败: {e}")
        print(f"错误：图片生成失败 - {e}")
        return None

# ============================================================
# 批量生成
# ============================================================

def generate_batch(prompts_file: str):
    """批量生成 - 使用优化的批量处理器"""
    if not os.path.exists(prompts_file):
        logger.error(f"批量生成文件不存在: {prompts_file}")
        print(f"错误：文件不存在 {prompts_file}")
        return

    try:
        with open(prompts_file, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]
    except UnicodeDecodeError:
        logger.error(f"文件编码错误: {prompts_file}")
        print(f"错误：文件编码错误，请确保文件为 UTF-8 编码")
        return
    except Exception as e:
        logger.error(f"读取文件失败: {e}")
        print(f"错误：读取文件失败 - {e}")
        return

    if not lines:
        logger.warning("批量生成文件为空")
        print("错误：文件为空")
        return

    prompts = [line for line in lines if not line.startswith("#")]

    if not prompts:
        logger.warning("没有有效的 prompt")
        print("错误：没有有效的 prompt（所有行都被注释）")
        return

    # 使用批量处理器
    from .utils.batch import batch_processor
    
    print("=" * 50)
    print(f"  批量生成模式（优化版）")
    print(f"  共 {len(prompts)} 个 prompt")
    print("=" * 50)

    # 预览所有 prompt
    for i, text in enumerate(prompts, 1):
        parsed = parse_input(text, ask_clarification=False)
        prompt = build_prompt(parsed)
        print(f"  [{i}] {text}")
        print(f"      → {prompt[:60]}...")
    print()

    confirm = input(">> 开始批量生成？(y/n): ").strip().lower()
    if confirm != "n":
        print("已取消")
        return

    # 定义生成函数
    def generate_func(text):
        parsed = parse_input(text, ask_clarification=False)
        prompt = build_prompt(parsed)
        return generate_image(prompt, raw_input=text)
    
    # 加载任务
    batch_processor.load_from_list(prompts)
    
    # 设置输出目录
    output_dir = os.path.join(BASE_DIR, CONFIG["output_dir"])
    
    # 设置进度回调
    def on_progress(task, success, failed, total):
        status = "✓" if task.status == "completed" else "✗"
        print(f"  {status} [{task.id}/{total}] {task.prompt[:30]}...")
    
    batch_processor.on_progress = on_progress
    
    # 执行批量处理
    result = batch_processor.process(
        generate_func=generate_func,
        output_dir=output_dir,
        resume=True  # 支持断点续传
    )
    
    print(f"\n最终结果：成功 {result['success']} 张，失败 {result['failed']} 张")

# ============================================================
# 主程序
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="CPU Image Gen - 自然语言 Prompt 架构")
    parser.add_argument("--batch", type=str, help="批量生成模式，指定 prompts.txt 文件路径")
    parser.add_argument("--prompt", type=str, help="直接传入 prompt 生成图片（非交互）")
    parser.add_argument("--negative", type=str, help="负面提示（排除不想出现的内容）")
    parser.add_argument("--steps", type=int, help="推理步数（覆盖 config.json）")
    parser.add_argument("--size", type=str, choices=["512", "768", "1024"], help="分辨率")
    parser.add_argument("--model", type=str, help="模型名称（覆盖 config.json）")
    parser.add_argument("--mode", type=str, choices=["image", "video", "3d"], default="image", help="生成模式")
    parser.add_argument("--deepseek", action="store_true", help="使用 DeepSeek 增强语义理解")
    parser.add_argument("--open", action="store_true", help="生成后自动打开图片")
    args = parser.parse_args()

    if args.batch:
        generate_batch(args.batch)
        return

    if args.prompt:
        raw_input = args.prompt
        
        # 使用 DeepSeek 增强
        if args.deepseek:
            from .adapters.deepseek import deepseek_adapter
            if deepseek_adapter.is_configured():
                print("\n[DeepSeek] 正在分析语义...")
                enhanced = deepseek_adapter.parse_complex_prompt(raw_input)
                raw_input = enhanced.get("prompt_en", raw_input)
                print(f"[DeepSeek] 增强后的 prompt: {raw_input}")
            else:
                print("\n[DeepSeek] API Key 未配置，使用基础解析")
        
        parsed = parse_input(raw_input, ask_clarification=False)
        
        if args.mode == "video":
            video_kw = get_video_keywords()
            prompt = build_video_prompt(raw_input)
            print(f"\n[Video Prompt] {prompt}")
            print("注意：视频生成需要专用模型（如 AnimateDiff），当前仅生成 prompt")
            return
        elif args.mode == "3d":
            prompt = build_3d_prompt(raw_input)
            print(f"\n[3D Prompt] {prompt}")
            print("注意：3D 生成需要专用模型，当前仅生成 prompt")
            return
        else:
            prompt = build_prompt(parsed)
            print(f"Prompt: {prompt}")

        size = int(args.size) if args.size else None
        result = generate_image(prompt, steps=args.steps, width=size, height=size,
                               raw_input=raw_input, model_name=args.model)
        if args.open and result:
            try: os.startfile(result)
            except: pass
        return

    print("=" * 50)
    print("  CPU Image Gen - 自然语言 Prompt 架构")
    print("  支持 SDXL Turbo / SDXL / SD3 / Flux")
    print("  支持图片/视频/3D 生成")
    print("=" * 50)
    print()
    print("选择控制层级：")
    print("  [1] 基础 - 一键出图，零门槛")
    print("  [2] 控制 - 选择风格和模板")
    print("  [3] 高级 - 调整生成参数")
    print("  [4] 专家 - 完全掌控模型")
    print()
    print("或直接选择功能：")
    print("  [v] 视频模式 - 生成视频 prompt")
    print("  [3d] 3D模式 - 生成 3D prompt")
    print("  [b] 批量模式 - 从文件读取多个 prompt")
    print()
    print("  [d] DeepSeek模式 - 增强语义理解")
    print()
    print("可用模型：")
    model_list = list(MODEL_CONFIGS.keys())
    for i, model_key in enumerate(model_list, 1):
        model_name = MODEL_CONFIGS[model_key]["name"]
        print(f"  [m{i}] {model_name}")
    print()

    choice = input(">> 请选择: ").strip()

    # 检查是否选择了模型
    selected_model = None
    if choice.startswith("m") and choice[1:].isdigit():
        model_idx = int(choice[1:]) - 1
        if 0 <= model_idx < len(model_list):
            selected_model = model_list[model_idx]
            print(f"\n已选择模型: {MODEL_CONFIGS[selected_model]['name']}")
            choice = ""

    raw_input = ""
    prompt = ""
    template_settings = None
    generation_mode = "image"
    layer_params = {}

    # 层级选择
    if choice == "1":
        # Layer 1: 基础模式
        from .utils.layers import layer_manager
        layer_manager.set_layer(1)
        print("\n[基础模式] 一键出图，零门槛")
        raw_input = input("\n>> 你想要什么？\n   ").strip()
        if not raw_input: raw_input = "a beautiful scene"
        parsed = parse_input(raw_input)
        prompt = build_prompt(parsed)
        
    elif choice == "2":
        # Layer 2: 控制模式
        from .utils.layers import layer_manager
        layer_manager.set_layer(2)
        print("\n[控制模式] 选择风格和模板")
        
        # 风格选择
        print("\n可用风格：")
        styles = ["默认", "油画", "水彩", "素描", "动漫", "赛博朋克", "极简"]
        for i, s in enumerate(styles, 1):
            print(f"  [{i}] {s}")
        style_choice = input(">> 选择风格 (数字): ").strip()
        if style_choice.isdigit() and 1 <= int(style_choice) <= len(styles):
            layer_params["style"] = styles[int(style_choice) - 1]
        
        # 模板选择
        print("\n可用模板：")
        template_cats = list(TEMPLATE_CATEGORIES.keys())
        for i, cat in enumerate(template_cats, 1):
            print(f"  [{i}] {cat}")
        tpl_choice = input(">> 选择模板类别 (数字，回车跳过): ").strip()
        
        raw_input = input("\n>> 你想要什么？\n   ").strip()
        if not raw_input: raw_input = "a beautiful scene"
        parsed = parse_input(raw_input)
        prompt = build_prompt(parsed)
        
    elif choice == "3":
        # Layer 3: 高级模式
        from .utils.layers import layer_manager
        layer_manager.set_layer(3)
        print("\n[高级模式] 调整生成参数")
        
        raw_input = input("\n>> 你想要什么？\n   ").strip()
        if not raw_input: raw_input = "a beautiful scene"
        parsed = parse_input(raw_input)
        prompt = build_prompt(parsed)
        
        # 参数选择
        steps = input(">> 步数 (4-50，默认4): ").strip()
        if steps.isdigit():
            layer_params["steps"] = int(steps)
        
        resolution = input(">> 分辨率 (512/768/1024，默认512): ").strip()
        if resolution in ["512", "768", "1024"]:
            layer_params["resolution"] = int(resolution)
        
        negative = input(">> 负面提示 (回车使用默认): ").strip()
        if negative:
            layer_params["negative"] = negative
        
    elif choice == "4":
        # Layer 4: 专家模式
        from .utils.layers import layer_manager
        layer_manager.set_layer(4)
        print("\n[专家模式] 完全掌控模型")
        print(layer_manager.get_help_text(4))
        
        raw_input = input("\n>> 你想要什么？\n   ").strip()
        if not raw_input: raw_input = "a beautiful scene"
        parsed = parse_input(raw_input)
        prompt = build_prompt(parsed)
        
        # 所有参数
        steps = input(">> 步数 (4-50，默认4): ").strip()
        if steps.isdigit():
            layer_params["steps"] = int(steps)
        
        resolution = input(">> 分辨率 (512/768/1024，默认512): ").strip()
        if resolution in ["512", "768", "1024"]:
            layer_params["resolution"] = int(resolution)
        
        negative = input(">> 负面提示 (回车使用默认): ").strip()
        if negative:
            layer_params["negative"] = negative
        
        print("\n可用模型：")
        for i, model_key in enumerate(model_list, 1):
            print(f"  [{i}] {MODEL_CONFIGS[model_key]['name']}")
        model_choice = input(">> 选择模型 (数字): ").strip()
        if model_choice.isdigit() and 1 <= int(model_choice) <= len(model_list):
            selected_model = model_list[int(model_choice) - 1]
        
        upscale = input(">> 是否放大 2x？(y/n): ").strip().lower()
        layer_params["upscale"] = upscale == "y"
        
    elif choice == "v":
        generation_mode = "video"
        print("\n" + "=" * 50)
        print("  视频 Prompt 生成模式")
        print("  注意：此模式仅生成视频描述 prompt，")
        print("  实际视频生成需要专用模型（如 AnimateDiff）")
        print("=" * 50)
        video_kw = get_video_keywords()
        print("\n可用动作关键词：")
        motions = list(video_kw.get("动作", {}).keys())
        for i, m in enumerate(motions, 1):
            print(f"  {m}", end="")
            if i % 5 == 0: print()
        print()
        raw_input = input("\n>> 描述场景：\n   ").strip()
        motion = input(">> 动作（可选，回车跳过）：\n   ").strip()
        camera = input(">> 镜头运动（可选，回车跳过）：\n   ").strip()
        prompt = build_video_prompt(
            raw_input,
            motion=video_kw.get("动作", {}).get(motion, motion) if motion else None,
            camera=video_kw.get("镜头运动", {}).get(camera, camera) if camera else None
        )
        print(f"\n[Video Prompt] {prompt}")
    elif choice == "3d":
        generation_mode = "3d"
        print("\n" + "=" * 50)
        print("  3D Prompt 生成模式")
        print("  注意：此模式仅生成 3D 模型描述 prompt，")
        print("  实际 3D 生成需要专用软件（如 Blender + AI 插件）")
        print("=" * 50)
        spatial_kw = get_3d_keywords()
        print("\n可用材质关键词：")
        materials = list(spatial_kw.get("材质", {}).keys())
        for i, m in enumerate(materials, 1):
            print(f"  {m}", end="")
            if i % 5 == 0: print()
        print()
        raw_input = input("\n>> 描述 3D 模型：\n   ").strip()
        material = input(">> 材质（可选，回车跳过）：\n   ").strip()
        render = input(">> 渲染风格（可选，回车跳过）：\n   ").strip()
        prompt = build_3d_prompt(
            raw_input,
            material=spatial_kw.get("材质", {}).get(material, material) if material else None,
            render_style=spatial_kw.get("渲染风格", {}).get(render, render) if render else None
        )
        print(f"\n[3D Prompt] {prompt}")
    elif choice == "d":
        # DeepSeek 模式
        from .adapters.deepseek import deepseek_adapter
        
        if not deepseek_adapter.is_configured():
            print("\n[DeepSeek] API Key 未配置")
            print("请设置环境变量 DEEPSEEK_API_KEY")
            print("或在代码中初始化: deepseek_adapter.api_key = 'your-key'")
            return
        
        print("\n" + "=" * 50)
        print("  DeepSeek 增强模式")
        print("  使用 AI 理解复杂中文描述")
        print("=" * 50)
        
        raw_input = input("\n>> 用中文描述你想要的图片：\n   ").strip()
        if not raw_input: raw_input = "a beautiful scene"
        
        print("\n[DeepSeek] 正在分析语义...")
        enhanced = deepseek_adapter.parse_complex_prompt(raw_input)
        raw_input = enhanced.get("prompt_en", raw_input)
        print(f"[DeepSeek] 增强后的 prompt: {raw_input}")
        
        parsed = parse_input(raw_input, ask_clarification=False)
        prompt = build_prompt(parsed)
    elif choice == "2":
        prompt = interactive_mode()
        raw_input = prompt
    elif choice == "3":
        prompt = input("\n>> 输入完整 prompt:\n   ").strip()
        raw_input = prompt
    elif choice == "t":
        tpl_key, template = select_template()
        if template:
            raw_input = input("\n>> 描述你的内容：\n   ").strip()
            if not raw_input: raw_input = "a beautiful scene"
            prompt = generate_prompt_from_template(template, raw_input)
            template_settings = template.get("recommended_settings", {})
            print(f"\n使用模板: {template['label']}")
        else:
            print("未选择模板，使用快速模式")
            raw_input = input("\n>> 你想要什么？\n   ").strip()
            if not raw_input: raw_input = "a beautiful scene"
            parsed = parse_input(raw_input)
            prompt = build_prompt(parsed)
    elif choice == "b":
        file_path = input("\n>> 输入 prompts.txt 文件路径: ").strip()
        if file_path: generate_batch(file_path)
        else: print("未指定文件")
        return
    else:
        print("无效选择，使用快速模式")
        raw_input = input("\n>> 你想要什么？\n   ").strip()
        if not raw_input: raw_input = "a beautiful scene"
        parsed = parse_input(raw_input)
        prompt = build_prompt(parsed)

    if not prompt:
        print("prompt 为空，使用默认")
        prompt = "a beautiful landscape, highly detailed"
        raw_input = raw_input or "default"

    print(f"\n最终 prompt:\n  {prompt}")
    confirm = input("\n>> 确认生成？(y/n): ").strip().lower()
    if confirm == "n":
        print("已取消")
        return

    if generation_mode != "image":
        print(f"\n[{generation_mode.upper()} Prompt] {prompt}")
        print("注意：视频/3D 生成需要专用模型，当前仅生成 prompt")
        return

    # 使用层级参数
    steps = layer_params.get("steps") or (template_settings and template_settings.get("steps"))
    size = layer_params.get("resolution") or (template_settings and template_settings.get("width"))
    
    # 生成图片
    result = generate_image(
        prompt,
        steps=steps,
        width=size,
        height=size,
        raw_input=raw_input,
        model_name=selected_model
    )
    
    # 图片放大（专家模式）
    if layer_params.get("upscale") and result:
        print("\n正在放大图片...")
        from .adapters.upscaler import upscaler
        upscaled = upscaler.upscale(result, scale=2)
        if upscaled:
            print(f"放大完成: {upscaled}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n已中断，退出程序")
    except Exception as e:
        print(f"\n错误：{e}")
