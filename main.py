# main.py
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_anthropic import ChatAnthropic
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
import os
from dotenv import load_dotenv

# --- Config ---
load_dotenv()
PDF_PATH = "ai_applications.pdf"

# --- Step 1: Load the PDF ---
def load_pdf(path):
    loader = PyPDFLoader(path)
    pages = loader.load()
    print(f"Loaded {len(pages)} pages")
    return pages

# --- Step 2: Split into chunks ---
def split_documents(pages):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    chunks = splitter.split_documents(pages)
    print(f"Split into {len(chunks)} chunks")
    return chunks

# --- Step 3: Embed and store in vector DB ---
def create_vectorstore(chunks):
    embeddings = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
    vectorstore = Chroma.from_documents(
        chunks, 
        embeddings, 
        persist_directory="./chroma_db")
    print("Vector store created")
    return vectorstore

def ask_question(vectorstore, question):
    llm = ChatAnthropic(model="claude-haiku-4-5-20251001", temperature=0)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

    # Get the source chunks first
    docs = retriever.invoke(question)
    sources = sorted(set([
        doc.metadata.get("page", "unknown") + 1  # pages are 0-indexed
        for doc in docs
    ]))

    prompt = ChatPromptTemplate.from_template("""
    You are a helpful assistant that answers questions strictly based on the provided document context.

    Rules:
    - Only use information from the context below
    - If the answer is not in the context, say exactly "I couldn't find that in the document."
    - Never make up information
    - Keep answers concise and clear
    - Quote the relevant part of the document when helpful

    Context: {context}
    Question: {question}
    """)

    chain = (
        {"context": retriever, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )

    answer = chain.invoke(question)
    return answer, sources  # now returns both

# --- Run it ---
if __name__ == "__main__":
    pages = load_pdf(PDF_PATH)
    chunks = split_documents(pages)
    vectorstore = create_vectorstore(chunks)

    print("\nReady! Ask a question about your document.")
    while True:
        question = input("\nYou: ")
        if question.lower() in ["exit", "quit"]:
            break
        answer, sources = ask_question(vectorstore, question)
        print(f"AI: {answer}")
        if sources:
            print(f"   (pages: {', '.join(str(p) for p in sources)})")