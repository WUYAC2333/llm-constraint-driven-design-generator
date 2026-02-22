# rules/__init__.py
"""
rules 模块：定义空间设计方案的校验规则，
包含面积、邻接、方位等核心校验函数。
"""
# 导入核心校验函数
from .area import validate_room_area, validate_total_area
from .adjacency import validate_required_adjacency
from .topology import validate_basic_function

# 明确对外暴露的核心接口（必须是字符串！）
__all__ = [
    "validate_room_area",
    "validate_total_area",
    "validate_required_adjacency",
    "validate_basic_function"
]