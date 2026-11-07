import streamlit as st
from agent.react_agent import ReactAgent
import time

# 标题
st.title("智扫通机器人智能客服")
st.divider()

if "agent" not in st.session_state:
    st.session_state["agent"] = ReactAgent()

if "message" not in st.session_state:
    st.session_state["message"] = []

for message in st.session_state["message"]:
    st.chat_message(message["role"]).write(message["content"])

# 用户输入提示词
prompt = st.chat_input()

if prompt:
    st.chat_message("user").write(prompt)

    # 先取历史（不含本轮输入），再把本轮输入写入会话记录，供后续轮次使用
    history = [
        {"role": message["role"], "content": message["content"]}
        for message in st.session_state["message"]
    ]
    st.session_state["message"].append({"role": "user", "content": prompt})

    response_messages = []
    with st.spinner("智能客服思考中..."):
        res_stream = st.session_state["agent"].execute_stream(prompt, history)

        def capture(generator, cache_list):

            for chunk in generator:
                cache_list.append(chunk)

                for char in chunk:
                    time.sleep(0.005)
                    yield char

        st.chat_message("assistant").write_stream(capture(res_stream, response_messages))

        # 流式没有任何产出时（模型报错 / 服务中断），不能直接取 [-1]
        answer = response_messages[-1] if response_messages else "抱歉，这次没有生成有效回答，请重试。"
        st.session_state["message"].append({"role": "assistant", "content": answer})
        st.rerun()