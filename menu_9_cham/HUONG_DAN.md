# Hướng Dẫn Kích Hoạt Menu 9 Chấm (App Switcher Fullscreen) Trên Server

Thư mục này chứa 3 file giao diện đã được tùy biến để tạo Menu 9 chấm (Home Menu kiểu Odoo Enterprise):
1. `navbar.js`: Xử lý đóng/mở toàn màn hình, tìm kiếm ứng dụng, phím tắt Escape/Enter.
2. `navbar.scss`: Giao diện tối sang trọng, lưới icon ứng dụng, hiệu ứng mượt mà.
3. `navbar.xml`: Nút bấm 9 chấm trên thanh navbar và màn hình tìm kiếm app toàn màn hình.

---

## 📌 Cách áp dụng trên Server Odoo 20:

Khi bạn `git clone` hoặc `git pull` repo này về Server (ví dụ tại `/opt/odoo/my_repo`):

Chỉ cần copy đè 3 file này vào thư mục `web/static/src/webclient/navbar/` của mã nguồn Odoo trên server:

### Lệnh thực hiện trên Linux/Ubuntu Server:
```bash
# Giả sử mã nguồn Odoo 20 trên server của bạn nằm ở /opt/odoo/src hoặc /opt/odoo/odoo:
sudo cp /opt/odoo/my_repo/menu_9_cham/* /opt/odoo/src/addons/web/static/src/webclient/navbar/

# Phân quyền lại cho user odoo
sudo chown -R odoo:odoo /opt/odoo/src/addons/web/static/src/webclient/navbar/

# Khởi động lại service Odoo
sudo systemctl restart odoo
```

*(Nếu Odoo nằm ở đường dẫn khác, bạn dùng lệnh `find / -name "navbar.xml" 2>/dev/null` để tìm vị trí chính xác trên server).*

Sau đó mở trình duyệt, bấm **Ctrl + Shift + R** (xóa cache web) là menu 9 chấm sẽ xuất hiện ngay lập tức!
