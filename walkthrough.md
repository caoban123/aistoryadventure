# Walkthrough: Chế Độ RPG Mở Rộng - Update 1-1

Tài liệu này tóm tắt toàn bộ các tính năng, nâng cấp và cải tiến đã triển khai trong phiên bản **RPG Mode Mở Rộng (Update 1-1)** của *AI Story Adventure*.

---

## 🚀 Các Tính Năng Đã Triển Khai (Implemented Features)

### 1. Tướng Mythic SilverAsh & Trạng Thái Băng Giá
- **Nhân vật mới:** SilverAsh (tộc Valkyrie, class Guard) được tích hợp đầy đủ kỹ năng:
  - *Nội tại Kỷ băng hà:* Khi địch dính đủ 2 tầng debuff `"Giá lạnh"`, tự động chuyển thành trạng thái `"Đông cứng"` kéo dài 1 lượt.
  - *Cơ chế Phá Băng:* Khi kẻ địch dính `"Đông cứng"`, nhận sát thương vật lý tăng x1.5 (riêng từ SilverAsh tăng x1.8).
  - *Kỹ năng 1 (Quét kiếm):* Gây 80% ATK và cộng 1 tầng `"Giá lạnh"` (max 2 tầng).
  - *Kỹ năng 2 (Băng tuyết vũ):* Chém nhanh 5 nhát (mỗi nhát 100% ATK), luôn kích hoạt trước kẻ địch (bỏ qua SPD).
- **Trạng thái:** Tích hợp hiệu ứng đóng băng `.frost-effect` và `.frozen-effect` với hiệu ứng neon tuyết rơi cao cấp trên CSS.

### 2. Hệ Thống World Map (Bản Đồ Thế Giới) & Dịch Chuyển Nhanh
- **Quản lý vị trí:** Lưu trữ trạng thái bản đồ lớn (`environment`) và vùng đất nhỏ (`current_region`) trong game state.
- **Di chuyển ngẫu nhiên:** Khi di chuyển ngoài map có tỷ lệ bắt gặp các địa điểm nhỏ (20%), lớn (10%) hoặc Dungeon (5%).
- **Chế độ Bản đồ (M & E):**
  - Nhấn phím `M` để bật/tắt bản đồ Lục Địa Linh Hồn.
  - Nhấn phím `E` hoặc click nút để bật **Chế độ Chỉnh sửa (Edit Mode)**, cho phép kéo thả các pin địa danh tùy biến và tự động lưu tọa độ vào `localStorage`.
- **Dịch chuyển nhanh (Fast Travel):** 
  - Thêm endpoint `/fast-travel` ở backend.
  - Người chơi click vào pin vương đô (Kiến trúc lớn) đã mở khóa dịch chuyển nhanh (`unlocked_fast_travel`) để di chuyển tức thời tới đó.
- **Vật phẩm Bản đồ cổ:** Thêm vật phẩm Epic `"Bản đồ cổ"` bán trong shop. Khi sử dụng, mở khóa ngay điểm dịch chuyển nhanh đến vương đô lớn của khu vực hiện tại.

### 3. Cơ Chế Dungeon & Trùm Cuối Alpha
- **Thám hiểm 3 ải:** Vượt qua 3 ải đấu boss của từng environment để nhận phần thưởng tích lũy ảo và nhận `"Mảnh vỡ chìa khoá vĩ đại"` của khu vực đó ở ải cuối.
- **Rest Phase (Safe Zone):** Sau khi vượt mỗi ải, tự động kích hoạt kỹ năng bị động của Supporter còn sống có độ ưu tiên cao nhất để phục hồi sinh mệnh cho cả đội (Angel > Elf > Royalty > Human).
- **Rút lui & Thất bại:** Nếu rút lui, nhận toàn bộ vàng & đồ tích lũy. Nếu thất bại hoặc bỏ cuộc giữa ải đấu, bị phạt mất sạch vàng và vật phẩm trong hành lý (giữ lại trang bị mặc trên người).
- **Trùm cuối Alpha & Cổng Hư Không:**
  - Thu thập đủ 7 mảnh vỡ chìa khóa của 7 khu vực để rèn `"Chìa khoá Hư Không vĩ đại"`.
  - Sử dụng chìa khóa để mở cổng diện kiến trùm cuối Alpha (HP 2000, ATK 200, DEF 90, RES 160).
  - Đánh bại Alpha mở ra 3 kết cục câu chuyện (Good, Bad, Continue Endings).

