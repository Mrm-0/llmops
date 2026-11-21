#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time     :2026/9/24 23:43
@Author   :314907015@qq.com
@File     :upload_file_schema.py
"""
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired, FileSize
from marshmallow import Schema, fields, pre_dump

from internal.entity.upload_file_entity import ALLOWED_DOCUMENT_EXTENSIONS, ALLOWED_IMAGE_EXTENSIONS
from internal.model import UploadFile


class UploadFileReq(FlaskForm):
    """上传文件请求"""
    file = FileField("file", validators=[
        FileRequired("上传文件不能为空"),
        FileSize(max_size=15 * 1024 * 1024, message="上传文件最大不能超过15MB"),
        FileAllowed(ALLOWED_DOCUMENT_EXTENSIONS, message=f"仅允许上传:{'/'.join(ALLOWED_DOCUMENT_EXTENSIONS)}")
    ])


class UploadFileResp(Schema):
    """上传文件接口响应"""
    id = fields.UUID(dump_default="")
    account_id = fields.UUID(dump_default="")
    name = fields.Str(dump_default="")
    key = fields.Str(dump_default="")
    size = fields.Integer(dump_default=0)
    extension = fields.Str(dump_default="")
    mime_type = fields.Str(dump_default="")
    created_at = fields.Integer(dump_default=0)

    @pre_dump
    def process_date(self, data: UploadFile, **kwargs):
        return {
            "id": data.id,
            "account_id": data.account_id,
            "name": data.name,
            "key": data.key,
            "size": data.size,
            "extension": data.extension,
            "mime_type": data.mime_type,
            "created_at": int(data.created_at.timestamp()),
        }

class UploadImageReq(FlaskForm):
    """上传图片请求"""
    file = FileField("file", validators=[
        FileRequired("上传图片不能为空"),
        FileSize(max_size=15 * 1024 * 1024, message="上传图片最大不能超过15MB"),
        FileAllowed(ALLOWED_IMAGE_EXTENSIONS, message=f"仅允许上传:{'/'.join(ALLOWED_IMAGE_EXTENSIONS)}")
    ])
