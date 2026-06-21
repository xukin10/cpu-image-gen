# 使用指南

## 快速开始

### 命令行使用

```bash
# 基础生成
python -m src.prompt_builder --prompt "赛博朋克城市夜景"

# 指定模型
python -m src.prompt_builder --prompt "水墨山水画" --model stabilityai/sdxl

# 批量生成
python -m src.prompt_builder --batch prompts.txt
```

### Python API 使用

```python
from src import parse_input, build_prompt, generate_image

# 解析中文输入
parsed = parse_input("赛博朋克城市夜景，雨天霓虹灯")

# 构建 prompt
prompt = build_prompt(parsed)

# 生成图片
generate_image(prompt)
```

## 交互模式

运行以下命令进入交互模式：

```bash
python -m src.prompt_builder
```

### 模式选择

| 模式 | 说明 |
|------|------|
| 1 | 快速模式 - 一句话描述 |
| 2 | 精细模式 - 逐步引导 |
| 3 | 直接输入 prompt |
| t | 模板模式 - 选择场景模板 |
| b | 批量模式 - 从文件读取 |
| v | 视频模式 - 生成视频 prompt |
| 3d | 3D模式 - 生成 3D prompt |

### 模型选择

| 选项 | 模型 | 说明 |
|------|------|------|
| m1 | SDXL Turbo | 快速生成，4步出图 |
| m2 | SDXL 1.0 | 高质量，25步 |
| m3 | SD 3.0 | 自然语言理解更好 |
| m4 | Flux.1 Dev | 长 prompt，高质量 |
| m5 | Flux.1 Schnell | Flux 快速版 |

## 文化实体

支持 62 个文化实体，自动识别文化背景：

```python
# 中国龙
parse_input("中国龙 在云端")
# → Chinese dragon, serpentine body, five claws, ...

# 西方龙
parse_input("西方龙 在洞穴")
# → Western dragon, winged, four legs with claws, ...

# 日本九尾狐
parse_input("日本九尾狐 神社")
# → Japanese nine-tailed fox (Kitsune), nine tails, ...
```

## 场景模板

24 个预定义模板：

### 人像类
- 肖像 (portrait)
- 全身像 (full_body)
- 情侣照 (couple)
- 儿童照 (child)
- 老人像 (elderly)

### 商业类
- 产品展示 (product)
- 美食摄影 (food)
- 珠宝首饰 (jewelry)
- 海报设计 (poster)

### 风景类
- 山水风景 (landscape)
- 海景 (seascape)
- 城市风光 (cityscape)
- 星空 (starry_sky)

### 艺术类
- 油画风格 (oil_painting)
- 水彩风格 (watercolor)
- 动漫风格 (anime)
- 概念艺术 (concept_art)

## 多模态生成

### 视频 Prompt

```python
from src import build_video_prompt, get_video_keywords

video_kw = get_video_keywords()
prompt = build_video_prompt(
    "a dragon flying over a city",
    motion="flying",
    camera="tracking shot"
)
```

### 3D Prompt

```python
from src import build_3d_prompt, get_3d_keywords

spatial_kw = get_3d_keywords()
prompt = build_3d_prompt(
    "a medieval sword",
    material="metallic material",
    render_style="photorealistic render"
)
```

## 高级配置

### 修改配置文件

所有配置在 `configs/` 目录：

- `config.json` - 全局配置
- `keywords.json` - 关键词映射
- `cultural_entities.json` - 文化实体
- `templates.json` - 场景模板
- `model_configs.json` - 模型配置

### 添加自定义关键词

编辑 `configs/keywords.json`：

```json
{
  "style": {
    "你的风格": "your style in english"
  }
}
```

### 添加自定义文化实体

编辑 `configs/cultural_entities.json`：

```json
{
  "your_entity": {
    "type": "creature",
    "label": "你的实体",
    "variants": {
      "chinese": {
        "name_en": "Your entity (Chinese)",
        "morphology": ["特征1", "特征2"],
        "elements": ["元素1", "元素2"],
        "atmosphere": ["氛围1"],
        "scenes": ["场景1"],
        "exclude": ["排除词1"]
      }
    }
  }
}
```
