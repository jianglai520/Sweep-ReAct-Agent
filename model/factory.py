from abc import ABC, abstractmethod
import os
from typing import Optional
from langchain_ollama import OllamaEmbeddings
from utils.config_handler import rag_conf

class BaseModelFactory(ABC):
    """模型工厂抽象基类，子类必须实现 generate()."""
    @abstractmethod
    def generator(self) -> Optional[Embeddings | BaseChatModel]:
        pass


# 聊天模型工厂类
class ChatModelFactory(BaseModelFactory):
    """聊天模型工厂：按配置返回本机 Ollama 模型或远端 API 模型。"""

    def generator(self) -> Optional[Embeddings | BaseChatModel]:
        if rag_conf.get("chat_model_provider", "ollama") == "ollama":
            return ChatOllama(model = rag_conf["chat_model_name"])

        return self.__build_api_model()

    def __build_api_model(self) -> Optional[BaseChatModel]:
        """构造 OpenAI 兼容协议的聊天模型（当前用于 DeepSeek 官方 API）。

        Returns:
            可传入 create_agent 的聊天模型实例。

        Raises:
            RuntimeError: 未安装 langchain-openai，或未配置 API Key 时抛出。
        """
        # 延迟导入：走本机 Ollama 时不要求安装 langchain-openai
        try:
            from langchain_openai import ChatOpenAI
        except ImportError as e:
            raise RuntimeError("使用 API 模式需要先安装 langchain-openai") from e

        api_key_env = rag_conf["chat_model_api_key_env"]
        api_key = os.getenv(api_key_env)
        if not api_key:
            raise RuntimeError(f"环境变量{api_key_env}未设置，请在工程根 .env 中配置")

        return ChatOpenAI(
            model = rag_conf["chat_model_name"],
            base_url = rag_conf["chat_model_base_url"],
            api_key = api_key,
            temperature = 0,
        )


# 嵌入模型工厂类
class EmbeddingsModelFactory(BaseModelFactory):
    """嵌入模型工厂：返回 Ollama 嵌入模型实例（带缓存）。"""
    def generator(self) -> Optional[Embeddings | BaseChatModel]:
        return OllamaEmbeddings(model = rag_conf["embedding_model_name"])

chat_model = ChatModelFactory().generator()
embed_model = EmbeddingsModelFactory().generator()

# 测试
if __name__ == "__main__":
    chat_model = ChatModelFactory().generator()
    embed_model = EmbeddingsModelFactory().generator()

    resp = chat_model.invoke("你好，请用一句话介绍你自己")
    print(resp.content)

    vec = embed_model.embed_query("测试文本")
    print(f"向量维度: {len(vec)}")