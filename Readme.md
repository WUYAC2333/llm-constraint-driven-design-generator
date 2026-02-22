# 基于 LLM 的设计意图 → 空间约束 → 可验证生成系统

> (本作品集包含三个基于 FastAPI 服务化封装的 AIGC 系统，分别聚焦生成、检索增强与评估任务，均支持 Swagger 交互测试。)

### 项目定位

本项目探索如何将自然语言形式的建筑设计意图，转化为**结构化、可验证的空间约束**，并在约束驱动下生成早期概念方案。项目重点不在于“生成造型”，而在于**确保生成方案遵循关键设计约束**。

## 1. 项目背景与问题定义

在建筑与空间设计的早期阶段，设计需求通常以自然语言形式出现，具有以下特征：

- 表述模糊、非形式化
- 隐含大量未被明确表达的空间约束
- 混合存在“必须满足”与“偏好满足”的条件

当前基于大模型的生成方法往往直接从文本生成方案，但在缺乏**显式约束建模与校验机制**时，生成结果容易出现逻辑错误或难以解释。

> 本项目关注的核心问题不是“如何生成方案”，而是：
> **当设计意图被转化为机器可处理的形式后，如何判断生成结果是否“违规”，以及违规原因是什么。**

## 2. 系统总体架构

系统采用**多阶段（multi-stage）的 AIGC 应用架构**，将设计理解、约束建模、生成与校验解耦：

```
自然语言设计需求（输入）
              ↓
① 意图解析层（LLM）
              ↓
② 结构化约束建模层（JSON Schema）
              ↓
③ 候选方案生成层（规则驱动）
              ↓
④ 约束校验与失败分析层
              ↓
结构化输出（合规 / 被拒方案 + 原因）
```

### 2.1 核心模块说明

