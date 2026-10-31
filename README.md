# Odoo 20 Dockerized Enterprise Architecture

Hệ thống triển khai **Odoo 20 (Community Edition)** chạy trên nền tảng **Python 3.12**, cơ sở dữ liệu **PostgreSQL 18** và được đóng gói hoàn chỉnh bằng **Docker & Docker Compose**. Dự án tích hợp sẵn các giải pháp chuyển đổi số chuyên sâu về Quản lý Tài liệu (**DMS**), Đào tạo Trực tuyến (**E-Learning**), Vòng đời Sản phẩm (**PLM**), và Báo cáo Kế toán Chuẩn Việt Nam (**VAS**).

---

## 📑 Mục lục
1. [Cấu trúc Thư mục Dự án](#1-cấu-trúc-thư-mục-dự-án)
2. [Các Module Trọng tâm](#2-các-module-trọng-tâm)
3. [Hướng dẫn Cài đặt & Chạy từ A-Z](#3-hướng-dẫn-cài-đặt--chạy-từ-a-z)
4. [Bảo mật & Biến Môi trường](#4-bảo-mật--biến-môi-trường)
5. [Tự động Sao lưu (Backup)](#5-tự-động-sao-lưu-backup)
6. [Quy trình CI/CD & Deploy Production](#6-quy-trình-cicd--deploy-production)

---

## 📁 1. Cấu trúc Thư mục Dự án

```text
odoo20-docker/
├── .github/workflows/        # Quy trình CI/CD tự động (GitHub Actions)
│   └── ci.yml                # Kiểm tra cú pháp Python, validate manifest & Docker build test
├── custom_addons/            # TẦNG 1: CÁC MODULE CUSTOM ĐẶC THÙ DOANH NGHIỆP
│   ├── tdb_dms_custom/       # Mở rộng Quản lý tài liệu (Thùng rác, Lọc ngày, Modal xem trước)
│   ├── tdb_slides_custom/    # Mở rộng E-Learning (Quản lý video, Stream IIS/Disk, Quiz)
│   ├── tdb_website_custom/   # Giao diện Website & Nhận diện thương hiệu
│   ├── custom_home_menu/     # Giao diện Menu 9 chấm hiện đại (Fullscreen Home Menu)
│   └── custom_editor_toolbar/# Thanh công cụ soạn thảo WYSIWYG, bộ chọn font chữ
├── addons/                   # TẦNG 2: CÁC MODULE CỘNG ĐỒNG (OCA) & BÁO CÁO VIỆT NAM (VAS)
│   ├── dms/                  # Document Management System chuẩn quốc tế từ hiệp hội OCA
│   ├── plm/                  # Product Lifecycle Management (Quản lý BOM, ECO, CAD)
│   ├── vn_core/              # Core Kế toán Việt Nam
│   ├── l10n_vn_vas_reports/  # Báo cáo Tài chính & Sổ sách kế toán (TT 200 / TT 133)
│   ├── l10n_vn_stock_reports/# Báo cáo Kho chuẩn VAS (Thẻ kho S12, Sổ chi tiết S10)
│   └── l10n_vn_mrp_reports/  # Báo cáo Sản xuất chuẩn VAS (Bảng tính giá thành S37)
├── config/                   # Cấu hình hệ thống Odoo
│   ├── odoo.conf.example     # Mẫu cấu hình chuẩn (dùng để tạo odoo.conf khi deploy)
│   └── odoo.conf             # Cấu hình cục bộ (chứa mật khẩu thật - ĐÃ BỊ GITIGNORE)
├── scripts/                  # Script vận hành & tự động hóa trên Windows Server / Linux
│   ├── backup_odoo.ps1       # Tự động sao lưu Database & Filestore nén ZIP
│   ├── register_backup_task.ps1 # Đăng ký lịch sao lưu 21:00 hàng ngày (Task Scheduler)
│   └── register_odoo_service.ps1# Đăng ký Odoo chạy ngầm 24/7 khi khởi động máy
├── .env.example              # File mẫu biến môi trường (Database user, password, port)
├── .gitignore                # Chặn rò rỉ mã nguồn nhạy cảm, log, data và cache
├── compose.yaml              # Cấu hình Docker Compose đa dịch vụ (Odoo 20 + PostgreSQL 18)
├── Dockerfile                # Image Odoo 20 tích hợp LibreOffice headless và font chữ
└── README.md                 # Tài liệu hướng dẫn sử dụng và triển khai
```

---

## 🎯 2. Các Module Trọng tâm

### 📄 A. Hệ thống Quản lý Tài liệu (DMS - Document Management System)
* **`addons/dms`**: Nền tảng DMS tiêu chuẩn quốc tế từ **OCA** (Odoo Community Association), thay thế hoàn hảo phân hệ trả phí Odoo Documents Enterprise.
* **`custom_addons/tdb_dms_custom`**:
  * Giao diện cây thư mục phân cấp chuyên nghiệp.
  * Tính năng **Thùng rác (Recycle Bin)** tự động dọn dẹp an toàn.
  * **Bộ lọc tài liệu theo ngày** trực quan (Hôm nay, 7 ngày, 30 ngày, Khoảng tùy chọn).
  * **Modal xem trước tài liệu** toàn màn hình (hỗ trợ PDF, Word, Excel, PowerPoint, Ảnh, Video).

### 🎓 B. Hệ thống Đào tạo Trực tuyến (E-Learning / Website Slides)
* **`custom_addons/tdb_slides_custom`**:
  * Tích hợp kho video nội bộ (hỗ trợ streaming video từ ổ đĩa máy chủ hoặc máy chủ web IIS qua giao thức HTTP `Accept-Ranges`).
  * Trình phát video chuyên dụng chống tải lậu, lưu tiến độ học tập theo thời gian thực.
  * Bộ trắc nghiệm (Quiz), tính điểm tự động và cấp chứng chỉ hoàn thành khóa học.

### 🏭 C. Quản lý Vòng đời Sản phẩm (PLM - Product Lifecycle Management)
* **`addons/plm`**: Quản lý phiên bản sản phẩm (Product Revisions), bảng định mức nguyên vật liệu (Engineering BOM), quy trình thay đổi kỹ thuật (ECO - Engineering Change Order).

### 🇻🇳 D. Hệ thống Báo cáo Kế toán Chuẩn Việt Nam (VAS)
* Tích hợp trọn bộ báo cáo tài chính và sổ sách theo **Thông tư 200/2014/TT-BTC** và **Thông tư 133/2016/TT-BTC**:
  * **Báo cáo tài chính:** B01-DN (Bảng cân đối kế toán), B02-DN (Báo cáo KQKD), B03-DN (Lưu chuyển tiền tệ), B09-DN (Thuyết minh BCTC).
  * **Sổ kế toán tổng hợp:** S03a-DN (Nhật ký chung), S03b-DN (Sổ Cái), S06-DN (Cân đối số phát sinh).
  * **Sổ chi tiết & Thuế:** S31-DN (Công nợ), S35-DN (Bán hàng), Tờ khai thuế GTGT 01/GTGT.
  * **Kho & Sản xuất:** S12-DN (Thẻ kho), S37-DN (Bảng tính giá thành sản phẩm).

---

## 🚀 3. Hướng dẫn Cài đặt & Chạy từ A-Z

### Yêu cầu Tiên quyết
* Cài đặt sẵn **Docker** và **Docker Compose** (hoặc **Docker Desktop** trên Windows/macOS).
* Đã cài đặt Git.

### Bước 1: Sao chép Mã nguồn (Clone Repository)
```bash
git clone https://github.com/tdbsolutionit/Odoo20.git
cd Odoo20
```

### Bước 2: Thiết lập Biến Môi trường & File Cấu hình
1. Tạo file `.env` từ `.env.example`:
   ```bash
   # Trên Linux/macOS
   cp .env.example .env

   # Trên Windows PowerShell
   Copy-Item .env.example .env
   ```
2. Chỉnh sửa mật khẩu an toàn trong `.env`:
   ```dotenv
   POSTGRES_DB=postgres
   POSTGRES_USER=odoo
   POSTGRES_PASSWORD=MatKhauBaoMatCuaBan
   ODOO_PORT=8069
   ODOO_ADMIN_PASSWORD=MatKhauAdminDatabaseManager
   ```

3. Tạo file `config/odoo.conf` từ `config/odoo.conf.example`:
   ```bash
   # Trên Linux/macOS
   cp config/odoo.conf.example config/odoo.conf

   # Trên Windows PowerShell
   Copy-Item config\odoo.conf.example config\odoo.conf
   ```
   *(Điền `db_password` trong file `config/odoo.conf` khớp với `POSTGRES_PASSWORD` trong `.env`)*.

### Bước 3: Khởi chạy Hệ thống Container
```bash
docker compose up -d
```
> **💡 Lưu ý:** Lần đầu khởi động, Docker sẽ build image `odoo:20.0-custom` (cài đặt Odoo 20 source, LibreOffice headless và font chữ hệ thống). Quá trình này diễn ra trong khoảng 2 - 3 phút.

### Bước 4: Kiểm tra Trạng thái
```bash
docker compose ps
```
Cả hai container `odoo20` và `odoo20-db` (status: `healthy`) chuyển sang `Up` là hệ thống đã sẵn sàng.

### Bước 5: Truy cập Ứng dụng
1. Mở trình duyệt tại: **[http://localhost:8069](http://localhost:8069)**
2. Nhập **Master Password** (đã đặt trong `config/odoo.conf`) để tạo Database mới.
3. Vào menu **Apps**, tìm kiếm và kích hoạt các module:
   * **DMS** (`dms` và `tdb_dms_custom`)
   * **E-Learning** (`website_slides` và `tdb_slides_custom`)
   * **PLM** (`plm`)
   * **VAS Reports** (`l10n_vn_vas_reports`)

---

## 🔒 4. Bảo mật & Biến Môi trường

Dự án áp dụng nguyên tắc **Zero-Secret in Codebase**:
1. **Không commit mật khẩu thật:**
   * File `config/odoo.conf` chứa master password hash và database password thật đã được đưa vào `.gitignore`.
   * File `.env` chứa mật khẩu production bị chặn bởi `.gitignore`.
   * File mẫu `.env.example` và `config/odoo.conf.example` chỉ cung cấp placeholder.
2. **Bộ lọc `.gitignore` tiêu chuẩn:**
   * Ngăn chặn toàn bộ database data (`postgres-data/`), filestore (`odoo-data/`), file tạm (`scratch/`), video lưu trữ (`videos/`).
   * Không lưu các file bytecode Python (`__pycache__`, `*.pyc`).
   * Tách biệt các module gốc Odoo core ra khỏi git để tránh xung đột mã nguồn.

---

## 💾 5. Tự động Sao lưu (Backup)

Thư mục `scripts/` cung cấp giải pháp sao lưu định kỳ cho Windows Server và môi trường Production:
* **Sao lưu thủ công:**
  ```powershell
  .\scripts\backup_odoo.ps1 -DbName "odoo20" -DbPassword "MatKhauDB" -BackupDir "D:\odoo_backups"
  ```
* **Đăng ký tự động sao lưu lúc 21:00 hàng ngày (Run as Administrator):**
  ```powershell
  .\scripts\register_backup_task.ps1
  ```

---

## 🔄 6. Quy trình CI/CD & Deploy Production

### 1. Kiến trúc CI/CD (GitHub Actions)
Pipeline được định nghĩa tại [`.github/workflows/ci.yml`](.github/workflows/ci.yml) với 3 giai đoạn tự động:
1. **Lint & Validation (CI):**
   * Biên dịch kiểm tra lỗi cú pháp Python toàn bộ `custom_addons/` và `addons/`.
   * Kiểm tra định dạng và cấu trúc tệp `__manifest__.py` của tất cả các module.
2. **Docker Build Test (CI):**
   * Thử nghiệm build Docker image trên runner Ubuntu để đảm bảo Dockerfile luôn tương thích và không bị lỗi phụ thuộc hệ điều hành.
3. **Automated Deployment (CD):**
   * Tự động kích hoạt khi có commit mới được merge vào nhánh `main`.

### 2. Hướng dẫn Triển khai Lên Server Production (VPS / Cloud Server)
Khi triển khai lên máy chủ Linux (Ubuntu 22.04 / Debian 12):

1. **Chuẩn bị môi trường trên VPS:**
   ```bash
   sudo apt-get update && sudo apt-get install -y docker.io docker-compose-plugin git
   sudo usermod -aG docker $USER
   ```

2. **Clone mã nguồn về thư mục làm việc:**
   ```bash
   cd /opt
   git clone https://github.com/tdbsolutionit/Odoo20.git odoo20-docker
   cd odoo20-docker
   ```

3. **Cấu hình bảo mật môi trường Production:**
   ```bash
   cp .env.example .env
   cp config/odoo.conf.example config/odoo.conf
   nano .env            # Điền mật khẩu mạnh cho Database và Admin
   nano config/odoo.conf# Khớp thông tin db_password
   ```

4. **Khởi chạy dưới dạng dịch vụ:**
   ```bash
   docker compose up -d
   ```

5. **Quy trình Cập nhật Không Gián đoạn (Zero Downtime Update):**
   Mỗi khi có cập nhật mới trên GitHub:
   ```bash
   git pull origin main
   # Nâng cấp module tự động trong container mà không làm mất dữ liệu
   docker compose exec -T odoo /opt/odoo/venv/bin/python3 /opt/odoo/src/odoo-bin -c /etc/odoo/odoo.conf -d <ten_db> -u tdb_dms_custom,tdb_slides_custom --stop-after-init
   docker compose restart odoo
   ```

---

## 📞 Hỗ trợ Kỹ thuật
* **Đơn vị phát triển:** TDB Solution Co., Ltd
* **Website:** [www.tdbsolution.com.vn](http://www.tdbsolution.com.vn)
* **Kho mã nguồn:** [https://github.com/tdbsolutionit/Odoo20](https://github.com/tdbsolutionit/Odoo20)
