#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time     :2026/9/25 12:00
@Author   :314907015@qq.com
@File     :cos_service.py
"""
import os
import uuid
from dataclasses import dataclass
from datetime import datetime

from injector import inject
from qcloud_cos import CosS3Client, CosConfig
from werkzeug.datastructures import FileStorage

from internal.entity.upload_file_entity import ALLOWED_DOCUMENT_EXTENSIONS, ALLOWED_IMAGE_EXTENSIONS
from internal.exception import FailException
from internal.model import UploadFile, Account
from .upload_file_service import UploadFileService
from ..lib.helper import generate_text_hash


@inject
@dataclass
class CosService:
    """腾讯云COS对象存储服务"""
    upload_file_service: UploadFileService

    def upload_file(self, file: FileStorage, account: Account, only_image: bool = False) -> UploadFile:
        """上传文件到腾讯云COS对象存储，上传并返回文件的信息"""
        # 1.提取文件扩展名并检测是否可以上传
        filename = file.filename
        extension = filename.rsplit(".")[-1] if "." in filename else ""
        if extension.lower() not in (ALLOWED_DOCUMENT_EXTENSIONS + ALLOWED_IMAGE_EXTENSIONS):
            raise FailException(f"该.{extension}扩展名的文件不允许上传")
        elif only_image and extension.lower() not in ALLOWED_IMAGE_EXTENSIONS:
            raise FailException(f"该.{extension}扩展名的文件不允许上传，请上传正确的图片")

        # 2.获取客户端+存储桶名称
        client = self._get_client()
        bucket = self._get_bucket()

        # 3.生成随机名字
        random_filename = str(uuid.uuid4()) + '.' + extension
        now = datetime.now()
        upload_filename = f"{now.year}/{now.month:02d}/{now.day:02d}/{random_filename}"

        # 4.流式读取文件并上传到cos中
        file_content = file.stream.read()

        try:
            # 5.将数据上传到cos存储桶中
            client.put_object(bucket, file_content, upload_filename)
        except Exception as e:
            raise FailException("上传文件失败，请稍后重试")

        # 6.创建upload_file记录
        return self.upload_file_service.create_upload_file(
            account_id=account.id,
            name=filename,
            key=upload_filename,
            size=len(file_content),
            extension=extension,
            mime_type=file.mimetype,
            hash=generate_text_hash(file_content),
        )

    def download_file(self, key: str, target_file_path: str):
        """下载cos云端文件到本地指定路径"""
        client = self._get_client()
        bucket = self._get_bucket()

        client.download_file(bucket, key, target_file_path)

    @classmethod
    def get_file_url(cls, key: str) -> str:
        """根据传递的cos云端key获取图片实际的URL地址"""
        cos_domain = os.getenv("COS_DOMAIN")

        if cos_domain:
            bucket = os.getenv("COS_BUCKET")
            scheme = os.getenv("COS_SCHEME")
            region = os.getenv("COS_REGION")
            cos_domain = f"{scheme}://{bucket}.cos.{region}.myqcloud.com"

        return f"{cos_domain}/{key}"

    @classmethod
    def _get_client(cls) -> CosS3Client:
        conf = CosConfig(
            Region=os.getenv("COS_REGION"),
            Secret_id=os.getenv("COS_SECRET_ID"),
            Secret_key=os.getenv("COS_SECRET_KEY"),
            Token=None,
            Scheme=os.getenv("COS_SCHEME", "https"),
            Timeout=60
        )
        return CosS3Client(conf)

    @classmethod
    def _get_bucket(cls) -> str | None:
        """获取储存桶名称"""
        return os.getenv("COS_BUCKET")
