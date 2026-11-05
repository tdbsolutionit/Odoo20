# TÀI LIỆU TOÀN DIỆN VỀ HỆ THỐNG API ODOO 20 & PHÂN HỆ PLM (OMNIASOLUTIONS)

> **Dự án:** Odoo 20 Docker (`odoo20-docker`)  
> **Phiên bản:** Odoo 20.0 Community Edition (Python 3.12, PostgreSQL 18)  
> **Phân hệ chuyên sâu:** `plm` (OmniaSolutions OdooPLM v20.0.1.0.6)  
> **Tài liệu gồm 3 phần:**
> 1. [Phần A: Toàn bộ Hệ thống API Gốc của Nhân Odoo 20 (Odoo Core API)](#phần-a--toàn-bộ-hệ-thống-api-gốc-của-nhân-odoo-20-odoo-core-api)
> 2. [Phần B: Kiến trúc & API Riêng của Phân hệ PLM OmniaSolutions](#phần-b--kiến-trúc--api-riêng-của-phân-hệ-plm-omniasolutions)
> 3. [Phần C: Cheat Sheet & Mẫu Code Gọi API Thực Tế (Python, cURL, Postman, JS)](#phần-c--cheat-sheet--mẫu-code-gọi-api-thực-tế)

---

# PHẦN A — TOÀN BỘ HỆ THỐNG API GỐC CỦA NHÂN ODOO 20 (ODOO CORE API)

Trong nhân cốt lõi Odoo 20, mọi bảng dữ liệu (Model) tạo ra trong hệ thống đều tự động được phơi bày (expose) qua các cổng API tiêu chuẩn mà không cần viết thêm bất kỳ route nào.

---

## 🔑 1. CƠ CHẾ XÁC THỰC & BẢO MẬT TRONG ODOO 20

Odoo 20 hỗ trợ 3 phương thức xác thực khi gọi API từ bên ngoài:

### a. Xác thực bằng API Key (Khuyên dùng nhất cho hệ thống tích hợp)
* **Ưu điểm:** Không cần dùng mật khẩu tài khoản thật, có thể tạo nhiều key cho các phần mềm khác nhau (CAD, Mobile App, Web ngoài), có thể thu hồi từng key bất cứ lúc nào.
* **Cách tạo:** Đăng nhập Odoo bằng tài khoản User ➔ Bấm vào Avatar góc trên cùng bên phải ➔ Chọn **Preferences (Tùy chọn)** ➔ Chọn tab **Account Security (Bảo mật tài khoản)** ➔ Bấm nút **New API Key (Tạo khóa API mới)**.
* **Cách dùng:** Khi gọi API (XML-RPC hoặc JSON-RPC), tại vị trí điền `password`, bạn chỉ cần điền chuỗi `API_KEY` vừa tạo!

### b. Xác thực bằng Password thông thường
* Truyền trực tiếp `db`, `username/email`, `password` trong các hàm kết nối RPC.

### c. Xác thực Session Cookie (Dành cho Web Client / Mobile App)
* Gửi request `POST` đến `/web/session/authenticate`. Odoo sẽ trả về cookie `session_id` để đính kèm trong các HTTP request tiếp theo.

---

## 🌐 2. DANH MỤC CÁC URL ENDPOINT CỐT LÕI CỦA ODOO 20 CORE

| Nhóm chức năng | Phương thức & URL | Định dạng dữ liệu | Mục đích sử dụng |
| :--- | :--- | :---: | :--- |
| **Session** | `POST /web/session/authenticate` | JSON-RPC | Đăng nhập và lấy phiên làm việc (Session ID, quyền hạn, ngữ cảnh công ty). |
| **Session** | `POST /web/session/get_session_info` | JSON-RPC | Lấy thông tin trạng thái user hiện tại đang login. |
| **Session** | `POST /web/session/destroy` | JSON-RPC | Đăng xuất, hủy session làm việc. |
| **ORM RPC** | `POST /web/dataset/call_kw` | JSON-RPC | Cổng gọi mọi hàm ORM Model từ giao diện Web và Frontend. |
| **ORM RPC** | `POST /web/dataset/call_kw/<model>/<method>` | JSON-RPC | Cổng gọi ORM chỉ định rõ Model và Method trên URL. |
| **Action** | `POST /web/dataset/call_button` | JSON-RPC | Kích hoạt các nút bấm nghiệp vụ trên form (Duyệt đơn, Đóng kỳ, Chuyển kho...). |
| **Universal RPC**| `POST /jsonrpc` | JSON-RPC 2.0 | Cổng RPC vạn năng: nhận service `object` và method `execute_kw` để thao tác mọi model. |
| **Universal RPC**| `POST /xmlrpc/2/common` | XML-RPC | Cổng XML-RPC lấy phiên bản Odoo (`version`) và xác thực đăng nhập (`authenticate`). |
| **Universal RPC**| `POST /xmlrpc/2/object` | XML-RPC | Cổng XML-RPC thực thi mọi method ORM trên toàn bộ hệ thống. |
| **File / Image**| `GET /web/content/<id>` | HTTP Binary | Tải file đính kèm hoặc nội dung nhị phân từ bảng `ir.attachment`. |
| **File / Image**| `GET /web/image/<model>/<id>/<field>` | HTTP Stream | Stream hình ảnh (ví dụ avatar user, ảnh sản phẩm `product.product`). Hỗ trợ cache ETag. |
| **Database** | `POST /web/database/list` | JSON-RPC | Liệt kê danh sách các Database đang có trên server Odoo. |

---

## ⚙️ 3. TẬP HỢP CÁC METHOD ORM MẶC ĐỊNH TRÊN MỌI MODEL ODOO 20

Mọi model (từ bảng `res.partner`, `sale.order`, `product.product`, đến các model PLM `plm.material`, `ir.attachment`) đều sở hữu các hàm sau:

### 1. `search_read(domain, fields=None, offset=0, limit=None, order=None)`
* **Chức năng:** Tìm kiếm và trả về trực tiếp danh sách bản ghi (gồm các trường yêu cầu) theo điều kiện lọc `domain`. Đây là API được dùng nhiều nhất (tương đương câu lệnh `SELECT ... WHERE ...`).
* **Ví dụ gọi qua XML-RPC:**
  ```python
  records = models.execute_kw(
      db, uid, password,
      'res.partner', 'search_read',
      [[['is_company', '=', True]]],   # Domain lọc
      {'fields': ['id', 'name', 'email', 'phone'], 'limit': 10, 'order': 'name asc'}
  )
  ```

### 2. `create(vals_list)`
* **Chức năng:** Tạo mới bản ghi. Trong Odoo 20, `create` nhận vào một danh sách các Dictionary để tạo hàng loạt (Batch Create) với tốc độ cao.
* **Ví dụ:**
  ```python
  new_ids = models.execute_kw(
      db, uid, password,
      'res.partner', 'create',
      [[
          {'name': 'Công ty Cơ khí ABC', 'is_company': True, 'email': 'abc@gmail.com'},
          {'name': 'Công ty Nhựa XYZ', 'is_company': True, 'email': 'xyz@gmail.com'}
      ]]
  )
  ```

### 3. `write(vals)`
* **Chức năng:** Cập nhật thông tin của một hoặc nhiều bản ghi theo ID (Tương đương lệnh `UPDATE ... WHERE id IN (...)`).
* **Ví dụ:**
  ```python
  models.execute_kw(
      db, uid, password,
      'res.partner', 'write',
      [[15], {'phone': '0988123456', 'comment': 'Khách hàng VIP'}]
  )
  ```

### 4. `unlink()`
* **Chức năng:** Xóa bản ghi vĩnh viễn khỏi hệ thống (Tương đương `DELETE FROM ...`).
* **Ví dụ:**
  ```python
  models.execute_kw(
      db, uid, password,
      'res.partner', 'unlink',
      [[15]]   # Danh sách ID cần xóa
  )
  ```

### 5. `read(ids, fields=None)`
* **Chức năng:** Đọc thông tin chi tiết của danh sách ID cụ thể đã biết trước.

### 6. `search_count(domain)`
* **Chức năng:** Đếm số lượng bản ghi thỏa mãn điều kiện lọc (Tương đương `SELECT COUNT(*)`), cực nhanh mà không phải kéo dữ liệu về.

### 7. `fields_get(allfields=None, attributes=None)`
* **Chức năng (Introspection / Thay thế Swagger):** Trả về toàn bộ Schema cấu trúc của Model (tên trường, kiểu dữ liệu `Char`, `Integer`, `Many2one`, quan hệ liên kết, nhãn mô tả, trường bắt buộc `required=True`...).

### 8. `name_search(name='', args=None, operator='ilike', limit=100)`
* **Chức năng:** Tìm kiếm phục vụ tính năng Autocomplete / Dropdown khi người dùng gõ tìm tên hoặc mã.

### 9. `copy(default=None)`
* **Chức năng:** Nhân bản (Duplicate) bản ghi kèm khả năng ghi đè các trường chỉ định.

---

## 🎯 4. CÚ PHÁP ĐẶC TRƯNG TRONG ODOO 20 API

### a. Quy tắc viết Domain Lọc dữ liệu (Polish Prefix Notation)
Domain trong Odoo là một danh sách các bộ 3 phần tử: `[(tên_trường, toán_tử, giá_trị)]`.
* **Toán tử hợp lệ:** `=`, `!=`, `>`, `<`, `>=`, `<=`, `like`, `ilike` (tìm gần đúng không phân biệt hoa thường), `in`, `not in`, `child_of` (tìm con cháu trong cây phân cấp).
* **Kết hợp nhiều điều kiện:**
  * Mặc định nhiều dòng là phép **AND**: `[('customer_rank', '>', 0), ('city', '=', 'Hà Nội')]`
  * Dùng toán tử tiền tố **OR (`'|'`)** hoặc **NOT (`'!'`)**:
    ```python
    ['|', ('city', '=', 'Hà Nội'), ('city', '=', 'Hải Phòng')]
    ```

### b. Quy tắc thao tác trường Quan hệ (One2many & Many2many) — Command Tuples
Khi gọi lệnh `create` hoặc `write` trên các bảng có chi tiết con (như danh sách linh kiện trong BoM `bom_line_ids`, hoặc đơn hàng có chi tiết dòng hàng `order_line`), Odoo 20 quy chuẩn thành các bộ tuple:

| Tuple lệnh | Ý nghĩa nghiệp vụ | Ví dụ |
| :---: | :--- | :--- |
| `(0, 0, {values})` | **Tạo mới dòng con** liên kết với cha | `(0, 0, {'product_id': 10, 'product_qty': 2})` |
| `(1, id, {values})`| **Cập nhật dòng con** có sẵn ID | `(1, 45, {'product_qty': 5})` |
| `(2, id, 0)` | **Xóa hẳn dòng con** khỏi database | `(2, 45, 0)` |
| `(3, id, 0)` | **Gỡ liên kết** (nhưng không xóa bản ghi con) | `(3, 45, 0)` |
| `(4, id, 0)` | **Gắn liên kết** một bản ghi con đã có sẵn ID | `(4, 99, 0)` |
| `(5, 0, 0)` | **Gỡ bỏ toàn bộ** danh sách liên kết con | `(5, 0, 0)` |
| `(6, 0, [ids])` | **Thay thế toàn bộ** danh sách liên kết bằng list ID mới | `(6, 0, [10, 20, 30])` |

---

# PHẦN B — KIẾN TRÚC & API RIÊNG CỦA PHÂN HỆ PLM OMNIASOLUTIONS

---

## 🏛️ 1. MÔ HÌNH PHÂN LUỒNG LAI 2 TẦNG (2-TIER ARCHITECTURE)

Do đặc thù file CAD 3D (.SLDASM, .SLDPRT) và bản vẽ PDF rất nặng (từ 50MB đến hàng trăm MB), OdooPLM phân tách rõ:

```
                                    ┌──────────────────────────────────────────────────┐
                                    │   MÁY TRẠM CLIENT (SOLIDWORKS / POSTMAN / APP)   │
                                    └─────────┬──────────────────────────────┬─────────┘
                                              │                              │
                     LUỒNG 1: TRUYỀN FILE NẶNG│                              │LUỒNG 2: XỬ LÝ DỮ LIỆU & LOGIC
                   (Bản vẽ 3D, PDF, Zip, Ảnh) │                              │(Check-in, Check-out, BoM, Rev)
                                              │                              │
                                              ▼                              ▼
┌─────────────────────────────────────────────────────────────┐ ┌──────────────────────────────────────────────┐
│        TẦNG CONTROLLER RIÊNG CỦA PLM                        │ │       TẦNG CONTROLLER MẶC ĐỊNH CỦA ODOO CORE │
│        (File: addons/plm/controllers/main.py)               │ │       (Endpoint: /jsonrpc & /xmlrpc/2/object)│
└─────────────────────────────┬───────────────────────────────┘ └──────────────────────┬───────────────────────┘
                              │ Gọi vào hàm Model                                    │ Odoo Dispatcher bắn thẳng
                              ▼                                                      ▼
┌──────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                           TẦNG MODEL NGHIỆP VỤ                                               │
│             ir.attachment  │  plm.client  │  product.product  │  mrp.bom  │  plm.checkout                    │
└──────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔗 2. BẢNG ÁNH XẠ: THẰNG CONTROLLER NÀO GỌI THẰNG MODEL NÀO?

### a. Bảng Controller gọi Model (Luồng 1 — File `addons/plm/controllers/main.py`)

| URL Endpoint | Hàm trong Controller (`main.py`) | Model được gọi | Method / Hành động cụ thể của Model | Mục đích nghiệp vụ |
| :--- | :--- | :--- | :--- | :--- |
| **`/plm_document_upload/download`** | `download()` | `ir.attachment` | **`GetSomeFiles(requestvals)`** | Controller nhận yêu cầu từ CAD và gọi Model bóc tách dữ liệu file gửi về. |
| **`/plm/download`** | `plm_download()` | `ir.attachment`<br>`ir.binary` | `search()`,<br>**`_get_stream_from(..., field_name='raw')`** | Controller tìm bản ghi document và mở luồng Binary Stream file CAD 3D trả về Client. |
| **`/plm/download_structure`** | `plm_download_structure()` | `ir.attachment` | **`getRelatedHiTree()`**<br>**`getRelatedLyTree()`** | Controller gọi Model để quét cây phả hệ cha-con 2D/3D của cụm máy rồi tải về. |
| **`/plm_document_upload/get_zip_archive`** | `get_zip_archive()` | `ir.attachment` | **`getRelatedPkgTree()`** | Controller gọi Model tìm gói package nén ZIP của bản vẽ để tải về. |
| **`/plm_document_upload/upload`** | `upload()` | `ir.attachment` | `search()`,<br>`write({'raw': base64...})` | Controller tiếp nhận file 3D (.SLDPRT, .SLDASM) từ CAD đẩy vào trường dữ liệu `raw` của Model. |
| **`/plm_document_upload/upload_pdf`** | `upload_pdf()` | `ir.attachment` | `search()`,<br>`write({'printout': base64...})` | Controller nhận file PDF 2D đẩy vào trường `printout` của Model. |
| **`/plm_document_upload/upload_preview`** | `upload_preview()` | `ir.attachment` | `browse()`,<br>`write({'preview': base64...})` | Controller lưu ảnh chụp màn hình 3D vào trường `preview` của Model. |
| **`/plm_document_upload/extra_file`** | `extra_file()` | `ir.attachment`<br>`plm.component.document.rel` | `create()`,<br>**`createFromIds(product_id, ir_attachment_id)`** | Controller tạo tài liệu phụ và gọi Model liên kết tài liệu với chi tiết linh kiện cơ khí. |
| **`/plm_document_upload/zip_archive`** | `zip_archive()` | `ir.attachment`<br>`ir.attachment.relation` | `search()`,<br>`create()`,<br>`write({'is_plm': True})` | Controller tạo bản ghi quan hệ tài liệu và nạp file zip lắp ráp. |
| **`/plm_document_upload/get_files_write_time`** | `get_files_write_time()` | `ir.attachment` | `search_read([('id', 'in', ...)], ['name', 'write_date'])` | Controller lấy thời gian cập nhật lần cuối của các file từ Model để kiểm tra phiên bản mới. |
| **`/plm/ir_attachment_printout/<id>`** | `get_printout()` | `report.plm.ir_attachment_pdf` | **`_render_qweb_pdf(ir_attachement_id)`** | Controller gọi QWeb Engine kết xuất bản vẽ kỹ thuật thành luồng PDF xem trên trình duyệt. |
| **`/plm/product_product_image_1920/<id>`** | `product_product_image_1920()` | `product.product` | `browse(id).image_1920` | Controller lấy dữ liệu ảnh chi tiết từ Model để stream trực tiếp. |
| **`/plm/product_product_preview/<id>`** | `product_product_preview()` | `product.product` | `browse(id).preview` | Controller lấy hình thumbnail 3D CAD của sản phẩm để stream HTTP. |
| **`/plm_document_upload/login`** | `login()` | `odoo.http.session` | `authenticate(db, login, password)` | Controller xác thực thông tin đăng nhập và tạo phiên làm việc (Session Cookie). |
| **`/plm_document_upload/isalive`** | `isalive()` | Không gọi Model | Trả về `"True"` | Controller phản hồi trạng thái máy chủ PLM đang hoạt động. |

---

### b. Bảng các API Model được gọi trực tiếp qua RPC Odoo Core (Luồng 2)
*(Không qua `controllers/main.py`, Client gửi trực tiếp vào `/jsonrpc` hoặc `/xmlrpc/2/object`)*

| Model | Hàm API được gọi trực tiếp | Lý do gọi trực tiếp qua RPC Gateway mà không qua Controller PLM |
| :--- | :--- | :--- |
| **`plm.client`** | **`client_can_check_out`** | Kiểm tra quyền khóa file ngay tức thì trên máy trạm trước khi mở bản vẽ. |
| **`plm.client`** | **`pre_check_in_recursive_all`** | Gửi cấu trúc JSON để server phân tích xung đột phiên bản trước khi lưu. |
| **`plm.client`** | **`check_in_documents`** | Check-in hàng loạt file và gỡ bỏ khóa sửa đổi. |
| **`plm.client`** | **`check_out_recursive`** | Khóa đồng loạt cả cây lắp ráp Assembly và các chi tiết con. |
| **`plm.client`** | **`get_checkout_snapshot`** | Lấy snapshot toàn bộ file đang bị khóa kèm mã băm SHA-1 để Client cache offline. |
| **`ir.attachment`** | **`saveStructure`** | **API bóc tách BoM:** Nhận cây cha-con từ CAD để tự động tạo quan hệ lắp ráp và BOM. |
| **`ir.attachment`** | **`NewRevision`** | Tăng chỉ số Revision kỹ thuật (Rev A ➔ Rev B). |
| **`ir.attachment`** | **`Clone`** | Nhân bản bản vẽ và linh kiện sang mã mới. |
| **`ir.attachment`** | **`action_confirm` / `action_release`** | Phê duyệt và phát hành bản vẽ kỹ thuật. |
| **`product.product`** | **`getParentBomStructure`** | Phân tích vị trí sử dụng **Where-Used** của linh kiện trong các BoM cấp cha. |
| **`product.product`** | **`reviseCompAndDoc`** | Nâng Revision đồng bộ cả linh kiện và file bản vẽ đính kèm trong 1 transaction. |
| **`product.product`** | **`getLeafBom`** | Phân rã cây BoM lấy danh sách toàn bộ linh kiện đơn (chi tiết lá). |
| **`mrp.bom`** | **`SaveStructure`** | Tự động sinh các dòng định mức nguyên vật liệu `mrp.bom.line`. |
| **`mrp.bom`** | **`get_explode` / `GetExploseSum`** | Xuất bảng tổng hợp bóc tách vật tư đa cấp độ (Exploded BoM). |

---

# PHẦN C — CHEAT SHEET & MẪU CODE GỌI API THỰC TẾ

---

## 1. MẪU GỌI BẰNG PYTHON (XML-RPC VỚI CẢ ODOO CORE VÀ PLM)

```python
import xmlrpc.client

URL = "http://192.168.103.8:8080"
DB = "odoo20"
USERNAME = "admin"
PASSWORD = "admin_password"   # Hoặc chuỗi API_KEY

# 1. Xác thực đăng nhập qua Core Endpoint
common = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/common")
uid = common.authenticate(DB, USERNAME, PASSWORD, {})
models = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/object")

print(f"✅ Đăng nhập Odoo 20 thành công! UID: {uid}")

# 2. GỌI ODOO 20 CORE API: Tìm kiếm đối tác khách hàng
customers = models.execute_kw(
    DB, uid, PASSWORD,
    'res.partner', 'search_read',
    [[['customer_rank', '>', 0]]],
    {'fields': ['name', 'phone', 'email'], 'limit': 5}
)
print(f"👉 Khách hàng Odoo Core: {customers}")

# 3. GỌI ODOO 20 CORE API: Lấy schema cấu trúc bảng (thay thế Swagger)
schema = models.execute_kw(
    DB, uid, PASSWORD,
    'product.product', 'fields_get',
    [],
    {'attributes': ['string', 'type', 'required']}
)
print("👉 Số lượng trường của Product:", len(schema))

# 4. GỌI ODOO PLM API: Lấy Snapshot file CAD đang bị khóa Check-out
snapshot = models.execute_kw(
    DB, uid, PASSWORD,
    'plm.client', 'get_checkout_snapshot',
    [],
    {'stamp': '', 'file_names': []}
)
print("👉 Snapshot khóa PLM:", snapshot.get("rows"))

# 5. GỌI ODOO PLM API: Phân tích Where-Used của linh kiện (ID: 15)
where_used = models.execute_kw(
    DB, uid, PASSWORD,
    'product.product', 'getParentBomStructure',
    [[15]],
    {'filterBomType': 'normal'}
)
print("👉 Vị trí sử dụng linh kiện:", where_used)
```

---

## 2. MẪU GỌI BẰNG CURL / POSTMAN (HTTP REST CONTROLLER)

### a. Ping máy chủ Odoo PLM:
```bash
curl -X GET http://192.168.103.8:8080/plm_document_upload/isalive
```

### b. Đăng nhập tạo Session Cookie:
```bash
curl -X POST http://192.168.103.8:8080/web/session/authenticate \
     -H "Content-Type: application/json" \
     -d '{
       "jsonrpc": "2.0",
       "params": {
         "db": "odoo20",
         "login": "admin",
         "password": "admin_password"
       }
     }'
```

### c. Gọi hàm ORM qua JSON-RPC (/web/dataset/call_kw):
```bash
curl -X POST http://192.168.103.8:8080/web/dataset/call_kw/res.partner/search_read \
     -H "Content-Type: application/json" \
     -H "Cookie: session_id=YOUR_SESSION_ID" \
     -d '{
       "jsonrpc": "2.0",
       "method": "call",
       "params": {
         "model": "res.partner",
         "method": "search_read",
         "args": [[["is_company", "=", true]]],
         "kwargs": {
           "fields": ["name", "email"],
           "limit": 5
         }
       },
       "id": 1
     }'
```

---

## 3. MẪU GỌI BẰNG JAVASCRIPT / NODE.JS (FETCH API)

```javascript
async function callOdoo(model, method, args = [], kwargs = {}) {
  const response = await fetch("http://192.168.103.8:8080/jsonrpc", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      jsonrpc: "2.0",
      method: "call",
      params: {
        service: "object",
        method: "execute_kw",
        args: ["odoo20", 2, "admin_password", model, method, args, kwargs]
      },
      id: Date.now()
    })
  });
  const data = await response.json();
  return data.result;
}

// Chạy thử đọc danh sách sản phẩm PLM
callOdoo("product.product", "search_read", [[["is_plm", "=", true]]], {
  fields: ["name", "engineering_code", "engineering_revision"],
  limit: 5
}).then(console.log);
```

---
*Tài liệu được cập nhật toàn diện bao gồm cả Hệ thống API Gốc của Odoo 20 Core và Hệ thống API Chuyên sâu của Phân hệ OdooPLM (OmniaSolutions).*
