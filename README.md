# Sweep-ReAct-Agent

**A domain customer-service agent for robot vacuum cleaners, built on a LangChain 1.x ReAct loop with Chroma RAG and a Streamlit chat UI.**

English | [简体中文](README.zh-CN.md)

![Python](https://img.shields.io/badge/Python-3.14-3776AB?logo=python&logoColor=white)
![LangChain](https://img.shields.io/badge/LangChain-1.x-1C3C3C)
![Streamlit](https://img.shields.io/badge/Streamlit-1.67-FF4B4B?logo=streamlit&logoColor=white)
![Chroma](https://img.shields.io/badge/Vector%20Store-Chroma-FF6B6B)
![LLM](https://img.shields.io/badge/Chat%20Model-DeepSeek%20API-4D6BFE)

---

## Overview

Sweep-ReAct-Agent (UI name: 智扫通) answers pre-sales, everyday-usage, maintenance and troubleshooting questions about robot vacuum cleaners and vacuum-mop combos.

Instead of a fixed prompt chain, the agent runs a **ReAct loop**: the model decides which tools to call, in which order, and how many times. Tools cover domain knowledge retrieval, weather/location lookups, user identity and usage-record queries. When the user asks for a personal usage report, the agent walks a fixed tool sequence and the system prompt is switched at runtime to a report-writing persona.

Chat completion calls the **DeepSeek API** (OpenAI-compatible); embeddings run **locally on Ollama** and the vector index lives in a local Chroma database.

> This is a learning / demonstration project, not a production system. Weather, user IDs, current month and usage records are all simulated. There is no authentication and no automated test suite.

## Features

- **ReAct tool calling** — tool selection and call count are decided by the model at runtime, not hard-coded.
- **Local RAG** — 6 knowledge files (PDF + TXT) are chunked, embedded and stored in Chroma; answers are grounded in retrieved passages.
- **Report generation** — a dedicated flow (`get_user_id → get_current_month → fill_context_for_report → fetch_external_data`) plus a runtime system-prompt switch.
- **Tool-call observability** — middleware logs every tool name, arguments and result, and logs each model invocation.
- **Multi-turn chat** — recent conversation history is passed back to the model (capped at 20 messages).
- **Config-driven** — model names, endpoints, chunking parameters, paths and prompts all live in YAML / prompt files.
- **Swappable chat backend** — DeepSeek API by default, local Ollama as a fallback.

## Architecture

```text
Streamlit UI (app.py)
  └─ ReactAgent.execute_stream(query, history)
       └─ LangChain create_agent
            ├─ middleware
            │    ├─ monitor_tool              logs tool calls; flips report context on
            │    │                            fill_context_for_report
            │    ├─ log_before_model          logs each model invocation
            │    └─ report_prompt_switch      picks main / report system prompt
            └─ tools (7)
                 ├─ rag_summarize(query)              -> local Chroma retriever + LLM
                 ├─ get_weather(city)                 -> simulated
                 ├─ get_user_location()               -> simulated
                 ├─ get_user_id()                     -> simulated
                 ├─ get_current_month()               -> simulated
                 ├─ fetch_external_data(user_id, month) -> records.csv cache
                 └─ fill_context_for_report()         -> context flag only
```

**Chat model:** DeepSeek API `deepseek-flash` (OpenAI-compatible endpoint).
**Embedding model:** local Ollama `qwen3-embedding:0.6b` (1024-dim).

### RAG pipeline

```text
data/*.pdf|*.txt
  -> PyPDFLoader / TextLoader
  -> RecursiveCharacterTextSplitter(chunk_size=200, chunk_overlap=20)
  -> OllamaEmbeddings(qwen3-embedding:0.6b)
  -> Chroma(collection="agent", persist_directory=<project_root>/chroma_db)
  -> as_retriever(k=3)
  -> PromptTemplate | chat_model | StrOutputParser
```

Knowledge files are ingested incrementally: file MD5 hashes are recorded in `md5.txt`, and the loader detects a stale manifest (empty vector store + recorded hashes) and rebuilds automatically.

## Tech stack

| Layer | Choice |
| --- | --- |
| Language | Python 3.14 |
| Agent framework | LangChain 1.x (`create_agent`, `AgentState`, middleware: `wrap_tool_call` / `before_model` / `dynamic_prompt`) |
| Runtime context | LangGraph (`Runtime`, `Command`) |
| Chat model | DeepSeek API `deepseek-flash` (OpenAI-compatible) |
| Embeddings | Ollama `qwen3-embedding:0.6b` (local) |
| Vector store | Chroma (`langchain-chroma`) |
| Document loading | `PyPDFLoader` / `TextLoader`, `RecursiveCharacterTextSplitter` |
| Web UI | Streamlit |
| Config | YAML + plain-text prompt files |

## Quick start

### Prerequisites

- Python **3.14**
- [Ollama](https://ollama.com) running locally (used for embeddings only)
- A **DeepSeek API key**

### 1. Install dependencies

```bash
git clone <repo-url>
cd Sweep_ReAct_Agent

python -m venv .venv

# Windows (PowerShell)
.\.venv\Scripts\Activate.ps1
# macOS / Linux
source .venv/bin/activate

python -m pip install -r requirements.txt
```

> If PowerShell rejects the activation script, run
> `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once.
> You can also skip activation entirely and use `.\.venv\Scripts\python.exe -m ...`.

### 2. Configure the API key

```bash
cp .env.example .env
# then edit .env
DEEPSEEK_API_KEY=your-key-here
```

`.env` is ignored by git. The key is read from the environment at import time; it is never written into code or configuration.

### 3. Prepare the embedding model

```bash
ollama serve
ollama pull qwen3-embedding:0.6b
```

Only the embedding model is required locally. Chat completion goes through the API.

### 4. Build the knowledge base

```bash
python -m rag.vector_store
```

This reads `data/`, chunks and embeds the documents, writes them to `chroma_db/` at the project root, records file MD5s in `md5.txt`, and runs a sample retrieval query.

### 5. Run

```bash
python -m streamlit run app.py
```

Then open <http://localhost:8501>.

Try:

- `滤网多久需要更换一次？` — triggers `rag_summarize`
- `深圳现在天气怎么样？` — triggers `get_user_location` + `get_weather`
- `生成我的使用报告` — walks the report flow and switches the system prompt

## Configuration

| File | Contents |
| --- | --- |
| `config/rag.yaml` | chat model provider (`api` / `ollama`), model name, base URL, API-key env var, embedding model name |
| `config/chroma.yaml` | collection name, persist directory, top-k, data path, MD5 manifest, chunk size/overlap, separators |
| `config/prompts.yaml` | paths of the three prompt files |
| `config/agent.yaml` | path of the simulated usage records CSV |

To switch back to a local chat model, set:

```yaml
chat_model_provider: ollama
chat_model_name: <a-tool-calling-capable-ollama-model>
```

Note: the bundled local model `deepseek-r1:1.5b` does **not** emit `tool_calls` in practice, so the ReAct loop never fires with it.

## Tools

| Tool | Arguments | Purpose |
| --- | --- | --- |
| `rag_summarize` | `query` | Retrieve from the vector store and summarise an answer |
| `get_weather` | `city` | Simulated weather for a city |
| `get_user_location` | — | Simulated user city |
| `get_user_id` | — | Simulated user ID (`1001`–`1010`) |
| `get_current_month` | — | Simulated month (`2025-01`–`2025-12`) |
| `fetch_external_data` | `user_id`, `month` | Usage record from `data/external/records.csv` |
| `fill_context_for_report` | — | Flips the runtime context flag that switches to the report prompt |

## Project structure

```text
.
├── app.py                  # Streamlit entry point
├── requirements.txt        # pinned direct dependencies
├── .env.example            # API-key template
├── config/                 # rag / chroma / prompts / agent YAML
├── prompts/                # main, RAG-summary and report system prompts
├── agent/
│   ├── react_agent.py      # agent assembly, streaming interface
│   └── tools/
│       ├── agent_tools.py  # 7 tools + simulated data
│       └── middleware.py   # tool monitoring, model logging, prompt switch
├── model/
│   └── factory.py          # chat model factory (API / Ollama) + embedding model
├── rag/
│   ├── vector_store.py     # ingest + retriever
│   └── rag_service.py      # retrieval + prompt + model chain
├── utils/                  # config, paths, prompts, files, logging, .env loader
├── data/                   # knowledge sources + simulated records
├── chroma_db/              # Chroma persistence (not committed)
└── logs/                   # daily log files
```

## Smoke tests

Each module has a `__main__` block that can be executed with `-m` from the project root:

```bash
python -m model.factory             # chat model + embedding model connectivity
python -m rag.vector_store          # incremental ingest + retrieval sample
python -m rag.rag_service           # RAG summary sample
python -m agent.tools.agent_tools   # external records lookup
python -m agent.react_agent         # end-to-end agent call
```

The RAG and agent tests need a working API key; the ingest test needs Ollama.

## Known limitations

- **Simulated data** — weather, location, user ID, month and usage records are mock values.
- **No authentication** — do not expose the Streamlit port publicly.
- **No automated tests** — verification relies on the `__main__` smoke scripts.
- **Retrieval is plain top-k** — no MMR or score threshold.
- **`md5.txt` and `chroma_db/` must stay paired** — if you copy one without the other across machines, you get either duplicated ingestion or missed ingestion.
- **Debug output** — the RAG chain prints the full rendered prompt to stdout.
- **No license file** — the repository is for learning and demonstration.

---

[简体中文版 README](README.zh-CN.md)
