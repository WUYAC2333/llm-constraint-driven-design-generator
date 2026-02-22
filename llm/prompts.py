from pathlib import Path
# 导入io模块中的路径常量和读取方法
from utils.io import (
    USER_INPUT_FILE,  # 对应 CONFIG_DIR / "user_input.txt"
    read_text         # 读取文本文件的方法
)
from intent import intent_schema

PROMPT = """
You are a strict architectural spatial constraint engine.
OUTPUT ONLY VALID JSON. NO OTHER TEXT, NO EXPLANATION, NO MARKDOWN, NO CODE BLOCKS.

Rules (MUST follow strictly):

1. Room ID format: <RoomType>_<Number> (e.g., LivingRoom_1, BedRoom_2)
2. Each room MUST contain:
   - "type"
   - "area"
   - "adjacent_to"
3. Area rules (unit: square meters):
   The value of "area" MUST be a number (not a string).
   It MUST fall within the allowed range for that room type:

   LivingRoom: 12 – 22
   BedRoom: 9 – 18
   Kitchen: 4.5 – 9
   DiningRoom: 6 – 12
   BathRoom: 3 – 7
   Storage: 1.5 – 5
   Entry: 1.5 – 5
   Garage: 12 – 20
   Garden: 3 – 30
   Outdoor: 2 – 15

   If the area is outside the allowed range, the output is INVALID.
   All rooms must have realistic residential area proportions.
   Avoid generating extreme boundary values unless necessary.
4. Adjacency format: "direction + connection" (e.g., "north by door")
5. Only use values from allowed lists below:

ALLOWED_ROOM_TYPES = ["LivingRoom", "BedRoom", "Kitchen", "DiningRoom", "BathRoom", "Storage", "Entry", "Garage", "Garden", "Outdoor"]
ALLOWED_CONNECTIONS = ["by connected space", "by door"]
ALLOWED_DIRECTIONS = ["in the north", "in the south", "in the east", "in the west"]

Output ONLY the JSON structure below, fill with correct values:
{intent_schema}
"""

def load_design_intention() -> str:
    """从user_input.txt文件中读取设计意图内容"""
    try:
        # 调用io模块的read_text方法读取文件，自动处理路径校验和编码
        intention_content = read_text(USER_INPUT_FILE)
        # 确保读取的内容格式和原PROMPT中的一致（每行以-开头）
        # 如果文件内容本身格式正确，直接返回；如果需要格式化，可在这里处理
        return intention_content.strip()  # 去除首尾空白符，避免格式问题
    except FileNotFoundError as e:
        # 可选：自定义异常提示，方便定位问题
        raise FileNotFoundError(f"设计意图文件读取失败：{e}")

def build_intention_prompt(user_input: str) -> str:
    """构建完整的prompt，包含动态读取的设计意图和用户输入"""
    # 1. 读取设计意图内容
    design_intention = load_design_intention()
    # 2. 填充PROMPT模板中的设计意图占位符、JSON结构占位符
    prompt_with_intention = PROMPT.format(intent_schema=intent_schema)
    # 3. 拼接用户输入（保持你原有逻辑）
    full_prompt = f"""
{prompt_with_intention}

Design intention:
{user_input}
"""
    return full_prompt