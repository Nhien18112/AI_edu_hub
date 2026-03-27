from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from qdrant_client.models import Filter, FieldCondition, MatchValue
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
from fastembed.rerank.cross_encoder import TextCrossEncoder
from app.core.config import settings
import uuid

client = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)

embeddings = FastEmbedEmbeddings()

reranker = TextCrossEncoder(model_name="Xenova/ms-marco-MiniLM-L-6-v2")

NEW_COLLECTION_NAME = settings.COLLECTION_NAME + "_v2"

def init_collection():
    """Tạo collection nếu chưa tồn tại"""
    if not client.collection_exists(NEW_COLLECTION_NAME):
        client.create_collection(
            collection_name=NEW_COLLECTION_NAME,
            vectors_config=VectorParams(size=384, distance=Distance.COSINE),
        )

def insert_documents(documents: list[dict]):
    """Nhúng vector và lưu vào Qdrant"""
    if not documents:
        return

    init_collection()
    texts = [doc["page_content"] for doc in documents]

    # Batch embeddings giúp tăng tốc đáng kể khi tài liệu có nhiều chunk.
    try:
        vectors = list(embeddings.embed_documents(texts))
    except Exception:
        vectors = [embeddings.embed_query(text) for text in texts]

    points = []
    for doc, vector in zip(documents, vectors):
        metadata = doc.get("metadata", {})
        points.append(PointStruct(
            id=str(uuid.uuid4()),
            vector=vector,
            payload={
                "text": doc["page_content"],
                "filename": metadata.get("filename", "Unknown"),
                "document_id": metadata.get("document_id"),
                "document_type": metadata.get("document_type", "document"),
                "source_name": metadata.get("source_name", metadata.get("filename", "Unknown")),
                "uploaded_at": metadata.get("uploaded_at"),
            }
        ))
    client.upsert(collection_name=NEW_COLLECTION_NAME, points=points)

def _collection_exists() -> bool:
    return client.collection_exists(NEW_COLLECTION_NAME)


def _document_filter(document_id: str) -> Filter:
    return Filter(
        should=[
            FieldCondition(
                key="document_id",
                match=MatchValue(value=document_id),
            ),
            FieldCondition(
                key="filename",
                match=MatchValue(value=document_id),
            ),
        ]
    )


def search_documents(query: str, document_id: str, top_k: int = 3):
    """
    TÌM KIẾM 2 GIAI ĐOẠN (ADVANCED RAG)
    Giai đoạn 1: Qdrant tìm thô 15 đoạn văn bản (Broad Search)
    Giai đoạn 2: Reranker chấm điểm logic chéo và lọc ra 3 đoạn đỉnh nhất (Rerank)
    """
    
    # --- GIAI ĐOẠN 1: TÌM KIẾM THÔ BẰNG VECTOR ---
    if not _collection_exists():
        return []

    query_vector = embeddings.embed_query(query)
    initial_results = client.search(
        collection_name=NEW_COLLECTION_NAME,
        query_vector=query_vector,
        limit=15,
        query_filter=_document_filter(document_id),
    )
    if not initial_results:
        return []

    # --- GIAI ĐOẠN 2: CHẤM ĐIỂM LẠI BẰNG RERANKER ---
    texts_to_rerank = [doc.payload["text"] for doc in initial_results]
    scores = list(reranker.rerank(query, texts_to_rerank))
    
    for i, doc in enumerate(initial_results):
        doc.score = float(scores[i]) 
        
    initial_results.sort(key=lambda x: x.score, reverse=True)
    
    return initial_results[:top_k]


def search_documents_multi(query: str, document_ids: list[str], top_k: int = 8):
    """Tìm kiếm theo nhiều tài liệu đã chọn."""
    if not _collection_exists() or not document_ids:
        return []

    query_vector = embeddings.embed_query(query)

    should_conditions = []
    for doc_id in document_ids:
        should_conditions.append(FieldCondition(key="document_id", match=MatchValue(value=doc_id)))
        should_conditions.append(FieldCondition(key="filename", match=MatchValue(value=doc_id)))

    initial_results = client.search(
        collection_name=NEW_COLLECTION_NAME,
        query_vector=query_vector,
        limit=max(top_k * 4, 20),
        query_filter=Filter(should=should_conditions),
    )
    if not initial_results:
        return []

    texts_to_rerank = [doc.payload["text"] for doc in initial_results]
    scores = list(reranker.rerank(query, texts_to_rerank))

    for i, doc in enumerate(initial_results):
        doc.score = float(scores[i])

    initial_results.sort(key=lambda x: x.score, reverse=True)
    return initial_results[:top_k]


def list_documents() -> list[dict]:
    """Lấy danh sách tài liệu duy nhất theo document_id từ Qdrant."""
    if not _collection_exists():
        return []

    offset = None
    docs_by_id: dict[str, dict] = {}

    while True:
        points, next_offset = client.scroll(
            collection_name=NEW_COLLECTION_NAME,
            with_payload=True,
            with_vectors=False,
            limit=200,
            offset=offset,
        )

        for point in points:
            payload = point.payload or {}
            document_id = payload.get("document_id") or payload.get("filename")
            if not document_id or document_id in docs_by_id:
                continue

            docs_by_id[document_id] = {
                "document_id": document_id,
                "filename": payload.get("filename", "Unknown"),
                "document_type": payload.get("document_type", "document"),
                "source_name": payload.get("source_name", payload.get("filename", "Unknown")),
                "uploaded_at": payload.get("uploaded_at"),
            }

        if next_offset is None:
            break
        offset = next_offset

    return sorted(
        docs_by_id.values(),
        key=lambda item: item.get("uploaded_at") or "",
        reverse=True,
    )


def delete_document(document_id: str) -> None:
    """Xóa toàn bộ chunks thuộc 1 tài liệu khỏi Qdrant."""
    if not _collection_exists():
        return

    client.delete(
        collection_name=NEW_COLLECTION_NAME,
        points_selector=_document_filter(document_id),
        wait=True,
    )