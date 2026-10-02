# Hướng dẫn Chạy Odoo 20 & PostgreSQL trên Docker từ A-Z

Hệ thống triển khai **Odoo 20 (Community Edition)** chạy trên môi trường **Python 3.12** kết hợp cùng cơ sở dữ liệu **PostgreSQL 18** hoàn toàn bằng Docker & Docker Compose.

---

## 📁 1. Cấu trúc thư mục dự án (Kiến trúc Đa Khách Hàng)

```text
odoo20-docker/
├── AGENTS.md            # Quy chuẩn bắt buộc cho AI/Dev: Kế thừa chuẩn, không hack core
├── Dockerfile           # Kéo base odoobot/odoo:20.0 và cài Odoo 20 từ source
├── compose.yaml         # Cấu hình container Odoo 20 và PostgreSQL 18 cho Client Test
├── config/
│   └── odoo.conf        # Cấu hình Odoo (addons_path nạp shared-addons và extra-addons)
├── shared-addons/       # TẦNG 1: DÙNG CHUNG CHO MỌI KHÁCH HÀNG
│   └── custom_editor_toolbar/ # Module thanh công cụ soạn thảo cố định, nút +/- font, font type
├── addons/              # TẦNG 2: MODULE DÀNH CHO DỰ ÁN HIỆN TẠI (Client Test)
│   ├── sale/
│   ├── sale_management/
│   └── custom_sale_order/
├── clients/             # TẦNG 3: MÔI TRƯỜNG CHO CÁC KHÁCH HÀNG MỚI TIẾP THEO
│   ├── README.md
│   └── client-company-A/# Mẫu sẵn có cho Khách hàng A (chạy cổng riêng)
├── huong_dan_lay_module.md # Hướng dẫn chi tiết cách lấy & cài đặt module
└── README.md            # Tài liệu hướng dẫn sử dụng
```

---

## 🚀 2. Các bước tự chạy Docker

### Bước 1: Mở Terminal tại thư mục dự án
Mở PowerShell, Command Prompt hoặc Git Bash tại thư mục dự án:
```powershell
cd c:\Work\odoo20-docker
```

### Bước 2: Khởi động hệ thống Container
Chạy lệnh sau để Docker tự động dựng và khởi chạy các container dưới chế độ nền (`detached mode`):

```powershell
docker compose up -d
```
> **Lưu ý:** Lần đầu chạy, Docker sẽ build image `odoo:20.0-custom` (tải mã nguồn Odoo 20 và đóng gói). Các lần chạy tiếp theo sẽ khởi động ngay lập tức trong vài giây.

### Bước 3: Kiểm tra trạng thái hoạt động
Kiểm tra xem 2 container `odoo20` và `odoo20-db` đã chạy ổn định chưa:
```powershell
docker compose ps
```
*Kết quả hiển thị trạng thái `Up` (và `odoo20-db` hiển thị `healthy`) là hệ thống đã sẵn sàng.*

### Bước 4: Xem log hoạt động (nếu cần theo dõi)
```powershell
# Xem log liên tục của Odoo
docker compose logs -f odoo

# Xem log liên tục của cơ sở dữ liệu PostgreSQL
docker compose logs -f db
```
*(Nhấn `Ctrl + C` để thoát màn hình theo dõi log)*

---

## 🌐 3. Hướng dẫn truy cập và thiết lập Odoo 20

