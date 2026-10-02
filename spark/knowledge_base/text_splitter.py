# knowledge_base/text_splitter.py

from typing import List, Dict


def split_text(
    text: str,
    chunk_size: int = 500,
    overlap: int = 80
) -> List[str]:
    """
    把长文本切成多个小片段。
    
    chunk_size：每个片段最大长度
    overlap：相邻片段重叠长度，避免上下文断裂
    """
    text = text.replace("\r", "\n")
    text = "\n".join([line.strip() for line in text.split("\n") if line.strip()])

    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]

        if chunk.strip():
            chunks.append(chunk.strip())

        start = end - overlap

        if start < 0:
            start = 0

        if start >= len(text):
            break

    return chunks


def split_documents(
    documents: List[Dict],
    chunk_size: int = 500,
    overlap: int = 80
) -> List[Dict]:
    """
    把多个文档切成知识片段。
    
    返回格式：
    [
        {
            "id": 1,
            "file_name": "xxx.pptx",
            "file_path": "...",
            "chunk_index": 0,
            "content": "文本片段"
        }
    ]
    """
    all_chunks = []
    chunk_id = 1

    for doc in documents:
        chunks = split_text(
            text=doc["content"],
            chunk_size=chunk_size,
            overlap=overlap
        )

        for index, chunk in enumerate(chunks):
            all_chunks.append({
                "id": chunk_id,
                "file_name": doc["file_name"],
                "file_path": doc["file_path"],
                "chunk_index": index,
                "content": chunk
            })
            chunk_id += 1

    return all_chunks