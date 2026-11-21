#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time     :2026/10/28 21:56
@Author   :314907015@qq.com
@File     :account_schema.py
"""
from flask_wtf import FlaskForm
from marshmallow import Schema, fields, pre_dump
from wtforms.fields.simple import StringField
from wtforms.validators import DataRequired, regexp, Length, URL

from internal.lib.helper import datetime_to_timestamp
from internal.model import Account
from pkg.password import password_pattern


class GetCurrentUserResp(Schema):
    """获取当前登录账号信息响应"""

    id = fields.UUID(dump_default='')
    name = fields.Str(dump_default='')
    email = fields.Str(dump_default='')
    avatar = fields.Str(dump_default='')
    last_login_at = fields.Int(dump_default=0)
    last_login_ip = fields.Str(dump_default='')
    created_at = fields.Int(dump_default=0)

    @pre_dump
    def process_data(self, data: Account, **kwargs):
        return {
            'id': data.id,
            'name': data.name,
            'email': data.email,
            'avatar': data.avatar,
            'last_login_at': datetime_to_timestamp(data.last_login_at),
            'last_login_ip': data.last_login_ip,
            'created_at': datetime_to_timestamp(data.created_at),
        }


class UpdatePasswordReq(FlaskForm):
    """更新账户密码请求体"""
    password = StringField('password', validators=[
        DataRequired("登录密码不能为空"),
        regexp(regex=password_pattern, message="密码至少包含一个字母，一个数字，并且长度为8-16位")
    ])


class UpdateNameReq(FlaskForm):
    """更新账户名称请求"""
    name = StringField('name', validators=[
        DataRequired("账号名称不能为空"),
        Length(min=3, max=30, message="账号名称长度在3-30")
    ])


class UpdateAvatarReq(FlaskForm):
    """更新账户头像请求"""
    avatar = StringField('avatar', validators=[
        DataRequired("账号头像不能为空"),
        URL(message="账号头像必须是URL图片地址")
    ])
