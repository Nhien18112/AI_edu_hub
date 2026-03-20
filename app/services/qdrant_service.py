from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
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
    init_collection()
    points = []
    for doc in documents:
        vector = embeddings.embed_query(doc["page_content"])
        points.append(PointStruct(
            id=str(uuid.uuid4()),
            vector=vector,
            payload={"text": doc["page_content"], "filename": doc["metadata"]["filename"]}
        ))
    client.upsert(collection_name=NEW_COLLECTION_NAME, points=points)

def search_documents(query: str, top_k: int = 3):
    """
    TÌM KIẾM 2 GIAI ĐOẠN (ADVANCED RAG)
    Giai đoạn 1: Qdrant tìm thô 15 đoạn văn bản (Broad Search)
    Giai đoạn 2: Reranker chấm điểm logic chéo và lọc ra 3 đoạn đỉnh nhất (Rerank)
    """
    
    # --- GIAI ĐOẠN 1: TÌM KIẾM THÔ BẰNG VECTOR ---
    query_vector = embeddings.embed_query(query)
    initial_results = client.search(
        collection_name=NEW_COLLECTION_NAME,
        query_vector=query_vector,
        limit=15 
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