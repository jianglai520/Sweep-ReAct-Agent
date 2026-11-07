# AGENTS.md

本文件面向第一次接触本仓库的 AI 编码代理，说明项目目标、目录结构、运行方式、开发约定和已知陷阱。项目内的注释、文档、提示词、日志与提交说明均为中文，新增内容请保持中文。

## 项目概览

**Sweep-ReAct-Agent**（界面名称为“智扫通机器人智能客服”）是一个领域问答 Agent，应用、嵌入模型与向量库都在本机运行，聊天模型走 DeepSeek 官方 API：

- 面向扫地机器人 / 扫拖一体机器人的售前、使用、保养、故障排查问答；
- 使用 LangChain 的 `create_agent` 构建 ReAct 循环，由模型自主决定调用哪些工具、调用几次；
- 通过 Chroma 向量库做 RAG 检索，回答专业知识问题；
- 通过 CSV 模拟“用户使用记录”，支持生成个人使用报告（报告场景会动态切换系统提示词）；
- 使用 Streamlit 提供聊天界面；聊天模型走 DeepSeek 官方 API（`deepseek-flash`，OpenAI 兼容协议），嵌入模型走本机 Ollama（`qwen3-embedding:0.6b`）。

这是一个学习 / 演示型项目，不是生产系统：天气、用户 ID、当前月份、外部使用记录都是模拟数据，没有鉴权、没有自动化测试、没有部署配置。

## 技术栈

| 类别 | 使用方式 |
| --- | --- |
| 语言 / 运行时 | Python 3.14（`.venv/pyvenv.cfg` 记录为 3.14.3；PyCharm 解释器名称为 `Python 3.14 (.virtualenvs)`） |
| Agent 框架 | LangChain 1.x 的 `langchain.agents.create_agent`、`AgentState`、`langchain.agents.middleware`（`wrap_tool_call` / `before_model` / `dynamic_prompt` / `ModelRequest`） |
| 运行时上下文 | LangGraph 的 `Runtime`、`Command`、`langchain.tools.tool_node.ToolCallRequest` |
| 模型 | 聊天模型走 DeepSeek 官方 API（`deepseek-flash`，OpenAI 兼容协议）；嵌入模型走本机 Ollama `qwen3-embedding:0.6b`；两者都在 `config/rag.yaml` 配置 |
| 向量库 | Chroma（`langchain_chroma.Chroma`），集合名 `agent` |
| 文档加载 / 切分 | `langchain_community` 的 `PyPDFLoader` / `TextLoader`，`langchain_text_splitters.RecursiveCharacterTextSplitter` |
| Web UI | Streamlit（`app.py`） |
| 配置 / 提示词 | `PyYAML` 读取 `config/*.yaml`，提示词放在 `prompts/*.txt` |
| 依赖管理 | `requirements.txt` 已锁定 11 个直接依赖的精确版本（含 `langchain-openai`）；没有 `pyproject.toml`、`uv.lock`、`Pipfile` 或打包配置 |

代码直接 import 的第三方包：`streamlit`、`langchain`、`langgraph`、`langchain-core`、`langchain-ollama`、`langchain-openai`（API 模式延迟导入）、`langchain-chroma`、`langchain-community`、`langchain-text-splitters`、`pyyaml`；`PyPDFLoader` 还需要 `pypdf`。读取 `.env` 用 `utils/env_loader.py` 的极简实现，不依赖 `python-dotenv`。如果安装的是 LangChain 0.x，`langchain.agents.create_agent` 和 middleware 相关模块不存在，项目无法启动。

## 目录结构