| 模块                    | 功能                                      | 备注                                              |
| ----------------------- | ----------------------------------------- | ------------------------------------------------- |
| **main.py**             | 系统入口：串联 LLM → Validator → 输出结果 | 控制数据流与执行顺序                              |
| **config/**             | 用户输入、LLM 配置、设计约束文件          | 支持快速调整与复现                                |
| **llm/**                | 与 LLM API 交互、意图解析                 | 唯一不确定性来源，可替换为不同模型                |
| **intent/**             | 中间结构定义（schema）                    | 文档化设计意图，可扩展高级验证                    |
| **design_ir/**          | JSON → Graph 转换，标准化设计表示         | 支持空间关系分析                                  |
| **constraint_checker/** | 规则调度与校验                            | 包含 adjacency/area/topology 等规则，提供合规反馈 |
| **utils/**              | 文件读写与日志记录                        | 工程辅助工具                                      |

> 本项目强调 **约束驱动生成** 而非造型生成。

## 3. 模块一：意图解析层（Intent Parsing Layer）

### 3.1 目标

该模块负责将自然语言形式的设计描述，转化为**结构化、可区分类型的设计意图**。
在本阶段，LLM 被明确限定为**需求分析助手**，而非设计生成器，主要关注信息抽取与约束解析。

**核心目标：**

- 提取设计元素及功能
- 识别硬性约束（must-have）与软性偏好（nice-to-have）
- 输出可被下游模块直接使用的 JSON 结构

### 3.2 输入示例（自然语言）

```
我希望你为我设计一个住宅，住宅中入口位于前部，直通客厅。
客厅东侧设餐厅，餐厅北侧为开放式厨房。
客厅西侧通过走廊连接三间卧室，主卧设独立卫生间。
客厅附近还有一个共用卫生间。
储藏室位于厨房旁，方便物品归置。
住宅总建筑面积约为 90 平方米。
```

### 3.3 核心实现方式（代码层面）

- 高性能大语言模型 API（如通义千问）进行意图解析
- 通过 Prompt 明确约束模型行为，仅做信息抽取
  - **不生成设计方案**
  - **不补充不存在的信息**
  - **仅提取文本中已出现或可直接推断的意图**
- API credentials 通过环境变量管理，保证安全
- 输出的 JSON 可直接作为下游模块的输入

## 4. 模块二：结构化约束建模层（Constraint Representation Layer）

### 4.1 目标

该模块是系统的核心，用于将**自然语言意图**显式建模为**可被程序校验的约束规则**。
输出的结构化约束为后续候选方案生成与校验提供标准化接口。
**核心目标：**

- 区分**硬性约束（Hard Constraints）**与**偏好约束（Soft Constraints）**
- 确保每条约束具有明确可检验条件
- 完全独立于几何或图形表示

### 4.2 约束建模原则

- **硬性约束（Hard Constraints）**：必须满足，否则方案判定为违规
- **偏好约束（Soft Constraints）**：尽量满足，用于引导方案，但不直接导致拒绝
- 所有约束必须可被下游规则引擎解析与验证
- 与几何或视觉渲染解耦，便于快速迭代与扩展

### 4.3 约束 Schema 示例

```
{
    "rooms": [
        {
            "type": "<RoomType_ID>",
            "adjacent_to": {
                "<OtherRoomType_ID>": "<connection> <direction>"
            }
        }
    ]
}
```

> 该模块**为候选方案生成与校验提供明确规则接口**，保证生成结果可验证、可追溯。

## 5. 模块三：候选方案生成层（Candidate Generation）

### 5.1 目标

该模块的任务是生成**符合约束结构的候选解**，用于验证约束系统的有效性与可操作性。

注意：**本阶段不追求最优设计，只保证可校验与结构合法。**

### 5.2 实现方式

- 通过 LLM 在明确结构限制下生成 JSON 表示的候选方案
- 保持输出与约束 Schema 对齐，便于下游校验模块直接使用
- 可在输入意图或约束变化时快速生成新的候选方案

### 5.3 候选方案示例

```
{
  "rooms": [
    {
      "type": "Entry_1",
      "adjacent_to": {
        "LivingRoom_1": "by connected space"
      }
    },
    {
      "type": "LivingRoom_1",
      "adjacent_to": {
        "Entry_1": "by connected space",
        "DiningRoom_1": "by connected space east",
        "BedRoom_1": "by door south",
        "BedRoom_2": "by door south",
        "BedRoom_3": "by door south",
        "BathRoom_2": "by door"
      }
    },
    {
      "type": "DiningRoom_1",
      "adjacent_to": {
        "LivingRoom_1": "by connected space west",
        "Kitchen_1": "by connected space north"
      }
    },
    {
      "type": "Kitchen_1",
      "adjacent_to": {
        "DiningRoom_1": "by connected space south",
        "Storage_1": "by door"
      }
    },
    {
      "type": "BedRoom_1",
      "adjacent_to": {
        "LivingRoom_1": "by door north",
        "BathRoom_1": "by door"
      }
    },
    {
      "type": "BathRoom_1",
      "adjacent_to": {
        "BedRoom_1": "by door"
      }
    },
    {
      "type": "BathRoom_2",
      "adjacent_to": {
        "LivingRoom_1": "by door"
      }
    },
    {
      "type": "Storage_1",
      "adjacent_to": {
        "Kitchen_1": "by door"
      }
    },
    {
      "type": "BedRoom_2",
      "adjacent_to": {
        "LivingRoom_1": "by door south"
      }
    },
    {
      "type": "BedRoom_3",
      "adjacent_to": {
        "LivingRoom_1": "by door south"
      }
    }
  ]
}
```

> 该模块**强调约束一致性与结构合法性**，确保生成结果可以直接交由校验模块进行验证，而无需人工干预。

## 6. 模块四：约束校验与失败分析（Validation Layer）v2.0(0208)

### 6.1 目标

- 自动判断候选方案是否违反约束
- 输出明确、可解释的失败原因
- 提供可扩展接口，未来可接入更多规则或 LLM 生成的需求

### 6.2 核心校验逻辑

**实现方式：** Python 验证器 (validator.py)

**当前支持的四类核心规则：**

**6.2.1 基本功能合理性**

- 入口必须连接客厅
- 卧室只能连接客厅、餐厅或卫生间
- 厨房必须连接餐厅
- 客厅必须连接餐厅

**6.2.2 空间面积原则（单位：㎡）**

- LivingRoom: 12–22
- BedRoom: 9–18
- Kitchen: 4.5–9
- DiningRoom: 6–12
- BathRoom: 3–7
- Storage / Entry: 1.5–5
- Garage: 12–20
- Garden: 3–30
- Outdoor: 2–15

**6.2.3 总建筑面积原则**

- 总面积控制在 60–130㎡
  **6.2.4 邻接关系正确性**
- 核对设计要求中每对必须邻接房间是否存在

注： Validator 会在遇到第一条违规规则时停止校验，以保证可解释性。系统目前校验主要针对四类核心规则，可按需扩展更多规则（如未知房间类型、通透性、采光等）。

### 6.3 运行示例

```
# 从项目根目录运行 run_check，批量校验 examples 内设计
python run_check.py
```

**输出示例：**

```
Checking: example_ok_1_minimal.json
  with requirements ✔
✅ PASS: Design valid

Checking: example_bad_4_adjacency.json
  with requirements ✔
❌ REJECT: Missing required adjacency: Entry_1-LivingRoom_1
```

**6.4 可扩展性**

- 可接入 LLM 生成不同 requirements.json，实现“自然语言 → 结构化约束 → 校验”的完整流程
- 可新增校验规则，如：
  - 未定义房间类型
  - 功能复合空间面积比例
  - 空间通透性、采光、声环境等级等

## 7. 运行方式

### 方式1：本地运行（命令行模式）

```
pip install -r requirements.txt
python main.py
```

执行完整流程：
LLM生成 → SpatialGraph构建 → JSON转换 → 规则校验

### 方式2：运行 API 服务

```
pip install -r requirements.txt
uvicorn api:app --host 127.0.0.1 --port 8002
```

访问：
` http://127.0.0.1:8002/docs`
通过 Swagger UI 进行交互式测试。
推荐的“user_input”示例：

```
Entry_1 at front, directly connected to LivingRoom_1, DiningRoom_1 is EAST of LivingRoom (by connected space), open Kitchen_1 is NORTH of DiningRoom_1 (by connected space), LivingRoom_1 connects to BedRoom_1, BedRoom_2, BedRoom_3 on SOUTH side (by door), BedRoom_1 (Master) has private BathRoom_1 (by door), shared BathRoom_2 near LivingRoom_1 (by door), Storage_1 next to Kitchen_1 (by door)
```

### 7.3 配置环境

编辑 model_config.yaml 文件，配置 LLM 相关参数：

```
llm:
  provider: dashscope
  api_key_env: QWEN_API_KEY  # 环境变量名（可选）
  api_key_fallback: 你的实际API密钥  # 本地测试直接填写，优先级高于环境变量
  url: https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions
  model: qwen-turbo
```

### 7.4 运行主程序（核心入口）

```
# 执行完整流程：LLM生成空间方案 → 格式转换 → 规则校验 → 输出结果
python main.py
```

### 7.5 可选：仅运行批量校验脚本（无 LLM 生成，仅校验示例文件）

```
# 仅校验 examples/ 目录下的预制示例文件（无LLM调用，快速验证校验规则）
python drafts/constraint_checker/run_check.py
```

> 运行 main.py 会执行全流程：调用 LLM 生成空间方案 → 转换为 SpatialGraph 格式 → 转回 JSON → 执行面积 / 邻接关系等规则校验 → 输出最终结果；
> 运行 run_check.py 仅批量校验预制示例文件，无需调用 LLM，适合快速验证校验规则是否正常；
> 若出现 API Key 相关错误，优先检查 model_config.yaml 中的 api_key_fallback 是否配置正确；

## 8. 项目总结

本项目通过引入**约束建模与校验机制**，展示了一种不同于传统“端到端生成”的 AIGC 应用思路：

- 生成过程被拆解为多个可解释阶段
- 每一阶段均可独立分析与调试
- 系统能够明确说明“为什么一个结果不可用”
  该思路同样适用于其他需要高可靠性的生成任务，例如：
- 规则文本生成
- 结构化内容生成
- 智能配置或设计验证

## Appendix A｜English Summary

**Project Title**

LLM-driven Intent Parsing and Constraint-aware Generative Pipeline for Spatial Design

**Summary**

This project presents a multi-stage AIGC pipeline that transforms vague natural-language design intents into structured, verifiable spatial constraints. Instead of directly generating design forms, the system focuses on identifying constraint violations and explaining why certain generated configurations are invalid. The approach emphasizes interpretability, robustness, and practical usability in early-stage design scenarios.
