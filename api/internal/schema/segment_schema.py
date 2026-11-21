#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time     :2026/10/14 16:46
@Author   :314907015@qq.com
@File     :segment_schema.py
"""
from flask_wtf import FlaskForm
from marshmallow import Schema, pre_dump, fields
from wtforms import StringField, BooleanField
from wtforms.validators import Optional, ValidationError, DataRequired, Length

from internal.lib.helper import datetime_to_timestamp
from internal.model import Segment
from internal.schema import ListField
from pkg.paginator import PaginatorReq


class GetSegmentsWithPageReq(PaginatorReq):
    """文档片段列表请求"""
    search_word = StringField("search_word", default='', validators=[
        Optional()
    ])


class GetSegmentsWithPageResp(Schema):
    """文档片段列表响应结构"""
    id = fields.UUID(dump_default='')
    document_id = fields.UUID(dump_default='')
    dataset_id = fields.UUID(dump_default='')
    position = fields.Int(dump_default=0)
    content = fields.Str(dump_default='')
    keywords = fields.List(fields.Str, dump_default=[])
    character_count = fields.Int(dump_default=0)
    token_count = fields.Int(dump_default=0)
    hit_count = fields.Int(dump_default=0)
    enabled = fields.Bool(dump_default=False)
    disabled_at = fields.Int(dump_default=0)
    status = fields.Str(dump_default='')
    error = fields.Str(dump_default='')
    updated_at = fields.Int(dump_default=0)
    created_at = fields.Int(dump_default=0)

    @pre_dump
    def process_data(self, data: Segment, **kwargs):
        return {
            'id': data.id,
            'document_id': data.document_id,
            'dataset_id': data.dataset_id,
            'position': data.position,
            'content': data.content,
            'keywords': data.keywords,
            'character_count': data.character_count,
            'token_count': data.token_count,
            'hit_count': data.hit_count,
            'enabled': data.enabled,
            'disabled_at': datetime_to_timestamp(data.disabled_at),
            'status': data.status,
            'error': data.error,
            'updated_at': datetime_to_timestamp(data.updated_at),
            'created_at': datetime_to_timestamp(data.created_at),
        }


class GetSegmentResp(Schema):
    """文档片段详情响应结构"""
    id = fields.UUID(dump_default='')
    document_id = fields.UUID(dump_default='')
    dataset_id = fields.UUID(dump_default='')
    position = fields.Int(dump_default=0)
    content = fields.Str(dump_default='')
    keywords = fields.List(fields.Str, dump_default=[])
    character_count = fields.Int(dump_default=0)
    token_count = fields.Int(dump_default=0)
    hit_count = fields.Int(dump_default=0)
    hash = fields.Str(dump_default='')
    enabled = fields.Bool(dump_default=False)
    disabled_at = fields.Int(dump_default=0)
    status = fields.Str(dump_default='')
    error = fields.Str(dump_default='')
    updated_at = fields.Int(dump_default=0)
    created_at = fields.Int(dump_default=0)

    @pre_dump
    def process_data(self, data: Segment, **kwargs):
        return {
            'id': data.id,
            'document_id': data.document_id,
            'dataset_id': data.dataset_id,
            'position': data.position,
            'content': data.content,
            'keywords': data.keywords,
            'character_count': data.character_count,
            'token_count': data.token_count,
            'hit_count': data.hit_count,
            'hash': data.hash,
            'enabled': data.enabled,
            'disabled_at': datetime_to_timestamp(data.disabled_at),
            'status': data.status,
            'error': data.error,
            'updated_at': datetime_to_timestamp(data.updated_at),
            'created_at': datetime_to_timestamp(data.created_at),
        }


class UpdateSegmentReq(FlaskForm):
    """更新文档片段信息请求体"""
    content = StringField('content', validators=[
        DataRequired("更新片段信息不能为空"),
    ])
    keywords = ListField('keywords')

    def validate_keywords(self, field: ListField) -> None:
        """校验关键词列表，涵盖长度不能为空，默认值为空列表"""
        # 1.校验数据类型和非空
        if field.data is None:
            field.data = []
        if not isinstance(field.data, list):
            raise ValidationError("关键词列表格式必须为列表")

        # 2.校验数据长度不能超过10
        if len(field.data) > 10:
            raise ValidationError("关键词长度范围在1-10")

        # 3.循环遍历列表，列表元素需为字符串
        for keyword in field.data:
            if not isinstance(keyword, str):
                raise ValidationError("关键词必须为字符串")

        # 4.删除重复数据并更新
        field.data = list(dict.fromkeys(field.data))

class UpdateSegmentEnabledReq(FlaskForm):
    """更新文档片段启用状态请求"""
    enabled = BooleanField('enabled')

    def validate_enabled(self, field: BooleanField) -> None:
        """校验文档启用状态enabled"""
        if not isinstance(field.data, bool):
            raise ValidationError("enabled状态不能为空且必须为布尔值")


class CreateSegmentReq(FlaskForm):
    """创建片段请求"""
    content = StringField('content', validators=[
        DataRequired("片段内容不能为空")
    ])
    keywords = ListField('keywords')

    def validate_keywords(self, field: ListField) -> None:
        """校验关键词列表，涵盖长度不能为空，默认值为空列表"""
        # 1.校验数据类型和非空
        if field.data is None:
            field.data = []
        if not isinstance(field.data, list):
            raise ValidationError("关键词列表格式必须为列表")

        # 2.校验数据长度不能超过10
        if len(field.data) > 10:
            raise ValidationError("关键词长度范围在1-10")

        # 3.循环遍历列表，列表元素需为字符串
        for keyword in field.data:
            if not isinstance(keyword, str):
                raise ValidationError("关键词必须为字符串")

        # 4.删除重复数据并更新
        field.data = list(dict.fromkeys(field.data))
