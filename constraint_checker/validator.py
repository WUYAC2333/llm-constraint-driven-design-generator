# %% [markdown]
# /*
# constraint_checker/
# ├── **validator.py**    # 调度规则
# ├── examples/
# │      ├── example_ok_1_minimal.json    # 最小可行解（不多不少，刚好满足规则）
# │      ├── example_ok_2_typical.json    # 典型住宅（最常展示的“正常方案”）
# │      ├── example_ok_3_edge.json    # 边界测试（面积与总量接近上限）
# │      ├── example_bad_1_function.json    # 功能关系错误（Bedroom 连到 Storage）
# │      ├── example_bad_2_area.json    #单个空间面积违规（LivingRoom 过小）
# │      ├── example_bad_3_total_area.json    # 总建筑面积超限
# │      └── example_bad_4_adjacency.json    # 缺失必需邻接（Kitchen 没有连 Dining）
# └── run_check.py    # 运行入口
# */

# %% [markdown]
# ### 具体规则：
# ### 空间功能及代号：LivingRoom (a), BedRoom (b), Kitchen (c), DiningRoom (d), BathRoom (e), Storage (f), Entry (g), Garage (h), Garden (j), Outdoor (o)，其中Garden (j)和 Outdoor (o)属于emi-outdoor，不计入建筑面积。
# **1. 基本功能合理性：**
# >① Entry (g)应连接LivingRoom (a)
# >② BedRoom 的所有邻接节点 ⊆ {a, d, e}
# >③ Kitchen (c)和 DiningRoom (d)必须连接
# >④ LivingRoom (a)和DiningRoom (d)必须连接
# **2.空间面积原则 （单位：㎡）**
# >LivingRoom (a): {"min": 12, "max": 22},
# >BedRoom (b):{"min": 9, "max": 18},
# >Kitchen (c): {"min": 4.5, "max": 9},
# >DiningRoom (d): {"min": 6, "max": 12},
# >BathRoom (e): {"min": 3, "max": 7},
# >Storage (f): {"min": 1.5, "max": 5},
# >Entry (g): {"min": 1.5, "max": 5},
# >Garage (h): {"min": 12, "max": 20},
# >Garden (j) {"min": 3, "max": 30},
# >Outdoor (o): {"min": 2, "max": 15}
# **3. 建筑面积原则（90㎡上下）**
# Total_Area: {"min": 60, "max": 130} 
# **4. 邻接关系正确与否（只在“输入中明确给出邻接要求”时才校验）**
# 房间之间邻接关系是否与输入要求一致。

# %%
# example_bad
'''design ={
  "rooms": [
    {
      "type": "Entry_1",
      "area": 3,
      "adjacent_to": {
        "LivingRoom_1": "by connected space in the east"
      }
    },
    {
      "type": "LivingRoom_1",
      "area": 10,
      "adjacent_to": {
        "Entry_1": "by connected space in the west",
        "Dining_1": "by connected space in the east and south",
        "BedRoom_1": "by door in the west"
      }
    },
    {
      "type": "Dining_1",
      "area": 9,
      "adjacent_to": {
        "LivingRoom_1": "by connected space in the west",
        "Kitchen_1": "by connected space in the north"
      }
    },
    {
      "type": "Kitchen_1",
      "area": 4.5,
      "adjacent_to": {
        "Dining_1": "by connected space in the south",
        "Storage_1": "by door in the east"
      }
    },
    {
      "type": "BedRoom_1",
      "area": 12,
      "adjacent_to": {
        "LivingRoom_1": "by door in the east"
      }
    },
    {
      "type": "BedRoom_2",
      "area": 15,
      "adjacent_to": {
        "LivingRoom_1": "by door in the east"
      }
    },
    {
      "type": "BedRoom_3",
      "area": 9,
      "adjacent_to": {
        "LivingRoom_1": "by door in the east"
      }
    },
    {
      "type": "BathRoom_1",
      "area": 3,
      "adjacent_to": {
        "LivingRoom_1": "by door in the east"
      }
    },
    {
      "type": "BathRoom_2",
      "area": 4.5,
      "adjacent_to": {
        "BedRoom_1": "by door in the west"
      }
    },
    {
      "type": "Storage_1",
      "area": 5,
      "adjacent_to": {
        "Kitchen_1": "by door in the west"
      }
    }
  ]
}'''

# constraint_checker/validator.py
# constraint_checker/validator.py
from .rules import (
    validate_basic_function,
    validate_room_area,
    validate_total_area,
    validate_required_adjacency
)

# %%
# 总校验入口
def validate_design(design, requirements=None):
    """
    校验设计是否满足硬规则和用户显式约束
    :param design: dict, JSON 格式设计数据
    :param requirements: dict, 可选，包含用户显式约束（如 adjacency）
    :return: tuple(bool, str), 是否通过及提示信息
    """
    # 1. 通用硬规则（不依赖用户输入）
    validators = [
        validate_basic_function,
        validate_room_area,
        validate_total_area
    ]

    for v in validators:
        ok, msg = v(design)
        if not ok:
            return False, msg

    # 2. 用户显式约束（可选）
    if requirements:
        if "adjacency" in requirements:
            ok, msg = validate_required_adjacency(
                design, requirements["adjacency"]
            )
            if not ok:
                return False, msg

        # 未来可以加：
        # if "orientation" in requirements:
        # if "priority" in requirements:

    return True, "Design valid"

