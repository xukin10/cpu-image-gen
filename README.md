# CPU Image Gen

> 一个让任何人都能用中文生成高质量图片的 AI 工具

## 为什么做这个项目？

AI 生图很强大，但有两个门槛：
1. **语言门槛**：需要写英文 prompt
2. **技术门槛**：需要 GPU 和复杂配置

我们的目标：**用中文描述，一键出图，CPU 也能跑。**

---

## 快速开始（3 分钟）

### 1. 安装

```bash
git clone https://github.com/xukin10/cpu-image-gen.git
cd cpu-image-gen
pip install -r requirements.txt
```

### 2. 生成第一张图

```python
from src import parse_input, build_prompt, generate_image

# 用中文描述
parsed = parse_input("赛博朋克城市夜景，雨天霓虹灯")

# 自动生成英文 prompt
prompt = build_prompt(parsed)
print(prompt)
# cyberpunk, night cityscape, in a city, rainy, neon lights, highly detailed...

# 生成图片
generate_image(prompt)
```

### 3. 或者用命令行

```bash
python -m src.prompt_builder --prompt "赛博朋克城市夜景"
```

---

## 核心功能

### 1. 中文自然语言输入

直接用中文描述，自动翻译为高质量英文 prompt：

```python
# 输入
parse_input("中国龙 在云端 梦幻")

# 自动生成
"Chinese dragon, serpentine body, five claws, pearl, clouds, imperial, sky above clouds, dreamlike, highly detailed..."
```

### 2. 文化实体系统（70个）

内置 70 个文化实体，自动识别文化背景：

| 实体 | 文化 | 变体 |
|------|------|------|
| 龙 | 中国/西方/日本 | 3 种不同形态 |
| 凤凰 | 中国/西方 | 2 种不同形态 |
| 九尾狐 | 中国/日本/韩国 | 3 种不同形态 |
| 剑 | 中国/日本/西方 | 3 种不同形态 |
| ... | ... | ... |

```python
# 自动识别文化
parse_input("中国龙")  # → Chinese dragon (serpentine, no wings)
parse_input("西方龙")  # → Western dragon (winged, fire-breathing)
```

### 3. 场景模板（23个）

一键套用专业场景：

| 分类 | 模板 |
|------|------|
| 人像 | 肖像、全身像、情侣照、儿童照 |
| 商业 | 产品展示、美食、珠宝、海报 |
| 风景 | 山水、海景、城市、星空 |
| 艺术 | 油画、水彩、动漫、概念艺术 |

```python
# 使用模板
from src import TEMPLATES, generate_prompt_from_template
template = TEMPLATES["portrait"]
prompt = generate_prompt_from_template(template, "a young woman")
```

### 4. 图片放大

将 512x512 放大到 2048x2048：

```python
from src.adapters import upscaler
upscaled = upscaler.upscale("image.png", scale=4)
```

### 5. 负面提示

自动排除低质量内容：

```python
# 默认负面提示
"low quality, blurry, deformed, watermark, text, bad anatomy..."

# 自定义
generate_image(prompt, negative_prompt="ugly, blurry, text")
```

### 6. 批量生成

从文件批量生成：

```bash
# 创建 prompts.txt
echo 赛博朋克城市夜景 > prompts.txt
echo 水墨山水画 >> prompts.txt

# 批量生成
python -m src.prompt_builder --batch prompts.txt
```

### 7. DeepSeek 增强

用 AI 理解复杂中文描述：

```bash
# 设置 API Key
export DEEPSEEK_API_KEY="your-key"

# 使用 DeepSeek 增强
python -m src.prompt_builder --prompt "画一个有中国风的赛博朋克城市" --deepseek
```

---

## 使用场景

### 场景 1：快速生图

```python
from src import parse_input, build_prompt, generate_image

parsed = parse_input("水墨山水画 清晨 云雾缭绕")
prompt = build_prompt(parsed)
generate_image(prompt)
```

### 场景 2：精确控制

```python
from src import parse_input, build_prompt, generate_image

# 指定文化实体
parsed = parse_input("中国龙 在云端 梦幻")

# 指定负面提示
generate_image(prompt, negative_prompt="blurry, low quality")

# 指定模型
generate_image(prompt, model_name="stabilityai/sdxl")
```

### 场景 3：批量处理

```python
from src.utils.batch import batch_processor
from src import parse_input, build_prompt, generate_image

# 定义生成函数
def generate(text):
    parsed = parse_input(text, ask_clarification=False)
    prompt = build_prompt(parsed)
    return generate_image(prompt)

# 加载任务
prompts = ["赛博朋克城市", "水墨山水画", "樱花 日落"]
batch_processor.load_from_list(prompts)

# 执行批量生成
result = batch_processor.process(generate_func=generate, output_dir="output")
```

---

## API 接口

启动 API 服务器：

```bash
python -m api.server
# 访问 http://localhost:8000
```

### 接口列表

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/parse` | POST | 解析中文为 prompt |
| `/api/generate` | POST | 生成图片 |
| `/api/upscale` | POST | 放大图片 |
| `/api/templates` | GET | 获取模板列表 |
| `/api/models` | GET | 获取模型列表 |

### 示例

```javascript
// 解析 prompt
const res = await fetch('http://localhost:8000/api/parse', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ text: '赛博朋克城市夜景' })
});
const { prompt } = await res.json();

// 生成图片
const genRes = await fetch('http://localhost:8000/api/generate', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ prompt })
});
const { image } = await genRes.json();
```

---

## 项目结构

```
cpu-image-gen/
├── src/                    # 核心代码
│   ├── core/              # 解析器、构建器
│   ├── entities/          # 文化实体、模板
│   ├── adapters/          # 图片放大、DeepSeek
│   ├── utils/             # 配置、日志、批量
│   └── prompt_builder.py  # 主入口
├── api/                    # API 服务器
├── configs/               # 配置文件
├── docs/                  # 文档
├── tests/                 # 测试
├── web/                   # Web UI
└── examples/              # 示例
```

---

## 配置文件

| 文件 | 说明 |
|------|------|
| `configs/config.json` | 全局配置（步数、分辨率、负面提示） |
| `configs/keywords.json` | 中文关键词映射 |
| `configs/cultural_entities.json` | 文化实体库 |
| `configs/templates.json` | 场景模板 |
| `configs/model_configs.json` | 模型配置 |

---

## 扩展指南

### 添加新关键词

编辑 `configs/keywords.json`：

```json
{
  "style": {
    "你的风格": "your style in english"
  }
}
```

### 添加新文化实体

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
        "scenes": ["场景1"]
      }
    }
  }
}
```

### 添加新模板

编辑 `configs/templates.json`：

```json
{
  "your_template": {
    "label": "你的模板",
    "category": "类别",
    "base_prompt": "{subject}",
    "quality_additions": ["quality1", "quality2"]
  }
}
```

---

## 常见问题

**Q: 生成速度慢怎么办？**
A: 这是 CPU 生图的正常速度（约 50 秒/张）。如需加速，可以：
- 使用云 GPU 服务
- 降低分辨率（512x512）
- 减少步数（4 步）

**Q: 模型下载失败？**
A: 检查网络连接，或使用代理。模型缓存在 `~/.cache/huggingface/`。

**Q: 内存不足？**
A: 确保关闭其他程序，32GB 内存足够。

---

## 许可证

MIT License

---

## 致谢

- [Hugging Face Diffusers](https://github.com/huggingface/diffusers)
- [Stable Diffusion](https://stability.ai/)
- [SDXL Turbo](https://huggingface.co/stabilityai/sdxl-turbo)
