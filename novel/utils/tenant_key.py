import os
from typing import Dict, Any

from dotenv import load_dotenv

load_dotenv()

def get_tenant_llm_config(tenant_id :str) -> Dict[str, Any]:
    # 可以去数据库查询缓存到Redis里，我这里直接固定
    llm_config = {
        "api_key": os.getenv("QWEN_API_KEY"),
        "base_url": os.getenv("QWEN_BASE_URL"),
    }
    return llm_config