### 4. Hệ Thống Quest & Achievements
- **Quest (Q):** Nhận danh sách 6 quest thuộc 6 category khác nhau. Sử dụng phím `Q` để xem, tiêu 2 vàng để làm mới (refresh) quest ngẫu nhiên cùng loại qua API `/quest/refresh`. Tự động nhận thưởng Vàng & EXP khi hoàn thành.
- **Achievements:** Theo dõi tiến trình 9 danh hiệu truyền kỳ cố định trong quá trình chơi game.

### 5. Nâng Cấp UI/UX & Phím Tắt Tiện Ích
- **Ẩn/Hiện Sidebars:** 
  - Nhấn phím `I` để ẩn/hiện panel thông tin người chơi bên phải.
  - Nhấn phím `N` để ẩn/hiện panel thông tin NPC bên trái.
  - Khi ẩn, khung chat truyện chính sẽ tự động co giãn tối đa toàn màn hình nhờ thiết kế layout grid linh hoạt.
- **See the World (S):** Nhấn phím `S` để xem ảnh phong cảnh thế giới do AI vẽ. Hệ thống tự động sinh ảnh nền mờ ảo (ambient image) ở background bất đồng bộ mỗi khi thay đổi environment lớn hoặc region.
- **Custom Name Hiring:** Cho phép đặt tên tùy ý cho nhân vật lính đánh thuê không phải Mythic trước khi chiêu mộ.

---

## 🛠️ Kết Quả Xác Minh (Verification Details)

1. **Biên dịch Backend:** Chạy biên dịch kiểm tra thành công tất cả các file Python được sửa đổi và thêm mới:
   ```powershell
   python -m py_compile app/api/rpg_routes.py app/services/rpg_service.py app/services/rpg_engine.py app/domain/rpg_schemas.py
   ```
   *Kết quả:* **Thành công 100%**, không có lỗi cú pháp nào.

2. **Frontend Scripts:** file `rpg_app.js` được tích hợp các hàm mới, các Event Listener, Keyboard Shortcuts và các hàm sync trạng thái từ `renderState(rpgState)`.

3. **Giao diện & Modal:** Các Modal Quest/Achievement, World Map, Dungeon, và Help Guide trong `index.html` được gán đầy đủ class và style neon glassmorphism mượt mạ.


## 🚀 Bản Vá & Hoàn Thiện Trải Nghiệm RPG (Update v1.1.1)

Phiên bản này sửa đổi triệt để các lỗi layout giao diện, khôi phục hoạt động của script client-side, tối ưu hóa cơ chế dịch chuyển trên bản đồ và cập nhật prompt thế giới sử thi.

### 1. Sửa Lỗi Giao Diện Sidebar Co Giãn (CSS & Layout Grid)
- **Vấn đề cũ:** Khi nhấn `I` để ẩn thông tin nhân vật, các card Party và Inventory trong sidebar phải bị bóp méo, co rúm và không biến mất do chỉ có Card nhân vật chính bị ẩn còn sidebar cha vẫn tồn tại với kích thước cố định. Nhấn `N` cũng tương tự và khiến Inventory kéo dài không cần thiết.
- **Giải pháp:** 
  - Cập nhật `.rpg-grid-container` để tự động điều chỉnh số lượng và độ rộng các cột (tương ứng `1fr 350px`, `290px 1fr`, hoặc `1fr` khi ẩn cả hai).
  - Ẩn hoàn toàn toàn bộ sidebar cha (`.rpg-left-sidebar` / `.rpg-right-sidebar` bằng `display: none !important`) thay vì chỉ ẩn các card con riêng lẻ. Việc này khôi phục layout co giãn hoàn hảo, khi ẩn 1 hoặc cả 2 bên thì phần còn lại là khung text-based kể chuyện chính chiếm trọn màn hình.

