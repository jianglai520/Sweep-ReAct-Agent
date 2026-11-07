# Sweep-ReAct-Agent

**基于 LangChain 1.x ReAct 循环、Chroma RAG 与 Streamlit 的扫地机器人领域智能客服 Agent。**

[English](README.md) | 简体中文

![Python](https://img.shields.io/badge/Python-3.14-3776AB?logo=python&logoColor=white)
![LangChain](https://img.shields.io/badge/LangChain-1.x-1C3C3C)
![Streamlit](https://img.shields.io/badge/Streamlit-1.67-FF4B4B?logo=streamlit&logoColor=white)
![Chroma](https://img.shields.io/badge/Vector%20Store-Chroma-FF6B6B)
![LLM](https://img.shields.io/badge/Chat%20Model-DeepSeek%20API-4D6BFE)

---

## 项目简介

Sweep-ReAct-Agent（界面名称：智扫通）面向扫地机器人 / 扫拖一体机器人的售前咨询、日常使用、维护保养与故障排查问答。

它不是一条固定的提示词链，而是一个 **ReAct 循环**：由模型在运行时自行决定调用哪些工具、按什么顺序、调用几次。工具覆盖领域知识检索、天气与位置查询、用户身份和用量记录查询。当用户要求生成个人使用报告时，Agent 会走一条固定的工具调用序列，并在运行时把系统提示词切换为报告写手人设。

聊天补全调用 **DeepSeek 官方 API**（OpenAI 兼容协议）；嵌入模型在 **本机 Ollama** 上运行，向量索引存放在本地 Chroma 库中。

> 这是一个学习 / 演示型项目，不是生产系统。天气、用户 ID、当前月份与使用记录均为模拟数据，没有鉴权，也没有自动化测试。

## 功能特性

- **ReAct 工具调用** —— 调用哪些工具、调用几次，由模型在运行时决定，而非写死在代码里。
- **本地 RAG** —— 6 个知识文件（PDF + TXT）经切分、向量化后存入 Chroma，回答基于检索到的原文片段。
- **报告生成** —— 专用流程（`get_user_id → get_current_month → fill_context_for_report → fetch_external_data`），配合运行时的系统提示词切换。
- **工具调用可观测** —— 中间件记录每次工具调用的名称、参数、结果，以及每次模型调用的消息数量。
- **多轮对话** —— 最近若干轮对话会回传给模型（上限 20 条消息）。
- **配置驱动** —— 模型名、接口地址、切分参数、路径与提示词全部放在 YAML / 提示词文件中。
- **聊天模型可切换** —— 默认 DeepSeek API，可回退到本机 Ollama。

## 架构

```text
Streamlit 界面（app.py）
  └─ ReactAgent.execute_stream(query, history)
       └─ LangChain create_agent
            ├─ middleware
            │    ├─ monitor_tool              记录工具调用；遇到
            │    │                            fill_context_for_report 时打开报告上下文标记
            │    ├─ log_before_model          记录每次模型调用
            │    └─ report_prompt_switch      选择主提示词 / 报告提示词
            └─ 工具（7 个）
                 ├─ rag_summarize(query)               -> 本地 Chroma 检索 + 模型总结
                 ├─ get_weather(city)                  -> 模拟数据
                 ├─ get_user_location()                -> 模拟数据
                 ├─ get_user_id()                      -> 模拟数据
                 ├─ get_current_month()                -> 模拟数据
                 ├─ fetch_external_data(user_id, month) -> 读取 records.csv 缓存
                 └─ fill_context_for_report()          -> 仅触发上下文标记
```

**聊天模型：** DeepSeek 官方 API `deepseek-flash`（OpenAI 兼容接口）
**嵌入模型：** 本机 Ollama `qwen3-embedding:0.6b`（1024 维）

### RAG 链路

```text
data/*.pdf|*.txt
  -> PyPDFLoader / TextLoader
  -> RecursiveCharacterTextSplitter(chunk_size=200, chunk_overlap=20)
  -> OllamaEmbeddings(qwen3-embedding:0.6b)
  -> Chroma(collection="agent", persist_directory=<工程根>/chroma_db)
  -> as_retriever(k=3)
  -> PromptTemplate | chat_model | StrOutputParser
```

知识文件采用增量入库：文件 MD5 记录在 `md5.txt` 中；当检测到"向量库为空但清单已有记录"时，加载器会判定清单失效并自动清空重建。

## 技术栈

| 层次 | 选型 |
| --- | --- |
| 语言 | Python 3.14 |
| Agent 框架 | LangChain 1.x（`create_agent`、`AgentState`、middleware：`wrap_tool_call` / `before_model` / `dynamic_prompt`） |
| 运行时上下文 | LangGraph（`Runtime`、`Command`） |
| 聊天模型 | DeepSeek API `deepseek-flash`（OpenAI 兼容协议） |
| 嵌入模型 | 本机 Ollama `qwen3-embedding:0.6b` |
| 向量库 | Chroma（`langchain-chroma`） |
| 文档加载 | `PyPDFLoader` / `TextLoader`、`RecursiveCharacterTextSplitter` |
| Web 界面 | Streamlit |
| 配置 | YAML + 纯文本提示词文件 |

## 快速开始

### 环境要求

- Python **3.14**
- 本机运行中的 [Ollama](https://ollama.com)（仅用于嵌入）
- 一个 **DeepSeek API Key**

### 1. 安装依赖

```bash
git clone <repo-url>
cd Sweep_ReAct_Agent

python -m venv .venv

# Windows（PowerShell）
.\.venv\Scripts\Activate.ps1
# macOS / Linux
source .venv/bin/activate

python -m pip install -r requirements.txt
```

> PowerShell 若提示禁止运行脚本，执行一次
> `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`。
> 也可以完全不激活，直接用 `.\.venv\Scripts\python.exe -m ...` 执行命令。

### 2. 配置 API Key

```bash
cp .env.example .env
# 然后编辑 .env
DEEPSEEK_API_KEY=你的密钥
```

`.env` 已被 git 忽略。密钥在导入配置时从环境变量读取，不会写入代码或配置文件。

### 3. 准备嵌入模型

```bash
ollama serve
ollama pull qwen3-embedding:0.6b
```

本地只需要嵌入模型，聊天补全走 API。

### 4. 构建知识库

```bash
python -m rag.vector_store
```

该命令读取 `data/` 下的文档、切分并向量化，写入工程根的 `chroma_db/`，同时把文件 MD5 记录到 `md5.txt`，最后跑一次示例检索。

### 5. 启动应用

```bash
python -m streamlit run app.py
```

打开 <http://localhost:8501>。

可以试这几句：

- `滤网多久需要更换一次？` —— 触发 `rag_summarize`
- `深圳现在天气怎么样？` —— 触发 `get_user_location` + `get_weather`
- `生成我的使用报告` —— 走报告流程并切换系统提示词

## 配置说明

| 文件 | 内容 |
| --- | --- |
| `config/rag.yaml` | 聊天模型提供方（`api` / `ollama`）、模型名、接口地址、密钥环境变量名、嵌入模型名 |
| `config/chroma.yaml` | 集合名、持久化目录、Top-K、数据目录、MD5 清单、切分长度与重叠、分隔符 |
| `config/prompts.yaml` | 三个提示词文件的路径 |
| `config/agent.yaml` | 模拟使用记录 CSV 的路径 |

如需回退到本地聊天模型：

```yaml
chat_model_provider: ollama
chat_model_name: <一个真正支持工具调用的 Ollama 模型>
```

注意：项目里原先使用的本地 `deepseek-r1:1.5b` 实测**不产出 `tool_calls`**，ReAct 循环不会触发。

## 工具列表

| 工具 | 入参 | 作用 |
| --- | --- | --- |
| `rag_summarize` | `query` | 从向量库检索并总结回答 |
| `get_weather` | `city` | 模拟的指定城市天气 |
| `get_user_location` | — | 模拟的用户所在城市 |
| `get_user_id` | — | 模拟用户 ID（`1001`–`1010`） |
| `get_current_month` | — | 模拟月份（`2025-01`–`2025-12`） |
| `fetch_external_data` | `user_id`、`month` | 从 `data/external/records.csv` 读取使用记录 |
| `fill_context_for_report` | — | 打开运行时上下文标记，触发报告提示词切换 |

## 项目结构

```text
.
├── app.py                  # Streamlit 入口
├── requirements.txt        # 锁定的直接依赖
├── .env.example            # API Key 模板
├── config/                 # rag / chroma / prompts / agent 四份 YAML
├── prompts/                # 主提示词、RAG 总结提示词、报告提示词
├── agent/
│   ├── react_agent.py      # Agent 组装与流式接口
│   └── tools/
│       ├── agent_tools.py  # 7 个工具与模拟数据
│       └── middleware.py   # 工具监控、模型日志、提示词切换
├── model/
│   └── factory.py          # 聊天模型工厂（API / Ollama）+ 嵌入模型
├── rag/
│   ├── vector_store.py     # 文档入库与检索器
│   └── rag_service.py      # 检索 + 提示词 + 模型的一体化总结链
├── utils/                  # 配置、路径、提示词、文件、日志、.env 读取
├── data/                   # 知识源与模拟使用记录
├── chroma_db/              # Chroma 持久化目录（不提交）
└── logs/                   # 按天生成的日志文件
```

## 冒烟测试

每个模块底部都有 `__main__` 代码块，在工程根用 `-m` 运行：

```bash
python -m model.factory             # 聊天模型 + 嵌入模型连通性
python -m rag.vector_store          # 增量入库 + 检索示例
python -m rag.rag_service           # RAG 总结示例
python -m agent.tools.agent_tools   # 外部使用记录读取
python -m agent.react_agent         # 端到端 Agent 调用
```

RAG 与 Agent 的测试需要可用的 API Key；入库测试需要 Ollama。

## 已知限制

- **数据均为模拟** —— 天气、位置、用户 ID、月份、使用记录都是假数据。
- **无鉴权** —— 不要把 Streamlit 端口直接暴露到公网。
- **无自动化测试** —— 验证依赖上述 `__main__` 冒烟脚本。
- **检索为纯 Top-K** —— 没有 MMR 或相似度阈值过滤。
- **`md5.txt` 与 `chroma_db/` 必须配套** —— 换机器时只拷其中一个，会导致重复入库或漏入库。
- **调试输出** —— RAG 链会把渲染后的完整提示词打印到标准输出。
- **无 LICENSE 文件** —— 仓库仅用于学习与演示。

---

[English README](README.md)
