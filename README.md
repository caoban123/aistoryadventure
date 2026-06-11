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

3.  Tạo tệp `.env` dựa trên tệp cấu hình mẫu và điền API keys của bạn:
    ```bash
    cp .env.example .env
    ```
    *Cấu hình các API key cần thiết như `GEMINI_API_KEY`, cấu hình Firebase Admin SDK JSON, và đường dẫn tới Qdrant.*

4.  Khởi chạy server backend:
    ```bash
    uvicorn app.main:app --reload --port 8002
    ```

### 2. Thiết Lập Frontend

1.  Bạn chỉ cần khởi chạy một server tĩnh để phục vụ thư mục `frontend/`. 
2.  Nếu dùng VS Code, bạn có thể nhấn chuột phải vào `frontend/index.html` và chọn **Open with Live Server** (mặc định chạy ở cổng `5500`).
3.  Truy cập vào địa chỉ: `http://127.0.0.1:5500/index.html` trên trình duyệt để trải nghiệm game.

---

## 🚢 Hướng Dẫn Deploy (PaaS Coolify & Cloudflare)

Dự án hỗ trợ deploy tự động thông qua **Coolify** kết hợp dịch vụ proxy bảo mật **Cloudflare Tunnel**:

1.  **Coolify**: Cấu hình tệp `docker-compose` hoặc Dockerfile trong thư mục `deploy/` để build ứng dụng.
2.  **Cloudflare Tunnel**:
    *   Mở cấu hình tunnel cục bộ để trỏ tên miền chính tới cổng Docker:
        ```bash
        nano /root/.cloudflared/config.yml
        ```
    *   Đồng bộ cấu hình và khởi động lại dịch vụ Cloudflare daemon:
        ```bash
        sudo cp /root/.cloudflared/config.yml /etc/cloudflared/config.yml
        sudo systemctl restart cloudflared
        ```
    *   Kiểm tra kết nối SSL và định tuyến:
        ```bash
        curl -Iv https://aistoryadventure.xyz
        ```

---

## 🛡️ Bản Quyền & Giấy Phép
Dự án được phát triển nhằm mục đích phục vụ nghiên cứu công nghệ AI tương tác thế hệ mới. Toàn bộ mã nguồn và tài nguyên thiết kế thuộc bản quyền nhóm phát triển dự án AI Story Adventure.
