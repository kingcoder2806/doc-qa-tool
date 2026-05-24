# 📄 DocMind — Intelligent Document Q&A

> Upload any PDF. Ask questions in plain English. Get instant, context-aware answers — powered by Claude and LangChain.

---

## Preview

### Splash / Loading Screen
When the app first loads, a full-screen animated intro plays before fading into the main interface.

![DocMind splash screen](doc-mid.png)

### Main Application Layout

```
┌─────────────────────────┬──────────────────────────────────────────────────┐
│  SIDEBAR (dark navy)    │  MAIN AREA                                       │
│                         │                                                  │
│  📄 DocMind             │  ╔══════════════════════════════════════════════╗│
│  Your AI reading        │  ║  Ask anything about your document            ║│
│  assistant              │  ║  Upload a PDF, then ask questions in plain   ║│
│  ─────────────────      │  ║  English — DocMind reads it so you don't     ║│
│  Upload Document        │  ║  have to.                                    ║│
│  ┌───────────────────┐  │  ╚══════════════════════════════════════════════╝│
│  │  Drop a PDF here  │  │        (purple → violet gradient hero banner)    │
│  └───────────────────┘  │                                                  │
│                         │  ┌──────────────────────────────────────────────┐│
│  ✅ ai_applications.pdf │  │ 👤 User                                      ││
│  📃 12 pages            │  │  What are the main AI applications discussed? ││
│  🧩 48 chunks           │  └──────────────────────────────────────────────┘│
│                         │  ┌──────────────────────────────────────────────┐│
│  ─────────────────      │  │ 🤖 Assistant                                 ││
│  🗑️ Clear chat          │  │  The document covers three main areas: ...   ││
│                         │  └──────────────────────────────────────────────┘│
│  ─────────────────      │                                                  │
│  DocMind · Claude +     │  ┌──────────────────────────────────────────────┐│
│  LangChain              │  │  Ask a question about your document…     [↵] ││
│                         │  └──────────────────────────────────────────────┘│
└─────────────────────────┴──────────────────────────────────────────────────┘
```

> **Tip:** Replace this section with an actual screenshot once you have the app running.
> Place it at `screenshots/app.png` and update the line below:
> ```md
> ![DocMind Screenshot](screenshots/app.png)
> ```

---

## Features

- **Animated splash screen** — branded intro with spin animation fades out before the app appears
- **Step-by-step PDF processing** — live progress bar shows each pipeline stage
- **Persistent chat history** — full conversation stored in session state and rendered with `st.chat_message`
- **Document stats** — page count and chunk count displayed as chips after upload
- **Clear chat** button — resets conversation without reprocessing the document
- **"Thinking…" spinner** — visible feedback while the LLM generates a response
- **Context-grounded answers** — the model only answers from the document; responds with "I don't know" when information is absent

---

## Tech Stack

