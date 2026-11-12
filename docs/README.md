# 📚 THƯ VIỆN TÀI LIỆU KỸ THUẬT & NGHIỆP VỤ HỆ THỐNG ODOO 20 (TDB SOLUTION)

> **Mục đích:** Trung tâm lưu trữ, định vị và tra cứu toàn bộ tài liệu lý thuyết, kiến trúc hệ thống, nghiệp vụ chuyên sâu và hướng dẫn kỹ thuật của dự án Odoo 20 Dockerized.

---

## 🗂️ SƠ ĐỒ CẤU TRÚC THƯ MỤC TÀI LIỆU

```text
docs/
├── plm/                                  # PHÂN HỆ QUẢN LÝ VÒNG ĐỜI SẢN PHẨM & CAD PDM
│   ├── Ke_hoach_Trien_khai_PDM_Odoo_SolidWorks.docx
│   ├── ly_thuyet/                        # 1. Giáo trình & Lý thuyết nghiệp vụ sản xuất
│   │   └── PLM Learn.md
│   ├── kien_truc_va_mo_hinh/             # 2. Kiến trúc thực thể & mô hình dữ liệu OdooPLM
│   │   ├── Xác định model document, revision, attachment, BOM.docx
│   │   ├── Lập GAP Analysis - chức năng có sẵn và cần Customize.docx
│   │   └── Hướng dẫn Kiến trúc PDM cho SolidWorks - Khóa, Version, Batch.md
│   └── tich_hop_cad_api/                 # 3. Kỹ thuật tích hợp CAD, API & Phân quyền PDM
│       ├── SolidWorks_PDM_Authorization_Framework.md
│       ├── Phân tích source code các API login, upload, check-in, check-out.md
│       └── Odoo20_PLM_Omnia_API_Reference.md
│
├── ke_toan_vas/                          # PHÂN HỆ KẾ TOÁN & BÁO CÁO VIỆT NAM (VAS)
│   └── Odoo20_Vietnam_VAS_Reports_ManhNguyen.md
│
├── huong_dan_trien_khai/                 # HƯỚNG DẪN CÀI ĐẶT & VẬN HÀNH HỆ THỐNG
│   └── huong_dan_lay_module.md
│
└── README.md                             # Mục lục tra cứu tài liệu toàn hệ thống (File này)
```

---

## 📑 BẢNG TRA CỨU TÀI LIỆU CHI TIẾT

### 1. Phân hệ PLM & Tích hợp CAD / PDM

