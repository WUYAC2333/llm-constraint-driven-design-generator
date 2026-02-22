# llm/intention_parser.py
# examples = 不同设计方案，requirements = 当前用户意图
import re
from pathlib import Path
# 导入统一的路径变量和工具函数
from utils.io import (
    REQUIREMENTS_JSON,
    USER_INPUT_FILE,  # config/user_input.txt 路径
    read_text,        # 读取文本文件的方法
    write_json        # 写入JSON的方法
)
# 导入typing模块（适配低版本Python）
from typing import Union, Optional

def parse_intention_to_requirements(output_path: Optional[Union[Path, str]] = None):
    """
    从user_input.txt中解析设计需求，生成config/requirements.json文件
    :param output_path: 自定义输出路径（默认使用utils/io中定义的路径）
    """
    # 使用统一路径，无传参则用默认的REQUIREMENTS_JSON
    if output_path is None:
        output_path = REQUIREMENTS_JSON
    else:
        output_path = Path(output_path)

    # ========== 核心修改：读取user_input.txt文件内容 ==========
    try:
        # 调用io模块的read_text方法读取设计意图文本
        intention_text = read_text(USER_INPUT_FILE).strip()
        if not intention_text:
            raise ValueError("user_input.txt文件内容为空，请检查文件")
    except FileNotFoundError as e:
        raise FileNotFoundError(f"设计意图文件读取失败：{e}")

    # ========== 解析逻辑（完全复用原有逻辑，仅数据源改变） ==========
    requirements = {
        "area": {},
        "adjacency": [],
        "direction": {}
    }

    lines = intention_text.split("\n")
    for line in lines:
        line = line.strip().lstrip("-").strip()
        if not line:
            continue

        # 面积解析
        area_match = re.search(r"(\w+_\d+) \((\d+)㎡\)", line)
        if area_match:
            room_id = area_match.group(1)
            area = int(area_match.group(2))
            requirements["area"][room_id] = area

        # 邻接/方向解析
        adj_dir_match = re.search(r"(\w+_\d+) is (\w+) of (\w+_\d?)", line)
        if adj_dir_match:
            room1 = adj_dir_match.group(1)
            direction = adj_dir_match.group(2)
            room2 = adj_dir_match.group(3)
            if "_" not in room2:
                room2 += "_1"
            requirements["adjacency"].append([room1, room2])
            if room1 not in requirements["direction"]:
                requirements["direction"][room1] = {}
            requirements["direction"][room1][room2] = direction

        # 多房间邻接解析
        multi_adj_match = re.search(r"(\w+_\d+) connects to (.*?) on (\w+) side", line)
        if multi_adj_match:
            main_room = multi_adj_match.group(1)
            sub_rooms = [r.strip() for r in multi_adj_match.group(2).split(",")]
            direction = multi_adj_match.group(3)
            for sub_room in sub_rooms:
                if "_" not in sub_room:
                    sub_room += "_1"
                requirements["adjacency"].append([main_room, sub_room])
                if main_room not in requirements["direction"]:
                    requirements["direction"][main_room] = {}
                requirements["direction"][main_room][sub_room] = direction

    # ========== 使用统一的write_json工具函数 ==========
    write_json(output_path, requirements)
    print(f"✅ requirements.json已生成：{output_path.absolute()}")
    return requirements

if __name__ == "__main__":
    # 直接调用，无需传路径（自动使用REQUIREMENTS_JSON）
    parse_intention_to_requirements()