### Bước 1: Mở trình duyệt web
Truy cập vào địa chỉ:
👉 **[http://localhost:8069](http://localhost:8069)**

### Bước 2: Khởi tạo Cơ sở dữ liệu (Database)
Khi mở trang lần đầu, màn hình **Database Manager** sẽ xuất hiện:

| Mục | Thông tin cần điền | Ghi chú |
| :--- | :--- | :--- |
| **Master Password** | `admin` | Mật khẩu quản trị database (đã cấu hình trong `config/odoo.conf`) |
| **Database Name** | Ví dụ: `odoo20_db` | Tên cơ sở dữ liệu (viết liền không dấu, dùng chữ thường hoặc dấu gạch dưới) |
| **Email** | Ví dụ: `admin@example.com` | Tên tài khoản để đăng nhập Odoo |
| **Password** | Nhập mật khẩu bạn muốn đặt | Mật khẩu để đăng nhập Odoo |
| **Phone number** | Số điện thoại (tuỳ chọn) | Có thể để trống |
| **Language** | English (US) / Vietnamese | Ngôn ngữ giao diện |
| **Country** | Vietnam | Quốc gia |
| **Demo data** | Tích chọn hoặc bỏ chọn | Tích chọn nếu muốn có sẵn dữ liệu mẫu để thử nghiệm tính năng |

Bấm nút **Create database**. Hệ thống sẽ tiến hành tạo cấu trúc bảng và cài đặt các module cơ sở (mất khoảng 1 - 2 phút).

### Bước 3: Đăng nhập và bắt đầu sử dụng
Sau khi tạo xong, hệ thống sẽ tự động chuyển vào trang danh sách ứng dụng (**Apps**). Tại đây bạn có thể cài đặt các phân hệ như:
- **Sales (Bán hàng)**
- **Invoicing / Accounting (Kế toán)**
- **Inventory (Kho vận)**
- **CRM**, **Purchase**, **Website**, v.v.

---

## 🧩 4. Cách phát triển và cài đặt Custom Addon

1. Đặt thư mục module của bạn vào bên trong thư mục [addons/](file:///c:/Work/odoo20-docker/addons):
   ```text
   addons/
   └── my_custom_module/
       ├── __init__.py
       ├── __manifest__.py
       └── ...
   ```
2. Khởi động lại container Odoo để nhận diện file mới:
   ```powershell
   docker compose restart odoo
   ```
3. Trên giao diện Odoo web:
   - Vào **Settings** -> Cuộn xuống mục Developer Tools -> Bấm **Activate the developer mode**.
   - Vào menu **Apps** -> Bấm **Update Apps List** trên thanh điều hướng.
   - Tìm kiếm tên module của bạn và bấm **Activate (Install)**.

---

## ⚡ 5. Bảng tổng hợp các lệnh Init & Restart thường dùng

### 🟢 A. Nhóm lệnh Khởi tạo & Bật hệ thống (Init)

| Tình huống / Mục đích | Lệnh thực hiện (PowerShell / CMD) |
| :--- | :--- |
| **Khởi động hệ thống lần đầu / bật lại sau khi mở máy** | `docker compose up -d` |
| **Khởi tạo & nạp toàn bộ tùy chỉnh (Thanh công cụ popup, Menu 9 chấm Enterprise, Báo giá)** | `docker cp update_views.py odoo20:/tmp/update_views.py; docker exec odoo20 python3 /tmp/update_views.py` |
| **Lưu vĩnh viễn cấu hình vào Docker Image (tránh bị mất khi restart máy)** | `docker commit odoo20 odoo:20.0-custom` |
| **Nâng cấp/cập nhật module qua dòng lệnh (CLI)** | `docker exec -it odoo20 python3 /opt/odoo/src/odoo-bin -c /etc/odoo/odoo.conf -d odoo20_dev -u sale,web,html_editor --stop-after-init` |
| **Build lại toàn bộ Docker Image khi sửa `Dockerfile`** | `docker compose up -d --build` |

---

### 🔄 B. Nhóm lệnh Khởi động lại (Restart)

| Tình huống / Mục đích | Lệnh thực hiện (PowerShell / CMD) |
| :--- | :--- |
| **Khởi động lại nhanh container Odoo (khi sửa file Python/XML trong addons)** | `docker restart odoo20`<br>*(hoặc `docker compose restart odoo`)* |
| **Khởi động lại toàn bộ dịch vụ (cả Odoo và PostgreSQL)** | `docker compose restart` |
| **Tắt sạch và bật lại hoàn chỉnh hệ thống** | `docker compose down && docker compose up -d` |
| **Tạm dừng hệ thống khi không làm việc** | `docker compose stop` |
| **Bật lại hệ thống sau khi tạm dừng** | `docker compose start` |

---

### 📋 C. Quy trình làm việc chuẩn hàng ngày

1. **Bắt đầu làm việc (mở container):**
   ```powershell
   cd c:\Work\odoo20-docker
   docker compose up -d
   ```

2. **Khi chỉnh sửa file code trong thư mục `addons/`:**
   ```powershell
   docker restart odoo20
   ```
   *Sau đó trên trình duyệt nhấn `Ctrl + F5` để thấy thay đổi.*

3. **Khi chạy cập nhật giao diện & view (`update_views.py`):**
   ```powershell
   docker cp update_views.py odoo20:/tmp/update_views.py; docker exec odoo20 python3 /tmp/update_views.py
   docker commit odoo20 odoo:20.0-custom
   docker restart odoo20
   ```

4. **Kiểm tra trạng thái & Theo dõi log:**
   ```powershell
   # Kiểm tra trạng thái các container
   docker compose ps

   # Theo dõi log Odoo liên tục (Ctrl + C để thoát)
   docker compose logs -f odoo
   ```

---

## ⚠️ 6. Các lệnh dọn dẹp & Lưu ý quan trọng

| Lệnh | Ý nghĩa & Cảnh báo |
| :--- | :--- |
| `docker compose down` | Dừng và xóa container. **Dữ liệu database trong volume được giữ nguyên an toàn 100%.** |
| `docker compose down -v` | ⚠️ **CẢNH BÁO NGUY HIỂM:** Xóa sạch toàn bộ container và **xóa trắng cơ sở dữ liệu** (reset về ban đầu). Chỉ dùng khi muốn làm mới hoàn toàn. |

