from langchain.agents.middleware import wrap_tool_call, before_model
from langchain.tools.tool_node import ToolCallRequest
from typing import Callable
from langgraph.types import Command
from utils.logger_handler import logger
from langgraph.runtime import Runtime
from langchain.agents import AgentState
from utils.prompt_loader import load_report_prompts, load_system_prompts
from langchain_core.messages import ToolMessage
from langchain.agents.middleware import dynamic_prompt, ModelRequest


@wrap_tool_call
def monitor_tool(request: ToolCallRequest, handler: Callable[[ToolCallRequest], ToolMessage | Command]) -> ToolMessage | Command:
    """工具执行的监控"""
    logger.info(f"[tool monitor]执行工具: {request.tool_call['name']}")
    logger.info(f"[tool monitor]传入参数: {request.tool_call['args']}")

    try:
        result =  handler(request)
        logger.info(f"[tool monitor]工具{request.tool_call['name']}调用成功")

        if request.tool_call['name'] == "fill_context_for_report":
            request.runtime.context["report"] = True
            logger.info("[tool monitor]已切换到报告生成场景，后续模型调用使用 report_prompt")

        return result
    except Exception as e:
        logger.error(f"工具{request.tool_call['name']}调用失败，原因：{str(e)}")
        raise e

@before_model
def log_before_model(
        state: AgentState,   # 整个Agent智能体中的状态记录
        runtime: Runtime,   # 记录整个执行过程中的上下文信息
):
    """在模型执行前监控"""
    logger.info(f"[log_before_model]即将调用模型，带有{len(state['messages'])}条消息")
    logger.debug(f"[log_before_model]{type(state['messages'][-1]).__name__} | {state['messages'][-1].content.strip()}")

    return None

@dynamic_prompt   # 每一次在生成提示词之前调用此函数
def report_prompt_switch(request: ModelRequest):
    is_report = request.runtime.context.get("report", False)
    if is_report:  # 是报告生成场景
        return load_report_prompts()
    return load_system_prompts()