import requests
import re
from pptx import Presentation
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.core.config import settings

def process_pptx(file_path: str, filename: str) -> list[dict]:
    prs = Presentation(file_path)
    text = ""
    for slide in prs.slides:
        for shape in slide.shapes:
            if hasattr(shape, "text"):
                text += shape.text + "\n"
                
    if not text.strip():
        raise ValueError(f"File slide '{filename}' hoàn toàn rỗng hoặc chỉ chứa ảnh.")

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.CHUNK_SIZE,
        chunk_overlap=settings.CHUNK_OVERLAP,
    )
    chunks = text_splitter.split_text(text)
    return [{"page_content": chunk, "metadata": {"filename": filename}} for chunk in chunks]


# --- 2. HÀM LẤY NỘI DUNG YOUTUBE BẰNG JINA READER API ---
def process_youtube(url: str) -> list[dict]:
    match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11}).*", url)
    video_id = match.group(1) if match else "Unknown"
    
    try:
        # Sử dụng Jina Reader API để "cào" sạch sẽ trang YouTube (bao gồm cả phụ đề nếu có)
        jina_url = f"https://r.jina.ai/{url}"
        
        response = requests.get(jina_url, headers={"Accept": "text/plain"}, timeout=30)
        
        if response.status_code != 200:
            raise ValueError(f"Máy chủ Jina API từ chối truy cập. Mã lỗi: {response.status_code}")
            
        text = response.text
        
        if not text or len(text.strip()) < 100:
            raise ValueError("Video này không có phụ đề, hoặc nội dung quá ngắn không đủ để AI học.")
            
    except requests.exceptions.Timeout:
        raise ValueError("Quá thời gian chờ (Timeout). Link YouTube này tải quá chậm hoặc quá dài.")
    except Exception as e:
        raise ValueError(f"Không thể lấy nội dung YouTube: {str(e)[:150]}")

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.CHUNK_SIZE,
        chunk_overlap=settings.CHUNK_OVERLAP,
    )
    chunks = text_splitter.split_text(text)
    
    return [{"page_content": chunk, "metadata": {"filename": f"YouTube Video ({video_id})"}} for chunk in chunks]