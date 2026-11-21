#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time     :2026/8/23 18:49
@Author   :314907015@qq.com
@File     :test_app_handler.py
"""
from pkg.response import HttpCode

import pytest

class TestAppHandler:
    """app控制器的测试类"""

    @pytest.mark.parametrize(
        "app_id,query",
        [
            ("a4aef7be-f099-4668-ac04-7ee94c45d986",None),
            ("a4aef7be-f099-4668-ac04-7ee94c45d986","你好，你是？")
        ]
    )
    def test_completion(self,app_id,query,client):
        resp=client.post(f"/apps/{app_id}/debug",json={"query":query})
        assert resp.status_code == 200
        if query is None:
            assert resp.json.get("code") == HttpCode.VALIDATE_ERROR
        else:
            assert resp.json.get("code") == HttpCode.SUCCESS