# constraint_checker/rules/topology.py
from .adjacency import extract_adjacency, get_room_function


def validate_basic_function(design: dict):
    adj = extract_adjacency(design)

    def connected(x, y):
        return tuple(sorted((x, y))) in adj

    rooms = design["rooms"]

    entries = [r for r in rooms if get_room_function(r["type"]) == "Entry"]
    livings = [r for r in rooms if get_room_function(r["type"]) == "LivingRoom"]
    dinings = [r for r in rooms if get_room_function(r["type"]) == "DiningRoom"]
    kitchens = [r for r in rooms if get_room_function(r["type"]) == "Kitchen"]

    # ① Entry → LivingRoom
    for e in entries:
        if not any(connected(e["type"], l["type"]) for l in livings):
            return False, "Entry is not connected to LivingRoom"

    # ② Bedroom adjacency constraint
    allowed = {"LivingRoom", "DiningRoom", "BathRoom"}
    for r in rooms:
        if get_room_function(r["type"]) == "BedRoom":
            neighbors = [
                x for pair in adj if r["type"] in pair
                for x in pair if x != r["type"]
            ]
            for n in neighbors:
                if get_room_function(n) not in allowed:
                    return False, f"BedRoom connected to invalid space: {n}"

    # ③ Kitchen ↔ DiningRoom
    if not any(
        connected(k["type"], d["type"])
        for k in kitchens for d in dinings
    ):
        return False, "Kitchen and DiningRoom must be connected"

    # ④ LivingRoom ↔ DiningRoom
    if not any(
        connected(l["type"], d["type"])
        for l in livings for d in dinings
    ):
        return False, "LivingRoom and DiningRoom must be connected"

    return True, "Basic function valid"