```text
.
├── app.py                       # 唯一可运行入口：Streamlit 聊天界面
├── main.py                      # PyCharm 自动生成的示例脚本，未使用
├── README.md                    # 英文版项目说明（默认）
├── README.zh-CN.md              # 中文版项目说明
├── md5.txt                      # 已入库知识文件的 MD5 清单（当前未被 git 跟踪）
├── .env                         # 本地密钥配置（DEEPSEEK_API_KEY 等），已被 .gitignore 忽略
├── .env.example                 # 密钥模板（只有占位符），可复制为 .env
├── .gitignore                   # 忽略 .env（密钥文件禁止提交）
├── config/                      # 全部运行期配置
│   ├── agent.yaml               # external_data_path
│   ├── chroma.yaml              # 向量库、切分、知识库路径参数
│   ├── prompts.yaml             # 三个提示词文件路径
│   └── rag.yaml                 # 聊天模型提供方 / 模型名 / base_url / API Key 环境变量、嵌入模型名
├── prompts/
│   ├── main_prompt.txt          # 默认系统提示词（普通问答）
│   ├── rag_summarize_prompt.txt # RAG 总结提示词（{input} / {context}）
│   └── report_prompt.txt        # 报告生成场景的系统提示词
├── agent/
│   ├── react_agent.py           # ReactAgent：组装模型、工具、中间件并提供流式接口
│   └── tools/
│       ├── agent_tools.py       # 所有 @tool 工具与模拟数据
│       └── middleware.py        # 工具监控、模型调用日志、提示词动态切换
├── model/
│   └── factory.py               # 模型工厂 + 模块级 chat_model / embed_model
├── rag/
│   ├── vector_store.py          # 知识文件入库与 Retriever
│   └── rag_service.py           # 检索 + 提示词 + 模型的一体化总结链
├── utils/
│   ├── path_tool.py             # 工程根目录 / 绝对路径
│   ├── config_handler.py        # 加载 YAML，导出模块级配置单例（导入时先加载 .env）
│   ├── env_loader.py            # 极简 .env 读取，不依赖 python-dotenv
│   ├── prompt_loader.py         # 按配置读取三个提示词文件
│   ├── file_handler.py          # MD5、文件枚举、PDF/TXT 加载
│   └── logger_handler.py        # 统一 logger
├── data/                        # RAG 知识源（会被入库）
│   ├── 扫地机器人100问.pdf
│   ├── 扫地机器人100问2.txt
│   ├── 扫拖一体机器人100问.txt
│   ├── 故障排除.txt
│   ├── 维护保养.txt
│   ├── 选购指南.txt
│   └── external/records.csv     # 模拟用户使用记录（120 条 = 10 用户 × 12 个月）
├── docs/knowledge/              # 学习笔记（如“常见数据格式对比”），不参与 RAG
├── logs/                        # 运行日志，按天一个文件
└── chroma_db/                   # Chroma 向量库（全项目唯一一份，326 条向量，未跟踪）
```

注意：

- 各包目录（`agent/`、`agent/tools/`、`rag/`、`utils/`、`model/`）都**没有 `__init__.py`**，依靠命名空间包工作；代码使用从工程根出发的绝对导入（`from utils.xxx import ...`）。
- 全项目只有工程根一份 `chroma_db/`：`config/chroma.yaml` 的 `persist_directory` 在 `rag/vector_store.py` 中已经过 `get_abs_path()` 解析，实际路径与启动目录无关。

## 运行时架构

### 请求链路

```text
Streamlit app.py
  └─ 从 session_state 取 ReactAgent（每个浏览器会话一个）
       └─ ReactAgent.execute_stream(query)
            └─ LangChain create_agent（chat_model：由 ChatModelFactory 产出）
                 ├─ middleware
                 │    ├─ log_before_model：记录“即将调用模型”和消息数量
                 │    ├─ monitor_tool：记录工具名/参数/结果；当工具名为
                 │    │   fill_context_for_report 时把 runtime.context["report"] 置为 True
                 │    └─ report_prompt_switch：每次生成提示词前根据 report 标记
                 │        选择 prompts/main_prompt.txt 或 prompts/report_prompt.txt
                 └─ tools
                      ├─ rag_summarize(query)        -> RagSummarizeService
                      ├─ get_weather(city)           -> 固定晴天文案（模拟）
                      ├─ get_user_location()         -> 随机城市（模拟）
                      ├─ get_user_id()               -> 随机 1001~1010（模拟）
                      ├─ get_current_month()         -> 随机 2025-01~2025-12（模拟）
                      ├─ fetch_external_data(uid, month) -> 读取 records.csv 缓存
                      └─ fill_context_for_report()   -> 仅触发上下文标记
```

