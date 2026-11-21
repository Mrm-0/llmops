#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time     :2026/11/11 11:42
@Author   :314907015@qq.com
@File     :dataset_retrieval_entity.py
"""
from uuid import UUID

from pydantic import Field, BaseModel, field_validator

from internal.core.workflow.entities.node_entity import BaseNodeData
from internal.core.workflow.entities.variable_entity import VariableEntity, VariableValueType
from internal.entity.dataset_entity import RetrievalStrategy
from internal.exception import FailException


class RetrievalConfig(BaseModel):
    """检索配置"""
    retrieval_strategy: RetrievalStrategy = RetrievalStrategy.SEMANTIC
    k: int = 3
    score: float = 0


class DatasetRetrievalNodeData(BaseNodeData):
    """模板转换节点数据"""
    dataset_ids: list[UUID]
    retrieval_config: RetrievalConfig = RetrievalConfig()
    inputs: list[VariableEntity] = Field(default_factory=list)
    outputs: list[VariableEntity] = Field(
        exclude=True,
        default_factory=lambda: [
            VariableEntity(name="combine_documents", value={"type": VariableValueType.GENERATED})
        ]
    )

    @field_validator("inputs")
    def validate_inputs(cls, values: dict):
        """校验输入变量信息"""
        # 1.提取inputs对应信息
        inputs = values.get("inputs", [])

        # 2.判断是否只有一个输入变量，如果有多个则抛出错误
        if len(inputs) != 1:
            raise FailException("知识库节点输入变量信息出错")

        # 3.判断输入遍历那个的类型及字段名称是否出错
        query_input: VariableEntity = inputs[0]
        if query_input.name != "query" or query_input.type != VariableValueType.GENERATED or query_input.required is False:
            raise FailException("知识库节点输入变量名字/变量类型/必填属性出错")

        return values
