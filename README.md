
Backend thì chạy bằng docker 
Sau đó chạy FE bằng lệnh: 
streamlit run frontend/app.py


# 📚 AI Edu Hub - Trợ lý Học tập Thông minh (Advanced RAG System)

AI Edu Hub là một nền tảng Công nghệ Giáo dục (EdTech) mã nguồn mở, sử dụng kiến trúc **Advanced RAG (Retrieval-Augmented Generation)**. Dự án cho phép sinh viên tải lên các tài liệu học tập đa phương tiện (PDF, Slide, Video YouTube) và tương tác trực tiếp với Trợ lý AI để giải đáp thắc mắc, tóm tắt kiến thức, và tự động sinh bài tập trắc nghiệm ôn tập.

---

## ✨ Tính năng nổi bật

* 📄 **Đọc hiểu Đa phương tiện:** Hỗ trợ trích xuất văn bản từ file PDF, bài giảng PowerPoint (PPTX), và đặc biệt là bóc băng phụ đề tự động từ Video YouTube (thông qua Jina Reader API).
* 🧠 **Chatbot AI Siêu việt:** Tích hợp mô hình ngôn ngữ lớn Llama 3 (70 tỷ tham số) qua Groq API, mang lại tốc độ phản hồi gần như tức thời và khả năng lập luận logic sắc bén.
* 🎯 **Tìm kiếm Chính xác Tuyệt đối (Advanced RAG):** * *Giai đoạn 1 (Broad Search):* Tìm kiếm ngữ nghĩa thô (Semantic Search) bằng Vector Database **Qdrant** siêu tốc.
    * *Giai đoạn 2 (Reranking):* Sử dụng mô hình **Cross-Encoder** (`ms-marco-MiniLM-L-6-v2` qua `fastembed`) chạy hoàn toàn trên CPU để chấm điểm logic chéo, loại bỏ kết quả rác và đưa ra câu trả lời chuẩn xác nhất.
* 📝 **Tự động Sinh Trắc Nghiệm:** Sử dụng kỹ thuật Prompt Engineering (JSON Mode) để ép AI tự động đọc tài liệu và soạn ra các bài kiểm tra trắc nghiệm tương tác trực tiếp trên giao diện.
* 🎨 **Giao diện Hiện đại:** Xây dựng bằng Streamlit với các hiệu ứng CSS tùy chỉnh, mang lại trải nghiệm UX/UI chuyên nghiệp như các sản phẩm thương mại.

---

## 🛠️ Công nghệ sử dụng (Tech Stack)

**Backend:**
* [FastAPI](https://fastapi.tiangolo.com/): Khung web server hiệu năng cao.
* [Qdrant](https://qdrant.tech/): Cơ sở dữ liệu Vector (Vector Database) lưu trữ trí nhớ dài hạn.
* [FastEmbed](https://qdrant.github.io/fastembed/): Thư viện nhúng Vector và Reranking siêu nhẹ, tối ưu cho CPU.
* [LangChain](https://www.langchain.com/): Tiện ích chia nhỏ văn bản (Text Splitter).

**Frontend:**
* [Streamlit](https://streamlit.io/): Framework xây dựng giao diện tương tác tức thì bằng Python.

**AI Models:**
* **LLM:** `llama-3.3-70b-versatile` (via Groq API).
* **Embeddings:** `fast-bge-small-en-v1.5` (mặc định của FastEmbed).
* **Reranker:** `Xenova/ms-marco-MiniLM-L-6-v2`.

**DevOps:**
* [Docker & Docker Compose](https://www.docker.com/): Đóng gói và triển khai ứng dụng độc lập.

---

## 🚀 Hướng dẫn Cài đặt & Chạy dự án (Local)

### 1. Yêu cầu hệ thống
* Cài đặt sẵn [Docker Desktop](https://www.docker.com/products/docker-desktop/).
* Có tài khoản và API Key của [Groq](https://console.groq.com/keys) (Miễn phí).

### 2. Cài đặt biến môi trường
Tạo một file có tên `.env` ở thư mục gốc của dự án (ngang hàng với `docker-compose.yml`) và thêm API Key của bạn vào:

```
env
GROQ_API_KEY=gsk_your_api_key_here...
QDRANT_HOST=qdrant
QDRANT_PORT=6333
COLLECTION_NAME=ai_edu_collection
CHUNK_SIZE=1000
CHUNK_OVERLAP=200

3. Khởi chạy hệ thống bằng Docker
Mở Terminal tại thư mục dự án và gõ lệnh sau để tải các model và khởi động toàn bộ hệ thống:

docker compose up -d --build


```

ai-edu-hub/
├── app/
│   ├── api/          # Định tuyến các API (routes, dependencies)
│   ├── core/         # Cấu hình biến môi trường (config)
│   ├── models/       # Định nghĩa Pydantic schemas
│   └── services/     # Logic xử lý cốt lõi (PDF, YouTube, Qdrant, LLM)
├── frontend/
│   └── app.py        # Giao diện Streamlit & Custom CSS
├── data_uploads/     # Thư mục tạm chứa file người dùng tải lên
├── qdrant_data/      # Thư mục map volume lưu trữ Vector Database
├── .env              # File bảo mật chứa API Key
├── docker-compose.yml# File điều phối các container
├── Dockerfile        # File đóng gói Backend
└── requirements.txt  # Danh sách thư viện Python
