# utils/io.py
"""
IO 工具模块：统一管理项目所有路径，提供通用的文件读写工具函数
核心特性：
1. 动态推导项目根目录，无硬编码绝对路径
2. 预定义所有核心目录/文件路径，便于跨模块调用
3. 封装通用IO函数（JSON/YAML读写、目录创建等），减少重复代码
"""
from pathlib import Path
import json
import yaml
# 关键修复：导入typing模块的类型注解（适配Python 3.6+）
from typing import Dict, List, Any, Optional, Union

# ===================== 核心：动态定义项目根目录 =====================
# 原理：
# __file__ → utils/io.py
# .parent → utils/
# .parent → 项目根目录 (Project_1/drafts/)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent

# 路径合法性校验（确保根目录推导正确，避免后续路径错误）
def _validate_root_dir(root_dir: Path) -> None:
    """校验项目根目录是否包含核心文件夹，确保路径推导正确"""
    required_dirs = ["config", "llm", "intent", "design_ir", "constraint_checker", "utils"]
    missing_dirs = [d for d in required_dirs if not (root_dir / d).exists()]
    if missing_dirs:
        raise FileNotFoundError(
            f"项目根目录路径错误！未找到核心目录：{missing_dirs}\n"
            f"当前推导的根目录：{root_dir.absolute()}"
        )

# 执行根目录校验
_validate_root_dir(_PROJECT_ROOT)

# ===================== 对外暴露的核心路径（全项目统一使用） =====================
# 项目根目录
PROJECT_ROOT = _PROJECT_ROOT

# 核心文件
README_FILE = PROJECT_ROOT / "README.md"
MAIN_ENTRY_FILE = PROJECT_ROOT / "main.py"

# -------------------- config 目录 --------------------
CONFIG_DIR = PROJECT_ROOT / "config"
REQUIREMENTS_JSON = CONFIG_DIR / "requirements.json"  # 设计约束文件
MODEL_CONFIG_YAML = CONFIG_DIR / "model_config.yaml"  # LLM模型配置
USER_INPUT_FILE = CONFIG_DIR / "user_input.txt"

# -------------------- llm 目录 --------------------
LLM_DIR = PROJECT_ROOT / "llm"
LLM_INIT_FILE = LLM_DIR / "__init__.py"
LLM_CALL_LLM_FILE = LLM_DIR / "call_llm.py"          # LLM API调用
LLM_PROMPTS_FILE = LLM_DIR / "prompts.py"            # Prompt模板

# -------------------- intention_parser 目录/文件 --------------------
INTENTION_PARSER_FILE = PROJECT_ROOT / "intention_parser.py"  # 独立的意图解析文件

# -------------------- intent 目录 --------------------
INTENT_DIR = PROJECT_ROOT / "intent"
INTENT_INIT_FILE = INTENT_DIR / "__init__.py"
INTENT_SCHEMA_FILE = INTENT_DIR / "intent_schema.py"  # 设计意图Schema定义

# -------------------- design_ir 目录 --------------------
DESIGN_IR_DIR = PROJECT_ROOT / "design_ir"
DESIGN_IR_INIT_FILE = DESIGN_IR_DIR / "__init__.py"
DESIGN_IR_PARSER_FILE = DESIGN_IR_DIR / "parser.py"    # JSON→Graph解析
DESIGN_IR_GRAPH_FILE = DESIGN_IR_DIR / "graph.py"      # Room/Adjacency/Area类

# -------------------- constraint_checker 目录 --------------------
CONSTRAINT_CHECKER_DIR = PROJECT_ROOT / "constraint_checker"
CONSTRAINT_CHECKER_INIT_FILE = CONSTRAINT_CHECKER_DIR / "__init__.py"
CONSTRAINT_CHECKER_VALIDATOR_FILE = CONSTRAINT_CHECKER_DIR / "validator.py"  # 规则调度
CONSTRAINT_CHECKER_RUN_CHECK_FILE = CONSTRAINT_CHECKER_DIR / "run_check.py"  # 测试CLI

# constraint_checker/rules 子目录
CONSTRAINT_RULES_DIR = CONSTRAINT_CHECKER_DIR / "rules"
CONSTRAINT_RULES_INIT_FILE = CONSTRAINT_RULES_DIR / "__init__.py"
CONSTRAINT_RULES_ADJACENCY_FILE = CONSTRAINT_RULES_DIR / "adjacency.py"      # 邻接规则
CONSTRAINT_RULES_AREA_FILE = CONSTRAINT_RULES_DIR / "area.py"                # 面积规则
CONSTRAINT_RULES_TOPOLOGY_FILE = CONSTRAINT_RULES_DIR / "topology.py"        # 拓扑规则

