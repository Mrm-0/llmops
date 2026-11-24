#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@File     :download_model.py
@Brief    :从 HuggingFace 镜像站下载 bge-m3 嵌入模型到 models/bge-m3
          模型不入 Git 仓库（.gitignore 已排除），每台机器首次使用前执行一次：
              .\\venv\\Scripts\\python.exe download_model.py
"""
import os
import sys
from pathlib import Path

# 1.下载脚本必须能联网拉取，进程内临时关闭离线开关（.env 中的 TRANSFORMERS_OFFLINE=1 只影响运行时加载）
os.environ.pop("HF_HUB_OFFLINE", None)
os.environ.pop("TRANSFORMERS_OFFLINE", None)

# 2.默认走国内镜像 hf-mirror.com，无需科学上网，也无需登录 token（bge-m3 是公开仓库）
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

from huggingface_hub import snapshot_download

# 3.目标目录与项目代码保持一致：embeddings_service._DEFAULT_MODEL_DIR（api/models/bge-m3）
# 注意：本脚本在 scripts/ 子目录下，需取上级目录；compose 也是挂载的 api/models
MODEL_DIR = Path(__file__).resolve().parents[1] / "models" / "bge-m3"
WEIGHT_FILE = MODEL_DIR / "pytorch_model.bin"

# 4.bge-m3 仓库根目录的全部文件；显式列出以排除仓库中的 onnx/ 等无关大目录
ALLOW_PATTERNS = [
    "config.json",
    "config_sentence_transformers.json",
    "modules.json",
    "sentence_bert_config.json",
    "special_tokens_map.json",
    "tokenizer.json",
    "tokenizer_config.json",
    "sentencepiece.bpe.model",
    "pytorch_model.bin",
    "colbert_linear.pt",
    "sparse_linear.pt",
    "1_Pooling/config.json",
]


def main() -> int:
    # 1.已下载过则直接跳过（幂等：重复执行不会重复下载 2.2G）
    if WEIGHT_FILE.exists() and WEIGHT_FILE.stat().st_size > 2 * 1024**3:
        print(f"[跳过] 模型已存在：{WEIGHT_FILE}")
        return 0

    print(f"[下载] 目标目录：{MODEL_DIR}")
    print(f"[下载] 镜像站点：{os.environ['HF_ENDPOINT']}")

    # 2.snapshot_download 自带断点续传：中断后重新执行同一命令即可从断点继续
    snapshot_download(
        repo_id="BAAI/bge-m3",
        local_dir=MODEL_DIR,
        allow_patterns=ALLOW_PATTERNS,
        max_workers=4,
    )

    # 3.校验关键文件
    missing = [p for p in ALLOW_PATTERNS if not (MODEL_DIR / p).exists()]
    if missing:
        print(f"[失败] 以下文件缺失，请重新执行本脚本续传：{missing}")
        return 1

    print(f"[完成] 模型已就绪，共 {len(ALLOW_PATTERNS)} 个文件")
    return 0


if __name__ == "__main__":
    sys.exit(main())
