from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import List, Dict
import os
import json 

from app.services.pdf_processor import process_pdf
from app.services.qdrant_service import insert_documents, search_documents
from app.services.llm_service import generate_answer, generate_quiz 
from app.services.media_processor import process_pptx, process_youtube

router = APIRouter()

class ChatRequest(BaseModel):
    query: str
    history: List[Dict[str, str]] = []

class SearchQuery(BaseModel):
    query: str

class YouTubeRequest(BaseModel):
    url: str

class QuizRequest(BaseModel):
    topic: str 
    num_questions: int = 5 

@router.post("/chat")
async def chat(request: ChatRequest):
    try:
        search_results = search_documents(request.query)
        context = "\n\n".join([doc.payload["text"] for doc in search_results])
        answer = generate_answer(request.query, context, request.history)
        return {"answer": answer, "sources": search_results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        os.makedirs("data_uploads", exist_ok=True)
        file_path = f"data_uploads/{file.filename}"
        
        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())
        
        file_ext = file.filename.split('.')[-1].lower()
        if file_ext == 'pdf':
            documents = process_pdf(file_path, file.filename)
        elif file_ext == 'pptx':
            documents = process_pptx(file_path, file.filename)
        else:
            raise ValueError(f"Hệ thống chưa hỗ trợ định dạng .{file_ext}")
            
        insert_documents(documents)
        os.remove(file_path)
        
        return {"message": f"Đã xử lý và lưu vector thành công file {file.filename}!"}
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Lỗi xử lý file: {str(e)}")

@router.post("/upload-youtube")
async def upload_youtube(request: YouTubeRequest):
    try:
        documents = process_youtube(request.url)
        insert_documents(documents)
        return {"message": "Đã tải và xử lý phụ đề YouTube thành công!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi xử lý YouTube: {str(e)}")

@router.post("/search")
async def semantic_search(query: SearchQuery):
    try:
        results = search_documents(query.query)
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate-quiz")
async def create_quiz(request: QuizRequest):
    try:
        search_results = search_documents(request.topic, top_k=5)
        
        if not search_results:
            raise HTTPException(
                status_code=404, 
                detail="Không tìm thấy tài liệu nào trong bộ nhớ liên quan đến chủ đề này."
            )
            
        context = "\n\n".join([doc.payload["text"] for doc in search_results])
        
        quiz_json_string = generate_quiz(context, request.num_questions)
        
        try:
            quiz_data = json.loads(quiz_json_string)
            return quiz_data
        except json.JSONDecodeError:
            raise HTTPException(status_code=500, detail="AI không trả về đúng định dạng JSON.")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi tạo trắc nghiệm: {str(e)}")