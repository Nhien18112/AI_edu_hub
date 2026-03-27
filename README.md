# AI Edu Hub

AI Edu Hub là hệ thống RAG cho học tập với kiến trúc tách riêng:
- Backend API: FastAPI + Qdrant
- Frontend: React (Vite)

Hệ thống tập trung vào 3 chức năng chính:
1. Upload và xử lý tài liệu (PDF/PPTX) theo nền (background job)
2. Chat theo đúng tài liệu đã chọn
3. Tạo quiz theo đúng tài liệu đã chọn

## Tính năng chính

- Chỉ hỏi đáp theo tài liệu được chọn, tránh ngữ cảnh lẫn lộn
- Xóa tài liệu trên UI sẽ xóa luôn dữ liệu vector trong Qdrant
- Theo dõi tiến trình xử lý tài liệu theo thời gian thực (queued/processing/completed/failed)
- Giao diện React hiện đại, responsive, dùng tiếng Việt có dấu

## Công nghệ

### Backend
- FastAPI
- Qdrant
- FastEmbed + reranker
- LangChain text splitter

### Frontend
- React 18
- Vite
- Nginx (serve bản build frontend trong Docker)

## Cài đặt biến môi trường

Tạo file `.env` cùng cấp với `docker-compose.yml`:

```env
GROQ_API_KEY=gsk_your_api_key_here
QDRANT_HOST=qdrant
QDRANT_PORT=6333
COLLECTION_NAME=ai_edu_collection
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
```

## Chạy bằng Docker

```bash
docker compose up -d --build
```

## Truy cập

- Frontend React: http://localhost:3000
- Backend API: http://localhost:8000
- Swagger docs: http://localhost:8000/docs

## Luồng sử dụng

1. Vào tab Upload để tải PDF/PPTX
2. Theo dõi job xử lý trong hàng đợi
3. Chọn tài liệu ở sidebar
4. Vào tab Chat để hỏi đáp theo tài liệu đó
5. Vào tab Quiz để tạo và làm bài quiz theo tài liệu đó

## Lưu ý

- Chức năng ingest từ link YouTube đã được loại bỏ để đảm bảo tính ổn định.
- Nếu bạn muốn ingest video, khuyến nghị workflow ổn định hơn là upload file transcript `.txt` hoặc `.srt` trực tiếp (có thể bổ sung trong phiên bản tiếp theo).
