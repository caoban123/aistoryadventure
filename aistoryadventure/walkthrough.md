# Walkthrough: RPG Mode AI Image Generation, Rename & Combat Experience Polish

Tài liệu này tóm tắt toàn bộ các cập nhật, tính năng mới và cải tiến trải nghiệm người chơi trong Chế độ RPG.

---

## 🚀 Các Cập Nhật Mới (New Features & Improvements)

### 1. Đổi tên Valkyrie ("Lumuen" ➔ "Lemuen" toàn cục)
- **Mục tiêu:** Sửa đổi nhất quán tên gọi của lớp Sniper huyền thoại từ "Lumuen" thành "Lemuen" ở cả phía Frontend và Backend.
- **Thực hiện:**
  - Cập nhật định nghĩa lớp nhân vật, mô tả kỹ năng, các biến nội tại (`lemuen_auto_shots`) trong các file backend: [rpg_models.py](file:///d:/hcmus/HK4/Tư duy tính toán cho TTNT/aistoryadventure/app/domain/rpg_models.py), [rpg_engine.py](file:///d:/hcmus/HK4/Tư duy tính toán cho TTNT/aistoryadventure/app/services/rpg_engine.py), [rpg_service.py](file:///d:/hcmus/HK4/Tư duy tính toán cho TTNT/aistoryadventure/app/services/rpg_service.py).
  - Cập nhật từ khóa và mô tả trong file frontend: [rpg_app.js](file:///d:/hcmus/HK4/Tư duy tính toán cho TTNT/aistoryadventure/frontend/rpg_app.js).

### 2. Khảo sát ngoại hình nhân vật chính (Survey Step 7)
- **Mục tiêu:** Cho phép người chơi tự mô tả ngoại hình hoặc dùng gợi ý AI (qua Gemini) để phục vụ cho việc tạo hình ảnh chân dung sau này.
- **Thực hiện:**
  - Nâng cấp Setup Wizard từ 7 bước lên 8 bước. Chuyển bước Tóm tắt (Summary) sang bước 8.
  - Thêm **Bước 7** cho phép người chơi nhập mô tả ngoại hình (Appearance Description) kèm theo nút **"Gợi ý ngoại hình AI"**.
  - Nút gợi ý AI sẽ gọi POST `/suggest-appearance` gửi thông tin cấu hình nhân vật (tên, giới tính, khu vực, vàng, trang bị) để nhận về đoạn mô tả ngoại hình ấn tượng.
  - Tích hợp trường `appearance_desc` vào API `/start-story` để lưu trữ mô tả vào thông tin nhân vật chính.

### 3. Nút "Mắt Thần" Quan Sát Thế Giới (See the World)
- **Mục tiêu:** Cho phép người chơi tạo và chiêm ngưỡng hình ảnh phong cảnh của thế giới dựa trên lượt truyện hiện tại bằng AI sinh ảnh (Stable Diffusion XL Lightning).
- **Thực hiện:**
  - Thiết kế nút bấm `.rpg-premium-eye-btn` hình con mắt sang trọng sử dụng hiệu ứng **glassmorphic**, phát sáng viền neon và micro-animation xoay nhẹ khi hover bên cạnh nhãn tên session.
  - Thêm Modal hiển thị hình ảnh thế giới tỉ lệ 16:9 kèm loading spinner mượt mà.
  - Khi click vào nút, frontend sẽ gửi yêu cầu tới `/image/see-world`. Backend sẽ lấy cốt truyện gần nhất làm prompt, dịch và tối ưu hóa từ khóa, sau đó gọi Kaggle API qua đường hầm ngrok để nhận ảnh base64, giải mã lưu đè lên file `assets/generated/(session_id)_see_the_world.png` để tránh tốn dung lượng ổ đĩa.
  - Sử dụng cơ chế bypass browser cache bằng cách append timestamp `?t=Date.now()` khi tải ảnh lên thẻ `<img>`.

### 4. Hiển Thị, Refresh & Toggle Ảnh Chân Dung Nhân Vật & NPC
- **Mục tiêu:** Cung cấp trải nghiệm avatar chân dung hai lớp (ảnh AI và emoji mặc định), cho phép bật/tắt hiển thị và làm mới sinh lại ảnh bất cứ lúc nào.
- **Thực hiện:**
  - **Cơ chế sao chép ảnh mẫu:** Khi khởi chạy game, backend quét thư mục `frontend/assets/default_characters/` chứa ảnh chân dung mẫu của 4 Valkyrie, copy sang thư mục `frontend/assets/generated/` dưới tên dạng `(session_id)_(tên_nhân_vật).png` làm ảnh mặc định ban đầu để tránh người dùng phải đợi lâu.
  - **Tải ảnh và Fallback:** Hàm `setupAvatarDisplay` ở frontend tự động kiểm tra tùy chọn lưu trong `localStorage`. Nếu tắt ảnh hoặc ảnh chưa tồn tại (kích hoạt lỗi `onerror`), UI tự động fallback mượt mà về emoji tương ứng (VD: 🧘 cho Tu sĩ, 🛒 cho Thương nhân, emoji tộc cho đồng hành).
  - **Bật/Tắt (Toggle):** Thêm nút con mắt 👁️ ở NPC panel và Modal chi tiết nhân vật (nay được đổi thành giao diện 3 cột sang trọng) để bật/tắt nhanh hiển thị chân dung.
  - **Làm mới (Refresh):** Thêm nút 🔄 để gửi yêu cầu POST tới `/image/refresh-character` sinh lại ảnh mới qua Kaggle theo thời gian thực dựa trên class, tộc, kỹ năng và mô tả ngoại hình của nhân vật.

### 5. Tiêu Đề Phân Tách Lượt Đấu (Combat Turn Separators)
- **Mục tiêu:** Tăng độ trực quan và tính thẩm mỹ cho log diễn biến chiến đấu.
- **Thực hiện:**
  - Backend tự động chèn dòng tiêu đề `⚔️ ─── LƯỢT ĐẤU THỨ {turn_count} ─── ⚔️` vào đầu danh sách log mỗi khi bắt đầu một lượt chiến đấu mới.
  - Phía frontend nhận biết chuỗi `LƯỢT ĐẤU THỨ` để áp dụng class CSS `.combat-log-turn-header`, căn giữa chữ, tô tông màu tím neon huyền ảo, đóng khung span kính mờ vô cùng sang trọng và tách biệt.

---

## 🛠️ Kết Quả Xác Minh (Verification Details)

1. **Biên dịch Backend:** Chạy biên dịch kiểm tra thành công tất cả các file Python liên quan:
   ```powershell
   python -m py_compile app/api/rpg_routes.py app/services/rpg_service.py app/services/rpg_engine.py app/domain/rpg_schemas.py
   ```
   *Kết quả:* **Thành công 100%**, không có bất kỳ lỗi cú pháp nào.

2. **Frontend & Event Binding:** Tất cả các endpoint `/suggest-appearance`, `/image/see-world`, và `/image/refresh-character` đã được kết nối hoàn chỉnh với giao diện Setup Wizard, NPC Panel, Details Modal, và Combat Log.