# constraint_checker/examples 示例文件目录
CONSTRAINT_EXAMPLES_DIR = CONSTRAINT_CHECKER_DIR / "examples"
# 预定义所有示例文件路径（可选，便于批量处理）
EXAMPLE_FILES = [
    CONSTRAINT_EXAMPLES_DIR / "example_ok_1_minimal.json",
    CONSTRAINT_EXAMPLES_DIR / "example_ok_2_typical.json",
    CONSTRAINT_EXAMPLES_DIR / "example_ok_3_edge.json",
    CONSTRAINT_EXAMPLES_DIR / "example_bad_1_function.json",
    CONSTRAINT_EXAMPLES_DIR / "example_bad_2_area.json",
    CONSTRAINT_EXAMPLES_DIR / "example_bad_3_total_area.json",
    CONSTRAINT_EXAMPLES_DIR / "example_bad_4_adjacency.json"
]

# -------------------- utils 目录 --------------------
UTILS_DIR = PROJECT_ROOT / "utils"
UTILS_LOGGING_FILE = UTILS_DIR / "logging.py"  # 日志工具

# ===================== 通用IO工具函数（全项目复用） =====================
def ensure_dir(dir_path: Union[Path, str]) -> Path:
    """
    确保目录存在，不存在则递归创建（父目录也会创建）
    :param dir_path: 目录路径（支持字符串/Path对象）
    :return: 标准化的Path对象
    """
    dir_path = Path(dir_path).resolve()
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path

def write_json(
    file_path: Union[Path, str],
    data: Union[Dict, List],
    indent: int = 2,
    ensure_ascii: bool = False
) -> None:
    """
    写入JSON文件（自动创建父目录）
    :param file_path: 输出文件路径
    :param data: 要写入的JSON数据（字典/列表）
    :param indent: JSON格式化缩进
    :param ensure_ascii: 是否确保ASCII编码（False支持中文）
    """
    file_path = Path(file_path).resolve()
    ensure_dir(file_path.parent)  # 确保父目录存在
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=indent, ensure_ascii=ensure_ascii)

def read_json(file_path: Union[Path, str]) -> Union[Dict, List]:
    """
    读取JSON文件，返回解析后的数据
    :param file_path: JSON文件路径
    :return: 字典/列表格式的JSON数据
    :raises FileNotFoundError: 文件不存在时抛出
    """
    file_path = Path(file_path).resolve()
    if not file_path.exists():
        raise FileNotFoundError(f"JSON文件不存在：{file_path}")
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

def write_yaml(
    file_path: Union[Path, str],
    data: Union[Dict, List],
    indent: int = 2,
    sort_keys: bool = False
) -> None:
    """
    写入YAML文件（自动创建父目录）
    :param file_path: 输出文件路径
    :param data: 要写入的YAML数据（字典/列表）
    :param indent: YAML格式化缩进
    :param sort_keys: 是否按字母排序键
    """
    file_path = Path(file_path).resolve()
    ensure_dir(file_path.parent)
    with open(file_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, indent=indent, sort_keys=sort_keys, allow_unicode=True)

def read_yaml(file_path: Union[Path, str]) -> Union[Dict, List]:
    """
    读取YAML文件，返回解析后的数据
    :param file_path: YAML文件路径
    :return: 字典/列表格式的YAML数据
    :raises FileNotFoundError: 文件不存在时抛出
    """
    file_path = Path(file_path).resolve()
    if not file_path.exists():
        raise FileNotFoundError(f"YAML文件不存在：{file_path}")
    with open(file_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def read_text(file_path):
    file_path = Path(file_path).resolve()
    if not file_path.exists():
        raise FileNotFoundError(f"文本文件不存在：{file_path}")
    return file_path.read_text(encoding="utf-8")

def get_file_list(
    dir_path: Union[Path, str],
    suffix: Optional[str] = None,
    recursive: bool = False
) -> List[Path]:
    """
    获取目录下的文件列表（支持后缀过滤、递归查找）
    :param dir_path: 目标目录
    :param suffix: 文件后缀（如".json"），None则返回所有文件
    :param recursive: 是否递归查找子目录
    :return: 文件路径列表（Path对象）
    """
    dir_path = Path(dir_path).resolve()
    if not dir_path.is_dir():
        raise NotADirectoryError(f"不是有效目录：{dir_path}")
    
    glob_pattern = f"**/*{suffix}" if recursive and suffix else f"*{suffix}"
    if not suffix:
        glob_pattern = "**/*" if recursive else "*"
    
    file_list = [f for f in dir_path.glob(glob_pattern) if f.is_file()]
    return sorted(file_list)

# ===================== 调试用：打印所有路径（可选） =====================
def print_all_paths() -> None:
    """打印所有预定义的路径（调试用，确认路径是否正确）"""
    print("=" * 60)
    print("项目核心路径列表（当前根目录：{}）".format(PROJECT_ROOT.absolute()))
    print("=" * 60)
    # 遍历当前模块的所有变量，筛选出Path类型的路径变量
    for var_name, var_value in globals().items():
        if isinstance(var_value, Path) and not var_name.startswith("_"):
            exists = "✅ 存在" if var_value.exists() else "❌ 不存在"
            print(f"{var_name:<40} {var_value.absolute()} {exists}")
    print("=" * 60)

# 测试：直接运行io.py时打印所有路径，便于验证
if __name__ == "__main__":
    print_all_paths()