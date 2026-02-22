# constraint_checker/__init__.py
"""
constraint_checker 模块：空间设计方案的约束校验核心模块，
提供整体校验入口和各类规则校验函数。
"""
# 1. 导入核心校验调度器（validator.py的核心函数/类）
from .validator import validate_design  
from .run_check import run_example, batch_run_check

# 2. 导入rules模块的核心函数（可选，方便外部直接调用）
from .rules import (
    validate_room_area,
    validate_total_area,
    validate_required_adjacency,
    validate_basic_function
)

# 3. 明确对外暴露的核心接口（顶层接口+常用规则函数）
__all__ = [
    # 核心调度接口（外部优先用这个）
    "validate_design",
    # 常用规则函数（方便单独调用）
    "validate_room_area",
    "validate_total_area",
    "validate_required_adjacency",
    "validate_basic_function", 
    "run_example", 
    "batch_run_check"
]