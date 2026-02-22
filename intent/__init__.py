# intent/__init__.py
"""
intent 模块：提供JSON Schema
"""
# 导入核心函数和变量
from .intent_schema import intent_schema

# 明确对外暴露的接口
__all__ = ["intent_schema"]