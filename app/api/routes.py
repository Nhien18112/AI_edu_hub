from fastapi import APIRouter, UploadFile, File, HTTPException, status
from pydantic import BaseModel
from typing import List, Dict, Any
import os
import json
import threading
from uuid import uuid4
from datetime import datetime, timezone

from app.services.pdf_processor import process_pdf
from app.services.qdrant_service import (
    insert_documents,
    search_documents,
    search_documents_multi,
    list_documents,
    delete_document,
)
from app.services.llm_service import generate_answer, generate_quiz, generate_learning_path, generate_mindmap
from app.services.media_processor import process_pptx

router = APIRouter()


class ChatRequest(BaseModel):
    query: str
    document_id: str
    history: List[Dict[str, str]] = []


class SearchQuery(BaseModel):
    query: str
    document_id: str


class QuizRequest(BaseModel):
    topic: str
    document_id: str
    num_questions: int = 5


class LearningPathRequest(BaseModel):
    goal: str
    document_ids: List[str]
    level_count: int = 6


class MindmapRequest(BaseModel):
    topic: str
    document_ids: List[str]


class RoadmapQuizRequest(BaseModel):
    topic: str
    document_ids: List[str]
    num_questions: int = 5


jobs_lock = threading.Lock()
processing_jobs: Dict[str, Dict[str, Any]] = {}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _create_job(source_name: str) -> dict:
    job_id = f"job-{uuid4().hex[:10]}"
    job = {
        "job_id": job_id,
        "source_name": source_name,
        "status": "queued",
        "progress": 0,
        "message": "Đã nhận yêu cầu, chuẩn bị xử lý.",
        "created_at": _now_iso(),
        "updated_at": _now_iso(),
        "document": None,
        "error": None,
    }
    with jobs_lock:
        processing_jobs[job_id] = job
    return job


def _update_job(job_id: str, **updates) -> None:
    with jobs_lock:
        if job_id not in processing_jobs:
            return
        processing_jobs[job_id].update(updates)
        processing_jobs[job_id]["updated_at"] = _now_iso()


def _get_job(job_id: str) -> dict:
    with jobs_lock:
        job = processing_jobs.get(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Không tìm thấy job xử lý.")
        return job


def _attach_document_metadata(
    documents: list[dict],
    *,
    document_id: str,
    source_name: str,
    filename: str,
) -> list[dict]:
    uploaded_at = _now_iso()
    for doc in documents:
        metadata = doc.setdefault("metadata", {})
        metadata.update(
            {
                "document_id": document_id,
                "document_type": "document",
                "source_name": source_name,
                "filename": filename,
                "uploaded_at": uploaded_at,
            }
        )
    return documents


def _serialize_sources(search_results):
    serialized = []
    for doc in search_results:
        payload = doc.payload or {}
        serialized.append(
            {
                "score": float(getattr(doc, "score", 0.0)),
                "payload": {
                    "text": payload.get("text", ""),
                    "filename": payload.get("filename", "Unknown"),
                    "document_id": payload.get("document_id"),
                    "document_type": payload.get("document_type", "document"),
                    "source_name": payload.get("source_name", payload.get("filename", "Unknown")),
                },
            }
        )
    return serialized


def _build_grounded_context(search_results, *, max_chunks: int = 14, max_chars_per_chunk: int = 1200) -> str:
    lines = []
    for idx, doc in enumerate(search_results[:max_chunks], start=1):
        payload = doc.payload or {}
        text = (payload.get("text") or "").strip()
        if not text:
            continue

        compact_text = " ".join(text.split())
        excerpt = compact_text[:max_chars_per_chunk]
        if len(compact_text) > max_chars_per_chunk:
            excerpt += " ..."

        filename = payload.get("filename", "Unknown")
        document_id = payload.get("document_id", "Unknown")
        score = float(getattr(doc, "score", 0.0))

        lines.append(
            f"[Nguồn {idx}] file={filename}; document_id={document_id}; relevance={score:.4f}\n{excerpt}"
        )

    return "\n\n".join(lines)


def _process_document_job(job_id: str, file_path: str, filename: str, file_ext: str) -> None:
    try:
        _update_job(job_id, status="processing", progress=15, message="Đang trích xuất nội dung tài liệu.")

        if file_ext == "pdf":
            documents = process_pdf(file_path, filename)
        else:
            documents = process_pptx(file_path, filename)

        document_id = f"doc-{uuid4().hex[:12]}"
        documents = _attach_document_metadata(
            documents,
            document_id=document_id,
            source_name=filename,
            filename=filename,
        )

        _update_job(job_id, progress=70, message="Đang nhúng vector và ghi vào bộ nhớ.")
        insert_documents(documents)

        _update_job(
            job_id,
            status="completed",
            progress=100,
            message="Xử lý hoàn tất.",
            document={
                "document_id": document_id,
                "document_type": "document",
                "source_name": filename,
                "filename": filename,
            },
        )
    except Exception as exc:
        _update_job(
            job_id,
            status="failed",
            progress=100,
            message="Xử lý thất bại.",
            error=str(exc),
        )
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)


