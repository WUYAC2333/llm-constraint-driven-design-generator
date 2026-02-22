# 邻接相关规则与工具

def get_room_function(room_type: str) -> str:
    """
    'LivingRoom_1' -> 'LivingRoom'
    """
    return room_type.split("_")[0]


def extract_adjacency(design: dict) -> set:
    """
    从 rooms[].adjacent_to 中提取无向邻接对
    """
    edges = set()
    for room in design["rooms"]:
        r1 = room["type"]
        for r2 in room.get("adjacent_to", {}):
            edges.add(tuple(sorted((r1, r2))))
    return edges


def validate_required_adjacency(design: dict, required_pairs: list):
    adj = extract_adjacency(design)
    room_ids = {r["type"] for r in design["rooms"]}

    for a, b in required_pairs:
        if a not in room_ids or b not in room_ids:
            return False, f"Required adjacency refers to unknown room: {a} or {b}"

        if tuple(sorted((a, b))) not in adj:
            return False, f"Missing required adjacency: {a}-{b}"

    return True, "Required adjacency satisfied"
