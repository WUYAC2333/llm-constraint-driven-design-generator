# design_ir/graph.py
from enum import Enum
from typing import Dict, List, Optional
import re

# =========================
# 1. 合法空间类型定义
# =========================

ROOM_TYPES = {
    "LivingRoom",
    "BedRoom",
    "Kitchen",
    "DiningRoom",
    "BathRoom",
    "Storage",
    "Entry",
    "Garage",
    "Garden",
    "Outdoor",
}

def parse_room_name(room_name: str):
    """
    LivingRoom_1 -> ("LivingRoom", 1)
    """
    match = re.match(r"([A-Za-z_]+)_(\d+)", room_name)
    if not match:
        raise ValueError(f"Invalid room name format: {room_name}")

    room_type, room_id = match.group(1), int(match.group(2))

    if room_type not in ROOM_TYPES:
        raise ValueError(f"Unknown room type: {room_type}")

    return room_type, room_id


# =========================
# 2. 邻接关系语义定义
# =========================

class ConnectionType(Enum):
    CONNECTED_SPACE = "connected_space"
    DOOR = "door"


class Direction(Enum):
    NORTH = "north"
    SOUTH = "south"
    EAST = "east"
    WEST = "west"
    UNKNOWN = "unknown"


def parse_adjacency_description(desc: Optional[str]):
    """
    将自然语言/简述解析为结构化邻接语义
    """
    if not desc:
        return ConnectionType.CONNECTED_SPACE, Direction.UNKNOWN

    desc = desc.lower()

    connection = (
        ConnectionType.DOOR
        if "door" in desc
        else ConnectionType.CONNECTED_SPACE
    )

    direction = Direction.UNKNOWN
    for d in Direction:
        if d.value in desc:
            direction = d
            break

    return connection, direction


# =========================
# 3. 图结构定义
# =========================

class AdjacencyEdge:
    def __init__(
        self,
        target: "RoomNode",
        connection_type: ConnectionType,
        direction: Direction = Direction.UNKNOWN,
    ):
        self.target = target
        self.connection_type = connection_type
        self.direction = direction


class RoomNode:
    def __init__(self, name: str):
        self.name = name
        self.room_type, self.room_id = parse_room_name(name)
        self.area: Optional[float] = None
        self.adjacencies: List[AdjacencyEdge] = []

    def add_adjacency(
        self,
        target: "RoomNode",
        connection_type: ConnectionType,
        direction: Direction = Direction.UNKNOWN,
    ):
        self.adjacencies.append(
            AdjacencyEdge(target, connection_type, direction)
        )


class SpatialGraph:
    """
    设计 IR 的核心表示：空间拓扑图
    """
    def __init__(self):
        self.rooms: Dict[str, RoomNode] = {}

    def add_room(self, room_name: str) -> RoomNode:
        if room_name in self.rooms:
            return self.rooms[room_name]

        room = RoomNode(room_name)
        self.rooms[room_name] = room
        return room

    def add_adjacency(
        self,
        source_name: str,
        target_name: str,
        connection_type: ConnectionType,
        direction: Direction = Direction.UNKNOWN,
    ):
        if source_name not in self.rooms or target_name not in self.rooms:
            raise KeyError(
                f"Adjacency refers to unknown room: "
                f"{source_name} -> {target_name}"
            )

        source = self.rooms[source_name]
        target = self.rooms[target_name]

        source.add_adjacency(target, connection_type, direction)

    # =========================
    # 4. 最小一致性校验
    # =========================

    def check_bidirectional(self):
        """
        邻接应当是双向的（软校验，只给 warning）
        """
        for room in self.rooms.values():
            for adj in room.adjacencies:
                back_refs = [
                    a for a in adj.target.adjacencies
                    if a.target == room
                ]
                if not back_refs:
                    print(
                        f"⚠️ Warning: adjacency not bidirectional: "
                        f"{room.name} -> {adj.target.name}"
                    )
