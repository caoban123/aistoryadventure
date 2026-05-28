# Kế Hoạch Thực Hiện: Tích Hợp Tạo Hình Ảnh AI & Hoàn Thiện Trải Nghiệm Chế Độ RPG

Kế hoạch này tích hợp tính năng sinh hình ảnh AI thông qua backend Kaggle (Stable Diffusion XL Lightning) vào Chế độ RPG, sửa lỗi hiển thị và đổi tên nhân vật.

## User Review Required

> [!IMPORTANT]
> **Cấu hình Kaggle Backend URL:**
> Cần khai báo biến môi trường `KAGGLE_BACKEND_URL` trong file `.env` (ví dụ: `KAGGLE_BACKEND_URL=https://onion-vertical-squash.ngrok-free.dev`) để FastAPI backend có thể proxy và gửi yêu cầu sinh ảnh tới Kaggle server.

> [!NOTE]
> **Cơ chế Cache Hình Ảnh:**
> Để tránh người dùng phải chờ đợi lâu khi bắt đầu session mới, hệ thống sẽ tự động quét thư mục `frontend/assets/default_characters/` (chứa các ảnh mẫu của 4 Valkyrie và các Race/Class mặc định) và sao chép chúng sang thư mục `frontend/assets/generated/` dưới tên dạng `(session_id)_(tên_nhân_vật).png` khi khởi động thế giới. Người chơi có thể bấm nút "Làm mới (Refresh)" để gửi yêu cầu sinh lại ảnh mới theo thời gian thực nếu muốn.

## Open Questions

Không có câu hỏi mở. Chúng ta sẽ tiến hành triển khai các bước chi tiết dưới đây.

---

## Proposed Changes

### 1. Valkyrie Rename ("Lumuen" -> "Lemuen")

#### [MODIFY] [rpg_models.py](file:///d:/hcmus/HK4/Tư duy tính toán cho TTNT/aistoryadventure/app/domain/rpg_models.py)
- Thay đổi các biến/comment có từ khóa "lumuen" hoặc "Lumuen" thành "lemuen" hoặc "Lemuen" để nhất quán.

#### [MODIFY] [rpg_engine.py](file:///d:/hcmus/HK4/Tư duy tính toán cho TTNT/aistoryadventure/app/services/rpg_engine.py)
- Sửa đổi tên mặc định của lớp Sniper từ `"Lumuen"` thành `"Lemuen"`.
- Sửa đổi các tham chiếu biến `lumuen_auto_shots` thành `lemuen_auto_shots`.

#### [MODIFY] [rpg_service.py](file:///d:/hcmus/HK4/Tư duy tính toán cho TTNT/aistoryadventure/app/services/rpg_service.py)
- Cập nhật trường kiểm tra thuộc tính `lumuen_auto_shots` thành `lemuen_auto_shots`.

#### [MODIFY] [rpg_app.js](file:///d:/hcmus/HK4/Tư duy tính toán cho TTNT/aistoryadventure/frontend/rpg_app.js)
- Cập nhật comment và phần hiển thị kỹ năng của Sniper từ "Lumuen" thành "Lemuen".

---

### 2. Khảo Sát Ngoại Hình Nhân Vật Chính (Survey Step 7)

#### [MODIFY] [index.html](file:///d:/hcmus/HK4/Tư duy tính toán cho TTNT/aistoryadventure/frontend/index.html)
- Tăng số bước của Wizard từ 7 lên 8 bước.
- Thêm bước 7 (`rpgStep7`): Khảo sát ngoại hình nhân vật chính (Appearance Description). Cho phép nhập văn bản tùy chọn hoặc bấm nút "Gợi ý ngoại hình AI".
- Chuyển Tóm tắt & Bắt đầu sang bước 8 (`rpgStep8`).
- Cập nhật chỉ số thanh tiến trình (`#rpgWizardStepsContainer`) hiển thị 8 bước.

#### [MODIFY] [rpg_schemas.py](file:///d:/hcmus/HK4/Tư duy tính toán cho TTNT/aistoryadventure/app/domain/rpg_schemas.py)
- Bổ sung trường `appearance_desc: str | None = None` vào `RPGStartRequest` để lưu trữ mô tả ngoại hình người chơi nhập từ frontend.

#### [MODIFY] [rpg_routes.py](file:///d:/hcmus/HK4/Tư duy tính toán cho TTNT/aistoryadventure/app/api/rpg_routes.py)
- Cập nhật route `/start-story` để nhận thêm tham số `appearance_desc` dạng query parameter.
- Thêm route POST `/suggest-appearance` để sinh gợi ý ngoại hình bằng AI (Gemini).

