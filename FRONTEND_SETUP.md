# Setup Frontend React mới

Đã xây dựng lại frontend bằng **React + Vite** thay vì Streamlit.

## Cấu trúc mới

```
frontend/
├── src/
│   ├── components/          # 4 component chính
│   │   ├── Header.jsx       # Header
│   │   ├── ChatSection.jsx  # Chat AI
│   │   ├── UploadSection.jsx # Upload file/YouTube
│   │   └── SearchSection.jsx # Tìm kiếm
│   ├── styles/
│   │   ├── index.css        # Reset, global styles
│   │   └── App.css          # Component styles (gọn, ~400 lines)
│   ├── App.jsx              # Main component
│   └── main.jsx             # Entry point
├── Dockerfile               # Multi-stage build (nhẹ, ~50MB)
├── nginx.conf              # Serve + proxy API
└── package.json            # Dependencies
```

## Giao diện

**Tính chất:**
- ✅ Đơn giản, sạch sẽ
- ✅ Không dùng icon
- ✅ Responsive (mobile/tablet/desktop)
- ✅ Purple theme (#667eea)
- ✅ 3 tab chính: Chat | Upload | Search

**Component:**
1. **Header** - Logo + title
2. **Tab Navigation** - Chuyển giữa 3 section
3. **ChatSection** - Chat, message history
4. **UploadSection** - File upload + YouTube URL
5. **SearchSection** - Search & results

## Setup Development

```bash
cd frontend
npm install
npm run dev
```

Truy cập: http://localhost:3000

## Production - Docker

```bash
# Build image
docker compose build --no-cache frontend

# Run all services
docker compose up -d

# Check logs
docker compose logs -f frontend
```

3 services sẽ chạy:
- `localhost:3000` - Frontend (React)
- `localhost:8000` - Backend (FastAPI)
- `localhost:6333` - Qdrant DB

## CSS Structure

CSS được tổ chức gọn gàng:
- **index.css** - Global reset, basic styles (~50 lines)
- **App.css** - React component styles (~400 lines)

Không dùng:
- ❌ Icon library
- ❌ Gradient animation
- ❌ Heavy framework (Bootstrap, Tailwind)
- ✅ Pure CSS Grid/Flexbox

## Features

### 1. Chat Tab
- Message history
- Streaming message loading animation
- Disable send button khi loading

### 2. Upload Tab
- Drag & drop file upload
- YouTube URL input
- Progress indicator
- Success/error messages

### 3. Search Tab
- Search input
- Results display
- Loading state
- Empty state

## API Endpoints

Frontend gọi tới:
- `POST /api/v1/chat` - Chat
- `POST /api/v1/upload` - File upload
- `POST /api/v1/upload-youtube` - YouTube
- `POST /api/v1/search` - Search

(Nginx proxy từ `/api` → `backend:8000`)

## Notes

- Streamlit(`app.py`) có thể xóa được nếu không dùng nữa
- Frontend hoàn toàn tách biệt từ backend (API call)
- Build Docker tối ưu: ~50MB image (2 stage build)
