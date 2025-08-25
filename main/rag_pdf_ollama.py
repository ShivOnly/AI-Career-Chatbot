# rag_pdf_ollama.py

from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain_community.llms import Ollama
import os

def load_pdf(path):
    print("[1] Loading PDF...")
    loader = PyPDFLoader(path)
    pages = loader.load()
    print(f"Loaded {len(pages)} pages")
    if len(pages) > 0:
        print(f"Sample text from page 0:\n{pages[0].page_content[:300]}...\n---")
    return pages

def split_text(pages):
    print("[2] Splitting text into chunks...")
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_documents(pages)
    print(f"Chunks created: {len(chunks)}")
    return chunks

def embed_chunks(chunks):
    print("[3] Embedding chunks...")
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    vectorstore = FAISS.from_documents(chunks, embeddings)
    return vectorstore, embeddings

def save_vectorstore(vectorstore, path="faiss_index"):
    print("[4] Saving vectorstore...")
    vectorstore.save_local(path)

def load_vectorstore(path, embeddings):
    print("[Loading existing FAISS index...]")
    return FAISS.load_local(path, embeddings, allow_dangerous_deserialization=True)

def create_rag_chain(vectorstore):
    print("[5] Creating RAG chain with Ollama 3.1...")
    retriever = vectorstore.as_retriever()
    llm = Ollama(model="llama3.1")  # Use your running Ollama model name here
    chain = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=retriever,
        return_source_documents=True
    )
    return chain

def main():
    PDF_PATH = "/Users/shivthapa/Desktop/Rag/pdf/Thapa.pdf"
    INDEX_PATH = "faiss_index"

    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    if os.path.exists(INDEX_PATH):
        try:
            vectorstore = load_vectorstore(INDEX_PATH, embeddings)
        except Exception as e:
            print(f"⚠️ Failed to load FAISS index. Rebuilding it. Reason: {e}")
            pages = load_pdf(PDF_PATH)
            chunks = split_text(pages)
            vectorstore, _ = embed_chunks(chunks)
            save_vectorstore(vectorstore, INDEX_PATH)
    else:
        pages = load_pdf(PDF_PATH)
        chunks = split_text(pages)
        vectorstore, _ = embed_chunks(chunks)
        save_vectorstore(vectorstore, INDEX_PATH)

    chain = create_rag_chain(vectorstore)

    while True:
        query = input("\n💬 Ask a question (or type 'exit'): ")
        if query.lower() in ("exit", "quit"):
            break
        try:
            response = chain.invoke({"query": query})
            print("\n📌 Answer:", response["result"])
        except Exception as e:
            print(f"❌ Error during querying: {e}")

if __name__ == "__main__":
    main()
