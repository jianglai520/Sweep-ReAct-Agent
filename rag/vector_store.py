import os
from utils.file_handler import txt_loader, pdf_loader, listdir_with_allowed_type, get_file_md5_hex
from utils.path_tool import get_abs_path
from langchain_chroma import Chroma
from utils.config_handler import chroma_conf
from model.factory import embed_model
from langchain_text_splitters import RecursiveCharacterTextSplitter
from utils.logger_handler import logger
from langchain_core.documents import Document

class VectorStoreService:
    """
    向量库服务类：
    职责 = 读取本地知识文件 -> 分片 -> 向量化 -> 存入 Chroma -> 对外提供 Retriever
    设计要点：配置驱动、增量幂等（MD5 去重）、文件级容错、分层解耦
    """
    def __init__(self):
        self.vector_store = Chroma(
            collection_name = chroma_conf["collection_name"],
            embedding_function = embed_model,
            # Chroma 会把相对路径按进程 CWD 解析，这里统一转成基于工程根的绝对路径，
            # 避免在不同目录启动时生成多个 chroma_db
            persist_directory = get_abs_path(chroma_conf["persist_directory"])
        )

        self.spliter = RecursiveCharacterTextSplitter(
            chunk_size = chroma_conf["chunk_size"],
            chunk_overlap = chroma_conf["chunk_overlap"],
            separators = chroma_conf["separators"]
        )

    def get_retriever(self):
        """
        对外暴露检索器：
        返回标准 LangChain Retriever 接口，可直接接入 RetrievalQA / create_retrieval_chain 等链。
        当前是纯相似度 Top-K；如需 MMR 去冗余或阈值过滤，可在此扩展 search_type / score_threshold。
        """
        return self.vector_store.as_retriever(search_kwargs = {"k": chroma_conf["k"]})

    def _vector_count(self) -> int:
        """返回当前集合内的向量条数。

        Notes:
            langchain_chroma 未暴露计数接口，这里直接调用底层 chromadb 集合的 count()。
        """
        return self.vector_store._collection.count()

    def _md5_store_has_entries(self) -> bool:
        """判断 MD5 清单文件是否存在且至少有一条有效记录。"""
        md5_store_path = get_abs_path(chroma_conf["md5_hex_store"])
        if not os.path.exists(md5_store_path):
            return False

        with open(md5_store_path, "r", encoding = "utf-8") as f:
            return any(line.strip() for line in f)

    def load_document(self):
        """
        从数据文件夹内读取数据文件，转为向量存入向量库。

        核心特性：
          - MD5 去重：已处理过的文件跳过（增量入库）
          - 清单自愈：向量库为空但 MD5 清单已有记录时，判定清单失效并清空后重新入库
          - 文件级容错：单个文件失败不中断整批
          - 空内容防护：加载空 / 分片空都跳过，避免写入无效数据
        """
        # MD5 清单只对配套的向量库有效：库被删除或重建后，旧记录会让所有文件被跳过，
        # 这里先校验两者是否配套，不配套就清空清单，避免“删库不删清单导致全部跳过”。
        if self._vector_count() == 0 and self._md5_store_has_entries():
            logger.warning("[加载知识库]向量库为空但MD5清单已有记录，判定清单失效，清空后重新入库")
            open(get_abs_path(chroma_conf["md5_hex_store"]), "w", encoding = "utf-8").close()

        def check_md5_hex(md5_for_check: str):
            if not os.path.exists(get_abs_path(chroma_conf["md5_hex_store"])):
                open(get_abs_path(chroma_conf["md5_hex_store"]), "w", encoding = "utf-8").close()
                return False  # md5没有处理过

            with open(get_abs_path(chroma_conf["md5_hex_store"]), "r", encoding = "utf-8") as f:
                for line in f.readlines():
                    line = line.strip()
                    if line == md5_for_check:
                        return True  # md5 处理过了
                return False

        def save_md5_hex(md5_for_check: str):
            with open(get_abs_path(chroma_conf["md5_hex_store"]), "a", encoding = "utf-8") as f:
                f.write(md5_for_check + "\n")

        def get_file_documents(read_path: str):
            if read_path.endswith("txt"):
                return txt_loader(read_path)

            if read_path.endswith("pdf"):
                return pdf_loader(read_path)

            return []

        allowed_file_path = listdir_with_allowed_type(
            get_abs_path(chroma_conf["data_path"]),
            tuple(chroma_conf["allow_knowledge_file_type"]),
        )

        for path in allowed_file_path:
            # 获取文件的md5
            md5_hex = get_file_md5_hex(path)

            # MD5 计算失败时返回 None，写进清单会污染后续判断，直接跳过该文件
            if not md5_hex:
                logger.error(f"[加载知识库]{path}计算MD5失败，跳过该文件")
                continue

            if check_md5_hex(md5_hex):
                logger.info(f"[加载知识库]{path}已经存在知识库内，跳过")
                continue

            try:
                documents: list[Document] = get_file_documents(path)
                if not documents:
                    logger.warning(f"[加载知识库]{path}内没有有效文本，跳过")
                    continue
                split_document = self.spliter.split_documents(documents)

                if not split_document:
                    logger.warning(f"[加载知识库]{path}分片后没有有效文本内容，跳过")
                    continue

                # 将内容存入向量库
                self.vector_store.add_documents(split_document)

                # 记录这个已经处理过的文件的md5，避免下次重复加载
                save_md5_hex(md5_hex)

                logger.info(f"[加载知识库]{path}内容加载成功")
            except Exception as e:
                # exc_info为 True 会记录详细的报错堆栈
                logger.error(f"[加载知识库]{path}加载失败: {str(e)}", exc_info = True)


# 测试
if __name__ == '__main__':
    vs = VectorStoreService()

    vs.load_document()

    retriever = vs.get_retriever()

    res = retriever.invoke("迷路")
    for r in res:
        print(r.page_content)
        print("*" * 20)