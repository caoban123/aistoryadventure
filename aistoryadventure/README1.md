# README - Bộ Lệnh Quản Trị Cloudflare Tunnel, Git, Docker & WSL

## 📌 Tổng Quan

Tài liệu này tổng hợp các lệnh quan trọng để:

- Quản lý Cloudflare Tunnel
- Push code lên GitHub
- Kiểm tra và thao tác với Docker / Coolify
- Sử dụng nhanh Terminal WSL + Nano

---

# 1. 🌐 Quản Lý Cloudflare Tunnel

Dùng để điều phối, chỉnh sửa và vận hành luồng mạng từ internet (Cloudflare) về các cổng nội bộ trên máy chủ.

---

## ✏️ Mở file cấu hình Tunnel

```bash
nano /root/.cloudflared/config.yml
```

---

## 📂 Đồng bộ file cấu hình ra hệ thống

```bash
sudo cp /root/.cloudflared/config.yml /etc/cloudflared/config.yml
```

---

## 🔄 Khởi động lại dịch vụ Tunnel

Áp dụng cấu hình mới sau khi chỉnh sửa.

```bash
sudo systemctl restart cloudflared
```

---

## ⛔ Tắt dịch vụ Tunnel

Dùng khi cần debug trực tiếp.

```bash
sudo systemctl stop cloudflared
```

---

## 🖥️ Chạy Tunnel trực tiếp để xem log realtime

```bash
cloudflared tunnel run ai-story-tunnel
```

---

## 🔍 Kiểm tra phản hồi HTTP và debug mạng

Lệnh cực mạnh để bóc tách lỗi SSL / DNS / Routing.

```bash
curl -Iv https://aistoryadventure.xyz
```

---

# 2. 🚀 Quy Trình Git Push Lên GitHub

---

## ✅ Cách 1: Push tiêu chuẩn

Dùng khi máy đã lưu token GitHub.

### 1. Kiểm tra trạng thái file

```bash
git status
```

### 2. Thêm file thay đổi

```bash
git add frontend/config.js
```

Hoặc thêm toàn bộ:

```bash
git add .
```

### 3. Commit thay đổi

```bash
git commit -m "fix: update production API_BASE URL for frontend"
```

### 4. Push lên GitHub

```bash
git push origin main
```

> ⚠️ Thay `main` bằng tên branch thực tế nếu khác.

---

## 🔥 Cách 2: Ép Push trực tiếp bằng Token

Dùng khi Git bị kẹt xác thực hoặc đòi mật khẩu cũ.

```bash
git push https://TÊN_ACCOUNT_GITHUB:MÃ_TOKEN_GHP_CỦA_BẠN@github.com/TÊN_ACCOUNT_GITHUB/TÊN_REPO_CỦA_BẠN.git main
```

---

## 💡 Xóa cache mật khẩu Git cũ

```bash
git config --global --unset credential.helper
```

---

## 💾 Lưu Token vĩnh viễn

Chỉ cần nhập lại token một lần.

```bash
git config --global credential.helper store
```

---

# 3. 🐳 Docker & Coolify

Các lệnh giúp kiểm tra container và can thiệp sâu vào hệ thống Coolify.

---

## 🌍 Mở giao diện Coolify

```text
http://localhost:8000
```

---

## 📋 Liệt kê container đang chạy + Ports

```bash
docker ps --format "table {{.Names}}\t{{.Ports}}"
```

---

## 🧾 Chỉ lấy tên container

```bash
docker ps --format "{{.Names}}"
```

---

## 🌐 Lấy Docker IP của container

```bash
docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' TÊN_CONTAINER
```

---

## 🔐 Reset mật khẩu Coolify Dashboard

```bash
docker exec -it coolify php artisan App\Models\User::first()->update(['password' => bcrypt('MậtKhauMớiCủaBạn')])
```

---

# 4. ⚡ Phím Tắt Nano Trong WSL

Khi đang chỉnh sửa file bằng `nano`.