### 2. Khắc Phục Lỗi JavaScript Compile (rpg_app.js)
- **Vấn đề cũ:** Thiếu các dấu đóng ngoặc `});` tại dòng 659 ở sự kiện `input` của trường nhập liệu khu vực khiến tệp script `rpg_app.js` gặp lỗi cú pháp nghiêm trọng và bị trình duyệt từ chối thực thi.
- **Giải pháp:** Bổ sung đầy đủ các dấu đóng ngoặc, khôi phục thành công toàn bộ logic wizard, bản đồ kéo thả và các phím tắt.

### 3. Đồng Bộ Hóa Môi Trường Khởi Đầu (Backend start_rpg_game)
- **Vấn đề cũ:** Tại Step 3 của wizard tạo nhân vật, khi người chơi chọn các vương đô lớn (như `"Vương đô Victoria"`), backend khởi tạo game state với `environment = "Vương đô Victoria"`. Vì đây không phải là một trong 7 môi trường lớn (`Đồng bằng`, `Đồi núi`, ...), hệ thống không thể tìm thấy trong `REGION_CATALOG` dẫn đến lỗi render bản đồ (không định vị được vị trí hiện tại của người chơi), tính sai chi phí dịch chuyển nhanh (cost luôn ở giá trị fallback), và không thể roll ra các sự kiện ngẫu nhiên theo vùng đất.
- **Giải pháp:**
  - Triển khai ánh xạ từ vương đô được chọn sang môi trường tương ứng khi khởi động game (ví dụ: `"Vương đô Victoria"` -> `"Đồng bằng"`).
  - Đặt `environment = starting_env` và `current_region = starting_region`.
  - Tự động điền vương đô khởi hành vào danh sách `explored_regions` và `unlocked_fast_travel` để người chơi bắt đầu hành trình ngay tại thủ đô với đầy đủ chức năng.

### 4. Tích Hợp Cốt Truyện World Lore Vào Prompt AI
- **Vấn đề cũ:** AI dẫn chuyện sinh cốt truyện chung chung, không bám sát thần thoại kỷ nguyên và đặc trưng địa lý của 7 vùng đất trong tài liệu.
- **Giải pháp:**
  - Trích xuất toàn bộ thông tin sử thi từ tệp `WORLD LORE.pdf`.
  - Định nghĩa biến toàn cục `AETERNA_WORLD_LORE` bao gồm đầy đủ truyền thuyết về Vết Nứt Kỷ Nguyên, 7 Cổ Ngục và 7 Đại Ma Thần, cùng chi tiết đặc trưng của 7 vùng đất và các vị thủ hộ Valkyrie danh tiếng (VinaVictoria, Wang, Hoshiguma, SilverAsh, Lemuen).
  - Inject lore thế giới chi tiết này vào prompt khởi tạo game (`build_rpg_start_prompt`) và prompt lượt chơi (`build_rpg_turn_prompt`), giúp cốt truyện AI dẫn dắt đạt độ nhất quán và chân thực tuyệt đối với nguyên tác thiết kế.

---

## 🛠️ Kết Quả Xác Minh (v1.1.1)

1. **Kiểm Trả Biên Dịch Python:**
   ```powershell
   python -m py_compile app/ai/rpg_prompt.py app/services/rpg_service.py
   ```
   *Kết quả:* **Thành công 100%**, không có bất kỳ lỗi cú pháp nào.

