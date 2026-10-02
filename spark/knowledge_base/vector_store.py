# knowledge_base/vector_store.py

import json
import os
import threading
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np


_CACHE_LOCK = threading.Lock()
_MODEL_CACHE: Dict[str, Any] = {}
_VECTOR_CACHE: Dict[str, Tuple[Tuple[float, int, float, int], List[Dict], np.ndarray]] = {}
DEFAULT_VECTOR_DB_DIR = str(
    Path(__file__).resolve().parents[2] / ".local-data" / "vector_db"
)


def _env_flag(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on", "enabled"}


def _get_cached_model(model_name: str) -> Any:
    # sentence-transformers pulls in PyTorch/Transformers and may also inspect
    # TensorFlow. Import it only when a vector operation is actually requested,
    # so health checks and non-RAG endpoints stay lightweight.
    from sentence_transformers import SentenceTransformer

    with _CACHE_LOCK:
        model = _MODEL_CACHE.get(model_name)
        if model is None:
            print("[INFO] 正在加载向量模型...")
            offline = _env_flag("SPARK_VECTOR_MODEL_OFFLINE", True)
            if offline:
                os.environ.setdefault("HF_HUB_OFFLINE", "1")
                os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
            try:
                model = SentenceTransformer(model_name, local_files_only=offline)
            except TypeError:
                model = SentenceTransformer(model_name)
            _MODEL_CACHE[model_name] = model
            print("[INFO] 向量模型加载完成。")
        return model


def _file_signature(chunks_path: Path, embeddings_path: Path) -> Tuple[float, int, float, int]:
    chunks_stat = chunks_path.stat()
    embeddings_stat = embeddings_path.stat()
    return (
        chunks_stat.st_mtime,
        chunks_stat.st_size,
        embeddings_stat.st_mtime,
        embeddings_stat.st_size,
    )


class SimpleVectorStore:
    """
    简单向量库：
    1. 使用 sentence-transformers 生成文本向量
    2. 使用 numpy 保存向量
    3. 使用 json 保存文本片段
    """

    def __init__(
        self,
        db_dir: str = DEFAULT_VECTOR_DB_DIR,
        model_name: str = None,
    ):
        self.db_dir = Path(db_dir)
        self.db_dir.mkdir(parents=True, exist_ok=True)

        self.chunks_path = self.db_dir / "chunks.json"
        self.embeddings_path = self.db_dir / "embeddings.npy"

        self.model_name = model_name or os.getenv(
            "SPARK_EMBEDDING_MODEL",
            "paraphrase-multilingual-MiniLM-L12-v2",
        )
        self.model = _get_cached_model(self.model_name)

    def build(self, chunks: List[Dict]) -> None:
        """
        构建向量库
        """
        texts = [chunk["content"] for chunk in chunks]

        print(f"[INFO] 正在生成向量，共 {len(texts)} 个片段...")

        embeddings = self.model.encode(
            texts,
            normalize_embeddings=True,
            show_progress_bar=True
        )

        with open(self.chunks_path, "w", encoding="utf-8") as f:
            json.dump(chunks, f, ensure_ascii=False, indent=2)

        np.save(self.embeddings_path, embeddings)
        signature = _file_signature(self.chunks_path, self.embeddings_path)
        cache_key = str(self.db_dir.resolve())
        with _CACHE_LOCK:
            _VECTOR_CACHE[cache_key] = (signature, chunks, np.asarray(embeddings))

        print(f"[OK] 知识库构建完成，保存到：{self.db_dir}")

    def load(self):
        """
        加载已有向量库
        """
        if not self.chunks_path.exists() or not self.embeddings_path.exists():
            raise FileNotFoundError("未找到向量库，请先运行 build_knowledge_base.py")

        signature = _file_signature(self.chunks_path, self.embeddings_path)
        cache_key = str(self.db_dir.resolve())
        with _CACHE_LOCK:
            cached = _VECTOR_CACHE.get(cache_key)
            if cached and cached[0] == signature:
                return cached[1], cached[2]

        with open(self.chunks_path, "r", encoding="utf-8") as f:
            chunks = json.load(f)

        embeddings = np.load(self.embeddings_path)
        with _CACHE_LOCK:
            _VECTOR_CACHE[cache_key] = (signature, chunks, embeddings)

        return chunks, embeddings