@router.post("/chat")
async def chat(request: ChatRequest):
    try:
        search_results = search_documents(request.query, document_id=request.document_id)
        if not search_results:
            raise HTTPException(
                status_code=404,
                detail="Không tìm thấy nội dung trong tài liệu đã chọn. Hãy kiểm tra lại tài liệu hoặc tải lên lại.",
            )

        context = "\n\n".join([doc.payload["text"] for doc in search_results])
        answer = generate_answer(request.query, context, request.history)
        return {"answer": answer, "sources": _serialize_sources(search_results)}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/upload", status_code=status.HTTP_202_ACCEPTED)
async def upload_file(file: UploadFile = File(...)):
    os.makedirs("data_uploads", exist_ok=True)

    file_ext = file.filename.split(".")[-1].lower() if "." in file.filename else ""
    if file_ext not in {"pdf", "pptx"}:
        raise HTTPException(status_code=400, detail=f"Hệ thống chưa hỗ trợ định dạng .{file_ext}")

    job = _create_job(source_name=file.filename)
    file_path = os.path.join("data_uploads", f"{job['job_id']}_{file.filename}")

    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())

    thread = threading.Thread(
        target=_process_document_job,
        args=(job["job_id"], file_path, file.filename, file_ext),
        daemon=True,
    )
    thread.start()

    return {
        "message": "Đã nhận file và bắt đầu xử lý nền. Bạn có thể tiếp tục thao tác trên dashboard.",
        "job": job,
    }


@router.get("/jobs/{job_id}")
async def get_job_status(job_id: str):
    return _get_job(job_id)


@router.get("/jobs")
async def get_jobs():
    with jobs_lock:
        jobs = sorted(
            processing_jobs.values(),
            key=lambda item: item.get("created_at") or "",
            reverse=True,
        )
    return {"jobs": jobs}


@router.post("/search")
async def semantic_search(query: SearchQuery):
    try:
        results = search_documents(query.query, document_id=query.document_id)
        return {"results": _serialize_sources(results)}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/generate-quiz")
async def create_quiz(request: QuizRequest):
    try:
        search_results = search_documents(request.topic, document_id=request.document_id, top_k=5)

        if not search_results:
            raise HTTPException(
                status_code=404,
                detail="Không tìm thấy nội dung phù hợp trong tài liệu đã chọn.",
            )

        context = "\n\n".join([doc.payload["text"] for doc in search_results])
        quiz_json_string = generate_quiz(context, request.num_questions)

        try:
            quiz_data = json.loads(quiz_json_string)
            return quiz_data
        except json.JSONDecodeError:
            raise HTTPException(status_code=500, detail="AI không trả về đúng định dạng JSON.")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Lỗi tạo trắc nghiệm: {str(exc)}")


