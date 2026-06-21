# 快速开始指南

## 5 分钟上手

### 第 1 步：安装

```bash
# 克隆项目
git clone https://github.com/xukin10/cpu-image-gen.git
cd cpu-image-gen

# 安装依赖
pip install -r requirements.txt
```

### 第 2 步：生成第一张图

创建 `my_first_image.py`：

```python
from src import parse_input, build_prompt, generate_image

# 用中文描述你想要的图片
text = "赛博朋克城市夜景，雨天霓虹灯"

# 解析为英文 prompt
parsed = parse_input(text)
prompt = build_prompt(parsed)
print(f"生成的 prompt: {prompt}")

# 生成图片
result = generate_image(prompt, raw_input=text)
print(f"图片已保存: {result}")
```

运行：

```bash
python my_first_image.py
```

### 第 3 步：查看结果

图片会保存在 `output/` 目录。

---

## 更多用法

### 用命令行

```bash
# 快速生成
python -m src.prompt_builder --prompt "水墨山水画"

# 指定模型
python -m src.prompt_builder --prompt "樱花 日落" --model stabilityai/sdxl

# 批量生成
python -m src.prompt_builder --batch prompts.txt
```

### 用 Python API

```python
from src import parse_input, build_prompt, generate_image

# 基础用法
parsed = parse_input("中国龙 在云端")
prompt = build_prompt(parsed)
generate_image(prompt)

# 高级用法
generate_image(
    prompt,
    negative_prompt="blurry, low quality",  # 负面提示
    model_name="stabilityai/sdxl",          # 指定模型
    steps=8,                                 # 更多步数
    width=768,                               # 更高分辨率
    height=768
)
```

### 用 API

```bash
# 启动 API 服务器
python -m api.server

# 然后用 HTTP 请求调用
curl -X POST http://localhost:8000/api/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "赛博朋克城市夜景"}'
```

---

## 常见问题

### Q: 生成速度慢？
A: CPU 生图约 50 秒/张是正常的。如需加速：
- 使用云 GPU 服务
- 降低分辨率到 512x512
- 减少步数到 4

### Q: 模型下载失败？
A: 检查网络，或使用代理。模型缓存在 `~/.cache/huggingface/`

### Q: 内存不足？
A: 关闭其他程序，32GB 内存足够

### Q: 想生成视频？
A: 当前只支持生成视频 prompt，实际视频生成需要专用模型（如 AnimateDiff）

---

## 下一步

1. 阅读 [完整文档](README.md)
2. 查看 [API 文档](docs/api.md)
3. 了解 [Prompt 调控](prompt-guide.md)
4. 尝试 [扩展功能](#扩展指南)
