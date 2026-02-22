# design_ir/parser.py

import json
import re
from pathlib import Path
from typing import Dict, Any, Optional

from .graph import SpatialGraph, RoomNode, AdjacencyEdge, ConnectionType, Direction


# -------------------- JSON 清洗 --------------------
def fix_incomplete_json(content: str) -> str:
    """自动修复不完整的JSON（补全缺失的闭合符号）"""
    content = re.sub(r'\s+', ' ', content.strip())

    open_braces = content.count("{")
    close_braces = content.count("}")
    open_brackets = content.count("[")
    close_brackets = content.count("]")

    if open_braces > close_braces:
        content += "}" * (open_braces - close_braces)
    if open_brackets > close_brackets:
        content += "]" * (open_brackets - close_brackets)

    content = re.sub(r',\s*}', '}', content)
    content = re.sub(r',\s*]', ']', content)

    return content


def clean_and_validate_json(content: str) -> dict:
    """
    清洗 LLM 输出，并返回合法 JSON dict
    """
    content = content.strip()
    if content.startswith(("```json", "```")):
        content = content.split("```")[-2]

    content = fix_incomplete_json(content)

    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        raise ValueError(f"JSON 解析失败: {e}\n内容片段: {content[:500]}")


# -------------------- JSON → Graph --------------------
def parse_room_type(room_name: str):
    """解析房间名称，返回类型和序号"""
    match = re.match(r"([A-Za-z]+)_(\d+)", room_name)
    if not match:
        raise ValueError(f"Invalid room name: {room_name}")
    return match.group(1), int(match.group(2))


def parse_adjacency_description(desc: str):
    """解析邻接描述字符串，返回 connection_type + direction"""
    desc = desc.lower()

    connection = ConnectionType.DOOR if "door" in desc else ConnectionType.CONNECTED_SPACE
    direction = Direction.UNKNOWN
    for d in Direction:
        if d.value in desc:
            direction = d
            break
    
    return {"connection_type": connection, "direction": direction}