2. **Kiểm Tra Hoạt Động Của Layout:**
   - Ẩn/hiện bằng phím `I` và `N` hoạt động mượt mà, layout co giãn chính xác không còn hiện tượng dẹp méo phần tử con.
   - Nhập liệu và gợi ý ngẫu nhiên ở Step 3 chạy hoàn hảo sau khi sửa lỗi cú pháp JS.
   - Bản đồ lớn xác định chính xác vị trí khởi hành, tính phí dịch chuyển vàng chính xác dựa trên đồ thị kề & BFS.
   - **Cập nhật thêm:** Màn hình text-based kể chuyện (`.rpg-center-panel`) giờ đây giữ nguyên chiều cao cố định và tự xuất hiện thanh cuộn (`overflow-y: auto`) bên trong phần story log khi truyện dài ra, thay vì tự ý kéo giãn chiều dài toàn trang web ở mọi kích thước màn hình.
   - **Cập nhật thêm:** Biểu tượng mắt thần trang trí được di chuyển từ tiêu đề Bản đồ Thế giới (phím `M`) sang tiêu đề của popup Xem phong cảnh Thế giới (phím `S`) như yêu cầu của thiết kế.

---

## 🛠️ Bản Vá Giao Diện RPG (Update v1.1.2)

### 1. Thêm Nút Hành Động Vào Thanh Topbar
- **Vấn đề cũ:** Các chức năng phím tắt `M` (Bản đồ), `Q` (Quest), `S` (See the World), và Cài đặt không có nút UI tương ứng trong thanh topbar, nên người chơi không biết chúng tồn tại và nút 'S' không thể kích hoạt.
- **Giải pháp:**
  - Thêm 4 nút hành động vào thanh topbar trong khung `rpg-topbar-right`: `👁️‍🗨️ Xem TG` (rpgSeeWorldBtn), `🗺️ Bản đồ` (rpgMapBtn), `📜 Quest` (rpgQuestBtn), và `⚙️` (rpgSettingsBtn).
  - Thêm style `.rpg-topbar-action-btn` với hiệu ứng glassmorphism tím nhẹ và hover animation.
  - Gắn event listener cho `rpgMapBtn` (trong `initRpgMapController`) và `rpgQuestBtn` (trong `initRpgQuestController`) để bật/tắt modal tương ứng khi nhấn nút.
  - Phím 'S' giờ hoạt động đúng vì `rpgSeeWorldBtn` đã tồn tại trong DOM.

### 2. Sửa Bug Kỹ Năng "Mưa tên" Của Elf Biến Mất
- **Vấn đề cũ:** Kỹ năng "Mưa tên" của nhân vật Elf có thể biến mất khỏi dropdown kỹ năng trong combat.
- **Giải pháp:**
  - Giới hạn check `isAutoFiring` chỉ áp dụng cho nhân vật Sniper có `skill_1 === "Khóa mục tiêu"` (Lemuen), tránh vô hiệu hóa nhầm Elf khi `skill_1_activating` bị set sai.
  - Thêm bản đồ `raceSkillMap` dự phòng: nếu `special_skills` của nhân vật không có `skill_1` (do dữ liệu cũ thiếu trường), tự động tái tạo tên skill theo tộc (Elf → "Mưa tên", Angel → "Lá chắn", v.v.).
  - Thêm xử lý `isOneTimeUsed` (skill_1_activated = true) để hiển thị `[Đã dùng]` thay vì ẩn skill.

### 3. Sửa Layout Màn Hình Combat
- **Vấn đề cũ:** Màn hình combat bị lỗi hiển thị do `.rpg-combat-overlay` dùng `flex-direction` ngang, khiến thanh timeline và lưới combat đứng cạnh nhau thay vì xếp dọc.
- **Giải pháp:**
  - Thêm `flex-direction: column` vào `.rpg-combat-overlay` để timeline bar nằm phía trên grid combat.
  - Đổi `height: 100%` thành `flex: 1; min-height: 0` cho `.combat-grid` để chiếm không gian linh hoạt còn lại.
  - Cập nhật `.rpg-combat-timeline-bar`: bỏ `margin` cứng, dùng `width: 100%; max-width: 1550px; flex-shrink: 0` để căn chỉnh đúng với chiều rộng tối đa của grid.

## 🛠️ Kết Quả Xác Minh (v1.1.2)

1. **Kiểm Tra Biên Dịch JS:**
   ```powershell
   node --check frontend/rpg_app.js
   ```
   *Kết quả:* **Thành công 100%**, không có lỗi cú pháp nào.


