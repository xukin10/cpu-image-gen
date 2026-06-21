# API 文档

## 核心函数

### parse_input(text, ask_clarification=True)

解析用户输入，提取关键词和文化实体。

**参数：**
- `text` (str): 用户输入的中文文本
- `ask_clarification` (bool): 是否追问文化实体类型，默认 True

**返回：**
```python
{
    "subject": str,           # 主体描述
    "style": List[str],       # 风格关键词
    "time": List[str],        # 时间关键词
    "place": List[str],       # 地点关键词
    "weather": List[str],     # 天气关键词
    "light": List[str],       # 光影关键词
    "view": List[str],        # 视角关键词
    "quality": List[str],     # 质量关键词
    "artist": List[str],      # 艺术家关键词
    "material": List[str],    # 材质关键词
    "mood": List[str],        # 氛围关键词
    "raw": str,               # 原始输入
    "cultural_context": str,  # 文化上下文 (chinese/western/japanese/None)
    "resolved_entities": List[Dict]  # 解析后的文化实体
}
```

**示例：**
```python
from src import parse_input

parsed = parse_input("中国龙 在云端")
# parsed["cultural_context"] == "chinese"
# parsed["resolved_entities"] == [{"name_en": "Chinese dragon", ...}]
```

---

### build_prompt(parsed)

根据解析结果构建 prompt。

**参数：**
- `parsed` (Dict): parse_input 的返回值

**返回：**
- `str`: 生成的英文 prompt

**示例：**
```python
from src import parse_input, build_prompt

parsed = parse_input("中国龙 在云端")
prompt = build_prompt(parsed)
# "Chinese dragon, serpentine body, five claws, pearl, clouds, ..."
```

---

### generate_image(prompt, steps=None, width=None, height=None, raw_input=None, model_name=None)

生成图片。

**参数：**
- `prompt` (str): 英文 prompt
- `steps` (int): 推理步数，默认使用配置值
- `width` (int): 图片宽度，默认使用配置值
- `height` (int): 图片高度，默认使用配置值
- `raw_input` (str): 原始输入，用于日志记录
- `model_name` (str): 模型名称，默认使用配置值

**返回：**
- `Optional[str]`: 生成的图片路径，失败返回 None

**示例：**
```python
from src import generate_image

output_path = generate_image(
    "Chinese dragon, in the sky, highly detailed",
    steps=4,
    width=512,
    height=512
)
```

---

## 模板函数

### select_template()

交互式选择场景模板。

**返回：**
- `Tuple[Optional[str], Optional[Dict]]`: (模板键, 模板配置)

---

### generate_prompt_from_template(template, user_input)

根据模板生成 prompt。

**参数：**
- `template` (Dict): 模板配置
- `user_input` (str): 用户输入

**返回：**
- `str`: 生成的 prompt

---

## 多模态函数

### build_video_prompt(base_prompt, motion=None, camera=None, temporal=None, transition=None)

构建视频生成 prompt。

**参数：**
- `base_prompt` (str): 基础 prompt
- `motion` (str): 动作关键词
- `camera` (str): 镜头运动关键词
- `temporal` (str): 时间变化关键词
- `transition` (str): 转场关键词

**返回：**
- `str`: 视频 prompt

---

### build_3d_prompt(base_prompt, material=None, lighting=None, view=None, render_style=None)

构建 3D 生成 prompt。

**参数：**
- `base_prompt` (str): 基础 prompt
- `material` (str): 材质关键词
- `lighting` (str): 光照关键词
- `view` (str): 视角关键词
- `render_style` (str): 渲染风格关键词

**返回：**
- `str`: 3D prompt

---

### get_video_keywords()

获取视频生成关键词。

**返回：**
```python
{
    "动作": {"行走": "walking", "奔跑": "running", ...},
    "镜头运动": {"推镜头": "zoom in", ...},
    "时间变化": {...},
    "转场": {...}
}
```

---

### get_3d_keywords()

获取 3D 生成关键词。

**返回：**
```python
{
    "材质": {"金属": "metallic material", ...},
    "光照": {"全局光照": "global illumination", ...},
    "视角": {"正面": "front view", ...},
    "渲染风格": {"写实": "photorealistic render", ...}
}
```

---

## 工具函数

### detect_cultural_context(text)

检测文本中的文化上下文。

**参数：**
- `text` (str): 输入文本

**返回：**
- `Optional[str]`: "chinese"、"western"、"japanese" 或 None

---

### find_entities_in_text(text)

查找文本中的文化实体。

**参数：**
- `text` (str): 输入文本

**返回：**
- `List[Tuple[str, str]]`: [(关键词, 实体键), ...]

---

### resolve_entity(entity_key, cultural_context=None)

解析文化实体。

**参数：**
- `entity_key` (str): 实体键
- `cultural_context` (str): 文化上下文

**返回：**
- `Optional[Dict]`: 实体配置

---

### get_model_config(model_name)

获取模型配置。

**参数：**
- `model_name` (str): 模型名称

**返回：**
- `Dict`: 模型配置

---

## 配置文件

### keywords.json

中文关键词映射。

**结构：**
```json
{
    "style": {"赛博朋克": "cyberpunk", ...},
    "time": {"夜晚": "at night", ...},
    "place": {"城市": "in a city", ...},
    ...
}
```

### cultural_entities.json

文化实体库。

**结构：**
```json
{
    "dragon": {
        "type": "creature",
        "label": "龙",
        "variants": {
            "chinese": {...},
            "western": {...},
            "japanese": {...}
        }
    }
}
```

### templates.json

场景模板库。

**结构：**
```json
{
    "portrait": {
        "label": "肖像",
        "category": "人像",
        "base_prompt": "portrait of {subject}",
        "quality_additions": [...],
        "composition": "...",
        "lighting": "..."
    }
}
```

### model_configs.json

模型配置。

**结构：**
```json
{
    "stabilityai/sdxl-turbo": {
        "name": "SDXL Turbo",
        "max_tokens": 77,
        "prompt_format": "keywords",
        "recommended_settings": {
            "steps": 4,
            "width": 512,
            "height": 512
        }
    }
}
```

### config.json

全局配置。

**结构：**
```json
{
    "steps": 4,
    "width": 512,
    "height": 512,
    "guidance_scale": 0.0,
    "threads": 16,
    "model": "stabilityai/sdxl-turbo",
    "output_dir": "output",
    "auto_open": false
}
```