def build_graph_from_json(design: Dict[str, Any]) -> SpatialGraph:
    """
    将 JSON 设计数据转换为 SpatialGraph
    """
    graph = SpatialGraph()

    # 1. 添加房间节点
    for room in design.get("rooms", []):
        name = room["type"]
        room_type, room_id = parse_room_type(name)
        node = graph.add_room(name)
        node.room_type = room_type
        node.room_id = room_id
        node.area = room.get("area", 0)

    # 2. 添加邻接边（修改这部分逻辑，自动补全缺失的房间）
    # 定义枚举方向的反向映射（核心修正点）
    reverse_direction_enum_map = {
        Direction.NORTH: Direction.SOUTH,
        Direction.SOUTH: Direction.NORTH,
        Direction.EAST: Direction.WEST,
        Direction.WEST: Direction.EAST,
        Direction.UNKNOWN: Direction.UNKNOWN
    }

    for room in design.get("rooms", []):
        source_name = room["type"]
        source = graph.rooms[source_name]
        for target_name, desc in room.get("adjacent_to", {}).items():
            # 核心修改1：如果目标房间不存在，自动补全到 graph 中
            if target_name not in graph.rooms:
                print(f"动补全缺失的房间节点：{target_name}")
                # 解析目标房间名称，自动添加节点
                try:
                    target_type, target_id = parse_room_type(target_name)
                    target_node = graph.add_room(target_name)
                    # 给补全的节点赋值基础属性
                    target_node.room_type = target_type
                    target_node.room_id = target_id
                    target_node.area = 0  # 缺失面积默认设为0
                except ValueError as e:
                    raise ValueError(f"补全缺失房间失败：{e}")
            
            parsed = parse_adjacency_description(desc)
            source_conn_type = parsed["connection_type"]
            source_direction = parsed["direction"]

            # 核心修改2：添加源->目标的正向连接
            graph.add_adjacency(
                source_name,
                target_name,
                connection_type=source_conn_type,
                direction=source_direction
            )

            # 核心修改3：计算反向方向并添加目标->源的反向连接
            target_direction = reverse_direction_enum_map[source_direction]

            # 核心修改4：添加目标->源的反向连接（确保双向完整）
            graph.add_adjacency(
                target_name,
                source_name,
                connection_type=source_conn_type,
                direction=target_direction
            )

    # ===================== 新增：校验和修正逻辑 =====================
    # 步骤1：记录房间出现的顺序（以design中rooms的顺序为准）
    room_appear_order = [room["type"] for room in design.get("rooms", [])]
    
    # 步骤2：校验节点完整性（收集所有关联房间并补全）
    all_related_rooms = set(graph.rooms.keys())
    for room_name in graph.rooms.keys():
        room_node = graph.rooms[room_name]
        # 遍历所有邻接边，收集目标房间名
        for edge in room_node.adjacencies:
            all_related_rooms.add(edge.target.name)
    
    # 补全缺失的节点（确保add_adjacency不会报KeyError）
    for room_name in all_related_rooms:
        if room_name not in graph.rooms:
            print(f"校验阶段补全缺失节点：{room_name}")
            try:
                graph.add_room(room_name)
                graph.rooms[room_name].area = 0
            except ValueError as e:
                raise ValueError(f"校验阶段补全缺失房间失败：{e}")

    # 步骤3：校验并修正双向邻接关系和方向（以先出现的节点为准）
    for main_room_name in room_appear_order:
        if main_room_name not in graph.rooms:
            continue
        main_room = graph.rooms[main_room_name]
        
        # 遍历主节点的所有邻接边
        for main_edge in main_room.adjacencies:
            adj_room_name = main_edge.target.name
            if adj_room_name not in graph.rooms:
                continue
            adj_room = graph.rooms[adj_room_name]

            # 主节点的邻接信息（作为基准）
            main_conn_type = main_edge.connection_type
            main_direction = main_edge.direction

            # 修正点：如果主方向是 UNKNOWN，不参与方向修正
            if main_direction == Direction.UNKNOWN:
                expected_adj_direction = None
            else:
                expected_adj_direction = reverse_direction_enum_map[main_direction]

            # 手动查找邻接节点指向主节点的边
            adj_edge = None
            for edge in adj_room.adjacencies:
                if edge.target.name == main_room_name:
                    adj_edge = edge
                    break

            # 情况1：邻接节点缺失反向连接 → 补充
            if adj_edge is None:
                # 仅当主方向不是UNKNOWN时才补充（避免无意义的UNKNOWN反向）
                if main_direction != Direction.UNKNOWN:
                    print(f"🔧 补充反向连接：{adj_room_name} -> {main_room_name}（以{main_room_name}为准）")
                    graph.add_adjacency(
                        adj_room_name,
                        main_room_name,
                        connection_type=main_conn_type,
                        direction=expected_adj_direction
                    )
            # 情况2：邻接节点的反向连接信息不匹配 → 修正（先删除旧边，再添加新边）
            else:
                adj_conn_type = adj_edge.connection_type
                adj_direction = adj_edge.direction
                # 仅当主方向有效时才修正（避免覆盖有效方向为UNKNOWN）
                # 修正点：如果主方向为 UNKNOWN，只校验连接类型，不校验方向
                if main_direction == Direction.UNKNOWN:
                    need_fix = adj_conn_type != main_conn_type
                else:
                    need_fix = (
                        adj_conn_type != main_conn_type
                        or adj_direction != expected_adj_direction
                    )

                if need_fix:
                    print(f"🔧 修正不匹配的反向连接：{adj_room_name} -> {main_room_name}")
                    print(f"   原信息：连接类型={adj_conn_type.value}，方向={adj_direction.value}")
                    print(f"   修正为：连接类型={main_conn_type.value}，方向={expected_adj_direction.value}（以{main_room_name}为准）")
                    
                    # 步骤1：删除旧的不匹配边（遍历并过滤）
                    adj_room.adjacencies = [
                        edge for edge in adj_room.adjacencies 
                        if edge.target.name != main_room_name
                    ]
                    # 步骤2：添加修正后的新边
                    graph.add_adjacency(
                        adj_room_name,
                        main_room_name,
                        connection_type=main_conn_type,
                        direction=(
                            expected_adj_direction
                            if expected_adj_direction is not None
                            else adj_direction  # 保留原方向
                        )
                    )

    # 步骤4：额外补充：修正UNKNOWN方向（可选，基于双向映射推导）
    for room_name in graph.rooms.keys():
        room_node = graph.rooms[room_name]
        for edge in room_node.adjacencies:
            if edge.direction == Direction.UNKNOWN:
                # 查找反向边，用反向边的方向推导当前边的正确方向
                reverse_room = edge.target
                reverse_edge = None
                for e in reverse_room.adjacencies:
                    if e.target.name == room_name and e.direction != Direction.UNKNOWN:
                        reverse_edge = e
                        break
                if reverse_edge:
                    # 反向推导正确方向
                    correct_direction = reverse_direction_enum_map[reverse_edge.direction]
                    print(f"🔧 推导UNKNOWN方向：{room_name} -> {edge.target.name} 从 unknown 修正为 {correct_direction.value}")
                    # 删除旧边，添加修正后的新边
                    room_node.adjacencies = [e for e in room_node.adjacencies if not (e.target.name == edge.target.name and e.direction == Direction.UNKNOWN)]
                    graph.add_adjacency(room_name, edge.target.name, edge.connection_type, correct_direction)

    # 步骤5：打印校验结果（可选，便于验证）
    print("\n 校验修正完成，当前节点列表：")
    for idx, room_name in enumerate(room_appear_order):
        if room_name in graph.rooms:
            adj_count = len(graph.rooms[room_name].adjacencies)
            # 统计有效方向数
            valid_dir_count = sum(1 for e in graph.rooms[room_name].adjacencies if e.direction != Direction.UNKNOWN)
            print(f"   [{idx+1}] {room_name} - 邻接关系数：{adj_count}（有效方向数：{valid_dir_count}）")

    # ===================== 校验逻辑结束 =====================
    
    return graph


def parse_design_to_graph(content: str, fix_json: bool = True) -> SpatialGraph:
    """
    接收 raw LLM 输出或 JSON 文件内容，返回 SpatialGraph
    """
    if fix_json:
        design_json = clean_and_validate_json(content)
    else:
        design_json = json.loads(content)

    graph = build_graph_from_json(design_json)
    # 可选：检查邻接双向性
    graph.check_bidirectional()
    return graph


def parse_design_file(file_path: str) -> SpatialGraph:
    """从 JSON 文件生成 SpatialGraph"""
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"设计文件不存在: {file_path}")

    content = file_path.read_text(encoding="utf-8")
    return parse_design_to_graph(content)
