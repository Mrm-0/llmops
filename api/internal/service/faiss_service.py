#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time     :2026/11/17 11:16
@Author   :314907015@qq.com
@File     :faiss_service.py
"""
import logging
from pathlib import Path
from typing import Optional

from injector import inject
from langchain_community.vectorstores import FAISS
from langchain_core.tools import BaseTool, tool
from pydantic import BaseModel, Field

from internal.core.agent.entities.agent_entity import DATASET_RETRIEVAL_TOOL_NAME
from internal.lib.helper import combine_documents
from .embeddings_service import EmbeddingsService


@inject
class FaissService:
    """Faiss向量数据库服务"""
    faiss: FAISS
    embeddings_service: EmbeddingsService

    def __init__(self, embeddings_service: EmbeddingsService) -> None:
        """构造函数，完成Faiss向量数据库初始化"""
        # 1.赋值embeddings_service
        self.embeddings_service = embeddings_service

        # 2.获取internal路径并计算本地向量数据库的实际路径
        internal_path = Path(__file__).resolve().parent.parent
        self._faiss_vector_store_path = internal_path / "core" / "vector_store"

        # 3.faiss实例采取惰性加载：构造函数不做磁盘I/O，
        #   避免首次部署（vector_store目录尚不存在）时应用无法启动
        self._faiss: FAISS | None = None

        # 4.记录加载失败时的索引文件指纹，避免每次对话都重复加载/探测维度；
        #   索引被重建（文件时间或大小变化）后会自动重试
        self._failed_signature: tuple[int, int] | None = None

    def _index_signature(self) -> tuple[int, int] | None:
        """索引文件指纹（mtime_ns + size），用于判断索引是否已被重建"""
        try:
            stat = (self._faiss_vector_store_path / "index.faiss").stat()
            return stat.st_mtime_ns, stat.st_size
        except OSError:
            return None

    @property
    def is_available(self) -> bool:
        """判断本地FAISS索引是否可用（索引文件是否已生成）"""
        return (self._faiss_vector_store_path / "index.faiss").exists()

    @property
    def faiss(self) -> FAISS:
        """惰性加载FAISS索引：首次访问时才从磁盘读取"""
        if self._faiss is None:
            # 校验索引文件是否存在，不存在则给出明确的错误提示
            if not self.is_available:
                raise FileNotFoundError(
                    f"FAISS索引不存在：{self._faiss_vector_store_path}，"
                    f"请先创建知识库并完成文档索引后再使用知识库检索功能"
                )
            vector_store = FAISS.load_local(
                folder_path=self._faiss_vector_store_path,
                embeddings=self.embeddings_service.embeddings,
                allow_dangerous_deserialization=True,
            )

            # 校验索引维度与当前embedding模型是否一致。
            # 常见场景：索引来自旧环境（如OpenAI 1536维），而当前模型是BGE-M3（1024维），
            # 此时load_local能成功，但检索时faiss会因维度不符直接报错，提前拦下更清晰。
            expected_dim = len(self.embeddings_service.embeddings.embed_query("dimension-check"))
            if vector_store.index.d != expected_dim:
                raise ValueError(
                    f"FAISS索引维度({vector_store.index.d})与当前embedding模型维度({expected_dim})不一致，"
                    f"请执行 `python scripts/rebuild_faiss_index.py` 重建索引"
                )

            self._faiss = vector_store
        return self._faiss

    def convert_faiss_to_tool(self) -> Optional[BaseTool]:
        """将Faiss向量数据库检索器转换成LangChain工具

        索引不存在或不可用（如维度与当前embedding模型不匹配）时，
        返回None而不是抛异常，由调用方跳过该工具，避免整个Agent不可用。
        """
        try:
            if self._failed_signature is not None and self._failed_signature == self._index_signature():
                return None

            # 1.将Faiss向量数据库转换成检索器
            retrieval = self.faiss.as_retriever(
                search_type="mmr",
                search_kwargs={"k": 5, "fetch_k": 20},
            )
        except Exception as exc:  # noqa: BLE001 - 降级容错，任何加载失败都不应拖垮对话
            self._failed_signature = self._index_signature()
            logging.getLogger(__name__).warning(
                "FAISS索引不可用（%s）：%s，本次跳过知识库检索工具",
                self._faiss_vector_store_path,
                exc,
            )
            return None

        # 2.构建检索链，并将检索的结果合并成字符串
        search_chain = retrieval | combine_documents

        class DatasetRetrievalInput(BaseModel):
            """知识库检索工具输入结构"""
            query: str = Field(description="知识库检索query语句，类型为字符串")

        @tool(DATASET_RETRIEVAL_TOOL_NAME, args_schema=DatasetRetrievalInput)
        def dataset_retrieval(query: str) -> str:
            """如果需要检索扩展的知识库内容，当你觉得用户的提问超过你的知识范围时，可以尝试调用该工具，输入为搜索query语句，返回数据为检索内容字符串"""
            return search_chain.invoke(query)

        return dataset_retrieval
