#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time     :2026/10/9 12:45
@Author   :314907015@qq.com
@File     :dataset_service.py
"""
import logging
from dataclasses import dataclass
from uuid import UUID

from injector import inject
from sqlalchemy import desc

from internal.entity.dataset_entity import DEFAULT_DATASET_DESCRIPTION_FORMATTER
from internal.exception import ValidateErrorException, NotFoundException, FailException
from internal.lib.helper import datetime_to_timestamp
from internal.model import Dataset, Segment, DatasetQuery, AppDatasetJoin, Account
from internal.schema.dataset_schema import CreateDatasetReq, UpdateDatasetReq, GetDatasetsWithPageReq, HitReq
from internal.task.dataset_task import delete_dataset
from pkg.paginator import Paginator
from pkg.sqlalchemy import SQLAlchemy
from .base_service import BaseService
from .retrieval_service import RetrievalService


@inject
@dataclass
class DatasetService(BaseService):
    """知识库服务"""
    db: SQLAlchemy
    retrieval_service: RetrievalService

    def get_dataset_queries(self, dataset_id: UUID, account: Account) -> list[DatasetQuery]:
        """根据传递的知识库id获取最近10条的查询记录"""
        # 1.获取知识库并校验权限
        dataset = self.get(Dataset, dataset_id)
        if dataset is None or dataset.account_id != account.id:
            raise NotFoundException("知识库不存在")

        # 2.调用知识库查询模型查找最近的10条查询记录
        dataset_queries = self.db.session.query(DatasetQuery).filter(
            DatasetQuery.dataset_id == dataset_id,
        ).order_by(desc("created_at")).limit(10).all()

        return dataset_queries

    def create_dataset(self, req: CreateDatasetReq, account: Account) -> Dataset:
        """根据传递的请求信息创建知识库"""
        # 1.检测该账号下有没有同名知识库
        dataset = self.db.session.query(Dataset).filter_by(
            account_id=account.id,
            name=req.name.data,
        ).one_or_none()
        if dataset:
            raise ValidateErrorException(f"该知识库{req.name.data}已存在")

        # 2.检测是否传递了知识库的描述信息，没有则补充上
        if req.description.data is None or req.description.data.strip() == "":
            req.description.data = DEFAULT_DATASET_DESCRIPTION_FORMATTER.format(name=req.name.data)

        # 3.创建知识库并返回
        return self.create(
            Dataset,
            account_id=account.id,
            name=req.name.data,
            icon=req.icon.data,
            description=req.description.data,
        )

    def get_dataset(self, dataset_id: UUID, account: Account) -> Dataset:
        """根据传递的知识库id获取知识库记录"""
        dataset = self.get(Dataset, dataset_id)
        if dataset is None or dataset.account_id != account.id:
            raise NotFoundException("知识库不存在，或无权限，请稍后重试")
        return dataset

    def update_dataset(self, dataset_id: UUID, req: UpdateDatasetReq, account: Account) -> Dataset:
        """根据传递的知识库id+数据更新知识库"""
        # 1.检测知识库是否存在并校验
        dataset = self.get(Dataset, dataset_id)
        if dataset is None or dataset.account_id != account.id:
            raise NotFoundException("知识库不存在，或无权限，请稍后重试")

        # 2.检测修改后的知识库名称是否出现重名
        check_dataset = self.db.session.query(Dataset).filter(
            Dataset.account_id == account.id,
            Dataset.name == req.name.data,
            Dataset.id != dataset_id,
        ).one_or_none()
        if check_dataset:
            raise ValidateErrorException(f"该知识库{req.name.data}已存在")

        # 3.校验描述信息是否为空，为空则补充
        if req.description.data is None or req.description.data.strip() == "":
            req.description.data = DEFAULT_DATASET_DESCRIPTION_FORMATTER.format(name=req.name.data)

        # 4.更新数据
        self.update(
            dataset,
            name=req.name.data,
            icon=req.icon.data,
            description=req.description.data,
        )

        return dataset

    def get_datasets_with_page(self, req: GetDatasetsWithPageReq, account: Account) -> tuple[list[Dataset], Paginator]:
        """根据传递的请求信息获取知识库分页列表数据"""
        # 1.构建分页查询器
        paginator = Paginator(self.db, req)

        # 2.构建筛选器
        filters = [Dataset.account_id == account.id]
        if req.search_word.data:
            filters.append(Dataset.name.ilike(f"%{req.search_word.data}%"))

        # 3.执行分页并获取数据
        datasets = paginator.paginate(
            self.db.session.query(Dataset).filter(*filters).order_by(desc("created_at")),
        )

        return datasets, paginator

    def delete_dataset(self, dataset_id: UUID, account: Account) -> Dataset:
        """根据传递的知识库id删除指定知识库，涵盖知识库下的所有文档、片段、关键词以及向量数据库中储存的数据"""
        # 1.获取知识库并校验权限
        dataset = self.get(Dataset, dataset_id)
        if dataset is None or dataset.account_id != account.id:
            raise NotFoundException("知识库不存在，或无权限，请稍后重试")

        try:
            # 2.调用异步任务
            delete_dataset.delay(dataset_id)

            # 3.删除知识库基础记录以及知识库和应用关联的记录
            self.delete(dataset)
            with self.db.auto_commit():
                self.db.session.query(AppDatasetJoin).filter(
                    AppDatasetJoin.dataset_id == dataset_id,
                ).delete()

        except Exception as e:
            logging.exception(
                "删除知识库出现错误,知识库id:%(dataset_id)s,错误信息:%(error)s",
                {"dataset_id": dataset_id, "error": e}
            )
            raise FailException("删除知识库失败，请重试")

    def hit(self, dataset_id: UUID, req: HitReq, account: Account) -> list[dict]:
        """根据传递的知识库id+请求执行召回测试"""
        # 1.检测知识库是否存在并校验
        dataset = self.get(Dataset, dataset_id)
        if dataset is None or dataset.account_id != account.id:
            raise NotFoundException("知识库不存在")

        # 2.调用检索服务执行检索
        lc_documents = self.retrieval_service.search_in_datasets(
            account_id=account.id,
            dataset_ids=[dataset_id],
            **req.data,
        )
        lc_document_dict = {str(lc_document.metadata['segment_id']): lc_document for lc_document in lc_documents}

        # 3.根据检索的数据查询对应的片段信息
        segments = self.db.session.query(Segment).filter(
            Segment.id.in_([str(lc_document.metadata['segment_id']) for lc_document in lc_documents])
        ).all()
        segment_dict = {str(segment.id): segment for segment in segments}

        # 4.排序片段数据
        sorted_segments = [
            segment_dict[str(lc_document.metadata['segment_id'])]
            for lc_document in lc_documents
            if str(lc_document.metadata['segment_id']) in segment_dict
        ]

        # 5.组装响应数据
        hit_result = []
        for segment in sorted_segments:
            document = segment.document
            upload_file = document.upload_file
            hit_result.append({
                "id": segment.id,
                "document": {
                    "id": document.id,
                    "name": document.name,
                    "mime_type": upload_file.mime_type,
                    "extension": upload_file.extension,
                },
                "dataset_id": segment.dataset_id,
                "score": lc_document_dict[str(segment.id)].metadata['score'],
                "position": segment.position,
                "content": segment.content,
                "keywords": segment.keywords,
                "character_count": segment.character_count,
                "token_count": segment.token_count,
                "hit_count": segment.hit_count,
                "enabled": segment.enabled,
                "disabled_at": datetime_to_timestamp(segment.disabled_at),
                "status": segment.status,
                "error": segment.error,
                "updated_at": datetime_to_timestamp(segment.updated_at),
                "created_at": datetime_to_timestamp(segment.created_at),
            })

        return hit_result