- `agent/react_agent.py` 以 `stream_mode="values"` 调用 `agent.stream(...)`；该模式在每个节点结束后都推一次全量状态，因此代码只输出「`AIMessage` 且不带 `tool_calls`」的最后一条消息，用户输入回显、中间工具调用与 `ToolMessage` 都会被过滤掉。`context={"report": False}` 是提示词切换的初始标记。
- 聊天模型由 `model/factory.py` 的 `ChatModelFactory` 按 `config/rag.yaml` 的 `chat_model_provider` 产出：`api`（默认）延迟导入 `langchain_openai.ChatOpenAI`，用 `deepseek-flash` 走 OpenAI 兼容协议；`ollama` 走 `langchain_ollama.ChatOllama`。API Key 从环境变量 `DEEPSEEK_API_KEY` 读取，缺失时构造模型即抛 `RuntimeError`。
- `app.py` 会先把已有会话记录组装成 `history` 传给 `execute_stream(prompt, history)`，因此支持多轮对话；`ReactAgent.MAX_HISTORY_MESSAGES`（默认 20 条）用于截断历史，避免长对话撑爆模型上下文。
- `app.py` 的 `capture()` 按字符 `yield char`（每个字符 `sleep 0.005`）制造打字机效果；流式无产出时用兜底文案写入会话，不会因空列表取 `[-1]` 报错。

### RAG 链路

```text
data/*.pdf|*.txt
  -> PyPDFLoader / TextLoader
  -> RecursiveCharacterTextSplitter(chunk_size=200, chunk_overlap=20)
  -> OllamaEmbeddings(qwen3-embedding:0.6b)
  -> Chroma(collection_name="agent", persist_directory=<工程根>/chroma_db)
  -> as_retriever(k=3)
  -> PromptTemplate(rag_summarize_prompt.txt) | print_prompt | chat_model（ChatModelFactory 产出）| StrOutputParser
```

- `rag/vector_store.py` 的 `load_document()` 负责“读取 → 分片 → 向量化 → 入库”，带 MD5 增量去重、清单自愈和单文件容错；**应用启动时不会自动调用它**，需要手动执行。
- `rag/rag_service.py` 的 `RagSummarizeService` 在导入时构建 Chroma、Retriever 和 LCEL 链，链路里的 `chat_model` 与 `create_agent` 用的是同一个模型实例，因此 RAG 总结也走 DeepSeek API；只有嵌入环节用本机 Ollama。`agent/tools/agent_tools.py:17` 在模块导入时就实例化了它。
- `print_prompt` 会把完整提示词打印到标准输出（调试残留），运行时会出现在控制台/终端里。
- 检索结果是纯相似度 Top-K（k=3），没有 MMR 或分数阈值过滤。

## 配置与路径约定

所有 YAML 在 `utils/config_handler.py` 导入时一次性读取，并导出四个模块级单例：

| 单例 | 来源 | 关键内容 |
| --- | --- | --- |
| `rag_conf` | `config/rag.yaml` | `chat_model_provider: api`、`chat_model_name: deepseek-flash`、`chat_model_base_url: https://api.deepseek.com/v1`、`chat_model_api_key_env: DEEPSEEK_API_KEY`、`embedding_model_name: qwen3-embedding:0.6b` |
| `chroma_conf` | `config/chroma.yaml` | `collection_name: agent`、`persist_directory: chroma_db`、`k: 3`、`data_path: data`、`md5_hex_store: md5.txt`、允许类型 `["txt", "pdf"]`、`chunk_size: 200`、`chunk_overlap: 20`、中英文分隔符列表 |
| `prompts_conf` | `config/prompts.yaml` | `main_prompt_path`、`rag_summarize_prompt_path`、`report_prompt_path` |
| `agent_conf` | `config/agent.yaml` | `external_data_path: data/external/records.csv` |

路径规则：

- 所有相对路径（包括 Chroma 的 `persist_directory`）都应通过 `utils.path_tool.get_abs_path()` 转成绝对路径，避免受启动目录影响。
- `get_project_root()` 从当前文件向上逐级查找 **`.git` 目录**作为工程根；没有 `.git` 的源码副本（例如直接打包上传）会抛 `RuntimeError`。
- `chroma_conf["persist_directory"]` 的配置值虽然是相对路径 `chroma_db`，但 `rag/vector_store.py` 在传给 Chroma 之前已经用 `get_abs_path()` 处理，实际使用的是工程根下的 `chroma_db/`（见“已知问题”）。
- `.env` 在 `utils/config_handler.py` 导入时由 `utils/env_loader.py` 的 `load_env_file()` 加载：系统环境变量优先，已存在的键不会被 `.env` 覆盖；文件不存在时静默跳过。`.env` 已被 `.gitignore` 忽略，不要提交。

