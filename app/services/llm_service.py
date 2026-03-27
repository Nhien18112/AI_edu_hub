from groq import Groq
from app.core.config import settings
import json

client = Groq(api_key=settings.GROQ_API_KEY)

def generate_answer(query: str, context: str, history: list) -> str:
    system_prompt = f"""Bạn là một gia sư AI xuất sắc và thân thiện của Câu lạc bộ.
Nhiệm vụ của bạn là đọc tài liệu được cung cấp và trả lời câu hỏi của sinh viên một cách tự nhiên, dễ hiểu, có logic phân tích rõ ràng. 
Hãy tổng hợp thông tin thay vì chỉ copy y nguyên. Nếu tài liệu hoàn toàn không chứa thông tin để trả lời, hãy trung thực nói: "Xin lỗi, tài liệu hiện tại không đề cập đến vấn đề này."

TÀI LIỆU CUNG CẤP:
{context}
"""
    
    messages = [{"role": "system", "content": system_prompt}]
    
    if history:
        for msg in history[-4:]: 
            messages.append({"role": msg["role"], "content": msg["content"]})
            
    messages.append({"role": "user", "content": query})
    
    try:
        chat_completion = client.chat.completions.create(
            messages=messages,
            model="llama-3.3-70b-versatile", 
            temperature=0.3, 
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        return f"Lỗi từ Groq API: {str(e)}"

def generate_quiz(context: str, num_questions: int = 5) -> str:
    system_prompt = f"""Bạn là một giáo sư chuyên thiết kế bài tập trắc nghiệm.
Nhiệm vụ của bạn là đọc tài liệu dưới đây và tạo ra {num_questions} câu hỏi trắc nghiệm.
BẮT BUỘC trả về kết quả dưới định dạng JSON object. KHÔNG thêm bất kỳ lời chào hỏi hay văn bản giải thích nào khác ngoài chuỗi JSON.
Cấu trúc JSON BẮT BUỘC như sau:
{{
  "quiz": [
    {{
      "question": "Nội dung câu hỏi 1?",
      "options": ["A. Lựa chọn 1", "B. Lựa chọn 2", "C. Lựa chọn 3", "D. Lựa chọn 4"],
      "answer": "A. Lựa chọn 1",
      "explanation": "Giải thích ngắn gọn tại sao đây là đáp án đúng."
    }}
  ]
}}

TÀI LIỆU CUNG CẤP CHUYÊN SÂU:
{context}
"""
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "Hãy tạo bài trắc nghiệm bằng JSON ngay bây giờ dựa trên tài liệu trên."}
    ]
    
    try:
        chat_completion = client.chat.completions.create(
            messages=messages,
            model="llama-3.3-70b-versatile",
            temperature=0.1, 
            response_format={"type": "json_object"}
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        error_json = {"quiz": [], "error": f"Lỗi từ Groq API: {str(e)}"}
        return json.dumps(error_json, ensure_ascii=False)


def generate_learning_path(context: str, goal: str, level_count: int = 6) -> str:
        system_prompt = f"""Bạn là kiến trúc sư học tập chuyên thiết kế lộ trình học dạng game hóa.
Mục tiêu: tạo lộ trình học theo phong cách từng chặng như Duolingo (nhưng nội dung học thuật), dựa hoàn toàn trên tài liệu đã cung cấp.

Yêu cầu:
- Trả về JSON object hợp lệ, không có văn bản ngoài JSON.
- Số chặng (levels) đúng bằng {level_count}.
- Mỗi chặng có: mã chặng, tên chặng, mục tiêu, danh sách bài học, bài luyện tập, tiêu chí qua chặng.
- Các bài học phải tăng dần độ khó.
- Viết tiếng Việt rõ ràng, ngắn gọn, hành động cụ thể.

Schema JSON bắt buộc:
{{
    "goal": "...",
    "overview": "...",
    "levels": [
        {{
            "level": 1,
            "title": "...",
            "objective": "...",
            "lessons": ["...", "..."],
            "practice": "...",
            "pass_criteria": "..."
        }}
    ],
    "capstone": "..."
}}

Mục tiêu người học:
{goal}

Tài liệu nguồn:
{context}
"""

        messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": "Hãy tạo lộ trình học ngay bây giờ."},
        ]

        try:
                chat_completion = client.chat.completions.create(
                        messages=messages,
                        model="llama-3.3-70b-versatile",
                        temperature=0.2,
                        response_format={"type": "json_object"},
                )
                return chat_completion.choices[0].message.content
        except Exception as e:
                error_json = {"goal": goal, "overview": "", "levels": [], "capstone": "", "error": str(e)}
                return json.dumps(error_json, ensure_ascii=False)


def generate_mindmap(context: str, topic: str) -> str:
        system_prompt = f"""Bạn là chuyên gia xây dựng mindmap học tập.
Nhiệm vụ: từ tài liệu nguồn, tạo mindmap rõ ràng theo chủ đề người dùng yêu cầu.

Yêu cầu bắt buộc:
- Chỉ trả về JSON object hợp lệ, không thêm văn bản ngoài JSON.
- Viết tiếng Việt có dấu đầy đủ.
- Cấu trúc mindmap dễ đọc, phân cấp từ tổng quan đến chi tiết.

Schema JSON bắt buộc:
{{
    "topic": "...",
    "summary": "...",
    "branches": [
        {{
            "title": "...",
            "details": ["...", "..."],
            "sub_branches": [
                {{
                    "title": "...",
                    "details": ["...", "..."]
                }}
            ]
        }}
    ]
}}

Chủ đề:
{topic}

Tài liệu nguồn:
{context}
"""

        messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": "Hãy tạo mindmap ngay bây giờ theo đúng schema JSON."},
        ]

        try:
                chat_completion = client.chat.completions.create(
                        messages=messages,
                        model="llama-3.3-70b-versatile",
                        temperature=0.2,
                        response_format={"type": "json_object"},
                )
                return chat_completion.choices[0].message.content
        except Exception as e:
                error_json = {"topic": topic, "summary": "", "branches": [], "error": str(e)}
                return json.dumps(error_json, ensure_ascii=False)