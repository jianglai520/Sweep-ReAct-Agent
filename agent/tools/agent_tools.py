"""Agent 可调用的工具集合。

本模块集中定义 ReAct Agent 可调用的 LangChain 工具，包括向量检索、
天气/用户信息模拟、外部使用记录读取等。所有对外暴露的工具均通过
``@tool`` 装饰器注册；内部辅助函数不加装饰器，供工具内部调用。
"""
import csv
import json
import os.path
import random
from langchain_core.tools import tool
from rag.rag_service import RagSummarizeService
from utils.config_handler import agent_conf
from utils.logger_handler import logger
from utils.path_tool import get_abs_path

rag = RagSummarizeService()

# 模拟的用户 ID 列表，供 get_user_id 随机返回。
user_ids = ["1001", "1002", "1003", "1004", "1005",
            "1006", "1007", "1008", "1009", "1010"]

# 模拟的可用月份列表（2025 年全年），供 get_current_month 随机返回。
month_arr = [f"2025-{m:02d}" for m in range(1, 13)]

# 外部使用记录缓存，结构见 generate_external_data 的 docstring。
external_data: dict = {}


@tool(description="从向量存储中检索参考资料")
def rag_summarize(query: str) -> str:
    """从向量存储中检索与查询相关的参考资料。

    Args:
        query: 用户的查询语句。

    Returns:
        检索并汇总后的参考资料文本。
    """
    return rag.rag_summarize(query)


@tool(description="获取指定城市的天气，以消息字符串的形式返回")
def get_weather(city: str) -> str:
    """获取指定城市的天气信息（模拟数据）。

    Args:
        city: 城市名称，例如 ``"深圳"``。

    Returns:
        描述该城市天气的字符串，包含天气、气温、湿度与降雨概率。
    """
    return (
        f"{city}的天气为晴天，气温20摄氏度，空气湿度50%，"
        f"最近6小时降雨概率极低"
    )


@tool(description="获取用户所在城市的名称，以纯字符串形式返回")
def get_user_location() -> str:
    """获取用户所在的城市名称（模拟数据）。

    Returns:
        随机返回一个城市名称，如 ``"深圳"``、``"上海"``、``"杭州"``。
    """
    return random.choice(["深圳", "上海", "杭州"])


@tool(description="获取用户的ID，以纯字符串的形式返回")
def get_user_id() -> str:
    """获取当前用户的 ID（模拟数据）。

    Returns:
        从 ``user_ids`` 中随机选取的一个用户 ID 字符串。
    """
    return random.choice(user_ids)


@tool(description="获取当前月份，以纯字符串的形式返回")
def get_current_month() -> str:
    """获取当前月份（模拟数据）。

    从 2025 年全年（``2025-01`` ~ ``2025-12``）中随机返回一个月。

    Returns:
        月份字符串，格式为 ``YYYY-MM``，取值范围为
        ``"2025-01"`` 到 ``"2025-12"``。
    """
    return random.choice(month_arr)


def _normalize_field(text: str) -> str:
    """还原 CSV 字段中被字面量转义的换行。

    ``records.csv`` 的多行字段是以 ``\\n`` 两个字符存储的，csv 模块不会做转义，
    原样输出会让报告里出现一串 ``\\n`` 而不是换行。

    Args:
        text: CSV 单元格原始内容。

    Returns:
        换行已还原为真正换行符的文本。
    """
    return text.replace("\\n", "\n")


def generate_external_data() -> None:
    """从 CSV 文件加载外部使用记录到全局缓存 ``external_data``。

    仅在缓存为空时执行加载，加载后的数据结构如下::

        {
            "<user_id>": {
                "<YYYY-MM>": {
                    "特征": str,
                    "效率": str,
                    "耗材": str,
                    "对比": str,
                },
                ...
            },
            ...
        }

    文件路径由 agent_conf["external_data_path"]提供，并通过
    get_abs_path 转为绝对路径。CSV 第一行视为表头，其余每行
    按列顺序解析为 user_id, 特征, 效率, 耗材, 对比, time。

    Raises:
        FileNotFoundError: 当配置的外部数据文件不存在时抛出。
    """
    global external_data

    if external_data:
        return

    external_data_path = get_abs_path(agent_conf["external_data_path"])
    if not os.path.exists(external_data_path):
        raise FileNotFoundError(f"外部数据文件{external_data_path}不存在")

    # utf-8-sig 兼容 Excel 导出的带 BOM 的 UTF-8 文件。
    with open(external_data_path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        next(reader, None)  # 跳过表头

        for arr in reader:
            if len(arr) < 6:
                logger.warning(f"[generate_external_data]列数不足，跳过该行：{arr}")
                continue

            uid = arr[0].strip()
            feature = _normalize_field(arr[1].strip())
            efficiency = _normalize_field(arr[2].strip())
            consumables = _normalize_field(arr[3].strip())
            comparison = _normalize_field(arr[4].strip())
            time = arr[5].strip()

            external_data.setdefault(uid, {})[time] = {
                "特征": feature,
                "效率": efficiency,
                "耗材": consumables,
                "对比": comparison,
            }


@tool(description="从外部系统中获取用户的使用记录，以纯字符串的形式返回，如果未检索到返回空字符串")
def fetch_external_data(user_id: str, month: str) -> str:
    """获取指定用户在指定月份的外部使用记录。

    数据来源为 ``generate_external_data`` 加载的缓存。

    Args:
        user_id: 用户 ID，例如 ``"1001"``。
        month: 月份字符串，格式为 ``YYYY-MM``，例如 ``"2025-01"``。

    Returns:
        若命中记录，返回该记录序列化后的 JSON 字符串；
        若未命中，记录一条 warning 日志并返回空字符串。
    """
    generate_external_data()

    try:
        record = external_data[user_id][month]
    except KeyError:
        logger.warning(
            f"[fetch_external_data]未能检索到用户：{user_id}在{month}的使用记录数据"
        )
        return ""

    return json.dumps(record, ensure_ascii=False)

@tool(description = "无入参，无返回值，调用后触发中间件自动为报告生成的场景动态注入上下文信息，为后续提示词切换提供上下文信息")
def fill_context_for_report():
    return "fill_context_for_report已调用"


# 测试
if __name__ == '__main__':
    print(fetch_external_data.invoke({"user_id": "1001", "month": "2025-01"}))