修改配置时的约定：

1. 新增配置项：先改对应 `config/*.yaml`，再在 `utils/config_handler.py` 中通过已有 loader 读取（新文件才需要新增 loader 和全局单例）。
2. 新增提示词：放进 `prompts/`，在 `config/prompts.yaml` 注册路径，在 `utils/prompt_loader.py` 增加加载函数（参考 `load_report_prompts` 的 KeyError / 异常日志处理方式）。
3. 提示词是行为配置：`main_prompt.txt` 逐一列出了工具能力、报告生成的固定调用顺序（`get_user_id → get_current_month → fill_context_for_report → fetch_external_data`）和“5 次工具调用仍不足则回答不知道”的约束。改工具名/参数时必须同步修改提示词、`agent/react_agent.py` 的 `tools` 列表和 `middleware.py` 中的判断。

## 构建与运行

项目没有构建步骤，依赖清单为 `requirements.txt`。以下命令均在**工程根目录**执行。

### 1. 准备环境

```bash
python -m venv .venv
source .venv/Scripts/activate     # Git Bash；PowerShell 用 .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

把 `.env.example` 复制为工程根的 `.env`，填入 DeepSeek API Key（`.env` 已被 `.gitignore` 忽略，不要提交）：

```bash
cp .env.example .env
# 然后编辑 .env
DEEPSEEK_API_KEY=你的DeepSeek密钥
```

说明：`requirements.txt` 只列直接依赖并锁定精确版本（共 11 个，含 API 模式必需的 `langchain-openai`），LangChain 必须保持 1.x（`create_agent` / middleware API 在 0.x 不存在）。升级后需重新验证；如要完全可复现的环境，验证通过后执行 `pip freeze > requirements.lock.txt`。

### 2. 启动 Ollama 并准备嵌入模型

```bash
ollama serve                      # 若未作为服务运行
ollama pull qwen3-embedding:0.6b
```

聊天模型走 DeepSeek 官方 API，**不需要**本地拉取聊天模型；嵌入模型仍由本机 Ollama 提供，必须准备 `qwen3-embedding:0.6b`。`deepseek-r1:1.5b` 只在把 `chat_model_provider` 改回 `ollama` 时才需要，且该模型实测不产出 `tool_calls`（见“已知问题”），不要用它跑 ReAct。代码未显式配置 Ollama 地址，使用客户端默认的本机 `http://localhost:11434`。

### 3. 首次构建知识库

```bash
python -m rag.vector_store
```

该命令会读取 `data/` 下的 txt/pdf、分片、向量化并写入工程根下的 `chroma_db/`（经 `get_abs_path()` 解析，与启动目录无关），同时把文件 MD5 追加到 `md5.txt`，最后用查询“迷路”做一次检索自测。**注意**：`md5.txt` 已记录现有 6 个知识文件的 MD5；若目标库为空，`load_document()` 会检测到清单失效并自动清空后重新入库，无需手动删行（见“知识库维护”）。

### 4. 启动应用

```bash
streamlit run app.py
```

默认访问 `http://localhost:8501`。首次导入工具模块时会创建 Chroma 客户端（固定在工程根 `chroma_db/`，不会在启动目录生成新库），但不会自动灌数据。

### 5. 各模块冒烟入口

项目在每个模块底部都写了 `if __name__ == '__main__':` 形式的手动测试，可用 `-m` 运行：

```bash
python -m model.factory             # 调一次聊天模型 + 嵌入模型，打印回答和向量维度
python -m rag.vector_store          # 入库 + 检索“迷路”
python -m rag.rag_service           # RAG 总结示例：“小户型适合哪些扫地机器人？”
python -m agent.tools.agent_tools   # fetch_external_data("1001", "2025-01")
python -m agent.react_agent         # 端到端调用：“扫地机器人在我所在地区的气温下如何保养？”
```

必须用 `python -m <模块>` 而不是 `python rag/vector_store.py`：项目使用从工程根出发的绝对导入，`-m` 会把当前目录加入 `sys.path`；直接按文件路径运行会把子目录当作搜索起点，导致 `import utils...` 失败。`streamlit run app.py` 由 Streamlit 自行处理路径，不受此限制。

## 测试策略

