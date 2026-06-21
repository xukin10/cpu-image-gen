FROM python:3.10-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目文件
COPY . .

# 预下载模型（可选，会增加镜像大小）
# RUN python -c "from diffusers import AutoPipelineForText2Image; AutoPipelineForText2Image.from_pretrained('stabilityai/sdxl-turbo')"

# 暴露端口（如果需要 Web UI）
# EXPOSE 8080

# 启动命令
CMD ["python", "-m", "src.prompt_builder"]
