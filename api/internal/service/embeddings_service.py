#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time     :2026/10/10 13:09
@Author   :314907015@qq.com
@File     :embeddings_service.py
"""
import os
from dataclasses import dataclass
from pathlib import Path

import tiktoken
from injector import inject, singleton
from langchain_classic.embeddings import CacheBackedEmbeddings
from langchain_community.storage import RedisStore
from langchain_core.embeddings import Embeddings
from langchain_huggingface import HuggingFaceEmbeddings
from redis import Redis

# 兜底模型目录：基于 __file__ 推导（相对项目根），项目整体搬迁或换机器依然有效
_DEFAULT_MODEL_DIR = Path(__file__).resolve().parents[2] / "models" / "bge-m3"


def _resolve_model_path() -> str:
    """解析嵌入模型路径，优先读取环境变量，支持本地目录或 HuggingFace 仓库ID"""
    return os.getenv("EMBEDDINGS_MODEL_PATH") or str(_DEFAULT_MODEL_DIR)


def _is_local_only() -> bool:
    """是否只从本地加载，默认开启以避免启动时联网校验权重导致超时"""
    return (os.getenv("EMBEDDINGS_LOCAL_ONLY") or "true").strip().lower() == "true"


@singleton
@inject
@dataclass
class EmbeddingsService:
    """文本嵌入模型服务"""
    _store: RedisStore
    _embeddings: Embeddings
    _cache_backed_embeddings: CacheBackedEmbeddings
    _encoding = tiktoken.get_encoding("o200k_base")

    def __init__(self, redis: Redis):
        """初始化文本嵌入模型客户端、存储器、缓存客户端"""
        self._store = RedisStore(client=redis)

        self._embeddings = HuggingFaceEmbeddings(
            model_name=_resolve_model_path(),
            # 不再传 cache_folder：指向本地目录后该参数无意义，且 Path.cwd() 会随启动目录漂移
            model_kwargs={
                "device": os.getenv("EMBEDDINGS_DEVICE") or "cpu",  # 有 NVIDIA 显卡可设 cuda
                "trust_remote_code": True,
                "local_files_only": _is_local_only(),  # 禁止启动时发起任何 HEAD 请求
            },
            encode_kwargs={
                "normalize_embeddings": True,  # bge 系列必须归一化，相似度用内积/余弦才正确
                # bge-m3 最长支持 8192 token，不显式限制也行；显存/内存紧张可设 1024
            },
        )

        # 如需切回 OpenAI 兼容的嵌入服务（如 TEI），替换上面的 self._embeddings 即可：
        # self._embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
        self._cache_backed_embeddings = CacheBackedEmbeddings.from_bytes_store(
            self._embeddings,
            self._store,
            namespace="embeddings",
            # 注意：langchain的key_encoder只接受"sha256"（不带横线），带横线会抛Unsupported algorithm
            key_encoder="sha256",
        )

    @classmethod
    def calculate_token_count(cls, query: str) -> int:
        """计算传入文本的token数"""
        encoding = tiktoken.encoding_for_model("gpt-5")
        return len(encoding.encode(query))

    @property
    def store(self) -> RedisStore:
        return self._store

    @property
    def embeddings(self) -> Embeddings:
        return self._embeddings

    @property
    def cache_backed_embeddings(self) -> CacheBackedEmbeddings:
        return self._cache_backed_embeddings