- **没有自动化测试**：仓库中没有 `tests/`、pytest/unittest 配置，也没有 CI 配置。
- 现有“测试”就是各模块末尾的 `__main__` 冒烟代码，覆盖模型连接、RAG 入库/检索/总结、外部记录读取和完整 Agent 调用。
- 涉及聊天模型的冒烟测试需要可用的 `DEEPSEEK_API_KEY` 与 `api.deepseek.com` 网络连通；涉及嵌入或向量库的冒烟测试依赖本机 Ollama 与已入库的 Chroma 数据。离线环境下只能做静态检查。
- 修改后至少运行与改动模块对应的 `python -m ...` 入口，并检查 `logs/Sweep-ReAct-Agent_YYYYMMDD.log`（文件级 DEBUG，控制台 INFO）。
- 端到端验证方式：`streamlit run app.py`，在聊天框分别验证普通问答（触发 `rag_summarize` / 天气工具）和“生成我的使用报告”（触发提示词切换）。

## 代码风格与开发约定

- **文档字符串**：统一 Google 风格（`Args:` / `Returns:` / `Raises:`），模块、类、公开函数都要写。
- **语言**：注释、docstring、日志、提示词、提交说明均使用中文；代码标识符使用英文。
- **格式**：4 空格缩进；函数/变量 `snake_case`，类 `PascalCase`，模块级常量 `UPPER_SNAKE_CASE`（如 `LOG_ROOT`、`DEFAULT_LOG_FORMAT`）；关键字参数常写成 `key = value` 的带空格形式（沿用现有代码风格）。
- **导入**：一律使用从工程根出发的绝对导入（`from utils.logger_handler import logger`），不要写相对导入，也不要新增 `__init__.py`。
- **路径**：不要硬编码绝对路径；新增文件路径时走 `get_abs_path()` + YAML 配置。
- **日志**：统一 `from utils.logger_handler import logger`，消息前加 `[模块名]` 前缀（如 `[加载知识库]`、`[fetch_external_data]`）。配置/提示词缺失时记录 error 并 `raise`；批量处理单文件失败时记录 error（必要时 `exc_info=True`）后继续，不中断整批。
- **配置驱动**：模型名、集合名、chunk 参数、文件路径、提示词路径都放在 YAML/提示词文件中，不要写死在业务代码里。
- **模块级单例**：`chat_model`、`embed_model`、`rag`、四个 `*_conf` 都在导入时创建。新增工具时注意 `agent/tools/agent_tools.py` 在导入阶段就会初始化 RAG 服务；保持这一模式，不要无意中引入重复初始化。
- **新增工具的步骤**：
  1. 在 `agent/tools/agent_tools.py` 用 `@tool(description=...)` 注册，写 Google 风格 docstring；
  2. 在 `agent/react_agent.py` 的 `tools=[...]` 中加入；
  3. 在 `prompts/main_prompt.txt`（以及报告场景需要的 `prompts/report_prompt.txt`）补充工具能力、入参和调用规则；
  4. 若工具有特殊副作用，在 `agent/tools/middleware.py` 的 `monitor_tool` 中按工具名处理（参考 `fill_context_for_report`）。
- **提交信息**：沿用现有风格，使用 `feat:` / `fix:` / `feat(scope):` / `fix(scope):` 前缀，描述可用中文（如 `fix(agent_tools): 修复 @tool 调用错误并规范化 docstring`）。不要在未获用户确认时执行 `git commit` / `git push`。
- **不要改动的内容**：`main.py` 是 IDE 模板，不是项目入口，除非用户明确要求，不要据此调整代码。README 是正式项目文档（`README.md` 英文默认、`README.zh-CN.md` 中文），改动功能、配置或运行方式时应同步更新两份。

## 知识库维护

- 知识源目录由 `chroma_conf["data_path"]` 决定，当前为 `data/`；`docs/knowledge/` 不参与入库。
- 支持 `.txt` / `.pdf`（`allow_knowledge_file_type`），TXT 默认按 UTF-8 读取；GBK 文件会解码失败，需要先转码。
- 增量机制：`md5.txt` 保存已处理文件的 MD5（每行一个，当前 6 行正好对应 `data/` 下 6 个文件）。`load_document()` 命中 MD5 就跳过，因此在清单与库配套时：
  - 新增知识文件：直接 `python -m rag.vector_store`，只会处理新文件；
  - 修改已有文件：MD5 变化，会自动重新入库（旧分片不会自动删除，可能残留）；
  - 删除向量库后重建：`load_document()` 会发现“库为空但清单有记录”，判定清单失效并清空后全量重新入库，无需手动删行；
  - 反向风险仍在：`md5.txt` 当前未被 git 跟踪；若只拷库不拷 `md5.txt`（或反之），会出现重复入库或漏入库，换机器时需把 `md5.txt` 与库一起同步。
