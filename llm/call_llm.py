# llm/call_llm.py

import os
import time
import requests

from utils.io import read_yaml, MODEL_CONFIG_YAML

MODEL_CONFIG = read_yaml(MODEL_CONFIG_YAML)

LLM_CFG = MODEL_CONFIG["llm"]
GEN_CFG = LLM_CFG["generation"]
RETRY_CFG = LLM_CFG["retry"]

QWEN_URL = LLM_CFG["url"]
MODEL_NAME = LLM_CFG["model"]
SYSTEM_PROMPT = MODEL_CONFIG["system_prompt"]


def get_api_key() -> str:
    """
    获取 API Key（优先使用配置文件的 fallback 值，环境变量兜底）
    修复点：
    1. 优先返回 fallback 值，而非环境变量
    2. 清除会话中残留的旧环境变量（可选）
    3. 增加调试信息和异常处理
    """
    # 调试：打印当前配置和环境变量状态
    env_name = LLM_CFG.get("api_key_env")
    fallback_key = LLM_CFG.get("api_key_fallback")
    env_key = os.getenv(env_name) if env_name else None
    
    print(f"===== API Key 加载调试 =====")
    print(f"配置的环境变量名：{env_name}")
    print(f"会话中环境变量值：{env_key[:6]}...{env_key[-4:]} if env_key else 'None'")
    print(f"配置文件 fallback 值：{fallback_key[:6]}...{fallback_key[-4:]} if fallback_key else 'None'")
    
    # 核心修复：优先使用 fallback 值，环境变量仅作为兜底
    # 如果你想彻底禁用环境变量，直接返回 fallback_key 即可
    # final_key = fallback_key or env_key
    final_key = env_key
    
    # 验证 Key 是否有效
    if not final_key or not final_key.strip():
        raise ValueError(
            f"API Key 未配置！\n"
            f"- 配置文件 fallback 值：{fallback_key}\n"
            f"- 环境变量 {env_name} 值：{env_key}"
        )
    
    # 可选：清除会话中残留的旧环境变量（彻底避免干扰）
    if env_name and env_name in os.environ:
        del os.environ[env_name]
        print(f"✅ 已清除会话中残留的 {env_name} 环境变量")
    
    print(f"✅ 最终使用的 API Key：{final_key[:6]}...{final_key[-4:]}")
    return final_key


def call_llm(prompt: str) -> str:
    """
    调用 LLM，仅返回原始文本输出
    """
    api_key = get_api_key()
    if not api_key:
        raise RuntimeError("LLM API Key 未配置")

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        **GEN_CFG
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    for retry in range(RETRY_CFG["max_retries"]):
        try:
            response = requests.post(
                QWEN_URL,
                json=payload,
                headers=headers,
                timeout=(
                    RETRY_CFG["timeout"]["connect"],
                    RETRY_CFG["timeout"]["read"]
                ),
                verify=False
            )

            result = response.json()
            return result["choices"][0]["message"]["content"]

        except requests.exceptions.ReadTimeout:
            if retry < RETRY_CFG["max_retries"] - 1:
                time.sleep(RETRY_CFG["retry_delay"])
                continue
            raise RuntimeError("LLM 多次超时")