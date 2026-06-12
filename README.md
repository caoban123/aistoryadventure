# 🌟 AI Story Adventure: Hệ Thống Phiêu Lưu & Tương Tác Cốt Truyện AI Sinh Bản

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![HTML5](https://img.shields.io/badge/Frontend-HTML5-E34F26?style=for-the-badge&logo=html5&logoColor=white)](#)
[![CSS3](https://img.shields.io/badge/Styling-CSS3-1572B6?style=for-the-badge&logo=css3&logoColor=white)](#)
[![JavaScript](https://img.shields.io/badge/Logic-JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)](#)
[![Qdrant](https://img.shields.io/badge/VectorDB-Qdrant-red?style=for-the-badge&logo=qdrant&logoColor=white)](https://qdrant.tech/)
[![Docker](https://img.shields.io/badge/Container-Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![Cloudflare](https://img.shields.io/badge/Proxy-Cloudflare-F38020?style=for-the-badge&logo=cloudflare&logoColor=white)](https://www.cloudflare.com/)

Hệ thống ứng dụng web tương tác câu chuyện thế hệ mới, tích hợp Trí tuệ Nhân tạo sinh bản (Generative AI) để dệt nên các thế giới phiêu lưu độc bản. Dự án kết hợp giữa công nghệ lưu trữ ký ức vector thông minh (Vector Memory Database) và hệ thống gameplay nhập vai sâu sắc.

---

## 🗺️ Bản Đồ Thế Giới Game RPG
![Bản đồ thế giới RPG](frontend/assets/RPG_world_map_v2.png)
*Bản đồ thế giới giả tưởng được tự động tích hợp trong Chế độ RPG*

---

## 🚀 Tính Năng Nổi Bật

### 1. Bốn Chế Độ Chơi Đa Dạng (4 Gameplay Modes)
*   **Novel Mode (Tiểu Thuyết Tương Tác)**: Trải nghiệm đọc truyện . Từng chương truyện được dệt nên dựa trên các lựa chọn rẽ nhánh sâu sắc của người chơi.
*   **Adventure Mode (Phiêu Lưu Chữ)**: Chế độ Text-Adventure cổ điển nhưng thông minh hơn. AI đóng vai trò làm Quản trò (Dungeon Master) dẫn dắt bạn qua những vùng đất bí ẩn.
*   **RPG Mode (Nhập Vai RPG)**:
    *   Hệ thống Quản lý Tổ đội (Party Management) với các thuộc tính Chỉ số, Cấp độ, Phẩm chất (Rarity) chuẩn xác.
    *   Hệ thống Bản đồ, Nhiệm vụ (Quests), Phó bản (Dungeons) và tính năng dịch chuyển nhanh (Fast Travel).
    *   Hệ thống Chiến đấu theo lượt (Turn-based Combat) kết hợp Cửa hàng thương nhân (Merchant Shop) mua bán vật phẩm bằng Vàng.
*   **Creator Mode (Sáng Tạo Thế Giới)**: Công cụ dành cho các tác giả tự do thiết lập cốt truyện gốc, mô tả thế giới, bối cảnh nhân vật và xuất bản lên thư viện cộng đồng (Discover).

### 2. Trình Đọc Sách Discover Book Reader Tối Ưu
*   Giao diện đọc sách premium với phông chữ serif tinh tế, hỗ trợ hiển thị tiếng Việt hoàn chỉnh không lỗi dấu.
*   Hiệu ứng kính mờ (Glassmorphic Opaque Backdrop) giúp người dùng tập trung hoàn toàn vào nội dung câu chuyện, tránh bị rối mắt bởi giao diện nền.
*   Nội dung hội thoại phân tách chương rõ ràng, lồng ghép trực quan các hộp quyết định của người chơi.

### 3. Hệ Thống Ký Ức Vector (Vector Memory)
*   Sử dụng cơ sở dữ liệu vector **Qdrant** và **ChromaDB** để ghi nhớ các mốc sự kiện quan trọng trong quá trình chơi của bạn.
*   AI có thể truy hồi lại các quyết định trước đó của người chơi để phát triển mạch truyện tiếp theo một cách logic và nhất quán, khắc phục giới hạn context window của các LLM thông thường.

### 4. Cơ Chế Trust & Safety (An Toàn Học Thuật)
*   Tích hợp bộ lọc kiểm duyệt (Safety Filter) bảo mật cấp độ cao nhằm chống Prompt Injection hoặc các nội dung không phù hợp.
*   Bảo mật tài khoản người chơi tích hợp hệ thống xác thực **Firebase Authentication**.

---

## 📸 Hình Ảnh Thế Giới Trong Game
Để mang lại trải nghiệm nhập vai chân thực nhất, người chơi có thể khám phá nhiều thế giới độc đáo:

| Vùng đất Hollow Sea | Vương quốc Sunless Realm | Khối ký ức thế giới |
|:---:|:---:|:---:|
| ![Hollow Sea](frontend/assets/world-hollow-sea.png) | ![Sunless Realm](frontend/assets/world-sunless-realm.png) | ![World Memory](frontend/assets/world-memory.png) |

---

## 🛠️ Công Nghệ Sử Dụng

### Frontend
*   **Core**: HTML5, Vanilla JavaScript (ES6 Modules)
*   **Styling**: Vanilla CSS3 (Giao diện tối màu Glassmorphism cao cấp)
*   **Hiệu ứng**: GSAP & ScrollTrigger cho các chuyển động mượt mà
*   **Auth**: Firebase Client SDK

### Backend
*   **Framework**: FastAPI (Python 3.10+)
*   **Database**: Qdrant / ChromaDB (Vector Search), SQLite (Local data)
*   **Authentication**: Firebase Admin SDK
*   **LLM Integration**: Google Gemini API / OpenAI API

---

## 🧠 Chi Tiết Các Kỹ Thuật Chuyên Sâu (Advanced Technical Details)

### 1. Kiến Trúc RAG & Bộ Nhớ Dài Hạn Ngữ Nghĩa (Semantic Memory RAG Pipeline)
*   **Vectorization (Offline Embedding):** Khi người chơi kết thúc một cảnh, hệ thống không lưu toàn bộ text thô mà dùng mô hình cục bộ `BAAI/bge-small-en-v1.5` của thư viện **FastEmbed** để sinh vector embedding 384 chiều cực nhanh và tiết kiệm chi phí tính toán.
*   **Semantic Retrieval:** Khi người chơi gửi hành động mới, hệ thống tự động tìm kiếm Top-5 ký ức có độ tương đồng Cosine (Cosine Similarity) cao nhất trong Qdrant DB. Các ký ức này được đưa ngược vào Prompt dưới dạng ngữ cảnh quá khứ để LLM duy trì sự nhất quán của cốt truyện.
*   **Background Memory Condensation (Tóm tắt bất đồng bộ):** Nhằm giảm độ trễ (latency) của game, quá trình tóm tắt phân cảnh và ghi nhận ký ức vào Qdrant được đẩy vào **FastAPI BackgroundTasks** chạy ngầm để người chơi không phải chờ đợi trực tiếp.

### 2. Chuỗi Dự Phòng AI Tự Động (AI Fallback & Round-Robin Chain)
*   Để đối phó với các lỗi quá tải API (Quota Exceeded / Rate Limit) hoặc sự cố đường truyền của nhà cung cấp chính (ví dụ: Google Gemini API), hệ thống sử dụng một chuỗi xử lý lỗi dự phòng (**API Exception Handler Chain**).
*   Nếu Gemini gặp sự cố, hệ thống sẽ tự động chuyển tiếp request sang **OpenAI (GPT-4o-mini)** hoặc **Groq (LLaMA-3)** một cách mượt mà mà người chơi không hề bị ngắt quãng trải nghiệm.

### 3. Bộ Máy Tính Toán RPG Tất Định (Deterministic RPG Combat Engine)
*   Để giữ game được cân bằng và tránh các lỗi logic ngớ ngẩn do sự ngẫu nhiên của LLM, toàn bộ logic trận chiến, tính sát thương, né tránh, chí mạng và quản lý vật phẩm đều được tính toán bằng thuật toán thuần Python định sẵn (`app/services/rpg_engine.py`) dựa trên các thuộc tính của nhân vật.
*   AI chỉ đóng vai trò nhận các dữ liệu số liệu tất định này để "dệt" thành những câu mô tả trận đánh sống động và đầy màu sắc văn học.

### 4. Giao Tiếp Stream Thời Gian Thực qua Server-Sent Events (SSE)
*   Thay vì bắt người dùng đợi hàng chục giây cho đến khi AI viết xong toàn bộ chương truyện, Backend sử dụng giao thức **SSE (Server-Sent Events)** thông qua `StreamingResponse` của FastAPI để đẩy từng từ được sinh ra về phía Client ngay lập tức, tạo hiệu ứng chữ gõ (typing effect) thời gian thực mượt mà.

---

## 📂 Cấu Trúc Dự Án

```text
ai-story-tnt/
├── app/                  # Backend code (FastAPI)
│   ├── api/              # Các cổng định tuyến HTTP API (endpoints)
│   ├── domain/           # Định nghĩa Model dữ liệu (Pydantic / RPG models)
│   ├── services/         # Logic xử lý chính (Gemini, RPG Engine, Safety Filter)
│   └── main.py           # File khởi chạy server Backend
├── frontend/             # Giao diện Client (HTML, CSS, JS)
│   ├── assets/           # Hình ảnh thế giới, bản đồ, biểu tượng
│   ├── app.js            # Điều phối logic ứng dụng Client chính
│   ├── rpg_app.js        # Logic điều khiển giao diện game RPG
│   ├── index.html        # Giao diện chính của game
│   └── style.css         # Hệ thống định kiểu CSS toàn cục
├── deploy/               # Cấu hình Deploy (Coolify, Docker)
├── requirements.txt      # Thư viện Python dependencies
├── package.json          # Quản lý thư viện JS (nếu có)
└── .gitignore            # Cấu hình bỏ qua các tệp không cần thiết
```

---

## 💻 Hướng Dẫn Cài Đặt & Chạy Cục Bộ

### 1. Thiết Lập Backend (Python)

1.  Di chuyển vào thư mục dự án và khởi tạo môi trường ảo (virtual environment):
    ```bash
    python -m venv venv
    venv\Scripts\activate      # Trên Windows
    source venv/bin/activate    # Trên macOS/Linux
    ```
2.  Cài đặt các thư viện cần thiết:
    ```bash
    pip install -r requirements.txt
    ```
3.  Tạo tệp `.env` dựa trên tệp cấu hình mẫu `.env.example` và cấu hình các API Key của Gemini/OpenAI, cấu hình Firebase và Qdrant DB.
4.  Khởi chạy server backend trên cổng `8002` (cổng API mặc định được cấu hình trong `frontend/config.js`):
    ```bash
    uvicorn app.main:app --reload --port 8002
    ```

### 2. Thiết Lập Frontend

1.  Khởi chạy một máy chủ tĩnh phục vụ thư mục `frontend/` ở cổng `5500`:
    *   **Cách 1 (Sử dụng dòng lệnh Python):**
        ```bash
        cd frontend
        python -m http.server 5500
        ```
    *   **Cách 2 (Sử dụng VS Code Live Server):** Nhấp chuột phải vào file `frontend/index.html` và chọn **Open with Live Server** (mặc định chạy ở cổng `5500`).
2.  Truy cập vào trình duyệt:
    *   Trang người chơi: `http://localhost:5500`
    *   Trang quản trị (Admin Console): `http://localhost:5500/admin.html`

---

## 🚢 Hướng Dẫn Deploy (Coolify + WSL + Cloudflare Tunnel)

Dự án hỗ trợ deploy tự động thông qua **Coolify PaaS** chạy trên môi trường **WSL 2 (Windows Subsystem for Linux)** cục bộ, kết hợp dịch vụ proxy bảo mật **Cloudflare Tunnel**:

1.  **Thiết lập Coolify trên WSL:**
    *   Kích hoạt WSL 2 Ubuntu trên Windows và cài đặt Docker Engine.
    *   Cài đặt Coolify bằng lệnh terminal:
        ```bash
        curl -fsSL https://cdn.coollabs.io/coolify/install.sh | bash
        ```
2.  **Cấu hình Deploy:**
    *   Coolify lắng nghe webhook từ kho GitHub để tự động build và cập nhật (CI/CD) khi có commit mới trên nhánh `main`.
    *   Sử dụng cấu hình chạy dịch vụ đa container từ tệp `deploy/docker-compose.yml`.
3.  **Cloudflare Tunnel:**
    *   Cài đặt `cloudflared` trên WSL Ubuntu để tạo đường hầm mã hóa liên kết máy chủ cục bộ với Cloudflare Edge.
    *   Định cấu hình định tuyến tên miền phụ trong tệp `~/.cloudflared/config.yml` trỏ về các cổng tương ứng của Docker container chạy trên WSL:
        ```yaml
        tunnel: YOUR_TUNNEL_UUID
        credentials-file: /root/.cloudflared/YOUR_TUNNEL_UUID.json

        ingress:
          - hostname: aistoryadventure.xyz
            service: http://localhost:5500      # Cổng Frontend
          - hostname: api.aistoryadventure.xyz
            service: http://localhost:8002      # Cổng Backend FastAPI
          - service: http_status:404
        ```
    *   Kích hoạt chạy daemon dịch vụ tunnel:
        ```bash
        sudo systemctl restart cloudflared
        ```

---

## 🛡️ Bản Quyền & Giấy Phép
Dự án được phát triển nhằm mục đích phục vụ nghiên cứu công nghệ AI tương tác thế hệ mới. Toàn bộ mã nguồn và tài nguyên thiết kế thuộc bản quyền nhóm phát triển dự án AI Story Adventure.
