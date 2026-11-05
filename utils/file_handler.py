import os
from logger_handler import logger
import hashlib
from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader, TextLoader

def get_file_md5_hex(filepath: str):
    """获取文件的md5的十六进制字符串"""

    # 判断路径是否存在
    if not os.path.exists(filepath):
        logger.error(f"[md5计算]文件{filepath}不存在")
        return

    # 判断是否是普通文件
    if not os.path.isfile(filepath):
        logger.error(f"[md5计算]文件{filepath}不是文件")
        return

    # 创建md5对象
    md5_obj = hashlib.md5()

    chunk_size = 4096  # 4kb分片，避免文件过大爆内存
    try:
        with open(filepath, "rb") as f:   # 必须二进制读取（MD5是对字节序列做运算，必须保证读到的是原始字节）
            while chunk := f.read(chunk_size):
                md5_obj.update(chunk)
            """
            chunk = f.read(chunk_size)
            while chunk:
                md5_obj.update(chunk)
                chunk = f.read(chunk_size)
            """
            md5_hex = md5_obj.hexdigest()
            return md5_hex
    except Exception as e:
        logger.error(f"计算文件{filepath}md5失败，{str(e)}")
        return None


def listdir_with_allowed_type(path: str, allowed_types: tuple[str]):
    """返回文件夹内的文件列表（允许的文件后缀）"""
    files = []

    if not os.path.isdir(path):
        logger.error(f"[listdir_with_allowed_type]{path}不是文件夹")
        return ()

    for name in os.listdir(path):
        full = os.path.join(path, name)
        if os.path.isfile(full) and name.lower().endswith(allowed_types):
            files.append(full)

    return tuple(files)

def pdf_loader(filepath: str, passwd: str | None = None) -> list[Document]:
    """
    加载 PDF 文件，转换为 LangChain 的 Document 列表

    Args:
        filepath: PDF文件的完整路径
        passwd: 加密 PDF 的打开密码；无密码时为None

    Returns:
        list[Document]：每个元素对应 PDF 的一页文本。
    """
    return PyPDFLoader(filepath, passwd).load()


def txt_loader(filepath: str, encoding: str = "utf-8") -> list[Document]:
    """
    加载纯文本文件，转换为 LangChain 的 Document 列表。

    Args：
        filepath: TXT 文件的完整路径。
        encoding: 文件编码，默认 "utf-8"；若文件是 GBK 等需显式指定，
                  否则可能出现 UnicodeDecodeError 或乱码。

    Returns：
        list[Document]：长度为 1 的列表（整个文件一个 Document）。
    """
    return TextLoader(filepath, encoding = encoding).load()