"""
RAG 问答 — 基于 LangChain + GitHub Models
数据源: https://www.promptingguide.ai/zh (本地 HTML)
"""

import os
import glob
from dotenv import load_dotenv

from langchain.chat_models import init_chat_model
from langchain_openai import OpenAIEmbeddings
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_community.document_loaders import BSHTMLLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

# ============================================================
# 配置
# ============================================================
load_dotenv("code/.env")
os.environ["LANGSMITH_TRACING"] = "false"
os.environ["OPENAI_API_KEY"] = os.getenv("GITHUB_TOKEN")
os.environ["OPENAI_BASE_URL"] = os.getenv("GITHUB_MODEL_BASE_URL")

CHUNK_SIZE = 500  # 每个 chunk 的最大字符数
CHUNK_OVERLAP = 80  # chunk 之间的重叠字符数
RETRIEVAL_K = 3  # 检索 top-k 相关文档
PAGES_DIR = "code/stage2/prompt_guide_pages"  # 本地 HTML 文件目录

# ============================================================
# Phase 1: 索引 — 文档加载 → 切分 → 嵌入 → 向量库
# ============================================================
def build_index():
    # 加载所有 HTML 文档
    all_docs = []
    for f in glob.glob(f"{PAGES_DIR}/*.html"):
        all_docs.extend(BSHTMLLoader(f, open_encoding="utf-8").load())

    # 切分文档成 chunks
    chunks = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP
    ).split_documents(all_docs)

    # 创建嵌入模型和向量库
    model = OpenAIEmbeddings(model="text-embedding-3-large")
    store = InMemoryVectorStore(model)
    store.add_documents(chunks)

    print(f"索引完成: {len(all_docs)} 页面 → {len(chunks)} chunk")
    return store

# ============================================================
# Phase 2: 检索 + 生成
# ============================================================
def rag_qa(store, question):
    llm = init_chat_model(os.getenv("GITHUB_MODEL"), temperature=0)
    docs = store.similarity_search(question, k=RETRIEVAL_K)  # 返回相关文档列表
    context = "\n\n".join(doc.page_content[:500] for doc in docs)  # 取前 500 字作为上下文

    response = llm.invoke(
        f"基于以下资料回答。找不到就说'未找到'。\n\n"
        f"资料:\n{context}\n\n问题: {question}"
    )
    return response.content

# ============================================================
# 运行
# ============================================================
if __name__ == "__main__":
    store = build_index()
    answer = rag_qa(store, "什么是 Chain-of-Thought (CoT) 提示？")
    print(f"回答: {answer}")
