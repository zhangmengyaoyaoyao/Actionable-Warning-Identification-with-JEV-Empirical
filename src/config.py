import os

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

JAVA_PROJECTS = [
    "bcel",
    "codec",
    "collections",
    "configuration",
    "dbcp",
    "digester",
    "fileupload",
    "mavendp",
    "net",
    "pool",
]

PROMPT_TECHNIQUES = [
    "zero_shot",
    "one_shot",
    "few_shot",
    "general_info",
    "expertise",
    "chain_of_thought",
    "critique",
    "self_heuristic",
]

RESULT_MODELS = [
    "llama3.1-70b-instruct",
    "glm-4-flash",
    "gpt-3.5-turbo-0125",
    "DeepSeek-R1",
]

MULTI_TURN_TECHNIQUES = {"critique", "self_heuristic"}

PROVIDERS = {
    "gpt": {
        "env_key": "AIHUBMIX_API_KEY",
        "url": "https://aihubmix.com/v1",
        "model": "gpt-3.5-turbo-0125",
        "model_fullname": "gpt-3.5-turbo-0125",
        "client": "openai",
        "retry_sleep": 1,
    },
    "glm": {
        "env_key": "GLM_API_KEY",
        "url": "https://open.bigmodel.cn/api/paas/v4/",
        "model": "glm-4-flash",
        "model_fullname": "glm-4-flash",
        "client": "openai",
        "retry_sleep": 3,
    },
    "nvidia": {
        "env_key": "NVIDIA_API_KEY",
        "url": "https://integrate.api.nvidia.com/v1",
        "model": "llama3.1-70b-instruct",
        "model_fullname": "meta/llama-3.1-70b-instruct",
        "client": "openai",
        "retry_sleep": 1,
    },
    "openrouter": {
        "env_key": "OPENROUTER_API_KEY",
        "url": "https://openrouter.ai/api/v1",
        "model": "llama3.1-70b-instruct",
        "model_fullname": "meta-llama/llama-3.1-70b-instruct:free",
        "client": "openai",
        "retry_sleep": 1,
    },
    "aihubmix": {
        "env_key": "AIHUBMIX_API_KEY",
        "url": "https://aihubmix.com/v1",
        "model": "llama3.1-70b-instruct",
        "model_fullname": "aihubmix-Llama-3-1-70B-Instruct",
        "client": "openai",
        "retry_sleep": 1,
    },
    "deepseek": {
        "env_key": "AIHUBMIX_API_KEY",
        "url": "https://aihubmix.com/v1",
        "model": "DeepSeek-R1",
        "model_fullname": "DeepSeek-R1",
        "client": "openai",
        "retry_sleep": 1,
    },
    "aliyun": {
        "env_key": "DASHSCOPE_API_KEY",
        "url": None,
        "model": "llama3.1-70b-instruct",
        "model_fullname": "llama3.1-70b-instruct",
        "client": "dashscope",
        "retry_sleep": 3,
    },
    "ollama": {
        "env_key": None,
        "url": None,
        "model": "llama3.1-70b-instruct",
        "model_fullname": "llama3.1-70b-instruct",
        "client": "ollama",
        "retry_sleep": 1,
    },
}


def get_api_key(provider, override=None):
    if override:
        return override
    spec = PROVIDERS[provider]
    env_key = spec.get("env_key")
    if not env_key:
        return None
    value = os.environ.get(env_key) or os.environ.get("LLM_API_KEY")
    if not value and provider == "deepseek":
        value = os.environ.get("DEEPSEEK_API_KEY")
    if not value:
        raise SystemExit(
            f"未找到 API key。请设置环境变量 {env_key} 或 LLM_API_KEY。"
        )
    return value


def resolve_list(values, all_values, all_token="all"):
    if not values or values == [all_token]:
        return list(all_values)
    if len(values) == 1 and "," in values[0]:
        return [item.strip() for item in values[0].split(",") if item.strip()]
    return list(values)
