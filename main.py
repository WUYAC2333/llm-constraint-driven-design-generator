# main.py
from utils.io import USER_INPUT_FILE, read_text
from llm import call_llm, build_intention_prompt
from constraint_checker import validate_design
from design_ir import parse_design_to_graph
import time
import json
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def graph_to_json_dict(spatial_graph):
    """把 SpatialGraph 转回原始 JSON 格式的字典"""
    rooms = []
    for room_node in spatial_graph.rooms.values():
        # 构建邻接关系字典
        adjacent_to = {}
        for adj_edge in room_node.adjacencies:
            # 还原邻接描述字符串（如 "by door in the north"）
            direction = adj_edge.direction.value
            connection = "by door" if adj_edge.connection_type.value == "door" else "by connected space"
            desc = f"{connection} in the {direction}"
            adjacent_to[adj_edge.target.name] = desc
        
        rooms.append({
            "type": room_node.name,
            "area": room_node.area,
            "adjacent_to": adjacent_to
        })

        print(rooms)
    return {"rooms": rooms}

def run_design_pipeline(user_input: str):
    """
    执行完整流程：
    LLM生成 → 解析 → 构建图 → 转回JSON → 规则校验
    返回结构化结果
    """
    start_time = time.time()
    try:
        # 1. 构建 Prompt
        prompt = build_intention_prompt(user_input)

        # 2. 调用 LLM
        llm_result = call_llm(prompt)
        llm_result_record = json.dumps(llm_result, indent=2, ensure_ascii=False)
        logger.info(f"JSON 解析成功，结果：")
        logger.info(llm_result_record)

        # 3. 解析为图结构
        spatial_graph = parse_design_to_graph(llm_result, fix_json=True)
        logger.info(f"SpatialGraph 构建成功！包含 {len(spatial_graph.rooms)} 个房间节点")

        # 4. 转回 JSON
        json_dict = graph_to_json_dict(spatial_graph)
        logger.info(json_dict)

        # 5. 校验
        ok, result = validate_design(json_dict)
        if ok:
            logger.info("Validation passed!")
        else:
            logger.info(f"Rejected: {result}")

    except Exception as e:
        logger.error(f"程序执行失败：{e}")
    
    finally:
        logger.info(f"总耗时：{time.time() - start_time:.2f}s")

    return {
        "llm_raw_output": llm_result,
        "parsed_design": json_dict,
        "validation_passed": ok,
        "validation_result": result
    }

# 调用示例
if __name__ == "__main__":
        # 1. 读取用户输入
        user_input = read_text(USER_INPUT_FILE)
        results = run_design_pipeline(user_input)