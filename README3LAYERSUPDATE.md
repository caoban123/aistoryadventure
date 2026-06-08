# Báo cáo Cập nhật: Tích hợp Hệ thống 3-Layer Memory (AI Story Adventure)

Tài liệu này tổng hợp toàn bộ triết lý thiết kế và các thay đổi trong mã nguồn để hiện thực hóa **Hệ thống Trí nhớ 3 Lớp (3-Layer Memory System)**. Mục đích là để AI/Dev khác có thể dễ dàng nắm bắt kiến trúc và tích hợp vào kho lưu trữ GitHub.

---

## 1. Hệ thống 3-Layer Memory là gì?

Vấn đề cốt lõi của các game nhập vai Text-based sử dụng LLM là giới hạn của Cửa sổ ngữ cảnh (Context Window). Nếu nạp quá nhiều lịch sử, AI sẽ chạy chậm, tốn chi phí và bị "loãng" thông tin. Nếu nạp ít, AI sẽ mắc bệnh "não cá vàng" (quên dữ kiện cũ) hoặc ảo giác (tự bịa ra vật phẩm, trạng thái).

Hệ thống **3-Layer Memory** giải quyết bài toán này bằng cách chia trí nhớ thành 3 tầng độc lập, bổ trợ lẫn nhau:

### 🌟 Layer 1: Sliding Window (Trí nhớ Ngắn hạn)
- **Cơ chế:** Lưu giữ và nạp trực tiếp khoảng 4-8 lượt chat (turn) gần nhất vào Prompt dưới dạng văn bản thô (Raw Text).
- **Tác dụng:** Đảm bảo độ trôi chảy (fluency) của cuộc hội thoại ngay tại thời điểm hiện tại. AI hiểu ngay lập tức hành động bạn vừa làm cách đây vài giây.

### 🌟 Layer 2: Structured Fact (Trí nhớ Trung hạn / Sự kiện Cốt lõi)
- **Cơ chế:** Chạy ngầm một Background Task để "gạn đục khơi trong". Hệ thống liên tục theo dõi và tóm tắt các sự kiện cốt lõi không thể thay đổi (như: lượng máu hiện tại, vật phẩm trong túi, chức nghiệp, vị trí hiện tại, mối quan hệ NPC) rồi đóng gói thành một cấu trúc **JSON bất biến**. Cấu trúc này được ép thẳng vào cuối System Prompt.
- **Tác dụng:** Khóa chặt tính Logic và triệt tiêu lỗi Ảo giác (Hallucination). AI buộc phải tuân theo sự thật (ví dụ: túi đang rỗng thì không thể tự lấy ra thanh gươm thần).

### 🌟 Layer 3: Vector Reranking (Trí nhớ Dài hạn / Semantic Recall)
- **Cơ chế:** Toàn bộ 100% lịch sử chơi (Raw Data) đều được băm nhỏ (chunk), mã hóa thành Vector (dải số toán học) và lưu trữ vào Vector Database (Qdrant hoặc ChromaDB). Khi người chơi nhập hành động mới, hệ thống dùng **Semantic Search (Tìm kiếm Ngữ nghĩa)** để quét Vector DB, lôi chính xác sự kiện trong quá khứ liên quan đến hành động đó và chèn vào Prompt.
- **Tác dụng:** Giải quyết bài toán nhớ lâu. Dù người chơi quay lại một địa điểm sau 100 lượt, AI vẫn có thể lôi chính xác câu thoại của trưởng làng từ 100 lượt trước ra để tiếp nối mạch truyện mà không cần nạp cả 100 lượt đó vào Prompt.

---

## 2. Thống kê các File đã sửa đổi & Xây dựng trong Hệ thống

Để triển khai kiến trúc trên, các thay đổi lớn đã được thực hiện tập trung ở tầng Backend (`app/`):

### 📁 1. `app/domain/models.py`
- **Sửa đổi:** Nâng cấp Schema của `SessionState`.
- **Chi tiết:** Thêm các trường lưu trữ cho Layer 2 như `important_facts`, `rolling_summary`, `character_summary`, `world_summary`.
- **Thêm mới:** Model `MemoryChunk` để định dạng dữ liệu trước khi đẩy vào Layer 3 (Vector DB).

### 📁 2. `app/memory/memory_service.py` (Trái tim của hệ thống)
- **Sửa đổi:** Nơi "nhạc trưởng" điều phối cả 3 Lớp trí nhớ.
- **Chi tiết:**
  - Cung cấp hàm `recent_messages()` để thực thi Layer 1.
  - Cung cấp hàm `relevant_memories()` (gọi Vector DB) để thực thi Layer 3.
  - Cung cấp hàm `refresh_summary()` (chạy bất đồng bộ/Background Task) để trích xuất và cập nhật liên tục Layer 2 vào `SessionState`.

### 📁 3. `app/memory/vector_store.py` & `qdrant_store.py` & `chroma_store.py`
- **Sửa đổi:** Triển khai Layer 3.
- **Chi tiết:** Áp dụng **Factory Pattern** cho phép hệ thống linh hoạt chuyển đổi giữa `ChromaDB` (mặc định/offline) và `Qdrant` (đám mây/production) chỉ bằng 1 nút gạt trong file `.env` (`VECTOR_DB=qdrant`). Các file này chịu trách nhiệm nhúng (embedding) Raw Text thành Vector và truy vấn (Semantic Search).

### 📁 4. `app/ai/prompt.py`
- **Sửa đổi:** Định hình lại cách giao tiếp với LLM.
- **Chi tiết:** Cập nhật các hàm `build_turn_prompt` và `build_start_prompt`. Bơm cấu trúc Layer 2 (`structured_state_json`, `rolling_summary`) vào vị trí trọng yếu cuối cùng của System Prompt với nhãn `=== STRUCTURED FACTS ===` để ép LLM phải tuân thủ nghiêm ngặt bối cảnh.

### 📁 5. `app/services/story_service.py`
- **Sửa đổi:** Tích hợp `MemoryService` vào luồng (flow) điều khiển Game.
- **Chi tiết:** 
  - Tại hàm `continue_story`, hệ thống sẽ gọi Layer 1 và Layer 3 để gom context trước khi ném cho AI.
  - Sau khi AI trả lời xong, hàm `memory.refresh_summary(session)` được đẩy vào Background Task bằng `asyncio.create_task` để cập nhật Layer 2 mà không làm người chơi bị lag hay phải chờ đợi.

### 📁 6. `app/memory/firebase_store.py`
- **Sửa đổi:** Quản lý Lưu trữ dữ liệu thô (Raw Data Persistence).
- **Chi tiết:** Đảm bảo hệ thống **Dual Storage**: Mọi nội dung text đều được lưu thô nguyên vẹn ở Firebase (nếu có mạng) hoặc thư mục `local_data/` (nếu chạy offline). Điều này cam kết 100% tài sản truyện của người chơi không bị suy hao, đáp ứng hoàn hảo cho cơ chế "Continue" từ History và chức năng "Export Book".

---

## 3. Tổng kết
Bản cập nhật này biến **AI Story Adventure** từ một hệ thống Chatbot đơn thuần thành một hệ thống **Agentic Workflow** thực thụ. Kiến trúc 3-Layer đảm bảo game hoạt động liền mạch (Seamless Memory), chặt chẽ về mặt logic nhập vai (No Hallucination) và bảo toàn tuyệt đối toàn bộ lịch sử sáng tác của người dùng.