@router.post("/generate-learning-path")
async def create_learning_path(request: LearningPathRequest):
    try:
        if not request.document_ids:
            raise HTTPException(status_code=400, detail="Bạn cần chọn ít nhất một tài liệu để tạo lộ trình.")

        search_results = search_documents_multi(
            query=request.goal,
            document_ids=request.document_ids,
            top_k=max(8, request.level_count + 2),
        )
        if not search_results:
            raise HTTPException(
                status_code=404,
                detail="Không tìm thấy nội dung phù hợp trong các tài liệu đã chọn.",
            )

        context = "\n\n".join([doc.payload["text"] for doc in search_results])
        path_json_string = generate_learning_path(
            context=context,
            goal=request.goal,
            level_count=request.level_count,
        )

        try:
            return json.loads(path_json_string)
        except json.JSONDecodeError:
            raise HTTPException(status_code=500, detail="AI không trả về đúng định dạng JSON cho lộ trình.")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Lỗi tạo lộ trình học: {str(exc)}")


@router.post("/generate-roadmap-quiz")
async def create_roadmap_quiz(request: RoadmapQuizRequest):
    try:
        if not request.document_ids:
            raise HTTPException(status_code=400, detail="Bạn cần chọn ít nhất một tài liệu để tạo quiz theo chặng.")

        search_results = search_documents_multi(
            query=request.topic,
            document_ids=request.document_ids,
            top_k=10,
        )

        if not search_results:
            raise HTTPException(
                status_code=404,
                detail="Không tìm thấy nội dung phù hợp trong các tài liệu đã chọn.",
            )

        context = "\n\n".join([doc.payload["text"] for doc in search_results])
        quiz_json_string = generate_quiz(context, request.num_questions)

        try:
            quiz_data = json.loads(quiz_json_string)
            return quiz_data
        except json.JSONDecodeError:
            raise HTTPException(status_code=500, detail="AI không trả về đúng định dạng JSON.")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Lỗi tạo quiz theo chặng: {str(exc)}")


@router.post("/generate-mindmap")
async def create_mindmap(request: MindmapRequest):
    try:
        if not request.topic.strip():
            raise HTTPException(status_code=400, detail="Bạn cần nhập chủ đề để tạo mindmap.")

        if not request.document_ids:
            raise HTTPException(status_code=400, detail="Bạn cần chọn ít nhất một tài liệu để tạo mindmap.")

        collected_results = []
        for doc_id in request.document_ids:
            collected_results.extend(
                search_documents(
                    query=request.topic,
                    document_id=doc_id,
                    top_k=6,
                )
            )

        if not collected_results:
            collected_results = search_documents_multi(
                query=request.topic,
                document_ids=request.document_ids,
                top_k=12,
            )

        deduped = []
        seen_keys = set()
        for doc in collected_results:
            payload = doc.payload or {}
            key = (
                payload.get("document_id"),
                payload.get("filename"),
                payload.get("text", "")[:240],
            )
            if key in seen_keys:
                continue
            seen_keys.add(key)
            deduped.append(doc)

        deduped.sort(key=lambda item: float(getattr(item, "score", 0.0)), reverse=True)
        search_results = deduped[:14]

        if not search_results:
            raise HTTPException(
                status_code=404,
                detail="Không tìm thấy nội dung phù hợp trong các tài liệu đã chọn.",
            )

        context = _build_grounded_context(search_results)
        map_json_string = generate_mindmap(
            context=context,
            topic=request.topic,
            selected_document_ids=request.document_ids,
        )

        try:
            return json.loads(map_json_string)
        except json.JSONDecodeError:
            raise HTTPException(status_code=500, detail="AI không trả về đúng định dạng JSON cho mindmap.")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Lỗi tạo mindmap: {str(exc)}")


@router.get("/documents")
async def get_documents():
    try:
        return {"documents": list_documents()}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Lỗi lấy danh sách tài liệu: {str(exc)}")


@router.delete("/documents/{document_id}")
async def remove_document(document_id: str):
    try:
        existing = list_documents()
        found = any(doc.get("document_id") == document_id for doc in existing)
        if not found:
            raise HTTPException(status_code=404, detail="Không tìm thấy tài liệu để xóa.")

        delete_document(document_id)
        return {"message": "Đã xóa tài liệu khỏi hệ thống và bộ nhớ LLM.", "document_id": document_id}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Lỗi xóa tài liệu: {str(exc)}")
