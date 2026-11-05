from abc import ABC, abstractmethod
from typing import Optional
from langchain_ollama import ChatOllama, OllamaEmbeddings
from utils.config_handler import rag_conf

class BaseModelFactory(ABC):
    """模型工厂抽象基类，子类必须实现 generate()."""
    @abstractmethod
    def generator(self) -> Optional[Embeddings | BaseChatModel]:
        pass


# 聊天模型工厂类
class ChatModelFactory(BaseModelFactory):
    """聊天模型工厂：返回 Ollama 聊天模型实例（带缓存）。"""
    def generator(self) -> Optional[Embeddings | BaseChatModel]:
        return ChatOllama(model = rag_conf["chat_model_name"])


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