- 外部记录：`data/external/records.csv` 为 `utf-8-sig`（兼容 Excel BOM），表头为 `用户ID,特征,清洁效率,耗材,对比,时间`；`generate_external_data()` 按 `user_id → month → {特征, 效率, 耗材, 对比}` 建缓存，并用 `_normalize_field()` 把字段内的字面量 `\n` 还原成换行。少于 6 列的行会记 warning 并跳过。
- 修改配置中的 `collection_name` 或 `persist_directory` 会换一套库，旧库不会迁移。
- 不要手动编辑 Chroma 的 `chroma.sqlite3`；如需清库，直接删除目录即可，`md5.txt` 会在下次 `load_document()` 时自动失效并重建（属于破坏性操作，先与用户确认）。

## 安全与运维注意事项

- **API Key 管理**：聊天模型通过 DeepSeek API Key 调用，Key 存放在工程根 `.env`（已被 `.gitignore` 忽略），代码只从环境变量读取，**禁止把 Key 写进代码、配置或提交进版本库**；`.env` 也不要在日志、截图或聊天记录里外泄。若要在仓库里放密钥模板，只放占位符。
- **无鉴权**：Streamlit 应用没有登录/权限控制，通过 8501 端口直接提供 HTTP 服务。不要直接暴露到公网；如需对外，先加反向代理与认证。
- **提示词即策略**：系统提示词决定工具调用边界与报告生成流程，属于受信任配置；不要接受用户上传的提示词文件直接替换。
- **YAML 解析**：`utils/config_handler.py` 使用 `yaml.safe_load`，请保持，不要改成 `yaml.load`。
- **数据性质**：天气、位置、用户 ID、月份、使用记录均为模拟数据；`records.csv` 不要写入真实个人信息。
- **运行产物**：`logs/`、`__pycache__/`、根目录 `chroma_db/` 都是运行产物。`.gitignore` 目前只忽略 `.env`，`git add .` 仍会把它们加入版本库；提交前应显式挑选文件。
- **敏感输出**：`rag/rag_service.py:11-15` 的 `print_prompt` 会把完整提示词和检索上下文打印到标准输出，生产化前应移除或降级为 debug 日志。

## 已知问题与陷阱

1. **向量库路径不一致（已修复，留作记录）**：`config/chroma.yaml` 的 `persist_directory: chroma_db` 是相对路径，Chroma 按进程 CWD 解析，导致历史上在工程根、`rag/`、`agent/` 下各生成了一份 `chroma_db/`；其中只有 `rag/` 下的那份有数据（集合 `agent`，**326 条向量**），从工程根启动时 RAG 检索为空。
   - 修复方式：`rag/vector_store.py` 的 `VectorStoreService.__init__` 先用 `get_abs_path(chroma_conf["persist_directory"])` 转成绝对路径再传给 Chroma，路径固定在工程根；随后把原来 `rag/` 下的那份库整体迁移到工程根 `chroma_db/`，并删除另外两份空库。
   - 当前状态：全项目只有工程根一份 `chroma_db/`（326 条向量），路径与服务启动目录无关。
   - 排查提示：如果 `rag/` 或 `agent/` 下再次出现 `chroma_db/`，说明有代码又直接把相对路径交给了 Chroma。
