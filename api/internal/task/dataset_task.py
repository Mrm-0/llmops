#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time     :2026/10/19 20:32
@Author   :314907015@qq.com
@File     :dataset_task.py
"""
from uuid import UUID

from celery import shared_task


@shared_task
def delete_dataset(dataset_id: UUID) -> None:
    """根据传递的知识库id删除指定知识库"""
    from app.http.module import injector
    from internal.service import IndexingService

    indexing_service = injector.get(IndexingService)
    indexing_service.delete_dataset(dataset_id)
