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
            self._faiss = FAISS.load_local(
                folder_path=self._faiss_vector_store_path,
                embeddings=self.embeddings_service.embeddings,
                allow_dangerous_deserialization=True,
            )
        return self._faiss

    def convert_faiss_to_tool(self) -> Optional[BaseTool]:
        """将Faiss向量数据库检索器转换成LangChain工具

        本地FAISS索引不存在时（例如全新部署、尚未构建本地索引），
        返回None而不是抛异常，由调用方跳过该工具，避免整个Agent不可用。
        """
        if not self.is_available:
            logging.getLogger(__name__).warning(
                "FAISS索引不存在（%s），本次跳过知识库检索工具",
                self._faiss_vector_store_path,
            )
            return None

        # 1.将Faiss向量数据库转换成检索器
        retrieval = self.faiss.as_retriever(
            search_type="mmr",
            search_kwargs={"k": 5, "fetch_k": 20},
        )

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