| Layer | Technology | Version | Purpose |
|---|---|---|---|
| **UI** | [Streamlit](https://streamlit.io) | 1.57.0 | Web interface, chat UI, file uploader |
| **LLM** | [Claude Haiku](https://anthropic.com) (`claude-haiku-4-5-20251001`) | via API | Language model for answering questions |
| **LLM SDK** | [LangChain Anthropic](https://github.com/langchain-ai/langchain) | 1.4.3 | `ChatAnthropic` wrapper |
| **RAG orchestration** | [LangChain Core](https://github.com/langchain-ai/langchain) | 1.4.0 | Chains, prompts, output parsers |
| **PDF loading** | [LangChain Community](https://github.com/langchain-ai/langchain) | 0.4.2 | `PyPDFLoader` |
| **Text splitting** | [LangChain Text Splitters](https://github.com/langchain-ai/langchain) | 1.1.2 | `RecursiveCharacterTextSplitter` |
| **Embeddings** | [Sentence Transformers](https://www.sbert.net) | 5.5.1 | `all-MiniLM-L6-v2` local embedding model |
| **Vector store** | [ChromaDB](https://www.trychroma.com) | 1.5.9 | Persistent similarity search |
| **ML runtime** | [PyTorch](https://pytorch.org) | 2.12.0 | Backend for Sentence Transformers |
| **Env vars** | [python-dotenv](https://github.com/theskumar/python-dotenv) | 1.2.2 | Loads `ANTHROPIC_API_KEY` from `.env` |

### Architecture — how it works

```
PDF Upload
    │
    ▼
PyPDFLoader  ──────────────────────►  raw Document pages
    │
    ▼
RecursiveCharacterTextSplitter  ────►  500-token chunks (50-token overlap)
    │
    ▼
SentenceTransformerEmbeddings  ─────►  384-dim vectors  (all-MiniLM-L6-v2)
    │
    ▼
ChromaDB (persisted to ./chroma_db)  ◄──  stored & searchable
    │
    │   User question
    ▼
Retriever (top-3 chunks by cosine similarity)
    │
    ▼
ChatPromptTemplate  +  ChatAnthropic (Claude Haiku)
    │
    ▼
StrOutputParser  ───────────────────►  Answer displayed in chat
```

---

## Local Deployment

### Prerequisites

| Requirement | Notes |
|---|---|
| Python 3.10+ | `python --version` to check |
| pip | comes with Python |
| Anthropic API key | get one free at [console.anthropic.com](https://console.anthropic.com) |

---

### 1. Clone or download the project

```bash
git clone <your-repo-url>
cd doc-qa-tool
```

Or simply unzip the folder and open a terminal inside it.

---

### 2. Create and activate a virtual environment

**Windows (PowerShell)**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**macOS / Linux**
```bash
python -m venv venv
source venv/bin/activate
```

You should see `(venv)` at the start of your terminal prompt.

---

### 3. Install dependencies

```bash
pip install streamlit langchain langchain-anthropic langchain-community \
            langchain-core langchain-text-splitters chromadb \
            sentence-transformers pypdf python-dotenv torch
```

> **Note:** PyTorch (`torch`) is a large download (~2 GB). On a slow connection this may take a few minutes. The CPU-only build is sufficient — no GPU required.

---

### 4. Set your API key

Create a `.env` file in the project root:

```bash
# .env
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxxxxxx
```

> Never commit this file. It is already listed in `.gitignore`.

To get a key:
1. Go to [console.anthropic.com](https://console.anthropic.com)
2. Sign in → **API Keys** → **Create Key**
3. Copy the key and paste it into `.env`

---

### 5. Run the app

```bash
streamlit run app.py
```

Streamlit will print something like:

```
  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://192.168.x.x:8501
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

---

### 6. Use the app

1. **Watch the splash** — the animated intro plays for ~2.5 seconds on first load
2. **Upload a PDF** — click "Drop a PDF here" in the left sidebar
3. **Wait for processing** — a progress bar shows the 4 pipeline stages
4. **Ask questions** — type in the chat bar at the bottom and press Enter
5. **Clear & restart** — use the "Clear chat" button to reset the conversation

---

## Project Structure

```
doc-qa-tool/
│
├── app.py              # Streamlit UI — imports and calls functions from main.py
├── main.py             # RAG pipeline: load_pdf, split_documents,
│                       #   create_vectorstore, ask_question
│
├── .env                # Your API key (DO NOT commit)
├── .gitignore
│
├── chroma_db/          # Auto-created — ChromaDB persistence directory
│                       #   (re-created each time a new PDF is processed)
│
└── venv/               # Virtual environment (not committed)
```

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | ✅ Yes | Your Anthropic API key — used by `ChatAnthropic` in `main.py` |

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `ModuleNotFoundError: streamlit` | Run `pip install streamlit` inside your activated venv |
| `AuthenticationError` from Anthropic | Check your `ANTHROPIC_API_KEY` in `.env` — no extra spaces or quotes |
| App opens but chat input is greyed out | Upload a PDF first — the input is disabled until a document is loaded |
| Slow first startup | Sentence Transformers downloads `all-MiniLM-L6-v2` (~90 MB) on first use — wait for it to finish |
| `chroma_db` errors after changing PDFs | Delete the `chroma_db/` folder and re-upload — it will be rebuilt automatically |
| PowerShell execution policy error | Run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` then re-activate venv |

---

## License

MIT — free to use, modify, and distribute.