#### [MODIFY] [rpg_service.py](file:///d:/hcmus/HK4/Tư duy tính toán cho TTNT/aistoryadventure/app/services/rpg_service.py)
- Thêm phương thức `suggest_appearance` để xây dựng prompt và gọi LLM trả về gợi ý ngoại hình bằng tiếng Việt.
- Trong `start_rpg_story`, gán mô tả ngoại hình cho nhân vật chính: `rpg_state.player_character.description = appearance_desc`.

#### [MODIFY] [rpg_app.js](file:///d:/hcmus/HK4/Tư duy tính toán cho TTNT/aistoryadventure/frontend/rpg_app.js)
- Nâng cấp hàm `initRpgSetupWizard()` để hỗ trợ điều phối qua 8 bước.
- Gắn sự kiện click cho nút gọi gợi ý ngoại hình AI từ backend và điền vào ô nhập liệu.
- Truyền `appearance_desc` vào API `/start-story` khi người chơi bắt đầu hành trình.

---

### 3. Nút "Mắt Thần" Quan Sát Thế Giới (See the World)

#### [MODIFY] [index.html](file:///d:/hcmus/HK4/Tư duy tính toán cho TTNT/aistoryadventure/frontend/index.html)
- Thêm nút bấm hình "con mắt" sang trọng (`#rpgSeeWorldBtn`) nằm cạnh nhãn tên phiên chơi RPG (`#rpgSessionLabel`).
- Thêm Modal hiển thị hình ảnh thế giới (`#rpgWorldImgModal`) chứa container ảnh tỉ lệ 16:9 và loading spinner.

#### [MODIFY] [rpg_routes.py](file:///d:/hcmus/HK4/Tư duy tính toán cho TTNT/aistoryadventure/app/api/rpg_routes.py)
- Thêm endpoint `/image/see-world` để gọi backend sinh ảnh cảnh quan thế giới dựa trên phần cốt truyện hiện tại.

#### [MODIFY] [rpg_service.py](file:///d:/hcmus/HK4/Tư duy tính toán cho TTNT/aistoryadventure/app/services/rpg_service.py)
- Thực hiện phương thức `generate_world_image` sử dụng `urllib` gọi đến endpoint `/generate-world-theme` trên Kaggle server. Sau khi nhận được Base64, tiến hành giải mã và ghi đè trực tiếp lên file `frontend/assets/generated/(session_id)_see_the_world.png`.

#### [MODIFY] [rpg_app.js](file:///d:/hcmus/HK4/Tư duy tính toán cho TTNT/aistoryadventure/frontend/rpg_app.js)
- Gắn sự kiện bấm vào nút "Mắt thần" để hiển thị modal xem ảnh thế giới, tự động gọi endpoint `/image/see-world` và tải ảnh hiển thị.

#### [MODIFY] [rpg_style.css](file:///d:/hcmus/HK4/Tư duy tính toán cho TTNT/aistoryadventure/frontend/rpg_style.css)
- Thiết kế style cho nút mắt thần `.rpg-premium-eye-btn` với hiệu ứng kính mờ (glassmorphism), viền tím sáng phát quang (glow) và micro-animation xoay nhẹ khi hover.

---

### 4. Hiển Thị, Refresh & Tự Chọn Tắt/Mở Ảnh Nhân Vật & NPC

#### [MODIFY] [index.html](file:///d:/hcmus/HK4/Tư duy tính toán cho TTNT/aistoryadventure/frontend/index.html)
- Cập nhật `#rpgNpcPanel`: Giữ lại biểu tượng emoji cạnh tên nhân vật. Phần avatar `#rpgNpcAvatar` sẽ có 2 tầng: tầng ảnh thẻ `<img id="rpgNpcAvatarImg">` và tầng chữ mặc định `<span id="rpgNpcAvatarDefault">`. Thêm 2 nút bấm overlay nhỏ ở góc dưới: nút Làm mới (🔄) và nút Bật/Tắt (👁️).
- Cập nhật modal chi tiết nhân vật `#rpgCharDetailsModal`: Đổi thành bố cục 3 cột. Cột bên trái cùng hiển thị ảnh thẻ của nhân vật cùng 2 nút điều khiển Refresh và Toggle. Hai cột còn lại hiển thị các chỉ số cơ bản và kỹ năng như cũ.