2. **Kiểm Tra Biên Dịch Python:**
   ```powershell
   python -m py_compile app/ai/rpg_prompt.py app/api/rpg_routes.py app/services/rpg_service.py app/domain/rpg_models.py
   ```
   *Kết quả:* **Thành công 100%**, không có lỗi cú pháp nào.

---

## 🛠️ Bản Vá Giao Diện & Logic Hầm Ngục RPG (Update v1.1.3)

### 1. Hệ Thống Dungeon & Boss Đặc Biệt
- **Tự động hóa loot:** Khi vượt ải Dungeon thành công, bỏ qua hoàn toàn hộp thoại hỏi số phận (loot/recruit/leave) và tự động thực thi hành động "loot" để gom đồ tích lũy.
- **Màn hình Safe Zone (Rest Phase):** Sau mỗi ải, hiển thị popup thông tin ải hiện tại, số vàng/kinh nghiệm/vật phẩm tích lũy, tự động kích hoạt bị động hồi máu/hồi sinh của Supporter theo đúng thứ tự ưu tiên (Angel > Elf > Royalty > Human).
- **Rút lui & Phạt:** Lựa chọn rút lui khỏi hầm ngục sẽ xóa toàn bộ vàng (về 0) và đồ trong Inventory chưa trang bị.

### 2. Mở Cổng Hư Không & Final Boss Alpha
- **Sản sinh mảnh khóa:** Vượt ải 3 Dungeon rơi mảnh khóa Mythic gắn với environment hiện tại.
- **Kích hoạt cổng:** Click vào bất kỳ mảnh khóa nào khi sở hữu đủ 7 mảnh khóa của 7 môi trường khác nhau sẽ mở cổng hư không, tiêu thụ cả 7 mảnh và đưa tổ đội vào chiến đấu với trùm cuối Alpha.
- **Phân nhánh Ending:** Đánh bại Alpha cho phép chọn 3 nhánh kết thúc game (Good Ending cứu thế, Bad Ending bá chủ ma vương, hoặc tiếp tục phiêu lưu).
     - **Leave Region:** Rời khu vực thành công về hoang dã (`current_region = None`), không phát sinh lỗi `story_history`.
     - **Boss Stats Preservation:** Boss Medusa giữ nguyên 500 Max HP sau khi đồng bộ chỉ số.
     - **Combat Endings:** Hạ gục Alpha bằng lệnh `combat_kill` kết thúc trận đấu ngay lập tức và đề xuất chính xác 3 Ending lựa chọn:
       - Good Ending (Trở về thế giới thực)
       - Bad Ending (Đồng hóa với Hư Không)
       - Continue Ending (Tiếp tục hành trình vô tận)
     - **World Map Toggle & View/Edit Mode:** Loại bỏ hoàn toàn các nút bấm chuột "View" và "Edit" gây chồng lấn nút Đóng. Thay vào đó, thiết kế huy hiệu trạng thái inline `[Xem 👁️] / [Chỉnh sửa 🛠️]` nằm cạnh tiêu đề "Lục Địa Aeterna" và hỗ trợ chuyển đổi chế độ bản đồ bằng phím `E` trên bàn phím. Cửa sổ modal tự động mở rộng trở lại hợp lý theo tỷ lệ màn hình (tối đa `1000px`), giúp hiển thị bản đồ sắc nét, to rõ.

### 3. Khóa Avatar Đồng Hành Độc Bản & Đặt Tên
- **Khóa avatar:** Khi tuyển mộ thành công đồng hành mới (từ Shop hoặc thắng combat quy phục), nhân bản ảnh template sang `{session_id}_{character_id}.png`. Khi refresh ảnh bằng AI, chỉ ảnh của đồng hành đó thay đổi, tránh ảnh hưởng đến các nhân vật khác cùng race/class.
- **Tự đặt tên:** Cho phép đặt tên tùy chọn khi thu phục kẻ địch hoặc thuê lính đánh thuê không phải Mythic.