---

## ✂️ Xóa nhanh một dòng

```text
Ctrl + K
```

---

## 💾 Lưu file

```text
Ctrl + O
```

Sau đó nhấn:

```text
Enter
```

---

## 🚪 Thoát Nano

```text
Ctrl + X
```

---

## 📋 Paste vào Terminal WSL

```text
Chuột phải (Right Click)
```

Tự động dán nội dung vừa copy từ Windows.

---

# 🧠 Workflow Khuyên Dùng

## Sau khi sửa config Tunnel

```bash
nano /root/.cloudflared/config.yml
sudo cp /root/.cloudflared/config.yml /etc/cloudflared/config.yml
sudo systemctl restart cloudflared
curl -Iv https://aistoryadventure.xyz
```

---

## Sau khi sửa code frontend/backend

```bash
git status
git add .
git commit -m "your message"
git push origin main
```

---

## Kiểm tra nhanh Docker

```bash
docker ps
```

---

# ⚠️ Lưu Ý Quan Trọng

- Không public GitHub Token (`ghp_...`) lên internet.
- Không commit file `.env`.
- Sau khi đổi config Tunnel:
  - luôn restart `cloudflared`
  - luôn test bằng `curl -Iv`
- Khi debug:
  - ưu tiên chạy trực tiếp:

```bash
cloudflared tunnel run ai-story-tunnel
```

để xem log realtime.

---

# 📚 Gợi Ý Nâng Cấp README Sau Này

Bạn có thể bổ sung thêm:

- Docker Compose commands
- PM2 commands
- Nginx reverse proxy
- SSL troubleshooting
- Backup & restore database
- CI/CD workflow
- Auto deploy scripts

---

# 🛠️ Quick Command Cheat Sheet

## Cloudflare Tunnel

```bash
sudo systemctl restart cloudflared
sudo systemctl stop cloudflared
cloudflared tunnel run ai-story-tunnel
```

---

## Git Push

```bash
git add .
git commit -m "update"
git push origin main
```

---

## Docker

```bash
docker ps
docker ps --format "{{.Names}}"
```

---

## Nano

```text
Ctrl + O = Save
Ctrl + X = Exit
Ctrl + K = Delete line
```

---

# 🔥 Debug Checklist

## Nếu website không truy cập được:

### 1. Kiểm tra Tunnel

```bash
sudo systemctl status cloudflared
```

### 2. Kiểm tra HTTP Response

```bash
curl -Iv https://aistoryadventure.xyz
```

### 3. Kiểm tra container có chạy không

```bash
docker ps
```

### 4. Kiểm tra port nội bộ

```bash
docker ps --format "table {{.Names}}\t{{.Ports}}"
```

### 5. Chạy Tunnel realtime để xem log

```bash
cloudflared tunnel run ai-story-tunnel
```

---

# 📁 Cấu Trúc File Gợi Ý

```text
/root/.cloudflared/
├── config.yml
├── cert.pem
└── tunnel.json
```

---

# 🚀 Best Practice

- Luôn backup file config trước khi sửa
- Không push token lên GitHub
- Dùng `.env` cho secret
- Commit message nên rõ ràng
- Sau khi đổi config:
  - restart service
  - test bằng curl
  - check logs realtime

---

# 🧩 Công Cụ Đề Xuất

| Công cụ | Mục đích |
|---|---|
| Cloudflare Tunnel | Reverse Proxy / Public Access |
| Docker | Container Runtime |
| Coolify | Self-hosted PaaS |
| GitHub | Version Control |
| WSL | Linux Environment |
| Nano | Terminal Text Editor |

---

# ✅ Kết Luận

Đây là bộ lệnh nền tảng cực kỳ hữu ích cho:

- Self-hosted server
- Docker deployment
- Cloudflare networking
- Git workflow
- Debug production systems

Bạn có thể dùng README này như một “DevOps Cheat Sheet” cá nhân để thao tác nhanh hàng ngày.
