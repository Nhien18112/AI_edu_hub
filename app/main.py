# File khởi chạy app FastAPI, cấu hình CORS cho Web CLB gọi tới
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router
import os

# Đảm bảo thư mục lưu PDF tồn tại khi chạy app
os.makedirs("data_uploads", exist_ok=True)

app = FastAPI(
    title="AI Edu Hub API", 
    description="Hệ thống RAG Backend cho Câu lạc bộ AI", 
    version="1.0.0"
)

# Cấu hình CORS (Cho phép Web Frontend ở domain khác gọi được API này)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Trong thực tế có thể thay bằng domain web của CLB
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Gắn các route vào app
app.include_router(router, prefix="/api/v1")

@app.get("/")
def read_root():
    return {
        "message": "AI Edu Hub đang chạy!", 
        "docs_url": "Truy cập /docs để mở giao diện test API (Swagger UI)"
    }