#### [MODIFY] [rpg_routes.py](file:///d:/hcmus/HK4/Tư duy tính toán cho TTNT/aistoryadventure/app/api/rpg_routes.py)
- Thêm endpoint `/image/refresh-character` để tạo lại ảnh chân dung cho nhân vật.

#### [MODIFY] [rpg_service.py](file:///d:/hcmus/HK4/Tư duy tính toán cho TTNT/aistoryadventure/app/services/rpg_service.py)
- Triển khai phương thức sao chép tự động các file ảnh mẫu từ thư mục `frontend/assets/default_characters/` sang `frontend/assets/generated/` và đổi tên thêm prefix `session_id` khi tạo câu chuyện đầu game.
- Triển khai phương thức `refresh_character_image` để tạo prompt dựa trên thông tin Class, Race, mô tả kỹ năng của nhân vật, gửi đến Kaggle backend, và lưu đè lên file ảnh tương ứng của session đó.

#### [MODIFY] [rpg_app.js](file:///d:/hcmus/HK4/Tư duy tính toán cho TTNT/aistoryadventure/frontend/rpg_app.js)
- Thêm các hàm hỗ trợ `getCharacterImageFilename(char)` và `setupAvatarDisplay(...)` để quản lý việc tải ảnh, xử lý lỗi `onerror` (nếu chưa có ảnh sẽ tự động fallback về biểu tượng emoji) và lưu tùy chọn bật/tắt hiển thị ảnh nhân vật vào `localStorage`.
- Gắn sự kiện cho các nút Refresh và Toggle trong NPC panel và Modal chi tiết nhân vật để cập nhật hình ảnh thời gian thực.

---

### 5. Cải Tiến Log Trận Đấu (Combat Turn Separators)

#### [MODIFY] [rpg_engine.py](file:///d:/hcmus/HK4/Tư duy tính toán cho TTNT/aistoryadventure/app/services/rpg_engine.py)
- Trong phương thức `process_turn` của `CombatEngine`, chèn dòng tiêu đề `⚔️ ─── LƯỢT ĐẤU THỨ {turn_count} ─── ⚔️` vào đầu danh sách log trước khi thực thi hành động để phân tách các lượt đấu rõ ràng.

#### [MODIFY] [rpg_app.js](file:///d:/hcmus/HK4/Tư duy tính toán cho TTNT/aistoryadventure/frontend/rpg_app.js)
- Nhận biết các dòng log tiêu đề lượt đấu trong log chiến đấu để áp dụng class CSS đặc biệt `.combat-log-turn-header`.

#### [MODIFY] [rpg_style.css](file:///d:/hcmus/HK4/Tư duy tính toán cho TTNT/aistoryadventure/frontend/rpg_style.css)
- Style `.combat-log-turn-header` thành dạng tiêu đề căn giữa, chữ màu tím neon phát sáng nhẹ, bo tròn viền tạo độ tách biệt và sang trọng.

---

## Verification Plan

### Automated Tests
- Kiểm tra biên dịch code python:
  ```powershell
  python -m py_compile app/api/rpg_routes.py app/services/rpg_service.py app/services/rpg_engine.py app/domain/rpg_schemas.py
  ```

### Manual Verification
1. **Đổi tên Valkyrie:** Vào game và kiểm tra Sniper xem tên hiển thị đã chuyển thành "Lemuen" ở tất cả các nơi.
2. **Khảo sát bước 7:** Khởi tạo nhân vật mới, điền tên, giới tính, khu vực, vàng, trang bị, mục tiêu, sau đó tại bước 7 bấm "Gợi ý ngoại hình AI". Kiểm tra xem văn bản gợi ý có xuất hiện chuẩn xác không, rồi ấn "Tiếp theo" qua bước 8 xem bảng tóm tắt thông số.
3. **Mắt Thần:** Khởi chạy game, bấm nút mắt thần trên thanh công cụ xem có hiện loading spinner và tải về hình ảnh thế giới lưu tại `assets/generated/(session_id)_see_the_world.png` hay không.
4. **Hiển thị & Refresh Ảnh Nhân Vật:** Click nút "?" của một nhân vật bất kỳ để mở modal chi tiết, bấm nút Bật/Tắt ảnh, bấm nút Làm mới để xem ảnh có được sinh lại từ Kaggle backend. Kiểm tra NPC panel bên trái khi gặp thương nhân/quái vật xem có hiển thị tương tự không.
5. **Log Chiến Đấu:** Vào combat, thực hiện một vài hành động và quan sát xem log chiến đấu có các tiêu đề phân tách lượt đẹp mắt hay không.
