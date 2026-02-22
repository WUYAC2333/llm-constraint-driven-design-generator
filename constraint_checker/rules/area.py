from .adjacency import get_room_function


AREA_LIMITS = {
    "LivingRoom": (12, 22),
    "BedRoom": (9, 18),
    "Kitchen": (4.5, 9),
    "DiningRoom": (6, 12),
    "BathRoom": (3, 7),
    "Storage": (1.5, 5),
    "Entry": (1.5, 5),
    "Garage": (12, 20),
    "Garden": (3, 30),
    "Outdoor": (2, 15)
}


def validate_room_area(design: dict):
    for r in design["rooms"]:
        func = get_room_function(r["type"])
        if func in AREA_LIMITS:
            mn, mx = AREA_LIMITS[func]
            if not (mn <= r["area"] <= mx):
                return False, f"{r['type']} area out of bounds"
    return True, "Room areas valid"


def validate_total_area(design: dict, min_area=60, max_area=130):
    total = sum(r["area"] for r in design["rooms"])
    if not (min_area <= total <= max_area):
        return False, f"Total area {total} out of bounds"
    return True, "Total area valid"