### 4. Bản Đồ Cổ Từng Vùng & Căn Lề UI
- **Cẩm nang Bản đồ cổ:** Thêm vật phẩm Bản đồ cổ trị giá 199 vàng trong shop, mua xong tự tiêu thụ và kích hoạt dịch chuyển nhanh vĩnh viễn tới vương đô của môi trường đó.
- **Độ rộng grid container:** Tăng `max-width` của `.rpg-grid-container` lên `1650px` để nới rộng khung đọc cốt truyện chính.
- **Highlight lựa chọn:** Highlight Xanh lá cho các lựa chọn dịch chuyển vùng đất (`Khám phá ...`) và Đỏ rực cho lựa chọn vào Dungeon (`Tiến vào sâu bên trong...`).

## 🛠️ Kết Quả Xác Minh (v1.1.3)

1. **Kiểm Tra Biên Dịch JS:**
   ```powershell
   node --check frontend/rpg_app.js
   ```
   *Kết quả:* **Thành công 100%**, không có lỗi cú pháp nào.

2. **Kiểm Tra Biên Dịch Python:**
   ```powershell
   python -m py_compile app/ai/rpg_prompt.py app/api/rpg_routes.py app/services/rpg_engine.py app/services/rpg_service.py app/domain/rpg_models.py
   ```
   *Kết quả:* **Thành công 100%**, không có lỗi cú pháp nào.


## 🚀 Bản Vá Trải Nghiệm Giao Diện & Boss Scaling (Update v1.1.4)

### 1. Đồng bộ Cấp độ Debug `gain_maxlvl`
- **Vấn đề:** Khi dùng lệnh debug `gain_maxlvl` để tăng cấp tối đa tổ đội, cấp độ của các nhân vật trong combat lại bị reset về trước đó sau khi chọn lượt tiếp theo.
- **Giải pháp:** Đồng bộ hoá cả `rpg_state.combat.combat_party` khi đang chiến đấu, đảm bảo các bản sao nhân vật trong lượt đấu combat lưu trữ và sử dụng chỉ số cấp độ max mới.

### 2. Tăng chỉ số Boss theo Cấp độ người chơi (Boss Scaling)
- **Cơ chế:** Khi tạo ra Boss Elite 1-2 hoặc Final Boss Alpha, toàn bộ chỉ số trừ `defense` và `res_def` sẽ được nhân thêm tỷ lệ tăng +1% với mỗi cấp độ của người chơi chính (ví dụ: cấp 20 tăng 19% chỉ số).
- **Bảo toàn:** Các thuộc tính phòng thủ vật lý và phòng thủ phép của Boss giữ nguyên bản gốc để bảo đảm tính cân bằng game.

### 3. Tối ưu hoá Visual Prompt cho Model SDXL Lightning
- **Chi tiết:** Viết lại chi tiết hơn tất cả các prompts sinh ảnh cho các Boss Elite và Final Boss Alpha, thêm các mô tả nghệ thuật đặc thù giúp SDXL Lightning vẽ tranh chân thực, ấn tượng và đúng thần thái sử thi (ví dụ: Medusa quyến rũ, Golem đá cổ vĩ đại, Dracula huyền bí, Alpha tối cao).

### 4. Thiết lập Hiển thị Aspect-Ratio 4:3 cho Bản đồ Thế giới
- **Giao diện:** Bản đồ lớn tự động co giãn theo viewport nhưng khóa cứng aspect-ratio `4:3` bằng CSS `aspect-ratio: 4/3` kết hợp `max-height: 65vh` và `max-width`. Do đó ảnh bản đồ thế giới luôn vuông vức, sắc nét và không bị kéo giãn ở bất kỳ độ phân giải màn hình nào.
- **Phím tắt:**
  - Nhấn phím tắt `E` để chuyển đổi Xem/Sửa và `M` / `Escape` để tắt bản đồ tức thời ngay cả khi con trỏ đang focus tại ô input trò chuyện.
  - Tự động `blur()` input đang focus khi kích hoạt mở modal map.
  - Font size tiêu đề "Lục Địa Aeterna" được rút gọn xuống `1.15rem` tinh tế hơn.
