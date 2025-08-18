import chromadb
from typing import Any, Dict
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
from config import CHROMA_HOST, CHROMA_PORT, CHROMA_COLLECTION, EMBED_MODEL

client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)

existing = [c.name for c in client.list_collections()]
if CHROMA_COLLECTION in existing:
    collection = client.get_collection(name=CHROMA_COLLECTION)
else:
    collection = client.create_collection(
        name=CHROMA_COLLECTION,
        embedding_function=OpenAIEmbeddingFunction(model_name=EMBED_MODEL),
        metadata={"hnsw:space": "cosine"},
    )


def _to_primitive(meta: Dict[str, Any]):
    out: Dict[str, Any] = {}
    for k, v in meta.items():
        if isinstance(v, (list, tuple)):
            out[k] = ", ".join(map(str, v))
        elif isinstance(v, dict):
            out[k] = str(v)
        elif isinstance(v, (str, int, float, bool)) or v is None:
            out[k] = v
        else:
            out[k] = str(v)
    return out


def upsert_trace_summary(trace_id: str, summary_ko: str, meta: Dict[str, Any]):
    """요약문을 임베딩하여 trace_summary로 저장 (문서 ID = trace_id)"""
    safe_meta = _to_primitive(
        {
            "trace_id": trace_id,
            "type": "trace_summary",
            **meta,
        }
    )
    try:
        collection.delete(ids=[trace_id])
    except Exception:
        pass
    collection.add(
        ids=[trace_id],
        documents=[summary_ko],  # 요약문 자체를 임베딩
        metadatas=[safe_meta],
    )
    return trace_id
