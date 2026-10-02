# Thư mục Extra Addons / Custom Modules

Thư mục này được mount trực tiếp vào container Odoo tại đường dẫn: `/mnt/extra-addons`.

### Cách sử dụng:
1. Đặt các module Odoo tự phát triển hoặc tải từ third-party vào đây.
   Ví dụ:
   ```text
   addons/
   └── my_module/
       ├── __manifest__.py
       ├── __init__.py
       ├── models/
       └── views/
   ```
2. Khởi động lại Odoo để nhận diện file mới:
   ```powershell
   docker compose restart odoo
   ```
3. Bật **Developer Mode** trong Odoo web -> Vào menu **Apps** -> Bấm **Update Apps List** -> Tìm module và bấm **Activate**.

👉 Xem tài liệu hướng dẫn chạy hệ thống: [README.md](../README.md)  
👉 Xem hướng dẫn lấy và cài đặt module từ web/docker: [huong_dan_lay_module.md](../huong_dan_lay_module.md)
