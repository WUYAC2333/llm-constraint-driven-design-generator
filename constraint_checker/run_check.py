# constraint_checker/run_check.py 对示例文件进行检验
import json
from pathlib import Path
from .validator import validate_design
# 导入统一的示例目录路径
from utils.io import EXAMPLE_FILES, ensure_dir, REQUIREMENTS_JSON

def run_example(design_path):
    """校验单个 design 示例"""
    design_path = Path(design_path)
    if not design_path.exists():
        raise FileNotFoundError(f"设计文件不存在：{design_path}")

    # 读取design文件
    with open(design_path, "r", encoding="utf-8") as f:
        design = json.load(f)

    # 读取requirements.json（使用统一路径）
    req_path = REQUIREMENTS_JSON
    requirements = None
    if req_path.exists():
        with open(req_path, "r", encoding="utf-8") as f:
            requirements = json.load(f)

    # 调用校验函数
    ok, msg = validate_design(design, requirements)

    # 输出结果
    print(f"\nChecking: {design_path.name}")
    if requirements:
        print("  with requirements ✔")
    else:
        print("  no requirements ❌")

    if ok:
        print("✅ PASS:", msg)
    else:
        print("❌ REJECT:", msg)
    
    # 返回校验结果，方便批量统计
    return ok, msg

def batch_run_check(examples_dir=None):
    """批量校验示例文件（适配EXAMPLE_FILES是文件列表的场景）"""
    # 核心修复：优先使用EXAMPLE_FILES文件列表，而非目录路径
    if examples_dir is None:
        # 情况1：EXAMPLE_FILES是文件路径列表（你的实际情况）
        if isinstance(EXAMPLE_FILES, list) and len(EXAMPLE_FILES) > 0:
            file_paths = [Path(f) for f in EXAMPLE_FILES]
        # 情况2：传入了目录路径（兼容原有逻辑）
        else:
            examples_dir = Path("./constraint_checker/examples")  # 修正为子文件夹路径
            examples_dir = ensure_dir(examples_dir)
            # 遍历目录下的json文件（排除requirements）
            file_paths = [
                f for f in examples_dir.iterdir()
                if f.is_file() and f.suffix.lower() == ".json" and not f.name.endswith(".requirements.json")
            ]
    else:
        # 如果手动传入目录，按目录处理
        examples_dir = Path(examples_dir)
        ensure_dir(examples_dir)
        file_paths = [
            f for f in examples_dir.iterdir()
            if f.is_file() and f.suffix.lower() == ".json" and not f.name.endswith(".requirements.json")
        ]

    # 初始化统计变量
    total_files = len(file_paths)
    pass_files = 0
    fail_files = 0
    fail_details = []

    # 打印开始信息
    print(f"📁 开始批量校验，共找到 {total_files} 个示例文件")
    print("-" * 60)

    # 逐个校验文件列表中的文件
    for file_path in file_paths:
        try:
            # 调用run_example执行单个文件校验
            ok, msg = run_example(file_path)
            
            # 统计结果
            if ok:
                pass_files += 1
            else:
                fail_files += 1
                fail_details.append({"file": file_path.name, "reason": msg})
                
        except Exception as e:
            # 捕获单个文件的异常，避免批量执行中断
            fail_files += 1
            error_msg = f"校验出错：{str(e)}"
            fail_details.append({"file": file_path.name, "reason": error_msg})
            print(f"\nChecking: {file_path.name}")
            print(f"❌ ERROR: {error_msg}")

    # 打印汇总结果
    print("-" * 60)
    print(f"📊 校验汇总：总计 {total_files} 个文件")
    print(f"   ✅ 通过：{pass_files} 个")
    print(f"   ❌ 失败：{fail_files} 个")
    
    # 打印失败文件详情
    if fail_details:
        print("\n❌ 失败文件详情：")
        for idx, detail in enumerate(fail_details, 1):
            print(f"   {idx}. {detail['file']}: {detail['reason']}")

if __name__ == "__main__":
    # 直接调用，无需处理路径切换（根目录已统一）
    batch_run_check()