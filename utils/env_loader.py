"""
.env 文件加载工具。

API Key 等敏感配置放在工程根目录的 .env 中，不进入版本库。
这里用最小实现读取 KEY=VALUE 行，避免为了一个文件额外引入依赖。
"""
import os
from utils.path_tool import get_abs_path


def load_env_file(relative_path: str = ".env") -> None:
    """把 .env 文件中的键值对写入进程环境变量。

    只在目标键尚未存在于环境变量中时写入，因此系统环境变量优先级更高。
    文件不存在时静默返回；空行、注释、没有等号的行会被跳过，支持
    ``export KEY=VALUE`` 写法和值两端的引号。

    Args:
        relative_path: .env 文件相对工程根的路径，默认为工程根的 .env。
    """
    env_path = get_abs_path(relative_path)
    if not os.path.exists(env_path):
        return

    with open(env_path, "r", encoding = "utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            if line.startswith("export "):
                line = line[len("export "):]

            key, sep, value = line.partition("=")
            if not sep:
                continue

            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key:
                os.environ.setdefault(key, value)


if __name__ == '__main__':
    load_env_file()
    print("DEEPSEEK_API_KEY 是否已设置:", bool(os.getenv("DEEPSEEK_API_KEY")))