| Phân nhóm | Tên tài liệu | Định dạng | Mô tả nội dung chính |
| :--- | :--- | :---: | :--- |
| **Kế hoạch triển khai** | [**`Ke_hoach_Trien_khai_PDM_Odoo_SolidWorks.docx`**](./plm/Ke_hoach_Trien_khai_PDM_Odoo_SolidWorks.docx) | Word (45 KB) | Bản kế hoạch tổng thể triển khai tích hợp giải pháp PDM Odoo 20 với SolidWorks cho phòng thiết kế cơ khí. |
| **Lý thuyết nền tảng** | [**`PLM Learn.md`**](./plm/ly_thuyet/PLM%20Learn.md) | Markdown (91 KB) | Giáo trình toàn diện về PLM từ thực tế sản xuất cơ khí đến hệ sinh thái OdooPLM (`addons/plm`). Bao gồm: EBOM vs MBOM, Revision/Version, Quy trình đổi thiết kế (ECR/ECO/ECN), truy xuất nguồn gốc. |
| **Kiến trúc mô hình** | [**`Xác định model document, revision, attachment, BOM.docx`**](./plm/kien_truc_va_mo_hinh/X%C3%A1c%20%C4%91%E1%BB%8Bnh%20model%20document%2C%20revision%2C%20attachment%2C%20BOM.docx) | Word (504 KB) | Báo cáo kiến trúc phân tích 4 thực thể cốt lõi của OdooPLM: Bảng `ir.attachment` mở rộng, cơ chế Revision kiểm soát vòng đời, liên kết CAD phụ thuộc và cấu trúc eBOM kỹ thuật. |
| **Kiến trúc mô hình** | [**`Lập GAP Analysis - chức năng có sẵn và cần Customize.docx`**](./plm/kien_truc_va_mo_hinh/L%E1%BA%ADp%20GAP%20Analysis%20-%20ch%E1%BB%A9c%20n%C4%83ng%20c%C3%B3%20s%E1%BA%B5n%20v%C3%A0%20c%E1%BA%A7n%20Customize.docx) | Word (254 KB) | Báo cáo GAP Analysis đối chiếu năng lực OdooPLM với chuẩn PDM công nghiệp: Quản trị kho cây thư mục dự án (`plm.folder`), khóa độc quyền, duyệt 2 cấp. |
| **Kiến trúc mô hình** | [**`Hướng dẫn Kiến trúc PDM cho SolidWorks - Khóa, Version, Batch.md`**](./plm/kien_truc_va_mo_hinh/H%C6%B0%E1%BB%9Bng%20d%E1%BA%ABn%20Ki%E1%BA%BFn%20tr%C3%BAc%20PDM%20cho%20SolidWorks%20-%20Kh%C3%B3a%2C%20Version%2C%20Batch.md) | Markdown (17 KB) | Cẩm nang kiến trúc PDM thực chiến: Tư duy khóa bi quan (Pessimistic Locking), vòng đời state machine, giao dịch nguyên tử khối Assembly Batch và xử lý xung đột mạng LAN. |
| **Tích hợp CAD & PDM** | [**`SolidWorks_PDM_Authorization_Framework.md`**](./plm/tich_hop_cad_api/SolidWorks_PDM_Authorization_Framework.md) | Markdown (25 KB) | Báo cáo thiết kế phân quyền PDM 5 lớp cho SolidWorks 2022: Cơ chế cấp Token 180 ngày, phân quyền máy trạm LAN, giải quyết xung đột check-in và cơ chế ghi đè thay thế (Force Replace). |
| **Tích hợp CAD & PDM** | [**`Phân tích source code các API login, upload, check-in, check-out.md`**](./plm/tich_hop_cad_api/Ph%C3%A2n%20t%C3%ADch%20source%20code%20c%C3%A1c%20API%20login%2C%20upload%2C%20check-in%2C%20check-out.md) | Markdown (21 KB) | Báo cáo kỹ thuật phân tích luồng mã nguồn 4 API giữa SolidWorks Add-in và Odoo Backend (`login`, `upload`, `check-out`, `check-in`), xử lý transaction và chống race-condition. |
| **Tích hợp CAD & PDM** | [**`Odoo20_PLM_Omnia_API_Reference.md`**](./plm/tich_hop_cad_api/Odoo20_PLM_Omnia_API_Reference.md) | Markdown (22 KB) | Cẩm nang tra cứu toàn diện hệ thống API Odoo 20 và API riêng của phân hệ PLM OmniaSolutions: Xác thực API Key, gọi RPC, REST API và mẫu code mẫu (Python, cURL, Postman). |

---

### 2. Phân hệ Kế toán Chuẩn Việt Nam (VAS Reports)

| Phân nhóm | Tên tài liệu | Định dạng | Mô tả nội dung chính |
| :--- | :--- | :---: | :--- |
| **Kế toán & Thuế** | [**`Odoo20_Vietnam_VAS_Reports_ManhNguyen.md`**](./ke_toan_vas/Odoo20_Vietnam_VAS_Reports_ManhNguyen.md) | Markdown (35 KB) | Phân tích chuyên sâu bộ 4 module Việt Nam (`vn_core`, `l10n_vn_vas_reports`, `l10n_vn_stock_reports`, `l10n_vn_mrp_reports`): Báo cáo tài chính TT 200 / TT 133, Thẻ kho S12, Sổ vật liệu S10, Bảng tính giá thành sản xuất S37-DN. |

---

### 3. Hướng dẫn Triển khai & Vận hành

| Phân nhóm | Tên tài liệu | Định dạng | Mô tả nội dung chính |
| :--- | :--- | :---: | :--- |
| **Vận hành hệ thống** | [**`huong_dan_lay_module.md`**](./huong_dan_trien_khai/huong_dan_lay_module.md) | Markdown (11 KB) | Sổ tay hướng dẫn trích xuất module gốc từ bên trong container Docker Odoo ra máy tính host, cách cài đặt module từ kho Odoo Apps Store hoặc GitHub và kích hoạt module lên hệ thống. |

---

> [!TIP]
> Khi cần bổ sung tài liệu mới, vui lòng tạo file Markdown trong thư mục tương ứng theo phân loại trên và cập nhật đường dẫn vào bảng tra cứu này để đảm bảo tính đồng bộ của dự án.
