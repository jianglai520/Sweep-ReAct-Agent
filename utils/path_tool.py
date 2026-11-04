"""
为整个工程提供统一的绝对路径
"""
import os

def get_project_root() -> str:
    """
    获取工程所在的根目录（从当前文件向上查找 .git 锚点，与深度无关。）

    依赖调用文件位于工程内一层子目录中，例如 src/ 或 utils/ 下。
    若 __file__ 不可用（如交互式/打包环境）会抛出 RuntimeError。

    Returns:
        字符串根目录

    Raises:
        RuntimeError: 当无法确定当前文件路径时
    """
    file = globals().get("__file__")
    if file is None:
        raise RuntimeError("__file__不可用，无法定位工程根目录")

    # __file__可能是相对路径，先转绝对路径并规范化
    current_dir = os.path.dirname(os.path.abspath(__file__))

    path = current_dir
    while True:
        if os.path.exists(os.path.join(path, ".git")):
            return path

        parent = os.path.dirname(path)
        if parent  == path:
            raise RuntimeError(f"未在{current_dir}的上级找到 .git目录")
        path = parent


def get_abs_path(relative_path: str) -> str:
    """
    传入相对路径，返回绝对路径

    Args:
        relative_path: 相对路径

    Returns:
        绝对路径
    """
    project_root = get_project_root()
    return os.path.join(project_root, relative_path)

# 测试
if __name__ == '__main__':
    print(get_abs_path("utils/path_tool.py"))