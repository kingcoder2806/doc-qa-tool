import streamlit as st
import tempfile
import time
import os
import shutil
from dotenv import load_dotenv
from main import load_pdf, split_documents, create_vectorstore, ask_question

load_dotenv()

st.set_page_config(
    page_title="DocMind – Document Q&A",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global styles ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* Import font */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* ── Splash overlay ── */
@keyframes fadeOut {
    0%   { opacity: 1; }
    70%  { opacity: 1; }
    100% { opacity: 0; pointer-events: none; }
}
@keyframes pulse {
    0%, 100% { transform: scale(1);   opacity: 1; }
    50%       { transform: scale(1.1); opacity: 0.7; }
}
@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(24px); }
    to   { opacity: 1; transform: translateY(0);    }
}
@keyframes spinRing {
    to { transform: rotate(360deg); }
}

#splash {
    position: fixed;
    inset: 0;
    z-index: 9999;
    background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    animation: fadeOut 2.6s ease forwards;
}
#splash .ring {
    width: 72px; height: 72px;
    border: 4px solid rgba(255,255,255,0.15);
    border-top-color: #7c6af7;
    border-radius: 50%;
    animation: spinRing 0.9s linear infinite;
    margin-bottom: 28px;
}
#splash .brand {
    font-size: 2.4rem;
    font-weight: 700;
    color: #fff;
    letter-spacing: -0.5px;
    animation: pulse 1.6s ease infinite;
}
#splash .tagline {
    margin-top: 10px;
    font-size: 0.95rem;
    color: rgba(255,255,255,0.5);
    letter-spacing: 0.5px;
}

/* ── Main content fade-in ── */
@keyframes appFadeIn {
    from { opacity: 0; transform: translateY(12px); }
    to   { opacity: 1; transform: translateY(0); }
}
section.main > div { animation: appFadeIn 0.7s ease 2.4s both; }

/* ── Hide sidebar collapse/expand toggle ── */
[data-testid="collapsedControl"]          { display: none !important; }
section[data-testid="stSidebar"] > div > button { display: none !important; }

/* ── Sidebar width ── */
section[data-testid="stSidebar"]               { width: 360px !important; min-width: 360px !important; }
section[data-testid="stSidebar"] > div:first-child { width: 360px !important; min-width: 360px !important; }