2. **MD5 清单与向量库可能不配套**：`load_document()` 已能自愈“库为空但清单有记录”的情况（自动清空清单重新入库）；但“库有数据而 `md5.txt` 丢失”仍会导致重复入库，因为清单是唯一的去重依据，且未被 git 跟踪。
3. **依赖需按清单安装**：`.venv` 当前已按 `requirements.txt` 安装齐全（含 `langchain-openai==1.7.4` 及其 `openai` 依赖）；换机器或重建虚拟环境后必须重新执行 `pip install -r requirements.txt`，API 模式缺少 `langchain-openai` 会在构造模型时抛 `RuntimeError`。
4. **入口混淆**：真正的入口是 `app.py`；`main.py` 是 PyCharm 模板（打印 `Hi, PyCharm`）。
5. **RAG 调试输出**：`rag/rag_service.py` 的 `print_prompt` 会把渲染后的完整提示词和检索内容打印到标准输出，本地演示无碍，生产化前应移除或降级为 debug 日志。
6. **工具名已统一为 `fill_context_for_report`**：历史上工具函数曾拼成 `fill_context_fo_report`（少一个 `r`），导致 `middleware.py` 的工具名判断永不命中、报告提示词切换失效。现已改名并同步 `agent_tools.py`、`react_agent.py` 的 import 与 `tools` 列表；`middleware.py` 与提示词原本就是正确拼写。改动工具名时必须同步这四处。
7. **报告提示词切换依赖运行时上下文（已实测生效）**：`monitor_tool` 在工具成功后写 `request.runtime.context["report"] = True`，并要求该 dict 在图节点间共享。端到端日志在 `fill_context_for_report` 触发后会打印“已切换到报告生成场景，后续模型调用使用 report_prompt”，说明当前实现可用。若日后出现日志打印了但提示词没切，说明 context 在节点间被重建，应改为把 `report` 标志放进 `AgentState`。
8. **多轮历史无清理策略**：`ReactAgent.execute_stream(query, history)` 已支持多轮，历史由 `app.py` 从 `session_state["message"]` 组装后传入，只按 `MAX_HISTORY_MESSAGES`（20 条）截断；历史里不包含工具调用记录，模型无法回看上一轮检索到了什么。
9. **依赖 `.git` 目录**：`get_project_root()` 找不到 `.git` 会抛异常，所有配置/数据路径随之失败；源码分发时需保留 `.git` 或改造根目录定位逻辑。
10. **类型注解依赖新 Python**：`model/factory.py` 的返回注解使用了未导入的 `Embeddings` / `BaseChatModel`。Python 3.14 默认延迟求值注解，所以能运行；在 3.13 及更早版本会在导入时报 `NameError`。若要降级 Python，需要补 import 或改成字符串注解。
11. **本地 `deepseek-r1:1.5b` 不产出工具调用**：该模型虽然 `ollama show` 显示 tools 能力，但实测 `tool_calls` 恒为空，ReAct 工具链完全不会触发，这也是聊天模型改用 API 的原因。当前 DeepSeek 官方 API 可用模型只有 `deepseek-v4-pro` 和 `deepseek-flash`（**不存在** `deepseek-v4.1`），两者实测都能正确发起 `tool_calls`，项目默认用 `deepseek-flash`。若要回退本地模型，必须换一个真正支持工具调用的模型，并先确认 `tool_calls` 不为空。
12. **Git 状态**：截至本次检查，`app.py`、`agent/react_agent.py`、`agent/tools/middleware.py`、`chroma_db/`、`md5.txt` 等核心文件尚未被提交（`git status` 显示 untracked），从远程 `sra`（`git@github.com:jianglai520/Sweep-ReAct-Agent.git`，分支 `main`）全新克隆可能缺少这些内容。操作前先看 `git status`，不要假设工作区干净。

## 部署说明

仓库没有 Dockerfile、CI/CD、进程管理或打包配置，也不是可安装的 Python 包。当前“部署”等于在一台装有 Ollama、能访问 DeepSeek 官方 API 的机器上本地运行：

1. 准备 Python 3.14 环境并安装 `requirements.txt`；
2. 配置 `DEEPSEEK_API_KEY`（环境变量，或工程根 `.env`）；
3. 启动 Ollama，拉取嵌入模型 `qwen3-embedding:0.6b`（聊天模型走 API，无需本地拉取）；
4. 确认 `data/` 知识文件与可用的 Chroma 库（或重新入库）；
5. `streamlit run app.py`，默认端口 8501。

迁移机器时最容易遗漏：`.env` 中的 API Key、`.git` 锚点、本机 Ollama 嵌入模型、Chroma 库与 `md5.txt` 的配套关系。Chroma 路径已改为基于工程根的绝对路径；若要做成可分发部署，剩下的主要是移除 `print_prompt` 调试输出，并补齐 `.gitignore`（目前只忽略 `.env`）。
