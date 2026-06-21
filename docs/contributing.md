# 贡献指南

感谢你对 CPU Image Gen 的关注！我们欢迎各种形式的贡献。

## 如何贡献

### 报告问题

1. 在 GitHub Issues 中搜索是否已有相同问题
2. 如果没有，创建一个新的 Issue
3. 提供详细的问题描述和复现步骤

### 提交代码

1. Fork 本仓库
2. 创建你的特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交你的更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建一个 Pull Request

### 代码规范

- 遵循 PEP 8 代码风格
- 添加必要的注释
- 确保代码可以正常运行
- 更新相关文档

## 贡献方向

### 1. 扩展关键词库

添加更多中文关键词映射：

```json
// 在 configs/keywords.json 中添加
{
  "style": {
    "新风格": "new style in english"
  }
}
```

### 2. 添加文化实体

添加更多文化实体：

```json
// 在 configs/cultural_entities.json 中添加
{
  "new_entity": {
    "type": "creature",
    "label": "新实体",
    "variants": {
      "chinese": {
        "name_en": "New Entity (Chinese)",
        "morphology": ["特征"],
        "elements": ["元素"],
        "atmosphere": ["氛围"],
        "scenes": ["场景"]
      }
    }
  }
}
```

### 3. 添加场景模板

添加更多场景模板：

```json
// 在 configs/templates.json 中添加
{
  "new_template": {
    "label": "新模板",
    "category": "类别",
    "base_prompt": "{subject}",
    "quality_additions": ["quality1", "quality2"],
    "composition": "composition keywords",
    "lighting": "lighting keywords"
  }
}
```

### 4. 支持新模型

添加新模型的配置：

```json
// 在 configs/model_configs.json 中添加
{
  "model-name": {
    "name": "Model Name",
    "max_tokens": 77,
    "prompt_format": "keywords",
    "quality_keywords": ["quality1", "quality2"],
    "recommended_settings": {
      "steps": 20,
      "width": 1024,
      "height": 1024
    }
  }
}
```

### 5. 改进代码

- 优化性能
- 修复 bug
- 添加新功能
- 改进文档

## 开发环境设置

```bash
# 克隆仓库
git clone https://github.com/yourusername/cpu-image-gen.git
cd cpu-image-gen

# 创建虚拟环境
python -m venv venv
source venv/bin/activate

# 安装开发依赖
pip install -r requirements.txt
pip install pytest black flake8

# 运行测试
pytest tests/

# 代码格式化
black src/
```

## 提交规范

使用 [Conventional Commits](https://www.conventionalcommits.org/) 规范：

- `feat:` 新功能
- `fix:` 修复 bug
- `docs:` 文档更新
- `style:` 代码格式（不影响功能）
- `refactor:` 重构
- `test:` 测试相关
- `chore:` 构建/工具相关

示例：
```
feat: 添加日语文化实体支持
fix: 修复关键词映射错误
docs: 更新安装指南
```

## 问题反馈

如有问题，请通过以下方式反馈：

1. GitHub Issues
2. 邮件：telephonbox@outlook.com
3. 微信群：（添加群主微信）

## 许可证

贡献的代码将遵循 MIT 许可证。
