#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time     :2026/9/16 13:31
@Author   :314907015@qq.com
@File     :api_tool_schema.py
"""
from flask_wtf import FlaskForm
from marshmallow import fields, Schema, pre_dump
from wtforms.fields.simple import StringField
from wtforms.validators import DataRequired, Length, URL, ValidationError, Optional

from internal.model import ApiToolProvider, ApiTool
from pkg.paginator import PaginatorReq
from .schema import ListField


class ValidateOpenAPISchemaReq(FlaskForm):
    """校验OpenAPI规范字符串请求"""
    openapi_schema = StringField("openapi_schema", validators=[
        DataRequired(message="openapi_schema字符串不能为空")
    ])


class CreateApiToolReq(FlaskForm):
    """校验创建自定义API工具请求"""
    name = StringField("name", validators=[
        DataRequired(message="工具提供者名字不能为空"),
        Length(min=1, max=30, message="工具提供者名字长度在1-30字符")
    ])
    icon = StringField("icon", validators=[
        DataRequired(message="工具提供者的图标不能为空"),
        URL(message="工具提供者的图标必须是URL链接")
    ])
    openapi_schema = StringField("openapi_schema", validators=[
        DataRequired(message="openapi_schema字符串不能为空")
    ])
    headers = ListField("headers", default=[])

    @classmethod
    def validate_headers(cls, form, field):
        """校验headers请求的数据是否正确，涵盖列表校验，列表元素校验"""
        for header in field.data:
            if not isinstance(header, dict):
                raise ValidationError("headers里的每一个元素都必须是字典")
            if set(header.keys()) != {"key", "value"}:
                raise ValidationError("headers里的每一个元素都必须包含key/value两个属性，不允许有其他属性")


class GetApiToolProviderResp(Schema):
    """获取API工具提供者的响应信息"""
    id = fields.UUID()
    name = fields.Str()
    icon = fields.Str()
    openapi_schema = fields.Str()
    headers = fields.List(fields.Dict, dump_default=list)
    created_at = fields.Integer(dump_default=0)

    @pre_dump
    def process_data(self, data: ApiToolProvider, **kwargs):
        return {
            "id": data.id,
            "name": data.name,
            "icon": data.icon,
            "openapi_schema": data.openapi_schema,
            "headers": data.headers,
            "created_at": int(data.created_at.timestamp()),
        }


class GetApiToolResp(Schema):
    """获取API工具参数详细响应"""
    id = fields.UUID()
    name = fields.Str()
    description = fields.Str()
    inputs = fields.List(fields.Dict, dump_default=list)
    provider = fields.Dict()

    @pre_dump
    def process_data(self, data: ApiTool, **kwargs):
        provider = data.provider
        return {
            "id": data.id,
            "name": data.name,
            "description": data.description,
            "inputs": [{k: v for k, v in parameter.items() if k != "in"} for parameter in data.parameters],
            "provider": {
                "id": provider.id,
                "name": provider.name,
                "icon": provider.icon,
                "description": provider.description,
                "headers": provider.headers,
            }
        }


class GetApiToolProvidersWithPageReq(PaginatorReq):
    """校验获取API工具并提供分页"""
    search_word = StringField("search_word", validators=[
        Optional()
    ])


class GetApiToolProvidersWithoutPageResp(Schema):
    """获取API工具提供者分页列表数据响应"""
    id = fields.UUID()
    name = fields.Str()
    icon = fields.Str()
    description = fields.Str()
    headers = fields.List(fields.Dict, dump_default=list)
    tools = fields.List(fields.Dict, dump_default=list)
    created_at = fields.Integer(dump_default=0)

    @pre_dump
    def process_data(self, data: ApiToolProvider, **kwargs):
        tools = data.tools
        return {
            "id": data.id,
            "name": data.name,
            "icon": data.icon,
            "description": data.description,
            "headers": data.headers,
            "tools": [{
                "id": tool.id,
                "name": tool.name,
                "description": tool.description,
                "inputs": [{k: v for k, v in parameter.items() if k != "in"} for parameter in tool.parameters],
            } for tool in tools],
            "created_at": int(data.created_at.timestamp()),
        }


class UpdateApiToolProviderReq(FlaskForm):
    """校验更新API工具提供者信息"""
    name = StringField("name", validators=[
        DataRequired(message="工具提供者名字不能为空"),
        Length(min=1, max=30, message="工具提供者名字长度在1-30字符")
    ])
    icon = StringField("icon", validators=[
        DataRequired(message="工具提供者的图标不能为空"),
        URL(message="工具提供者的图标必须是URL链接")
    ])
    openapi_schema = StringField("openapi_schema", validators=[
        DataRequired(message="openapi_schema字符串不能为空")
    ])
    headers = ListField("headers", default=[])

    @classmethod
    def validate_headers(cls, form, field):
        """校验headers请求的数据是否正确，涵盖列表校验，列表元素校验"""
        for header in field.data:
            if not isinstance(header, dict):
                raise ValidationError("headers里的每一个元素都必须是字典")
            if set(header.keys()) != {"key", "value"}:
                raise ValidationError("headers里的每一个元素都必须包含key/value两个属性，不允许有其他属性")
