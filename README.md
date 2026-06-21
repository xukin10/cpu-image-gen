# CPU Image Gen

一个强大的 AI 生图 Prompt 构建工具，支持中文自然语言输入，自动构建高质量 prompt。

## 功能特性

- **中文自然语言输入**：直接用中文描述，自动翻译为英文 prompt
- **62 个文化实体**：覆盖中国/日本/西方/希腊/北欧/埃及六大文化体系
- **24 个场景模板**：人像/商业/风景/艺术四大类
- **5 个模型适配**：SDXL Turbo / SDXL 1.0 / SD 3.0 / Flux.1 Dev / Flux.1 Schnell
- **多模态支持**：视频 prompt / 3D prompt 生成
- **高级品质优化**：自动添加构图/光影/色彩/场景丰富度关键词

## 安装

### 环境要求

- Python 3.8+
- 16GB+ 内存（推荐 32GB）
- 7GB+ 磁盘空间（模型缓存）

### 安装步骤

```bash
# 克隆仓库
git clone https://github.com/xukin10/cpu-image-gen.git
cd cpu-image-gen

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
.\venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

## 快速开始

### 基础使用

```python
from src import parse_input, build_prompt, generate_image

# 解析中文输入
parsed = parse_input("赛博朋克城市夜景，雨天霓虹灯")

# 构建 prompt
prompt = build_prompt(parsed)
# 输出: cyberpunk, night cityscape, in a city, rainy, neon lights, ...

# 生成图片
generate_image(prompt)
```

### 命令行使用

```bash
# 快速生成
python -m src.prompt_builder --prompt "赛博朋克城市夜景"

# 指定模型
python -m src.prompt_builder --prompt "水墨山水画" --model stabilityai/sdxl

# 批量生成
python -m src.prompt_builder --batch prompts.txt
```

## 功能详解

### 1. 文化实体系统

支持 62 个文化实体，自动识别文化背景：

```python
# 输入
parse_input("中国龙 在云端")
# 自动识别为中国龙，生成：Chinese dragon, serpentine body, five claws, ...

# 输入
parse_input("西方龙 在洞穴")
# 自动识别为西方龙，生成：Western dragon, winged, four legs with claws, ...
```

### 2. 场景模板

24 个预定义模板，一键生成高质量 prompt：

```python
from src import select_template, generate_prompt_from_template

# 选择模板
tpl_key, template = select_template()

# 生成 prompt
prompt = generate_prompt_from_template(template, "a young woman")
```

### 3. 模型适配

支持 5 个主流模型，自动调整 prompt 格式：

| 模型 | 推荐步数 | 推荐分辨率 |
|------|----------|------------|
| SDXL Turbo | 4 | 512x512 |
| SDXL 1.0 | 25 | 1024x1024 |
| SD 3.0 | 25 | 1024x1024 |
| Flux.1 Dev | 25 | 1024x1024 |
| Flux.1 Schnell | 4 | 1024x1024 |

### 4. 多模态支持

```python
from src import build_video_prompt, build_3d_prompt

# 视频 prompt
video_prompt = build_video_prompt(
    "a dragon flying over a city",
    motion="flying",
    camera="tracking shot"
)

# 3D prompt
prompt_3d = build_3d_prompt(
    "a medieval sword",
    material="metallic material",
    render_style="photorealistic render"
)
```

## 配置文件

所有配置文件在 `configs/` 目录：

| 文件 | 说明 |
|------|------|
| `keywords.json` | 中文关键词映射 |
| `cultural_entities.json` | 文化实体库 |
| `templates.json` | 场景模板 |
| `model_configs.json` | 模型配置 |
| `multimodal_configs.json` | 多模态配置 |
| `config.json` | 全局配置 |

## 项目结构

```
cpu-image-gen/
├── src/                    # 源码
│   ├── __init__.py
│   └── prompt_builder.py   # 主程序
├── configs/                # 配置文件
├── docs/                   # 文档
├── examples/               # 示例
├── docker/                 # Docker 配置
├── tests/                  # 测试
├── requirements.txt        # 依赖
├── setup.py               # 安装脚本
├── pyproject.toml         # Python 配置
└── README.md              # 本文档
```

## 贡献指南

欢迎贡献！请查看 [CONTRIBUTING.md](docs/contributing.md)。

## 许可证

MIT License - 详见 [LICENSE](LICENSE)

## 致谢

- [Hugging Face Diffusers](https://github.com/huggingface/diffusers)
- [Stable Diffusion](https://stability.ai/)
- [SDXL Turbo](https://huggingface.co/stabilityai/sdxl-turbo)
