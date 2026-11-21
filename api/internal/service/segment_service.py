#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time     :2026/10/14 16:57
@Author   :314907015@qq.com
@File     :segment_service.py
"""
import logging
import uuid
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from injector import inject
from langchain_core.documents import Document as LCDocument
from redis import Redis
from sqlalchemy import asc, func

from internal.entity.cache_entity import LOCK_SEGMENT_UPDATE_ENABLED, LOCK_EXPIRE_TIME
from internal.entity.dataset_entity import SegmentStatus, DocumentStatus
from internal.exception import NotFoundException, ForbiddenException, FailException, ValidateErrorException
from internal.model import Segment, Document, Account
from internal.schema.segment_schema import GetSegmentsWithPageReq, CreateSegmentReq, UpdateSegmentReq
from pkg.paginator import Paginator
from pkg.sqlalchemy import SQLAlchemy
from .base_service import BaseService
from .embeddings_service import EmbeddingsService
from .jieba_service import JiebaService
from .keyword_table_service import KeywordTableService
from .vector_database_service import VectorDatabaseService
from ..lib.helper import generate_text_hash


@inject
@dataclass
class SegmentService(BaseService):
    """片段服务"""
    db: SQLAlchemy
    redis_client: Redis
    embeddings_service: EmbeddingsService
    jieba_service: JiebaService
    keyword_table_service: KeywordTableService
    vector_database_service: VectorDatabaseService

    def create_segment(self, dataset_id: UUID, document_id: UUID, req: CreateSegmentReq, account: Account) -> Segment:
        """根据传递的信息新增文档片段"""
        # 1.校验文档上传内容的总长度，最大为1000token
        token_count = self.embeddings_service.calculate_token_count(req.content.data)
        if token_count > 1000:
            raise ValidateErrorException("片段内容长度不能超过1000token")

        # 2.查询文档并校验权限
        document = self.get(Document, document_id)
        if (
                document is None
                or document.dataset_id != dataset_id
                or document.account_id != account.id
        ):
            raise FailException("该文档不存在，或无权限")

        # 3.判断文档装填是否可以新增片段数据，状态为completed才可以
        if document.status != DocumentStatus.COMPLETED:
            raise FailException("当前文档不可新增片段，请稍后重试")

        # 4.提取文档片段的最大位置
        position = self.db.session.query(func.coalesce(func.max(Segment.position), 0)).filter(
            Segment.document_id == document_id
        ).scalar()

        # 5.检测是否传递了keywords，没有则调用jieba服务生成关键词
        if req.keywords.data is None or len(req.keywords.data) == 0:
            req.keywords.data = self.jieba_service.extract_keywords(req.content.data, 10)

        # 6.在postgres和weaviate向量数据库中新增数据记录
        segment = None
        try:
            # 7.position+1并新增segment记录
            position += 1
            segment = self.create(
                Segment,
                account_id=account.id,
                dataset_id=dataset_id,
                document_id=document_id,
                node_id=uuid.uuid4(),
                position=position,
                content=req.content.data,
                character_count=len(req.content.data),
                token_count=token_count,
                keywords=req.keywords.data,
                hash=generate_text_hash(req.content.data),
                enabled=True,
                processing_started_at=datetime.now(),
                indexing_completed_at=datetime.now(),
                completed_at=datetime.now(),
                status=SegmentStatus.COMPLETED,
            )

            # 8.在weaviate向量数据库中新增记录
            self.vector_database_service.vector_store.add_documents(
                [LCDocument(
                    page_content=req.content.data,
                    metadata={
                        "account_id": str(document.account_id),
                        "dataset_id": str(document.dataset_id),
                        "document_id": str(document.id),
                        "segment_id": str(segment.id),
                        "node_id": str(segment.node_id),
                        "document_enabled": document.enabled,
                        "segment_enabled": True,
                    }
                )],
                ids=[str(segment.node_id)]
            )

            # 9.重新计算片段的字符总数和token总数
            document_character_count, document_token_count = self.db.session.query(
                func.coalesce(func.sum(Segment.character_count), 0),
                func.coalesce(func.sum(Segment.token_count), 0),
            ).filter(
                Segment.document_id == document_id
            ).first()

            # 10，更新文档的对应信息
            self.update(
                document,
                character_count=document_character_count,
                token_count=document_token_count,
            )

            # 11.更新关键词表信息
            if document.enabled is True:
                self.keyword_table_service.add_keyword_table_from_ids(dataset_id, [segment.id])

        except Exception as e:
            logging.exception("新增文档片段发生异常,错误信息:%(error)s", {"error": e})
            if segment:
                self.update(
                    segment,
                    error=str(e),
                    status=SegmentStatus.ERROR,
                    enabled=False,
                    disabled_at=datetime.now(),
                    stopped_at=datetime.now(),
                )
            raise FailException("新增文档片段失败，请稍后重试")

        return segment

    def get_segments_with_page(
            self,
            dataset_id: UUID,
            document_id: UUID,
            req: GetSegmentsWithPageReq,
            account: Account
    ) -> tuple[list[Segment], Paginator]:
        """根据传递的信息获取文档片段列表信息"""
        # 1.获取文档并校验权限
        document = self.get(Document, document_id)
        if document is None or document.dataset_id != dataset_id or document.account_id != account.id:
            raise NotFoundException("该文档不存在，或无权限，请核实后重试")

        # 2.构建分页器
        paginator = Paginator(db=self.db, req=req)

        # 3.构建筛选器
        filters = [Segment.document_id == document_id]
        if req.search_word.data:
            filters.append(Segment.content.ilike(f"%{req.search_word.data}%"))

        # 4.执行分页并获取数据
        segments = paginator.paginate(
            self.db.session.query(Segment).filter(*filters).order_by(asc("position"))
        )

        return segments, paginator

    def get_segment(self, dataset_id: UUID, document_id: UUID, segment_id: UUID, account: Account) -> Segment:
        """根据传递的信息获取指定文档片段"""
        segment = self.get(Segment, segment_id)
        if segment is None:
            raise NotFoundException("该文档不存在，请核实后重试")
        if (
                segment.dataset_id != dataset_id
                or segment.account_id != account.id
                or segment.document_id != document_id
        ):
            raise ForbiddenException("该用户无权限获取此文档，请核实后重试")

        return segment

    def update_segment(self, dataset_id: UUID, document_id: UUID, segment_id: UUID, req: UpdateSegmentReq,
                       account: Account):
        """根据传递的信息更新文档片段信息"""
        # 1.获取文档片段并校验权限
        segment = self.get(Segment, segment_id)
        if segment is None:
            raise NotFoundException("该文档不存在，请核实后重试")
        if (
                segment.dataset_id != dataset_id
                or segment.account_id != account.id
                or segment.document_id != document_id
        ):
            raise ForbiddenException("该用户无权限修改此文档，请核实后重试")

        # 2.判断文档是否处于可修改状态，只有构建完成completed状态下才可修改
        if segment.status != SegmentStatus.COMPLETED:
            raise ForbiddenException("当前文档处于不可修改状态，请稍后重试")

        # 3.检测是否传递了keywords，没有则调用jieba服务分词
        if req.keywords.data is None or len(req.keywords.data) == 0:
            req.keywords.data = self.jieba_service.extract_keywords(req.content.data, 10)

        # 4.计算新内容的hash值，用于判断是否需要更新向量数据库和关联文档详情
        new_hash = generate_text_hash(req.content.data)
        required_update = new_hash != segment.hash

        try:
            # 5.更新segment记录
            self.update(
                segment,
                keywords=req.keywords.data,
                content=req.content.data,
                hash=new_hash,
                character_count=len(req.content.data),
                token_count=self.embeddings_service.calculate_token_count(req.content.data),
            )

            # 6.更新片段归属关键词信息
            self.keyword_table_service.delete_keyword_table_from_ids(dataset_id, [segment.id])
            self.keyword_table_service.add_keyword_table_from_ids(dataset_id, [segment.id])

            # 7.检测是否需要更新文档信息和向量数据库
            if required_update:
                # 8.重新计算片段的字符总数和token总数
                document = segment.document
                document_character_count, document_token_count = self.db.session.query(
                    func.coalesce(func.sum(Segment.character_count), 0),
                    func.coalesce(func.sum(Segment.token_count), 0),
                ).filter(Segment.document_id == document_id).first()
                # 9，更新文档的对应信息
                self.update(
                    document,
                    character_count=document_character_count,
                    token_count=document_token_count,
                )
                # 10.更新向量数据库记录
                self.vector_database_service.collection.data.update(
                    uuid=str(segment.node_id),
                    properties={
                        "text": req.content.data,
                    },
                    vector=self.embeddings_service.embeddings.embed_query(req.content.data),
                )
        except Exception as e:
            logging.exception(
                "更新片段信息发生错误,segment_id:%(segment_id)s,错误信息:%(error)s",
                {"segment_id": segment_id, "error": e}
            )
            raise FailException("更新文档片段记录失败，请稍后重试")

        return segment

    def update_segment_enabled(self, dataset_id: UUID, document_id: UUID, segment_id: UUID, enabled: bool,
                               account: Account) -> Segment:
        """根据传递的信息更新文档片段的启用信息"""
        # 1.获取文档片段并校验权限
        segment = self.get(Segment, segment_id)
        if segment is None:
            raise NotFoundException("该文档不存在，请核实后重试")
        if (
                segment.dataset_id != dataset_id
                or segment.account_id != account.id
                or segment.document_id != document_id
        ):
            raise ForbiddenException("该用户无权限修改此文档，请核实后重试")

        # 2.判断文档是否处于可修改状态，只有构建完成completed状态下才可修改
        if segment.status != SegmentStatus.COMPLETED:
            raise ForbiddenException("当前文档处于不可修改状态，请稍后重试")

        # 3.判断修改的启用状态是否正确，需要与当前状态相反
        if segment.enabled == enabled:
            raise FailException(f"文档状态修改错误，当前已是{'启用' if enabled else '禁用'}状态")

        # 4.获取更新片段启用状态的缓存键并检测是否上锁
        cache_key = LOCK_SEGMENT_UPDATE_ENABLED.format(segment_id=segment.id)
        cache_result = self.redis_client.get(cache_key)
        if cache_result is not None:
            raise FailException("当前片段正在修改启用状态，请稍后再次尝试")

        # 5.上锁并更新对应的数据，涵盖：postgres记录、weaviate、关键词表
        with self.redis_client.lock(cache_key, LOCK_EXPIRE_TIME):
            try:
                # 6.修改postgres数据库里的文档片段启用状态
                self.update(
                    segment,
                    enabled=enabled,
                    disabled_at=None if enabled else datetime.now(),
                )

                # 7.更新关键词表的对应信息
                if enabled is True and segment.document.enabled is True:
                    self.keyword_table_service.add_keyword_table_from_ids(dataset_id, [segment_id])
                else:
                    self.keyword_table_service.delete_keyword_table_from_ids(dataset_id, [segment_id])

                # 8.同步处理weaviate向量数据库数据
                self.vector_database_service.collection.data.update(
                    uuid=segment.node_id,
                    properties={
                        "segment_enabled": enabled,
                    }
                )
            except Exception as e:
                logging.exception(
                    "更新文档片段启用状态出现异常,segment_id:%(segment_id)s,错误信息:%(error)s",
                    {"segment_id": segment_id, "error": e}
                )
                self.update(
                    segment,
                    error=str(e),
                    status=SegmentStatus.ERROR,
                    enabled=False,
                    disabled_at=datetime.now(),
                    stopped_at=datetime.now(),
                )
                raise FailException("更新文档片段启用状态失败，请稍后重试")

    def delete_segment(self, dataset_id: UUID, document_id: UUID, segment_id: UUID, account: Account) -> Segment:
        """根据传递的信息删除文档片段信息"""
        # 1.获取文档片段并校验权限
        segment = self.get(Segment, segment_id)
        if segment is None:
            raise NotFoundException("该文档不存在，请核实后重试")
        if (
                segment.dataset_id != dataset_id
                or segment.account_id != account.id
                or segment.document_id != document_id
        ):
            raise ForbiddenException("该用户无权限修改此文档，请核实后重试")

        # 2.判断文档片段是否处于可删除状态，只有completed和error状态才可以删除
        if segment.status not in [SegmentStatus.COMPLETED, SegmentStatus.ERROR]:
            raise FailException("该文档片段处于不可删除状态，请稍后重试")

        # 3，删除文档片段，获取文档
        document = segment.document
        self.delete(segment)

        # 4.同步删除关键词表中属于该片段的关键词
        self.keyword_table_service.delete_keyword_table_from_ids(dataset_id, [segment_id])

        # 5.同步删除向量数据库中的记录
        try:
            self.vector_database_service.collection.data.delete_by_id(str(segment.node_id))
        except Exception as e:
            logging.exception(
                "删除文档片段记录失败,segment_id:%(segment_id)s,错误信息:%(error)s",
                {"segment_id": segment_id, "error": e}
            )

        # 6.更新文档信息，涵盖字符总数、token总数
        document_character_count, document_token_count = self.db.session.query(
            func.coalesce(func.sum(Segment.character_count), 0),
            func.coalesce(func.sum(Segment.token_count), 0),
        ).filter(Segment.document_id == document_id).first()
        self.update(
            document,
            character_count=document_character_count,
            token_count=document_token_count,
        )

        return segment
