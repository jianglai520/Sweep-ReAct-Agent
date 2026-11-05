"""
YAML 配置加载工具模块。

统一读取 config/目录下的各YAML配置文件，解析为Python对象供其他模块使用。
路径统一走 get_abs_path()，避免受运行时工作目录影响
"""

import yaml
from utils.path_tool import get_abs_path

def load_yaml(config_path: str, encoding: str = "utf-8"):
    """读取并解析单个 YAML 文件，返回 Python对象"""
    with open(config_path, "r", encoding = encoding) as f:
        # 用 safe_load：配置文件是纯数据，避免 load 的反序列化安全风险
        return yaml.safe_load(f)


def load_rag_config(config_path: str = get_abs_path("config/rag.yaml"),
                    encoding: str = "utf-8"):
    """加载 RAG 配置（如模型名、检索参数等）。"""
    return load_yaml(config_path, encoding)


def load_chroma_config(config_path: str = get_abs_path("config/chroma.yaml"),
                       encoding: str = "utf-8"):
    """加载 Chroma 向量库配置。"""
    return load_yaml(config_path, encoding)


def load_prompts_config(config_path: str = get_abs_path("config/prompts.yaml"),
                        encoding: str = "utf-8"):
    """加载提示词配置。"""
    return load_yaml(config_path, encoding)


def load_agent_config(config_path: str = get_abs_path("config/agent.yaml"),
                      encoding: str = "utf-8"):
    """加载 Agent 配置。"""
    return load_yaml(config_path, encoding)


rag_conf = load_rag_config()
chroma_conf = load_chroma_config()
prompts_conf = load_prompts_config()
agent_conf = load_agent_config()


# 测试
if __name__ == '__main__':
    print(rag_conf['chat_model_name'])