/* ── Sidebar shell ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0d0b1e 0%, #13112b 55%, #0d0b1e 100%);
    border-right: 1px solid rgba(124,106,247,0.18);
    padding-top: 0 !important;
}
[data-testid="stSidebar"] > div:first-child { padding-top: 0 !important; }

/* accent bar at very top */
[data-testid="stSidebar"]::before {
    content: '';
    display: block;
    height: 4px;
    background: linear-gradient(90deg, #7c6af7, #a855f7, #ec4899);
    border-radius: 0 0 4px 4px;
    margin-bottom: 0;
}

/* all sidebar text */
[data-testid="stSidebar"] * { color: #ddd8ff !important; }
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 { color: #fff !important; }

/* ── Sidebar brand block ── */
.sidebar-brand {
    padding: 1.6rem 1.4rem 0.8rem;
}
.sidebar-brand .brand-icon { font-size: 2.4rem; line-height: 1; margin-bottom: 8px; }
.sidebar-brand .brand-name {
    font-size: 1.5rem;
    font-weight: 700;
    background: linear-gradient(90deg, #a78bfa, #e879f9);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    letter-spacing: -0.3px;
    line-height: 1.2;
}
.sidebar-brand .brand-tag {
    font-size: 0.78rem;
    color: rgba(255,255,255,0.38) !important;
    margin-top: 2px;
    letter-spacing: 0.4px;
}

/* ── Section labels ── */
.sidebar-section-label {
    font-size: 0.68rem;
    font-weight: 600;
    letter-spacing: 1.4px;
    text-transform: uppercase;
    color: rgba(167,139,250,0.7) !important;
    padding: 0 1.4rem;
    margin-bottom: 0.5rem;
}

/* ── File uploader (covers both selector spellings across Streamlit versions) ── */
[data-testid="stFileUploadDropzone"],
[data-testid="stFileUploaderDropzone"] {
    background: rgba(124,106,247,0.1) !important;
    border: 2px dashed #7c6af7 !important;
    border-radius: 12px !important;
    transition: border-color 0.2s, background 0.2s;
}
[data-testid="stFileUploadDropzone"]:hover,
[data-testid="stFileUploaderDropzone"]:hover {
    background: rgba(124,106,247,0.18) !important;
    border-color: #a855f7 !important;
}
/* label text and limit hint */
[data-testid="stFileUploadDropzone"] span,
[data-testid="stFileUploaderDropzone"] span,
[data-testid="stFileUploaderDropzone"] small,
[data-testid="stFileUploaderDropzone"] p {
    color: rgba(255,255,255,0.7) !important;
    font-size: 0.82rem !important;
}
/* upload arrow icon */
[data-testid="stFileUploadDropzone"] svg,
[data-testid="stFileUploaderDropzone"] svg {
    fill: #7c6af7 !important;
    color: #7c6af7 !important;
}
/* "Browse files" / "Upload" button — solid purple, prominent */
[data-testid="stFileUploadDropzone"] button,
[data-testid="stFileUploaderDropzone"] button,
[data-testid="stFileUploaderDropzone"] [data-testid="stBaseButton-secondary"] {
    background: #7c6af7 !important;
    border: none !important;
    border-radius: 8px !important;
    color: #fff !important;
    font-size: 0.85rem !important;
    font-weight: 600 !important;
    padding: 0.45rem 1.1rem !important;
    box-shadow: 0 2px 10px rgba(124,106,247,0.45) !important;
}
[data-testid="stFileUploadDropzone"] button:hover,
[data-testid="stFileUploaderDropzone"] button:hover {
    background: #6b58f0 !important;
    box-shadow: 0 4px 16px rgba(124,106,247,0.6) !important;
}
/* icon inside the button */
[data-testid="stFileUploaderDropzone"] button svg {
    fill: #fff !important;
    color: #fff !important;
}

/* ── Doc info card ── */
.doc-card {
    background: rgba(124,106,247,0.1);
    border: 1px solid rgba(124,106,247,0.25);
    border-radius: 12px;
    padding: 0.9rem 1rem;
    margin: 0.6rem 0;
}
.doc-card .doc-name {
    font-size: 0.82rem;
    font-weight: 600;
    color: #e0d9ff !important;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    margin-bottom: 8px;
}
.doc-stat-row {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 4px 0;
    font-size: 0.78rem;
    color: rgba(196,185,255,0.8) !important;
    border-top: 1px solid rgba(255,255,255,0.06);
}
.doc-stat-row:first-of-type { border-top: none; }
.doc-stat-row .stat-icon { font-size: 0.9rem; width: 18px; text-align: center; }
.doc-stat-row .stat-val  { margin-left: auto; font-weight: 600; color: #c4b9ff !important; }

/* ── Clear chat button ── */
[data-testid="stSidebar"] button[kind="secondary"] {
    background: rgba(236,72,153,0.12) !important;
    border: 1px solid rgba(236,72,153,0.3) !important;
    border-radius: 10px !important;
    color: #f9a8d4 !important;
    font-size: 0.85rem !important;
    transition: background 0.2s;
}
[data-testid="stSidebar"] button[kind="secondary"]:hover {
    background: rgba(236,72,153,0.22) !important;
}

/* ── Hero banner ── */
.hero {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 16px;
    padding: 2.5rem 2.8rem;
    margin-bottom: 2rem;
    animation: fadeInUp 0.6s ease 2.5s both;
    box-shadow: 0 8px 32px rgba(102,126,234,0.35);
}
.hero h1 {
    font-size: 2.2rem;
    font-weight: 700;
    color: #fff !important;
    margin: 0 0 0.4rem 0;
    letter-spacing: -0.5px;
}
.hero p {
    font-size: 1.05rem;
    color: rgba(255,255,255,0.82) !important;
    margin: 0;
}

/* ── Empty-state card ── */
.empty-state {
    text-align: center;
    padding: 4rem 2rem;
    animation: fadeInUp 0.7s ease 2.6s both;
}
.empty-state .icon { font-size: 4rem; margin-bottom: 1rem; }
.empty-state h3 { font-size: 1.4rem; font-weight: 600; color: #444; }
.empty-state p  { color: #888; font-size: 0.95rem; }

/* ── Chat bubbles ── */
[data-testid="stChatMessage"] {
    border-radius: 14px !important;
    padding: 0.2rem 0.4rem !important;
    margin-bottom: 0.6rem !important;
}

/* ── Stat chips in sidebar ── */
.stat-chip {
    display: inline-block;
    background: rgba(124,106,247,0.18);
    border: 1px solid rgba(124,106,247,0.35);
    border-radius: 20px;
    padding: 4px 14px;
    font-size: 0.8rem;
    color: #c4b9ff !important;
    margin: 3px 3px 3px 0;
}

/* ── Divider ── */
.sidebar-divider {
    border: none;
    border-top: 1px solid rgba(255,255,255,0.1);
    margin: 1.2rem 0;
}

/* hide default Streamlit header chrome */
#MainMenu, footer, header { visibility: hidden; }
</style>

<div id="splash">
    <div class="ring"></div>
    <div class="brand">📄 DocMind</div>
    <div class="tagline">Intelligent Document Q&A — powered by Claude</div>
</div>
""", unsafe_allow_html=True)

# ── Session state defaults ─────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "vectorstore" not in st.session_state:
    st.session_state.vectorstore = None
if "processed_file" not in st.session_state:
    st.session_state.processed_file = None
if "doc_stats" not in st.session_state:
    st.session_state.doc_stats = {}

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    # Brand
    st.markdown("""
    <div class="sidebar-brand">
        <div class="brand-icon">📄</div>
        <div class="brand-name">DocMind</div>
        <div class="brand-tag">Intelligent Document Q&amp;A</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown('<hr class="sidebar-divider">', unsafe_allow_html=True)

    # Upload section
    st.markdown('<div class="sidebar-section-label">Upload Document</div>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader(
        "Drop a PDF here",
        type="pdf",
        help="Supported: PDF files up to 200 MB",
        label_visibility="collapsed",
    )

    if uploaded_file is not None:
        is_new = st.session_state.processed_file != uploaded_file.name

        if is_new:
            progress_bar = st.progress(0, text="Reading PDF…")
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(uploaded_file.read())
                tmp_path = tmp.name
            try:
                progress_bar.progress(25, text="Loading pages…")
                pages = load_pdf(tmp_path)

                progress_bar.progress(55, text="Splitting into chunks…")
                chunks = split_documents(pages)

                progress_bar.progress(80, text="Building vector store…")
                if os.path.exists("./chroma_db"):
                    shutil.rmtree("./chroma_db")
                st.session_state.vectorstore = create_vectorstore(chunks)

                progress_bar.progress(100, text="Done!")
                time.sleep(0.4)
                progress_bar.empty()

                st.session_state.processed_file = uploaded_file.name
                st.session_state.messages = []
                st.session_state.doc_stats = {
                    "pages": len(pages),
                    "chunks": len(chunks),
                    "name": uploaded_file.name,
                }
            finally:
                os.unlink(tmp_path)

        if st.session_state.doc_stats:
            name = st.session_state.doc_stats["name"]
            pages_n = st.session_state.doc_stats["pages"]
            chunks_n = st.session_state.doc_stats["chunks"]
            st.markdown(f"""
            <div class="doc-card">
                <div class="doc-name">✅ &nbsp;{name}</div>
                <div class="doc-stat-row">
                    <span class="stat-icon">📃</span> Pages
                    <span class="stat-val">{pages_n}</span>
                </div>
                <div class="doc-stat-row">
                    <span class="stat-icon">🧩</span> Chunks
                    <span class="stat-val">{chunks_n}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('<hr class="sidebar-divider">', unsafe_allow_html=True)

    if st.session_state.messages:
        st.markdown('<div class="sidebar-section-label">Actions</div>', unsafe_allow_html=True)
        if st.button("🗑️ Clear conversation", use_container_width=True):
            st.session_state.messages = []
            st.rerun()
        st.markdown('<hr class="sidebar-divider">', unsafe_allow_html=True)


# ── Hero ───────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
    <h1>Ask anything about your document</h1>
    <p>Upload a PDF, then ask questions in plain English — DocMind reads it so you don't have to.</p>
</div>
""", unsafe_allow_html=True)

# ── Chat area ─────────────────────────────────────────────────────────────────
if st.session_state.vectorstore is None:
    st.markdown("""
    <div class="empty-state">
        <div class="icon">📂</div>
        <h3>No document loaded yet</h3>
        <p>Upload a PDF using the sidebar on the left to get started.</p>
    </div>
    """, unsafe_allow_html=True)
else:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if question := st.chat_input("Ask a question about your document…"):
        st.session_state.messages.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):
            with st.spinner("Thinking…"):
                answer, sources = ask_question(st.session_state.vectorstore, question)
            st.markdown(answer)
            if sources:
                pages_str = ", ".join(str(p) for p in sources)
                st.caption(f"📄 Referenced pages: {pages_str}")

        st.session_state.messages.append({"role": "assistant", "content": answer})
