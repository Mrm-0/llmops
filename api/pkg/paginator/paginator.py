#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time     :2026/9/18 11:23
@Author   :314907015@qq.com
@File     :paginator.py
"""
import math
from dataclasses import dataclass
from typing import Any, List

from flask_wtf import FlaskForm
from wtforms.fields.numeric import IntegerField
from wtforms.validators import Optional, NumberRange

from pkg.sqlalchemy import SQLAlchemy


class PaginatorReq(FlaskForm):
    """分页请求基础类，涵盖当前页面、页面条数，如果请求接口需要携带分页信息，可以直接继承该类"""
    current_page = IntegerField("current_page", default=1, validators=[
        Optional(),
        NumberRange(min=1, max=9999, message="当前页数范围在1-9999")
    ])
    page_size = IntegerField("page_size", default=20, validators=[
        Optional(),
        NumberRange(min=1, max=50, message="页面条数范围在1-50条")
    ])


@dataclass
class Paginator:
    """分页器"""
    total_pages: int = 0  # 总页面数
    total_record: int = 0  # 总条数
    current_page: int = 1  # 当前页面数
    page_size: int = 20  # 页面条数

    def __init__(self, db: SQLAlchemy, req: PaginatorReq):
        if req is not None:
            self.current_page = req.current_page.data
            self.page_size = req.page_size.data
        self.db = db

    def paginate(self, select) -> List[Any]:
        """对传入的查询进行分类"""
        # 1.调用db.paginate进行数据分页
        p = self.db.paginate(select, page=self.current_page, per_page=self.page_size, error_out=False)

        # 2.计算总页数+总条数
        self.total_record = p.total
        self.total_pages = math.ceil(p.total / self.page_size)

        # 3.返回分页后的数据
        return p.items

@dataclass
class PageModel:
    list:List[Any]
    paginator: Paginator