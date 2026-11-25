#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time     :2026/10/10 16:48
@Author   :314907015@qq.com
@File     :file_extractor.py
"""
import logging
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Union
from urllib.parse import urlparse, unquote

import requests
from injector import inject
from langchain_community.document_loaders import (
    UnstructuredExcelLoader,
    UnstructuredHTMLLoader,
    UnstructuredMarkdownLoader,
    UnstructuredPowerPointLoader,
    UnstructuredXMLLoader,
    UnstructuredCSVLoader,
    UnstructuredFileLoader,
    PyPDFLoader,
    TextLoader,
    Docx2txtLoader,
)
from langchain_core.documents import Document as LCDocument

from internal.exception import FailException
from internal.model import UploadFile
from internal.service import CosService


@inject
@dataclass
class FileExtractor:
    """文件提取器，用于将远程文件、upload_file记录加载成LangChain对应的文档或字符串"""
    cos_service: CosService

    def load(
            self,
            upload_file: UploadFile,
            return_text: bool = False,
            is_unstructured: bool = False
    ) -> Union[list[LCDocument], str]:
        """加载传入的upload_file记录，返回LangChain文档列表或字符串"""
        # 1.创建一个临时文件夹
        with tempfile.TemporaryDirectory() as tmp_dir:
            # 2.构建一个临时文件路径（保留原始扩展名，确保能正确选择加载器）
            file_path = os.path.join(tmp_dir, os.path.basename(upload_file.key))

            # 3.将对象存储中的文件下载到本地
            self.cos_service.download_file(upload_file.key, file_path)

            # 4.从指定的路径中去加载文件
            return self.load_from_file(file_path, return_text, is_unstructured)

    @classmethod
    def load_from_url(cls, url: str, return_text: bool = False) -> Union[list[LCDocument], str]:
        """从传入的url中去加载数据，返回LangChain文档列表或字符串"""
        # 1.下载远程的url文件到本地
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        # 2.将文件下载到本地的临时文件夹
        with tempfile.TemporaryDirectory() as tmp_dir:
            # 3.获取文件的扩展名（剥离URL查询参数并解码），构建临时存储路径
            url_path = unquote(urlparse(url).path)
            filename = os.path.basename(url_path) or "download"
            file_path = os.path.join(tmp_dir, filename)
            with open(file_path, "wb") as f:
                f.write(response.content)

            return cls.load_from_file(file_path, return_text)

    @classmethod
    def _get_loader(cls, file_path: str, file_extension: str, is_unstructured: bool):
        """根据文件扩展名返回对应的文档加载器"""
        if file_extension in (".xlsx", ".xls"):
            return UnstructuredExcelLoader(file_path)
        elif file_extension == ".pdf":
            return PyPDFLoader(file_path)
        elif file_extension in (".md", ".markdown"):
            return UnstructuredMarkdownLoader(file_path)
        elif file_extension in (".htm", ".html"):
            return UnstructuredHTMLLoader(file_path)
        elif file_extension == ".csv":
            return UnstructuredCSVLoader(file_path)
        elif file_extension in (".ppt", ".pptx"):
            return UnstructuredPowerPointLoader(file_path)
        elif file_extension == ".xml":
            return UnstructuredXMLLoader(file_path)
        elif file_extension == ".docx":
            # docx2txt仅支持.docx格式，轻量且无需额外系统依赖
            return Docx2txtLoader(file_path)
        elif file_extension == ".doc":
            # 旧版二进制.doc格式需要unstructured+libreoffice支持
            return UnstructuredFileLoader(file_path)
        else:
            return UnstructuredFileLoader(file_path) if is_unstructured else TextLoader(file_path)

    @classmethod
    def load_from_file(
            cls,
            file_path: str,
            return_text: bool = False,
            is_unstructured: bool = True
    ) -> Union[list[LCDocument], str]:
        """从本地文件中加载数据，返回LangChain文档列表或字符串"""
        # 1.校验文件存在
        if not os.path.isfile(file_path):
            raise FailException(f"文件不存在或已损坏: {os.path.basename(file_path)}")

        # 2.获取文件扩展名
        delimiter = "\n\n"
        file_extension = Path(file_path).suffix.lower()

        # 3.根据扩展名选择对应的加载器并加载文档
        loader = cls._get_loader(file_path, file_extension, is_unstructured)
        try:
            documents = loader.load()
        except Exception as error:
            logging.error("文件解析失败(%s): %s", file_extension, error, exc_info=True)
            raise FailException(f"文件解析失败，请确认文件「{os.path.basename(file_path)}」未损坏且格式受支持") from error

        # 4.过滤掉空白文档，若全部为空则给出友好提示
        documents = [doc for doc in documents if doc.page_content and doc.page_content.strip()]
        if not documents:
            raise FailException("文件内容为空或无法提取出有效文本")

        # 5.返回加载的文档或文本
        return delimiter.join(doc.page_content for doc in documents) if return_text else documents
