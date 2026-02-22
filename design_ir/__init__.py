# design_ir/__init__.py
"""
design_ir 模块：定义空间设计方案的内部表示（IR）数据结构，
并提供将LLM输出的非结构化JSON转换为标准化DesignGraph的解析器。
"""
# 导入核心类（而非零散函数），符合模块核心定位
from .parser import parse_design_to_graph

# 明确对外暴露的核心接口（只暴露类，隐藏内部实现细节）
__all__ = ["parse_design_to_graph"]