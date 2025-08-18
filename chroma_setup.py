# import chromadb
# from typing import Any, Dict
# from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
# from config import CHROMA_HOST, CHROMA_PORT, CHROMA_COLLECTION, EMBED_MODEL

# client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)

# existing = [c.name for c in client.list_collections()]
# if CHROMA_COLLECTION in existing:
#     collection = client.get_collection(name=CHROMA_COLLECTION)
# else:
#     collection = client.create_collection(
#         name=CHROMA_COLLECTION,
#         embedding_function=OpenAIEmbeddingFunction(model_name=EMBED_MODEL),
#         metadata={"hnsw:space": "cosine"},
#     )


# def _to_primitive(meta: Dict[str, Any]):
#     out: Dict[str, Any] = {}
#     for k, v in meta.items():
#         if isinstance(v, (list, tuple)):
#             out[k] = ", ".join(map(str, v))
#         elif isinstance(v, dict):
#             out[k] = str(v)
#         elif isinstance(v, (str, int, float, bool)) or v is None:
#             out[k] = v
#         else:
#             out[k] = str(v)
#     return out


# def upsert_trace_summary(trace_id: str, summary_ko: str, meta: Dict[str, Any]):
#     """요약문을 임베딩하여 trace_summary로 저장 (문서 ID = trace_id)"""
#     safe_meta = _to_primitive(
#         {
#             "trace_id": trace_id,
#             "type": "trace_summary",
#             **meta,
#         }
#     )
#     try:
#         collection.delete(ids=[trace_id])
#     except Exception:
#         pass
#     collection.add(
#         ids=[trace_id],
#         documents=[summary_ko],  # 요약문 자체를 임베딩
#         metadatas=[safe_meta],
#     )
#     return trace_id

# chroma_setup.py (교체/패치용)
import os
import chromadb
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction

CHROMA_HOST = os.getenv("CHROMA_HOST", "127.0.0.1")
CHROMA_PORT = int(os.getenv("CHROMA_PORT", "8000"))
CHROMA_COLLECTION = os.getenv("CHROMA_COLLECTION", "my_log_db")
EMBED_MODEL = os.getenv("EMBED_MODEL", "text-embedding-3-small")
OPENAI_KEY = os.getenv("CHROMA_OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
CHROMA_DIR = os.getenv("CHROMA_DIR", "./.chroma")  # 로컬 저장 경로


def _make_embed_fn():
    if not OPENAI_KEY:
        print(
            "[WARN] OPENAI_API_KEY/CHROMA_OPENAI_API_KEY가 없어 임베딩 없이 동작합니다."
        )
        return None
    return OpenAIEmbeddingFunction(api_key=OPENAI_KEY, model_name=EMBED_MODEL)


def _connect_client():
    # 1) 먼저 HttpClient 시도
    try:
        client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
        # 서버 살아있는지 ping
        client.heartbeat()
        print(f"[CHROMA] HttpClient connected -> http://{CHROMA_HOST}:{CHROMA_PORT}")
        return client
    except Exception as e:
        print(
            f"[CHROMA] HttpClient 연결 실패: {e}\n[CHROMA] PersistentClient로 fallback: {CHROMA_DIR}"
        )
        # 2) 실패 시 로컬 파일 기반으로 전환
        from chromadb import PersistentClient

        os.makedirs(CHROMA_DIR, exist_ok=True)
        return PersistentClient(path=CHROMA_DIR)


client = _connect_client()
embed_fn = _make_embed_fn()

# 컬렉션 준비
names = [c.name for c in client.list_collections()]
if CHROMA_COLLECTION in names:
    collection = client.get_collection(CHROMA_COLLECTION, embedding_function=embed_fn)
else:
    collection = client.create_collection(
        name=CHROMA_COLLECTION,
        embedding_function=embed_fn,
        metadata={"hnsw:space": "cosine"},
    )


def upsert_trace_summary(doc_id: str, text: str, metadata: dict):
    # Chroma는 metadata value 타입이 str/int/float/bool/None 여야 함
    safe_meta = {}
    for k, v in (metadata or {}).items():
        if isinstance(v, (str, int, float, bool)) or v is None:
            safe_meta[k] = v
        else:
            safe_meta[k] = str(v)
    # upsert
    collection.upsert(documents=[text], metadatas=[safe_meta], ids=[doc_id])
    return doc_id
