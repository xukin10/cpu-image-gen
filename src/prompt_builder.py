"""
CPU Image Gen - 自然语言 Prompt 架构
用自然语言描述需求，自动构建 AI 生图 prompt

支持：
- 中文自然语言输入
- 62 个文化实体（中国/日本/西方/希腊/北欧/埃及）
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
from typing import Dict, List, Optional, Tuple, Any

# ============================================================
# 路径配置
# ============================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIGS_DIR = os.path.join(BASE_DIR, "configs")

# ============================================================
# 加载关键词映射表
# ============================================================

KEYWORDS_PATH = os.path.join(CONFIGS_DIR, "keywords.json")

def load_keywords() -> Dict:
    with open(KEYWORDS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

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
    with open(TEMPLATES_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

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
    with open(CULTURAL_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

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
# 加载模型配置
# ============================================================

MODEL_CONFIGS_PATH = os.path.join(CONFIGS_DIR, "model_configs.json")

def load_model_configs() -> Dict:
    with open(MODEL_CONFIGS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

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
    with open(MULTIMODAL_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

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
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

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

    if not result.get("resolved_entities"):
        subject = text
        all_keys = []
        for m in ALL_MAPS:
            all_keys.extend(m.keys())
        for key in all_keys:
            subject = subject.replace(key, " ")
        subject = re.sub(r'[,，、。!！?？\s]+', ' ', subject).strip()
        subject = re.sub(r'[的了在是和与有]', ' ', subject)
        subject = re.sub(r'\s+', ' ', subject).strip()
        if subject and re.match(r'^[\u4e00-\u9fff\s]+$', subject):
            en_parts = []
            for cn, en in CN_TO_EN.items():
                if cn in subject:
                    en_parts.append(en)
                    subject = subject.replace(cn, "")
            subject = " ".join(en_parts) if en_parts else subject
        result["subject"] = subject if subject.strip() else "a scene"
    else:
        result["subject"] = ""

    return result

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

def build_prompt(parsed: Dict) -> str:
    parts = []
    exclude_words = []

    if parsed["style"]:
        parts.append(parsed["style"][0])

    if parsed.get("resolved_entities"):
        for entity in parsed["resolved_entities"]:
            if "name_en" in entity: parts.append(entity["name_en"])
            if "morphology" in entity: parts.extend(entity["morphology"][:2])
            if "elements" in entity: parts.extend(entity["elements"][:2])
            if "atmosphere" in entity: parts.append(entity["atmosphere"][0])
            if "exclude" in entity: exclude_words.extend(entity["exclude"])
    else:
        parts.append(parsed["subject"])

    if parsed["time"]:
        parts.append(parsed["time"][0])
    elif parsed.get("resolved_entities"):
        for entity in parsed["resolved_entities"]:
            if "scenes" in entity:
                parts.append(entity["scenes"][0])
                break

    if parsed["place"]:
        parts.append(parsed["place"][0])
    elif parsed["subject"]:
        subject_lower = parsed["subject"].lower()
        if any(k in subject_lower for k in ["dragon", "phoenix", "bird"]):
            parts.append("in the sky")
        elif any(k in subject_lower for k in ["fish", "whale", "coral"]):
            parts.append("underwater")
        elif any(k in subject_lower for k in ["tree", "forest", "wolf"]):
            parts.append("in a forest")

    if parsed["weather"]:
        parts.append(parsed["weather"][0])

    if parsed["light"]:
        parts.append(", ".join(parsed["light"]))
    elif parsed["subject"]:
        subject_lower = parsed["subject"].lower()
        if any(k in subject_lower for k in ["horror", "abandoned", "dark"]):
            parts.append("dim light, deep shadows, atmospheric fog")
        elif any(k in subject_lower for k in ["water", "ocean", "lake"]):
            parts.append("sunlight reflections, caustics, shimmering light")
        elif any(k in subject_lower for k in ["flower", "garden", "spring"]):
            parts.append("soft diffused light, gentle shadows")
        elif any(k in subject_lower for k in ["city", "cyber", "neon"]):
            parts.append("neon glow, colorful reflections, urban lighting")
        elif any(k in subject_lower for k in ["mountain", "landscape", "valley"]):
            parts.append("natural lighting, golden hour, atmospheric perspective")
        else:
            parts.append("dramatic lighting, volumetric light")

    if parsed["view"]:
        parts.append(parsed["view"][0])
    else:
        subject_lower = parsed["subject"].lower() if parsed["subject"] else ""
        if any(k in subject_lower for k in ["portrait", "face", "girl", "boy", "person"]):
            parts.append("portrait composition, shallow depth of field")
        elif any(k in subject_lower for k in ["city", "building", "architecture", "skyline"]):
            parts.append("wide angle, deep depth of field, architectural composition")
        elif any(k in subject_lower for k in ["dragon", "creature", "monster", "beast"]):
            parts.append("dynamic angle, dramatic composition")
        elif any(k in subject_lower for k in ["flower", "plant", "nature", "macro"]):
            parts.append("close-up, macro photography, bokeh background")
        elif any(k in subject_lower for k in ["landscape", "mountain", "valley", "forest"]):
            parts.append("panoramic view, rule of thirds, atmospheric perspective")

    for s in parsed["style"][1:]:
        parts.append(s)
    if parsed["artist"]: parts.append(", ".join(parsed["artist"][:2]))
    if parsed["material"]: parts.append(", ".join(parsed["material"][:2]))
    if parsed["mood"]: parts.append(", ".join(parsed["mood"][:2]))

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

    scene_richness = []
    if any(k in subject_lower for k in ["city", "urban", "street"]):
        scene_richness.extend(["busy streets", "atmospheric haze", "layered buildings"])
    elif any(k in subject_lower for k in ["forest", "jungle", "woodland"]):
        scene_richness.extend(["dense foliage", "dappled light", "moss-covered ground"])
    elif any(k in subject_lower for k in ["ocean", "sea", "underwater"]):
        scene_richness.extend(["light rays", "floating particles", "depth layers"])
    elif any(k in subject_lower for k in ["mountain", "peak", "cliff"]):
        scene_richness.extend(["misty valleys", "distant peaks", "rocky terrain"])
    elif any(k in subject_lower for k in ["castle", "palace", "fortress"]):
        scene_richness.extend(["stone textures", "dramatic architecture", "ancient details"])

    color_palette = []
    if parsed.get("cultural_context") == "chinese":
        color_palette.extend(["rich reds", "golden accents", "jade greens"])
    elif parsed.get("cultural_context") == "japanese":
        color_palette.extend(["subtle pastels", "natural tones", "harmonious colors"])
    elif parsed.get("cultural_context") == "western":
        color_palette.extend(["vibrant colors", "dramatic contrasts", "bold tones"])

    parts.extend(quality[:6])
    if scene_richness: parts.extend(scene_richness[:2])
    if color_palette: parts.extend(color_palette[:2])

    prompt = ", ".join([p for p in parts if p and p.strip()])

    if exclude_words:
        for word in exclude_words:
            prompt = prompt.replace(word, "")

    prompt = re.sub(r',\s*,', ',', prompt)
    prompt = re.sub(r'^\s*,\s*', '', prompt)
    prompt = re.sub(r'\s*,\s*$', '', prompt)

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
                   raw_input: str = None, model_name: str = None) -> Optional[str]:
    current_model = model_name or CONFIG["model"]
    model_config = get_model_config(current_model)
    recommended = model_config.get("recommended_settings", {})
    
    steps = steps or recommended.get("steps", CONFIG["steps"])
    width = width or recommended.get("width", CONFIG["width"])
    height = height or recommended.get("height", CONFIG["height"])
    raw_input = raw_input or prompt

    prompt = adapt_prompt_for_model(prompt, current_model)

    print(f"\n[Prompt] {prompt}")
    print(f"[Model] {model_config.get('name', current_model)}")

    import gc
    gc.collect()

    try:
        print(f"正在加载模型...")
        torch.set_num_threads(min(CONFIG["threads"], os.cpu_count() or 4))

        pipe = AutoPipelineForText2Image.from_pretrained(
            current_model,
            torch_dtype=torch.float32,
            local_files_only=True,
        )
        pipe = pipe.to("cpu")
        pipe.enable_attention_slicing()
    except Exception as e:
        print(f"错误：模型加载失败 - {e}")
        return None

    try:
        print(f"开始生成图片...")
        t0 = time.time()

        image = pipe(
            prompt=prompt,
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
            except: pass

        return output_path

    except Exception as e:
        print(f"错误：图片生成失败 - {e}")
        return None

    finally:
        del pipe
        gc.collect()

# ============================================================
# 批量生成
# ============================================================

def generate_batch(prompts_file: str):
    if not os.path.exists(prompts_file):
        print(f"错误：文件不存在 {prompts_file}")
        return

    with open(prompts_file, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    if not lines:
        print("错误：文件为空")
        return

    prompts = [line for line in lines if not line.startswith("#")]

    print("=" * 50)
    print(f"  批量生成模式")
    print(f"  共 {len(prompts)} 个 prompt")
    print("=" * 50)

    for i, text in enumerate(prompts, 1):
        parsed = parse_input(text, ask_clarification=False)
        prompt = build_prompt(parsed)
        print(f"  [{i}] {text}")
        print(f"      → {prompt}")
    print()

    confirm = input(">> 开始批量生成？(y/n): ").strip().lower()
    if confirm != "y":
        print("已取消")
        return

    print("\n正在加载模型（仅一次）...")
    torch.set_num_threads(min(CONFIG["threads"], os.cpu_count() or 4))

    import gc
    gc.collect()

    try:
        pipe = AutoPipelineForText2Image.from_pretrained(
            CONFIG["model"],
            torch_dtype=torch.float32,
            local_files_only=True,
        )
        pipe = pipe.to("cpu")
        pipe.enable_attention_slicing()
        print("模型加载完成\n")
    except Exception as e:
        print(f"错误：模型加载失败 - {e}")
        return

    output_dir = os.path.join(BASE_DIR, CONFIG["output_dir"])
    os.makedirs(output_dir, exist_ok=True)

    total_time = 0
    success_count = 0
    for i, text in enumerate(prompts, 1):
        print(f"[{i}/{len(prompts)}] {text}")

        parsed = parse_input(text, ask_clarification=False)
        prompt = build_prompt(parsed)
        print(f"  Prompt: {prompt}")

        try:
            t0 = time.time()
            image = pipe(
                prompt=prompt,
                num_inference_steps=CONFIG["steps"],
                guidance_scale=CONFIG["guidance_scale"],
                width=CONFIG["width"],
                height=CONFIG["height"],
            ).images[0]
            elapsed = time.time() - t0
            total_time += elapsed
            success_count += 1

            timestamp = time.strftime("%Y%m%d_%H%M%S")
            output_path = os.path.join(output_dir, f"batch{i:02d}_{timestamp}.png")
            image.save(output_path)
            print(f"  耗时 {elapsed:.1f}s → {output_path}\n")

            log_generation(text, prompt, output_path, elapsed)

        except Exception as e:
            print(f"  错误：生成失败 - {e}\n")
            continue

    print(f"=" * 50)
    print(f"  批量生成完成！")
    print(f"  成功 {success_count}/{len(prompts)} 张，总耗时 {total_time:.1f}s")
    if success_count > 0:
        print(f"  平均 {total_time/success_count:.1f}s/张")
    print(f"=" * 50)

    del pipe
    gc.collect()

# ============================================================
# 主程序
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="CPU Image Gen - 自然语言 Prompt 架构")
    parser.add_argument("--batch", type=str, help="批量生成模式，指定 prompts.txt 文件路径")
    parser.add_argument("--prompt", type=str, help="直接传入 prompt 生成图片（非交互）")
    parser.add_argument("--steps", type=int, help="推理步数（覆盖 config.json）")
    parser.add_argument("--size", type=str, choices=["512", "768", "1024"], help="分辨率")
    parser.add_argument("--model", type=str, help="模型名称（覆盖 config.json）")
    parser.add_argument("--mode", type=str, choices=["image", "video", "3d"], default="image", help="生成模式")
    parser.add_argument("--open", action="store_true", help="生成后自动打开图片")
    args = parser.parse_args()

    if args.batch:
        generate_batch(args.batch)
        return

    if args.prompt:
        raw_input = args.prompt
        parsed = parse_input(raw_input, ask_clarification=False)
        
        if args.mode == "video":
            video_kw = get_video_keywords()
            prompt = build_video_prompt(raw_input)
            print(f"[Video Prompt] {prompt}")
        elif args.mode == "3d":
            prompt = build_3d_prompt(raw_input)
            print(f"[3D Prompt] {prompt}")
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
    print("选择模式：")
    print("  [1] 快速模式 - 一句话描述，自动补全")
    print("  [2] 精细模式 - 逐步引导，每层可选")
    print("  [3] 直接输入 prompt")
    print("  [t] 模板模式 - 选择场景模板")
    print("  [b] 批量模式 - 从文件读取多个 prompt")
    print("  [v] 视频模式 - 生成视频 prompt")
    print("  [3d] 3D模式 - 生成 3D prompt")
    print()
    print("可用模型：")
    model_list = list(MODEL_CONFIGS.keys())
    for i, model_key in enumerate(model_list, 1):
        model_name = MODEL_CONFIGS[model_key]["name"]
        print(f"  [m{i}] {model_name}")
    print()

    choice = input(">> 请选择 (1/2/3/t/b/v/3d/m1-m5): ").strip()

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

    if choice == "1":
        raw_input = input("\n>> 你想要什么？\n   ").strip()
        if not raw_input: raw_input = "a beautiful scene"
        parsed = parse_input(raw_input)
        prompt = build_prompt(parsed)
    elif choice == "v":
        generation_mode = "video"
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

    if template_settings:
        generate_image(prompt, steps=template_settings.get("steps"),
                      width=template_settings.get("width"), height=template_settings.get("height"),
                      raw_input=raw_input, model_name=selected_model)
    else:
        generate_image(prompt, raw_input=raw_input, model_name=selected_model)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n已中断，退出程序")
    except Exception as e:
        print(f"\n错误：{e}")
