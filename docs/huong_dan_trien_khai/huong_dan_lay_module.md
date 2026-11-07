# Hướng Dẫn Lấy & Cài Đặt Module Odoo Từ A-Z

Tài liệu này hướng dẫn bạn cách:

1. **Trích xuất module gốc có sẵn từ Odoo (trong container)** ra máy tính để đọc và tùy chỉnh trực tiếp.
2. **Tải module từ kho ứng dụng Odoo Apps Store (`apps.odoo.com`) hoặc GitHub** về dự án để sử dụng.
3. **Kích hoạt và cài đặt module** lên hệ thống Odoo 20.

---

## 📦 PHẦN 1: Trích xuất Module gốc từ bên trong Docker ra máy tính

Cách này dùng khi bạn muốn lấy các module có sẵn của Odoo như `sale` (Bán hàng), `crm`, `stock` (Kho), `account` (Hóa đơn/Kế toán), `purchase` (Mua hàng![alt text](image.png))... ra máy tính để sửa đổi.

### Bước 1: Xem tên các module có sẵn trong container

Mở Terminal (PowerShell) tại thư mục `c:\Work\odoo20-docker` và gõ:

```powershell
# Xem toàn bộ danh sách module gốc
docker exec odoo20 ls /opt/odoo/src/addons

# Hoặc tìm kiếm module theo từ khóa (ví dụ: sale, crm, stock, account)
docker exec odoo20 ls /opt/odoo/src/addons | Select-String "sale"
```

### Bước 2: Dùng lệnh `docker cp` để copy module ra thư mục `addons/`

Cú pháp:

```powershell
docker cp odoo20:/opt/odoo/src/addons/<tên_module> ./addons/<tên_module>
```

**Ví dụ thực tế cho các module thông dụng:**

- **Module Bán hàng (`sale`):**
  ```powershell
  docker cp odoo20:/opt/odoo/src/addons/sale ./addons/sale
  ```
- **Module Quản lý Bán hàng mở rộng (`sale_management`):**
  ```powershell
  docker cp odoo20:/opt/odoo/src/addons/sale_management ./addons/sale_management
  ```
- **Module Kho vận (`stock`):**
  ```powershell
  docker cp odoo20:/opt/odoo/src/addons/stock ./addons/stock
  ```
- **Module Quan hệ khách hàng (`crm`):**
  ```powershell
  docker cp odoo20:/opt/odoo/src/addons/crm ./addons/crm
  ```
- **Module Mua hàng (`purchase`):**
  ```powershell
  docker cp odoo20:/opt/odoo/src/addons/purchase ./addons/purchase
  ```
- **Module Kế toán / Hóa đơn (`account`):**
  ```powershell
  docker cp odoo20:/opt/odoo/src/addons/account ./addons/account
  ```

> 💡 **Kết quả:** Ngay lập tức thư mục module tương ứng sẽ xuất hiện trong thư mục `addons/` trên máy tính của bạn với đầy đủ mã nguồn Python và giao diện XML.

---

### ⚠️ Lưu ý đặc biệt về các Module Enterprise (PLM, Documents, Studio, v.v.):
Một số module như **Product Lifecycle Management (PLM - `mrp_plm`)** và **Documents (`documents`)** là module thuộc **bản quyền Odoo Enterprise (trả phí)**, nên **không có sẵn trong container Odoo Community**.

Để thay thế, dự án đã tải về 2 module mã nguồn mở miễn phí chuẩn quốc tế tương đương vào thư mục `addons/`:
1. **`addons/plm`** (Product Lifecycle Management): Giải pháp PLM mã nguồn mở chuẩn cho Odoo, hỗ trợ quản lý vòng đời sản phẩm, phiên bản BOM (BOM revisions), quy trình thay đổi kỹ thuật (ECO), và tích hợp tài liệu kỹ thuật CAD.
2. **`addons/dms`** (Document Management System): Giải pháp Quản lý tài liệu mã nguồn mở từ hiệp hội cộng đồng Odoo (OCA), thay thế hoàn hảo cho Odoo Documents với tính năng phân quyền thư mục, lưu trữ tệp, gắn nhãn tag, danh mục và cổng thông tin chia sẻ tài liệu.

Cách kích hoạt:
1. Vào Odoo -> **Apps**.
2. Tìm kiếm `plm` hoặc `dms` (xóa bộ lọc `Apps` mặc định).
3. Bấm nút **Activate (Kích hoạt)**.

