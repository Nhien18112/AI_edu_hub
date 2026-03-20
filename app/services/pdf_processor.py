import fitz  
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.core.config import settings
import pytesseract
from pdf2image import convert_from_path
import os

def process_pdf(file_path: str, filename: str) -> list[dict]:
    doc = fitz.open(file_path)
    text = ""

    for page_num in range(len(doc)):
        page = doc[page_num]
        page_text = page.get_text().strip()

        if page_text:
            text += page_text + "\n"
        else:
            try:
                
                images = convert_from_path(file_path, first_page=page_num+1, last_page=page_num+1)
                if images:
                    ocr_text = pytesseract.image_to_string(images[0], lang='vie+eng')
                    text += ocr_text + "\n"
            except Exception as e:
                print(f"Lỗi OCR ở trang {page_num + 1}: {e}")

    if not text.strip():
        raise ValueError(f"Tài liệu '{filename}' hoàn toàn rỗng hoặc ảnh quá mờ, không thể đọc được nội dung.")
        
    # Chunking
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.CHUNK_SIZE,
        chunk_overlap=settings.CHUNK_OVERLAP,
        separators=["\n\n", "\n", " ", ""]
    )
    chunks = text_splitter.split_text(text)
    
    documents = [{"page_content": chunk, "metadata": {"filename": filename}} for chunk in chunks]
    return documents