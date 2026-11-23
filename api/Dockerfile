# 基础镜像：Python 3.12（与 requirements 中 langchain 1.x / pydantic 2.x 等新版本依赖兼容）
FROM python:3.12-slim-bookworm AS base

# 国内 pip 源，加速依赖安装
ENV PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple \
    PIP_DEFAULT_TIMEOUT=120

# 将 requirements.txt 拷贝到根目录下
COPY requirements.txt .

# 先单独安装 CPU 版 torch：Linux 下 PyPI 默认提供内置 CUDA 的 wheel（镜像会多出 2~3G），
# 项目实际只用 CPU（EMBEDDINGS_DEVICE 默认 cpu），这里从 pytorch 官方 CPU 源安装
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --prefix=/pkg torch==2.15.0+cpu --index-url https://download.pytorch.org/whl/cpu

# 安装主依赖
# PYTHONPATH 指向 /pkg 的 site-packages，让本次 pip 能识别上一步已安装的 torch==2.15.0+cpu，
# 否则 pip 感知不到（--prefix 不在默认 sys.path 里），sentence-transformers 会重新拉 CUDA 版 torch
RUN --mount=type=cache,target=/root/.cache/pip \
    PYTHONPATH=/pkg/lib/python3.12/site-packages pip install --prefix=/pkg -r requirements.txt

# 二阶段生产环境构建
FROM base AS production

# 设置工作目录
WORKDIR /app/api

# 定义环境变量
ENV FLASK_APP=app/http/app.py
ENV FLASK_ENV=production
ENV FLASK_DEBUG=0
ENV NLTK_DATA=/app/api/internal/core/unstructured/nltk_data
ENV HF_ENDPOINT=https://hf-mirror.com

# 设置容器时区为中国标准时间，避免时区错误
ENV TZ=Asia/Shanghai

# 拷贝第三方依赖包+源码文件
COPY --from=base /pkg /usr/local
COPY . /app/api

# 拷贝运行脚本并设置权限
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# 暴露5001端口
EXPOSE 5001

# 运行脚本并启动项目
ENTRYPOINT ["/bin/bash", "/entrypoint.sh"]