---

## 🌐 PHẦN 2: Tải Module từ Odoo Apps Store hoặc GitHub

### Cách A: Tải từ Odoo Apps Store (`apps.odoo.com`)

1. Truy cập: [https://apps.odoo.com/apps](https://apps.odoo.com/apps)
2. Chọn phiên bản tương ứng trên thanh lọc (ví dụ: `20.0`, `19.0`, hoặc `18.0`).
3. Tìm kiếm module bạn cần (có thể chọn bộ lọc `Free` để tìm module miễn phí).
4. Bấm nút **Download for version ...** để tải file `.zip` về máy.
5. Giải nén file `.zip`. Bạn sẽ được một hoặc nhiều thư mục module.
6. Sao chép toàn bộ thư mục module vừa giải nén thả vào thư mục `addons/` của dự án:
   ```text
   odoo20-docker/
   └── addons/
       └── ten_module_vua_tai/
           ├── __manifest__.py
           ├── __init__.py
           └── ...
   ```

### Cách B: Tải từ GitHub (Ví dụ: Kho module cộng đồng OCA)

Nếu bạn có link Git của một module hoặc bộ module trên GitHub:

1. Mở Terminal tại thư mục `addons/`:
   ```powershell
   cd c:\Work\odoo20-docker\addons
   ```
2. Clone repository về:
   ```powershell
   git clone <link_github_repository>
   ```
3. Quay trở lại thư mục gốc dự án:
   ```powershell
   cd c:\Work\odoo20-docker
   ```

---

## ⚙️ PHẦN 3: Kích Hoạt & Cài Đặt Module Lên Odoo

Sau khi đã có module trong thư mục `addons/`, thực hiện 3 bước sau:

### Bước 1: Khởi động lại container Odoo

Lệnh này giúp Odoo quét và nhận diện thư mục module mới:

```powershell
docker compose restart odoo
```

### Bước 2: Bật Developer Mode trên giao diện Odoo

1. Mở trình duyệt vào Odoo: **[http://localhost:8069](http://localhost:8069)**
2. Đăng nhập vào cơ sở dữ liệu của bạn.
3. Vào menu **Settings (Cài đặt)** -> Cuộn xuống cuối trang tìm mục **Developer Tools** -> Bấm **Activate the developer mode**.
4. Biểu tượng con bọ 🐞 sẽ xuất hiện trên góc phải thanh điều hướng.

### Bước 3: Cập nhật danh sách Apps & Cài đặt

1. Vào menu **Apps (Ứng dụng)**.
2. Trên thanh menu ngang màu đen phía trên, bấm nút **Update Apps List** -> Bấm xác nhận **Update**.
3. Tại ô tìm kiếm của trang Apps:
   - Xóa bộ lọc mặc định `Apps` đi.
   - Nhập tên module bạn vừa thêm vào.
4. Bấm nút **Activate (Kích hoạt / Cài đặt)** trên thẻ của module.

---

## 🛠️ PHẦN 4: Các Lỗi Thường Gặp & Cách Khắc Phục

### 1. Không tìm thấy module sau khi Update Apps List

- **Nguyên nhân:** Tên thư mục module chưa có file `__manifest__.py` hoặc đặt lồng thư mục con không đúng chuẩn.
- **Khắc phục:** Đảm bảo đường dẫn trực tiếp có dạng: `addons/<ten_module>/__manifest__.py`.

### 2. Lỗi thiếu module phụ thuộc (`Missing Dependencies`)

- **Nguyên nhân:** Module bạn tải yêu cầu phải cài đặt các module khác trước (được khai báo trong mục `'depends': [...]` của file `__manifest__.py`).
- **Khắc phục:** Xem thông báo lỗi hiển thị tên module bị thiếu, sau đó tìm và cài đặt module đó trước rồi cài lại module chính.

### 3. Lỗi thiếu thư viện Python bên thứ 3 (`ModuleNotFoundError`)

- **Khắc phục:** Cài đặt thư viện đó trực tiếp vào môi trường Python của container:
  ```powershell
  docker compose exec odoo /opt/odoo/venv/bin/pip install <ten_thu_vien>
  docker compose restart odoo
  ```

---

## 🏢 PHẦN 5: Quy trình Lấy Module cho từng Khách hàng riêng (Multi-Client)

Khi bạn tiếp nhận một khách hàng mới (ví dụ: `client-company-A` cần module Mua hàng `purchase` hoặc Kho `stock`), thực hiện 3 bước đơn giản:

### Bước 1: Trích xuất module vào đúng thư mục của khách hàng đó

```powershell
# Trích xuất module purchase từ container vào khách hàng A:
docker cp odoo20:/opt/odoo/src/addons/purchase ./clients/client-company-A/addons/purchase

# Hoặc trích xuất module kho stock:
docker cp odoo20:/opt/odoo/src/addons/stock ./clients/client-company-A/addons/stock
```
*(Nếu tải module từ trên mạng về, bạn chỉ cần giải nén và thả vào `./clients/client-company-A/addons/`).*

### Bước 2: Mở file ra chỉnh sửa trên máy tính (VS Code)

Toàn bộ mã nguồn đã nằm trên ổ cứng máy bạn:
- Sửa tính năng, logic tính toán: Mở file `.py` trong `models/`.
- Sửa giao diện, bố cục, nút bấm: Mở file `.xml` trong `views/`.
- Nhấn `Ctrl + S` để lưu. File lưu trên máy thật nên **không bao giờ bị mất khi khởi động lại Docker**.

### Bước 3: Xem kết quả chỉnh sửa

- **Nếu sửa file Python (`.py`)**: Khởi động lại container để nạp code mới:
  ```powershell
  docker compose restart odoo
  ```
- **Nếu sửa file XML giao diện (`.xml`)**:
  - Mở Odoo trên trình duyệt.
  - Vào **Apps** -> Tìm tên module bạn vừa sửa -> Bấm dấu 3 chấm -> Chọn **Upgrade (Nâng cấp)** -> F5 lại trang.

---

## 🚨 PHẦN 6: Khắc phục lỗi Màn Hình Trắng (White Screen of Death)

Lỗi màn hình trắng xảy ra khi JavaScript của Odoo gặp lỗi cú pháp (SyntaxError) hoặc bundle cache bị hỏng khiến giao diện không thể hiển thị.

### 1. Nguyên nhân thường gặp:
- **Lỗi cú pháp JS:** Khai báo trùng biến/import (ví dụ: import trùng `proxy` 2 lần trong OWL).
- **Lỗi bộ nhớ đệm Asset Bundles:** Trình duyệt hoặc cơ sở dữ liệu lưu các file JS/CSS minified bị lỗi thời.
- **Form đăng nhập bị ẩn:** Thuộc tính `d-none` trên form chưa được gỡ bỏ do script public component bị gián đoạn.

### 2. Cách kiểm tra lỗi hoàn toàn trong code (không cần mở trình duyệt):

Chạy lệnh kiểm tra cú pháp toàn bộ các file JS đã tùy biến:
```powershell
docker compose exec odoo node -e "
const fs = require('fs');
const { execSync } = require('child_process');
const files = [
    '/opt/odoo/src/addons/html_editor/static/src/wysiwyg.js',
    '/opt/odoo/src/addons/html_editor/static/src/main/toolbar/toolbar_plugin.js',
    '/opt/odoo/src/addons/html_editor/static/src/main/font/font_size_selector.js',
    '/opt/odoo/src/addons/web/static/src/webclient/navbar/navbar.js'
];
files.forEach(f => {
    try {
        execSync('node --input-type=module --check', { input: fs.readFileSync(f, 'utf8') });
        console.log('OK:', f);
    } catch (e) {
        console.log('ERROR:', f, e.stderr?.toString());
    }
});
"
```

### 3. Lệnh sửa dứt điểm lỗi màn hình trắng:

Chạy đoạn script một dòng này để xóa sạch cache Asset cũ trong Database và khởi động lại:
```powershell
# Xóa sạch asset bundles trong DB:
docker compose exec odoo python3 -c "import odoo; from odoo import api, SUPERUSER_ID; config = odoo.tools.config; config.parse_config(['-c', '/etc/odoo/odoo.conf', '-d', 'odoo20_dev']); registry = odoo.modules.registry.Registry('odoo20_dev');
with registry.cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    assets = env['ir.attachment'].search([('url', '=like', '/web/assets/%')])
    if assets:
        assets.unlink()
    cr.commit()
print('Đã dọn dẹp sạch Asset Bundles!')"

# Khởi động lại container:
docker compose restart odoo
```
Sau đó mở lại trình duyệt và nhấn `Ctrl + F5` (hoặc `Ctrl + Shift + R`) để trình duyệt tải lại toàn bộ giao diện mới!

