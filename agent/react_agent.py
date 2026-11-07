from langchain.agents import create_agent
from langchain_core.messages import AIMessage
from model.factory import chat_model
from utils.prompt_loader import load_system_prompts
from agent.tools.agent_tools import rag_summarize, get_weather, get_user_id, get_user_location, get_current_month, fetch_external_data, fill_context_for_report
from agent.tools.middleware import monitor_tool, log_before_model, report_prompt_switch

class ReactAgent:
    # 传给模型的历史消息条数上限，避免多轮对话无限增长撑爆 1.5B 模型的上下文
    MAX_HISTORY_MESSAGES = 20

    def __init__(self):
        self.agent = create_agent(
            model = chat_model,
            system_prompt = load_system_prompts(),
            tools = [rag_summarize, get_weather, get_user_id, get_user_location, get_current_month, fetch_external_data, fill_context_for_report],
            middleware = [monitor_tool, log_before_model, report_prompt_switch],
        )

    def execute_stream(self, query: str, history: list | None = None):
        """执行一轮对话，以流式方式返回模型输出。

        Args:
            query: 本轮用户输入。
            history: 历史对话列表，元素为 ``{"role": "user"|"assistant", "content": str}``；
                只取最近 ``MAX_HISTORY_MESSAGES`` 条。为 None 时退化为单轮问答。

        Yields:
            模型的最终回答文本；工具调用过程与工具返回的内容不会输出。
        """
        # 截断历史，避免长对话把上下文撑爆
        messages = list(history or [])[-self.MAX_HISTORY_MESSAGES:]
        messages.append({"role": "user", "content": query})

        input_dict = {
            "messages": messages
        }

        # 第三个参数context就是上下文runtime中的信息，就是做提示词切换的标记
        for chunk in self.agent.stream(input_dict, stream_mode = "values", context = {"report": False}):
            latest_message = chunk["messages"][-1]

            # stream_mode="values" 在每个节点结束后都会推一次全量状态，最后一条可能是
            # 用户输入回显、带 tool_calls 的中间消息或 ToolMessage，这些都不属于回答
            if not isinstance(latest_message, AIMessage) or latest_message.tool_calls:
                continue

            content = latest_message.content
            if isinstance(content, str) and content.strip():
                yield content.strip()

# 测试
if __name__ == '__main__':
    agent = ReactAgent()

    for chunk in agent.execute_stream("扫地机器人在我所在地区的气温下如何保养？"):
        print(chunk, end = "", flush = True)