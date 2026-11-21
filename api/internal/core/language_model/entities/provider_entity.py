#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time     :2026/11/15 15:09
@Author   :314907015@qq.com
@File     :provider_entity.py
"""
from pathlib import Path
from typing import Union, Type, Optional

import yaml
from pydantic import BaseModel, Field, model_validator

from internal.exception import NotFoundException
from internal.lib.helper import dynamic_import
from .default_model_parameter_template import DEFAULT_MODEL_PARAMETER_TEMPLATE
from .model_entity import ModelType, ModelEntity, BaseLanguageModel


class ProviderEntity(BaseModel):
    """模型提供商实体信息"""
    name: str = ""  # 提供商的名字
    label: str = ""  # 提供商的标签
    description: str = ""  # 提供商的描述信息
    icon: str = ""  # 提供商的图标
    background: str = ""  # 提供商的图标背景
    supported_model_types: list[ModelType] = Field(default_factory=list)  # 支持的模型类型


class Provider(BaseModel):
    """大语言模型服务提供商，在该类下，可以获取到该服务提供商的所有大语言模型、描述、图标、标签等多个信息"""
    name: str  # 提供商名字
    position: int  # 服务提供商的位置信息
    provider_entity: ProviderEntity  # 模型提供商实体
    model_entity_map: dict[str, ModelEntity] = Field(default_factory=dict)  # 模型实体映射
    model_class_map: dict[str, Union[None, Type[BaseLanguageModel]]] = Field(default_factory=dict)  # 模型类映射

    @model_validator(mode='after')
    def validate_provider(self) -> "Provider":
        for model_type in self.provider_entity.supported_model_types:
            symbol_name = model_type.value.capitalize()  # "chat" -> "Chat"
            self.model_class_map[model_type] = dynamic_import(
                f"internal.core.language_model.providers.{self.provider_entity.name}.{model_type.value}",
                symbol_name,
            )

        provider_path = Path(__file__).resolve().parent.parent / "providers" / self.provider_entity.name
        positions = yaml.safe_load((provider_path / "positions.yaml").read_text(encoding="utf-8")) or []

        for model_name in positions:
            data = yaml.safe_load((provider_path / f"{model_name}.yaml").read_text(encoding="utf-8"))
            parameters = []
            for p in data.get("parameters") or []:
                use_template = p.pop("use_template", None)
                parameters.append({**DEFAULT_MODEL_PARAMETER_TEMPLATE[use_template], **p} if use_template else p)
            data["parameters"] = parameters
            self.model_entity_map[model_name] = ModelEntity(**data)

        return self

    def get_model_class(self, model_type: ModelType) -> Optional[Type[BaseLanguageModel]]:
        """根据传递的模型类型获取该提供者的模型类"""
        model_class = self.model_class_map.get(model_type, None)
        if model_class is None:
            raise NotFoundException("该模型类不存在，请核实后重试")
        return model_class

    def get_model_entity(self, model_name: str) -> Optional[ModelEntity]:
        """根据传递的模型名字获取模型实体信息"""
        model_entity = self.model_entity_map.get(model_name, None)
        if model_entity is None:
            raise NotFoundException("该模型实体不存在，请核实后重试")
        return model_entity

    def get_model_entities(self) -> list[ModelEntity]:
        """获取该服务提供者的所有模型实体列表信息"""
        return list(self.model_entity_map.values())
