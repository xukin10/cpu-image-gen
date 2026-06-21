# 安装指南

## 环境要求

- Python 3.8 或更高版本
- 16GB+ 内存（推荐 32GB）
- 7GB+ 磁盘空间（用于模型缓存）
- Windows/Linux/macOS

## 安装步骤

### 1. 克隆仓库

```bash
git clone https://github.com/yourusername/cpu-image-gen.git
cd cpu-image-gen
```

### 2. 创建虚拟环境

```bash
# Linux/macOS
python -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
.\venv\Scripts\activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 验证安装

```bash
python tests/test_basic.py
```

## Docker 安装（可选）

```bash
cd docker
docker-compose up -d
```

## 常见问题

### 问题 1: PyTorch 安装失败

如果 PyTorch 安装失败，可以尝试：

```bash
pip install torch --index-url https://download.pytorch.org/whl/cpu
```

### 问题 2: 模型下载失败

首次运行会下载模型（约 6GB）。如果下载失败：

1. 检查网络连接
2. 使用代理
3. 手动下载模型到 `models/` 目录

### 问题 3: 内存不足

如果出现内存不足错误：

1. 关闭其他程序
2. 使用更小的模型（SDXL Turbo）
3. 降低分辨率（512x512）
