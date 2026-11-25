#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time     :2026/11/25 14:30
@Author   :314907015@qq.com
@File     :rebuild_faiss_index.py

重建本地 FAISS 向量索引，使其与当前 embedding 模型维度一致。

背景：
    internal/core/vector_store 下的 index.faiss 若来自旧环境（例如项目自带的
    OpenAI text-embedding-ada-002 版本，1536 维），与当前使用的 BGE-M3
    （1024 维）维度不匹配，检索时会直接抛错。
    本脚本从旧 index.pkl 的 docstore 中提取原始文档（page_content + metadata），
    用当前 embedding 模型重新向量化并覆盖写入，旧文件自动备份。

用法（在 api 容器内执行）：
    docker compose exec llmops-api python scripts/rebuild_faiss_index.py

可选环境变量：
    FAISS_STORE_DIR       索引目录，默认 <api根>/internal/core/vector_store
    EMBEDDINGS_MODEL_PATH 模型路径，默认 <api根>/models/bge-m3
    EMBEDDINGS_DEVICE     cpu / cuda，默认 cpu
"""
import os
import pickle
import shutil
import sys
import time
from pathlib import Path


def main() -> int:
    api_root = Path(__file__).resolve().parents[1]
    store_dir = Path(
        os.getenv("FAISS_STORE_DIR") or (api_root / "internal" / "core" / "vector_store")
    )
    index_file = store_dir / "index.faiss"
    pkl_file = store_dir / "index.pkl"

    print(f"索引目录：{store_dir}")
    if not pkl_file.exists():
        print(f"[x] 找不到旧索引的 docstore：{pkl_file}")
        print("    请把原始 index.pkl 放进该目录后再执行，或改用知识库(Weaviate)方案。")
        return 1

    # 1. 读取旧 docstore 中的原始文档
    print(f"[1/4] 读取旧 docstore：{pkl_file}")
    with pkl_file.open("rb") as fp:
        docstore, _index_to_docstore_id = pickle.load(fp)
    docs = list(getattr(docstore, "_dict", {}).values())
    print(f"      共 {len(docs)} 条文档片段")
    if not docs:
        print("[x] docstore 为空，没有内容可用于重建")
        return 1

    # 2. 加载当前 embedding 模型
    sys.path.insert(0, str(api_root))
    from langchain_community.vectorstores import FAISS
    from langchain_huggingface import HuggingFaceEmbeddings

    model_path = os.getenv("EMBEDDINGS_MODEL_PATH") or str(api_root / "models" / "bge-m3")
    local_only = (os.getenv("EMBEDDINGS_LOCAL_ONLY") or "true").strip().lower() == "true"
    print(f"[2/4] 加载 embedding 模型：{model_path}")
    embeddings = HuggingFaceEmbeddings(
        model_name=model_path,
        model_kwargs={
            "device": os.getenv("EMBEDDINGS_DEVICE") or "cpu",
            "trust_remote_code": True,
            "local_files_only": local_only,
        },
        encode_kwargs={"normalize_embeddings": True},
    )
    probe_dim = len(embeddings.embed_query("维度探测"))
    print(f"      当前模型输出维度：{probe_dim}")

    # 3. 重新向量化
    print("[3/4] 重新向量化并构建索引（耗时取决于文档量，请耐心等待）")
    started = time.time()
    vector_store = FAISS.from_documents(docs, embeddings)
    print(
        f"      完成，用时 {time.time() - started:.1f}s，"
        f"条数 {vector_store.index.ntotal}，维度 {vector_store.index.d}"
    )
    if vector_store.index.d != probe_dim:
        print("[x] 维度自检失败，已中止，旧文件未改动")
        return 1

    # 4. 备份旧文件并写入新索引
    print("[4/4] 备份旧索引并写入新索引")
    stamp = time.strftime("%Y%m%d%H%M%S")
    for path in (index_file, pkl_file):
        if path.exists():
            backup = path.with_name(f"{path.name}.bak-{stamp}")
            shutil.move(str(path), str(backup))
            print(f"      已备份 {path.name} -> {backup.name}")

    vector_store.save_local(str(store_dir))
    print(f"[✓] 新索引已写入 {store_dir}")
    print("    若该目录是挂载进容器的，文件会直接落到宿主机，重启不丢。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
