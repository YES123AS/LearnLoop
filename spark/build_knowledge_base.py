# build_knowledge_base.py

from pathlib import Path

from knowledge_base.document_loader import load_documents_from_folder
from knowledge_base.text_splitter import split_documents
from knowledge_base.vector_store import SimpleVectorStore


def main():
    base_dir = Path(__file__).resolve().parent
    docs_folder = str(base_dir / "docs")
    db_dir = str(base_dir.parent / ".local-data" / "vector_db")

    print("[INFO] 开始读取课程资料...")
    documents = load_documents_from_folder(docs_folder)

    if not documents:
        print("[ERROR] docs 文件夹中没有可用文档。")
        return

    print("[INFO] 开始切分文本...")
    chunks = split_documents(
        documents=documents,
        chunk_size=500,
        overlap=80
    )

    print(f"[INFO] 文本切分完成，共 {len(chunks)} 个知识片段。")

    vector_store = SimpleVectorStore(db_dir=db_dir)
    vector_store.build(chunks)

    print("[OK] 知识库构建完成。")


if __name__ == "__main__":
    main()
