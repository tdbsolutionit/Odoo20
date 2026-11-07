# PHÂN TÍCH CHUYÊN SÂU BỘ 4 MODULE VIỆT NAM (VAS / ERP FRAMEWORK) CỦA TÁC GIẢ MANH NGUYEN TRÊN ODOO 20

> **Nguồn Odoo Apps:** [https://apps.odoo.com/apps/modules/browse?author=Manh%20Nguyen](https://apps.odoo.com/apps/modules/browse?author=Manh%20Nguyen)  
> **Mã nguồn dự án:** [parabol123654/vn-odoo-framework (GitHub)](https://github.com/parabol123654/vn-odoo-framework)  
> **Phiên bản mục tiêu:** Odoo 20.0 Community Edition (tương thích đa phiên bản 14.0 -> 20.0)  
> **Giấy phép:** GNU Affero General Public License v3.0 (AGPL-3.0)  
> **Tác giả:** Manh Nguyen (`parabol123654@gmail.com`)

---

## MỤC LỤC TỔNG QUAN

1. [Tổng quan về tác giả Manh Nguyen & Bộ giải pháp Vietnam VAS Reports](#1-tổng-quan-về-tác-giả-manh-nguyen--bộ-giải-pháp-vietnam-vas-reports)
2. [Tại sao bộ 4 module này mang tính bước ngoặt trên Odoo 20 Community?](#2-tại-sao-bộ-4-module-này-mang-tính-bước-ngoặt-trên-odoo-20-community)
3. [Sơ đồ kiến trúc liên kết giữa 4 Module (Dependency & Data Flow)](#3-sơ-đồ-kiến-trúc-liên-kết-giữa-4-module-dependency--data-flow)
4. [Phân tích chi tiết Module 1: `vn_core` (Vietnam ERP Framework - Core)](#4-phân-tích-chi-tiết-module-1-vn_core-vietnam-erp-framework---core)
   - Chức năng trong Odoo 20
   - Kiến trúc MVC & Clean Architecture (Model - View - Controller/Engine)
5. [Phân tích chi tiết Module 2: `l10n_vn_vas_reports` (Vietnam VAS Reports)](#5-phân-tích-chi-tiết-module-2-l10n_vn_vas_reports-vietnam-vas-reports)
   - Chức năng trong Odoo 20 (TT200 / TT133 / TT99)
   - Kiến trúc MVC (Model - View - Controller/Reporting)
6. [Phân tích chi tiết Module 3: `l10n_vn_stock_reports` (VAS Reports - Inventory)](#6-phân-tích-chi-tiết-module-3-l10n_vn_stock_reports-vas-reports---inventory)
   - Chức năng trong Odoo 20 (Thẻ kho S12, Sổ vật liệu S10, Bảng NXT S11)
   - Kiến trúc MVC (Model - View - Controller/Engine)
7. [Phân tích chi tiết Module 4: `l10n_vn_mrp_reports` (VAS Reports - Manufacturing)](#7-phân-tích-chi-tiết-module-4-l10n_vn_mrp_reports-vas-reports---manufacturing)
   - Chức năng trong Odoo 20 (Chi phí SX 621, 622, 627 & Thẻ tính giá thành S37-DN)
   - Kiến trúc MVC (Model - View - Controller/Engine)
8. [Điểm sáng kỹ thuật (Design Patterns & Best Practices)](#8-điểm-sáng-kỹ-thuật-design-patterns--best-practices)
9. [Tổng kết & Khuyến nghị triển khai](#9-tổng-kết--khuyến-nghị-triển-khai)

---

## 1. TỔNG QUAN VỀ TÁC GIẢ MANH NGUYEN & BỘ GIẢI PHÁP VIETNAM VAS REPORTS

Trên Odoo Apps Store, tác giả **Manh Nguyen** là một chuyên gia giải pháp kế toán và nhà phát triển kỳ cựu chuyên sâu về **Hệ thống Kế toán Việt Nam (VAS - Vietnamese Accounting Standards)** cho Odoo.

Bộ 4 module được xuất bản trên Odoo Apps bao gồm:

| STT | Tên hiển thị (Module Name) | Technical Name | Phụ thuộc chính (Depends) | Số dòng code (LOC) | Chức năng tóm tắt |
|:---:|:---|:---|:---|:---:|:---|
| **1** | **Vietnam ERP Framework - Core** | `vn_core` | `account` | ~4.1K | Nền tảng kỹ thuật, Domain engine tính toán thuần Python, DTO, AST Parser và điểm mở rộng Provider. |
| **2** | **Vietnam VAS Reports** | `l10n_vn_vas_reports` | `vn_core`, `account` | ~43.4K | Toàn bộ sổ sách kế toán, BCTC, Thuyết minh B09, Bảng kê & Tờ khai thuế GTGT, Phiếu thu/chi theo TT200, TT133 và TT99. |
| **3** | **Vietnam VAS Reports - Inventory** | `l10n_vn_stock_reports` | `vn_core`, `l10n_vn_vas_reports`, `stock_account` | ~44.2K | Báo cáo kho VAS: Thẻ kho (S12-DN), Sổ chi tiết vật liệu (S10-DN), Bảng tổng hợp Nhập - Xuất - Tồn (S11-DN). |
| **4** | **Vietnam VAS Reports - Manufacturing** | `l10n_vn_mrp_reports` | `vn_core`, `l10n_vn_vas_reports`, `mrp`, `stock_account` | ~44.1K | Báo cáo sản xuất và giá thành: Phân bổ 3 yếu tố chi phí (621, 622, 627) theo lệnh MO và Thẻ tính giá thành (S37-DN). |

---

## 2. TẠI SAO BỘ 4 MODULE NÀY MANG TÍNH BƯỚC NGOẶT TRÊN ODOO 20 COMMUNITY?

Trong hệ sinh thái Odoo nói chung và Odoo 20 nói riêng, phân hệ **Accounting & Localisation** của bản **Community Edition** luôn có những khoảng trống khổng lồ:

1. **Odoo Community không có Dynamic Financial Reports:** Tính năng xem báo cáo tài chính động (drill-down, mở rộng, thu gọn, so sánh kỳ) bị khóa trong Odoo Enterprise (`account_reports`).
2. **Không hỗ trợ biểu mẫu luật định Việt Nam:** Kế toán Việt Nam bắt buộc phải tuân thủ nghiêm ngặt hệ thống mẫu biểu theo Thông tư của Bộ Tài Chính (có quốc hiệu, tiêu ngữ, chữ ký, đúng mẫu số ban hành).
3. **Đón đầu Thông tư mới nhất - Thông tư 99/2025/TT-BTC:**
   * Thông tư 200/2014/TT-BTC áp dụng cho doanh nghiệp lớn đến hết năm tài chính 2025.
   * Thông tư 133/2016/TT-BTC cho doanh nghiệp vừa và nhỏ (SME).
   * **Thông tư 99/2025/TT-BTC (áp dụng từ 01/01/2026):** Thay đổi lớn về tên gọi và mẫu biểu (chuyển sang Báo cáo tình hình tài chính, đổi cách trình bày luồng tiền gián tiếp, bổ sung mã biểu mẫu). Bộ module này đã hỗ trợ sẵn TT99 ngay trong Odoo 20!
4. **Nguyên tắc "Split on Dependencies" (Tách module theo nhu cầu):** Doanh nghiệp thương mại, dịch vụ không có kho hoặc sản xuất không bị ép phải cài `stock` hay `mrp` mà vẫn có trọn bộ sổ sách kế toán VAS.

---

## 3. SƠ ĐỒ KIẾN TRÚC LIÊN KẾT GIỮA 4 MODULE

```
                  ┌────────────────────────────────────────┐
                  │          Odoo Core (account)           │
                  └───────────────────┬────────────────────┘
                                      │
                                      ▼
                  ┌────────────────────────────────────────┐
                  │                vn_core                 │
                  │   (Domain Engine, AST Parser, DTO,     │
                  │    Report Mapping, Ledger Provider)    │
                  └───────────────────┬────────────────────┘
                                      │
                                      ▼
                  ┌────────────────────────────────────────┐
                  │          l10n_vn_vas_reports           │
                  │ (Sổ cái, NKC, B01, B02, B03, B09, Thuế,│
                  │  Phiếu Thu/Chi, TT200/TT133/TT99)      │
                  └─────────────┬────────────────────┬─────┘
                                │                    │
         + stock_account        │                    │ + mrp, stock_account
                                ▼                    ▼
┌──────────────────────────────────────┐  ┌──────────────────────────────────────┐
│        l10n_vn_stock_reports         │  │         l10n_vn_mrp_reports          │
│ • Thẻ kho (S12-DN)                   │  │ • Chi phí sản xuất theo MO          │
│ • Sổ chi tiết vật liệu (S10-DN)      │  │ • Phân bổ 3 yếu tố: 621, 622, 627   │
│ • Bảng tổng hợp N-X-T (S11-DN)       │  │ • Thẻ tính giá thành (S37-DN)        │
└──────────────────────────────────────┘  └──────────────────────────────────────┘
```

---

## 4. PHÂN TÍCH CHI TIẾT MODULE 1: `vn_core` (VIETNAM ERP FRAMEWORK - CORE)

### 4.1. Chức năng trong Odoo 20
`vn_core` là **trục xương sống kỹ thuật (Technical Core)** của toàn bộ hệ sinh thái VAS. Điểm độc đáo nhất là: **Trong mã nguồn Python của `vn_core` không hề chứa bất kỳ một mã tài khoản cứng (Hardcoded Account Code) nào của Việt Nam**. Nó đóng vai trò là một "Engine container" cung cấp:
* Bộ máy tính toán nghiệp vụ kế toán thuần Python (**Domain Calculation Engines**).
* Cấu hình ánh xạ chỉ tiêu báo cáo động (**Configurable Statement Mapping**). Khi chế độ kế toán hoặc thông tư thay đổi, người dùng chỉ cần sửa dữ liệu trên giao diện hoặc import XML, **không phải sửa một dòng code Python nào**.
* Bộ phân tích cú pháp biểu thức tài khoản (**AST Math Parser**) tự viết, tuyệt đối an toàn và **nói không với lệnh nguy hiểm `eval()`**.
* Điểm mở rộng (**Provider Pattern**): Cho phép bất kỳ bên thứ 3 nào mở rộng hoặc thay thế nguồn dữ liệu chỉ bằng một class `_inherit = 'vn.ledger.provider'`.

---

### 4.2. Kiến trúc MVC của `vn_core`

```
┌────────────────────────────────────────────────────────────────────────┐
│                        KIẾN TRÚC MVC: vn_core                          │
├────────────────────────────────────────────────────────────────────────┤
│ MODEL (M):                                                             │
│  • Odoo ORM Models:                                                    │
│    - vn.report.mapping: Ánh xạ mã chỉ tiêu BCTC, công thức tài khoản   │
│    - vn.report.mapping.line: Các dòng toán tử, biểu thức con           │
│    - vn.ledger.provider: Điểm mở rộng truy xuất dữ liệu sổ cái/kho/SX  │
│    - account.move.line (Inherit): Index tối ưu truy vấn đối ứng        │
│  • Pure Domain DTOs:                                                   │
│    - LedgerFilter, FinancialStatementFilter, InventoryFilter          │
│    - AccountBalanceDTO, LedgerLineDTO, StatementItemDTO                │
│                                                                        │
│ VIEW (V):                                                              │
│  • vn_report_mapping_views.xml: Giao diện Cấu hình ánh xạ chỉ tiêu      │
│    (Kế toán -> Cấu hình -> Statement Mappings).                        │
│                                                                        │
│ CONTROLLER / SERVICE / CALCULATION ENGINE (C):                         │
│  • core/utils/expression_parser.py: Bộ phân tích cú pháp AST biểu thức  │
│  • domain/ledger/ & domain/financial_statement/: Engine kế toán thuần   │
│  • infrastructure/odoo_ledger_repository.py: Chuyển đổi SQL Odoo sang  │
│    các DTO trung gian nạp cho Engine xử lý                             │
└────────────────────────────────────────────────────────────────────────┘
```

#### Phân tích chi tiết từng tầng:

* **Model (M):**
  * `vn.report.mapping`: Chứa mã chỉ tiêu (ví dụ: Mã 110 - Tiền và tương đương tiền), tên chỉ tiêu, loại báo cáo (`balance_sheet`, `income_statement`, `cash_flow`), thứ tự (`sequence`), và công thức toán học.
  * Hỗ trợ các toán tử biểu thức phong phú:
    * `[111]`: Lấy số dư tài khoản 111.
    * `[131:D]`: Lấy số dư Nợ (Debit balance) của tài khoản 131 theo từng đối tác.
    * `[131:C]`: Lấy số dư Có (Credit balance) của tài khoản 131 theo từng đối tác.
    * `{100} = {110} + {120}`: Chỉ tiêu tổng hợp tính từ các chỉ tiêu con.
* **View (V):**
  * Form view và Tree view cho phép kế toán viên nhìn thấy trực quan danh sách các chỉ tiêu của Bảng cân đối kế toán, Báo cáo KQKD. Kế toán có thể thêm tài khoản con vào chỉ tiêu mà không cần nhờ developer can thiệp.
* **Controller / Engine (C):**
  * Đóng vai trò bộ não tính toán: `domain/` tách biệt 100% với database của Odoo. Nhờ vậy, tác giả Manh Nguyen có thể viết **hàng trăm Unit Tests chạy độc lập** trên Python thuần (Pure Unit Test) mà không cần khởi động server Odoo hay kết nối PostgreSQL, đảm bảo tốc độ thực thi chỉ trong vài mili-giây.

---

## 5. PHÂN TÍCH CHI TIẾT MODULE 2: `l10n_vn_vas_reports` (VIETNAM VAS REPORTS)

### 5.1. Chức năng trong Odoo 20
Đây là module nghiệp vụ chính cho toàn bộ kế toán tài chính, kế toán tổng hợp và kế toán thuế:
1. **Ba chế độ kế toán trong 1 module:**
   * Doanh nghiệp vào `Cấu hình -> Công ty`, chỉ cần chọn Chế độ kế toán: **Thông tư 200/2014**, **Thông tư 133/2016** hoặc **Thông tư 99/2025**.
   * Toàn bộ mã biểu mẫu in ấn, căn cứ pháp lý ("Ban hành theo TT số..."), chức danh người ký (Giám đốc / Kế toán trưởng hay Người đại diện theo pháp luật), và cấu trúc chỉ tiêu sẽ tự động hoán đổi tương ứng!
2. **Sổ sách kế toán luật định (Accounting Books):**
   * **Sổ Nhật ký chung (Mẫu S03a-DN / S01a-DNN)**.
   * **Sổ Cái (Mẫu S03b-DN / S01b-DNN)**: Nhóm theo tài khoản cấp 1, cấp 2, tài khoản đối ứng từng dòng.
   * **Bảng cân đối số phát sinh / Bảng cân đối tài khoản (Mẫu S06-DN / F01-DNN)**: Đầy đủ 8 cột (Số dư đầu kỳ Nợ/Có, Phát sinh trong kỳ Nợ/Có, Số dư cuối kỳ Nợ/Có).
   * **Sổ quỹ tiền mặt (S07-DN) & Sổ tiền gửi ngân hàng (S08-DN)**.
   * **Sổ chi tiết thanh toán công nợ người mua / người bán (S31-DN)**: Theo dõi tuổi nợ, chi tiết từng hóa đơn, đối chiếu công nợ.
   * **Sổ chi phí sản xuất kinh doanh (S38-DN) & Sổ theo dõi bán hàng (S35-DN)**.
3. **Báo cáo tài chính (Financial Statements):**
   * **Bảng cân đối kế toán (B01-DN) / Báo cáo tình hình tài chính (B01-DN theo TT99)**.
   * **Báo cáo kết quả hoạt động kinh doanh (B02-DN)**: So sánh kỳ này với kỳ trước / năm nay với năm trước.
   * **Báo cáo lưu chuyển tiền tệ (B03-DN)**: Cả phương pháp Trực tiếp và Gián tiếp.
   * **Bản thuyết minh Báo cáo tài chính (B09-DN / B09-DNN)**: Khóa sổ theo năm, tự động điền các bảng số liệu tài sản, nguồn vốn, doanh thu, chi phí từ sổ cái.
4. **Kế toán Thuế GTGT & Chứng từ tiền mặt:**
   * Bảng kê hóa đơn chứng từ hàng hóa dịch vụ mua vào (Mẫu 01-2/GTGT) và bán ra (Mẫu 01-1/GTGT).
   * Tờ khai thuế GTGT khấu trừ (Mẫu 01/GTGT).
   * In Phiếu Thu (Mẫu 01-TT) và Phiếu Chi (Mẫu 02-TT) trực tiếp từ bút toán kế toán.

---

### 5.2. Kiến trúc MVC của `l10n_vn_vas_reports`

```
┌────────────────────────────────────────────────────────────────────────┐
│                   KIẾN TRÚC MVC: l10n_vn_vas_reports                   │
├────────────────────────────────────────────────────────────────────────┤
│ MODEL (M):                                                             │
│  • res.company (Inherit): Thêm trường accounting_regime (TT200/133/99) │
│  • account.move.voucher: Sinh số phiếu thu, phiếu chi, người nhận      │
│  • vn.fs.note: Quản lý bản thuyết minh BCTC lưu theo từng năm          │
│  • Transient Models (Wizards):                                         │
│    - vn.general.ledger.wizard, vn.trial.balance.wizard                 │
│    - vn.balance.sheet.wizard, vn.income.statement.wizard               │
│    - vn.cash.flow.wizard, vn.vat.declaration.wizard                    │
│                                                                        │
│ VIEW (V):                                                              │
│  • On-Screen HTML Interactive View: Giao diện xem trực tiếp trên màn   │
│    hình Odoo, hỗ trợ thu gọn/mở rộng, bấm vào dòng để mở bút toán      │
│  • QWeb PDF Templates: Khổ A4 ngang/dọc, chuẩn Bộ Tài Chính            │
│  • Excel Layouts: Xuất file .xlsx chuẩn chỉ từng đường viền và font    │
│                                                                        │
│ CONTROLLER / REPORT HANDLER (C):                                       │
│  • report/vn_report_qweb.py: Controller điều phối sinh dữ liệu QWeb    │
│  • report/xlsx_writer.py & xlsx_layouts.py: Engine sinh file Excel     │
│  • wizard/base_report_wizard.py: Controller tiếp nhận filter từ UI,    │
│    validate và gọi Service tính toán                                   │
└────────────────────────────────────────────────────────────────────────┘
```

#### Phân tích chi tiết:
* **Model (M):**
  * Sử dụng triệt để mô hình **`vn.report.wizard.mixin`**: Tất cả các wizard báo cáo đều kế thừa từ mixin này. Wizard không bao giờ truy vấn trực tiếp SQL mà chỉ làm nhiệm vụ: Gom input người dùng (Kỳ báo cáo, Tài khoản, Đối tác) -> Tạo `FilterDTO` -> Chuyển sang Service xử lý.
* **View (V):**
  * **On-Screen Viewer:** Khắc phục nhược điểm lớn nhất của Odoo Community (vốn chỉ cho xuất PDF/Excel thô). Màn hình xem báo cáo của tác giả cho phép kế toán viên tương tác trực tiếp: Bấm dấu `+` để bung tài khoản con, bấm vào số tiền để mở ngay bút toán gốc (`account.move`).
  * **Đa chế độ xem:** Một template QWeb duy nhất phục vụ đồng thời cho cả màn hình xem trước và in PDF xuất xưởng.
* **Controller (C):**
  * Lớp điều phối báo cáo xử lý dữ liệu từ DTO, định dạng tiền tệ Việt Nam (`#,##0`), xử lý số âm trong ngoặc đơn `(1,000,000)` theo chuẩn kế toán, và đẩy sang QWeb Renderer hoặc XlsxWriter.

---

## 6. PHÂN TÍCH CHI TIẾT MODULE 3: `l10n_vn_stock_reports` (VAS REPORTS - INVENTORY)

### 6.1. Chức năng trong Odoo 20
Trong kế toán kho Việt Nam, việc đối chiếu giữa số lượng thủ kho ghi chép và giá trị kế toán hạch toán là "cơn ác mộng" nếu hệ thống ERP bị lệch. `l10n_vn_stock_reports` giải quyết trọn vẹn bài toán này:
1. **Thẻ kho (Mẫu S12-DN / S08-DNN):**
   * Theo dõi biến động Nhập - Xuất - Tồn về mặt **Số lượng** của từng sản phẩm tại từng Kho/Địa điểm.
   * Ghi nhận ngày tháng chứng từ, số hiệu phiếu xuất/nhập kho.
2. **Sổ chi tiết vật liệu, dụng cụ, sản phẩm, hàng hóa (Mẫu S10-DN / S06-DNN):**
   * Theo dõi cả **Số lượng**, **Đơn giá** và **Thành tiền**.
   * **Cột Tài khoản đối ứng chuẩn xác:** Đọc trực tiếp từ chính bút toán định giá kho được hạch toán trong Odoo (`stock.account.move`).
3. **Bảng tổng hợp chi tiết Nhập - Xuất - Tồn (Mẫu S11-DN / S07-DNN):**
   * Bảng tổng hợp toàn bộ danh mục vật tư: Tồn đầu kỳ (SL, Tiền) -> Nhập trong kỳ -> Xuất trong kỳ -> Tồn cuối kỳ.
4. **Sự đồng bộ tuyệt đối với Định giá kho Odoo 20:**
   * Module đọc trực tiếp các dòng di chuyển kho (`stock.move`) và lớp định giá kho (`stock.valuation.layer`).
   * **Đảm bảo nguyên tắc vàng:** Số dư giá trị tồn cuối kỳ trên Bảng tổng hợp N-X-T **bằng đúng 100% giá trị tồn kho trên Tài khoản 152, 155, 156** trên Bảng cân đối kế toán, kể cả đối với phương pháp giá vốn Tiêu chuẩn (Standard Price - tự động tính dòng chênh lệch đánh giá lại kho khi đổi giá) hay Bình quân gia quyền (AVCO) / FIFO.

---

### 6.2. Kiến trúc MVC của `l10n_vn_stock_reports`

```
┌────────────────────────────────────────────────────────────────────────┐
│                   KIẾN TRÚC MVC: l10n_vn_stock_reports                 │
├────────────────────────────────────────────────────────────────────────┤
│ MODEL (M):                                                             │
│  • wizard/stock_card_wizard.py (vn.stock.card.wizard):                 │
│    - Inherit vn.report.wizard.mixin                                    │
│    - Filter: layout ('card', 'ledger', 'summary'), product_ids,        │
│      category_ids, location_ids, date_from, date_to                    │
│  • models/inventory_provider.py: Cung cấp dữ liệu kho từ stock.move    │
│                                                                        │
│ VIEW (V):                                                              │
│  • views/stock_card_wizard_views.xml: Form popup chọn kho & sản phẩm   │
│  • views/menus.xml: Menus Sổ kho đặt trong Kế toán -> Sổ chi tiết      │
│  • report/stock_card_templates.xml: Template QWeb hiển thị Thẻ kho,    │
│    Sổ chi tiết vật liệu, Bảng tổng hợp N-X-T                           │
│                                                                        │
│ CONTROLLER / SERVICE (C):                                              │
│  • services/inventory_service.py:                                      │
│    - StockCardService: Tính toán biến động thẻ kho                     │
│    - InventorySummaryService: Tổng hợp N-X-T                           │
│  • report/vn_stock_report_qweb.py: Controller render QWeb và xuất PDF  │
└────────────────────────────────────────────────────────────────────────┘
```

#### Luồng dữ liệu (Data Pipeline):
```
[User mở Wizard chọn Kho & Ngày] ──> [vn.stock.card.wizard tạo InventoryFilter DTO]
                                                      │
                                                      ▼
[StockCardService / Engine] <── [inventory_provider query stock.move & stock.valuation.layer]
            │
            ▼
[Tính toán Số dư đầu kỳ -> Lũy kế Nhập/Xuất -> Số dư cuối kỳ]
            │
            ├─────────────────────────────────────────┐
            ▼                                         ▼
[Render On-Screen / QWeb PDF]               [VnXlsxWriter xuất file Excel S10/S11/S12]
```

---

## 7. PHÂN TÍCH CHI TIẾT MODULE 4: `l10n_vn_mrp_reports` (VAS REPORTS - MANUFACTURING)

### 7.1. Chức năng trong Odoo 20
Trong các doanh nghiệp sản xuất cơ khí, chế tạo máy hoặc gia công tại Việt Nam, kế toán chi phí giá thành là một nghiệp vụ cực kỳ phức tạp. `l10n_vn_mrp_reports` đưa chuẩn mực kế toán giá thành Việt Nam vào quy trình sản xuất của Odoo:
1. **Phân bổ chuẩn 3 yếu tố chi phí sản xuất:**
   * **Chi phí nguyên vật liệu trực tiếp (TK 621):** Đo trực tiếp từ nguyên vật liệu xuất dùng thực tế cho Lệnh sản xuất (MO).
   * **Chi phí nhân công trực tiếp (TK 622):** Đo từ chi phí nhân công công đoạn (Work Center / Operation Work Order).
   * **Chi phí sản xuất chung (TK 627):** Đo từ chi phí khấu hao máy móc và chi phí phụ phân bổ vào lệnh.
   *(Đúng 3 yếu tố mà Odoo 20 kết chuyển vào giá trị thành phẩm nhập kho).*
2. **Thẻ tính giá thành sản phẩm, dịch vụ (Mẫu S37-DN theo TT200/TT99, S18-DNN theo TT133):**
   * Trình bày công thức tính giá thành kinh điển của VAS:
     $$\text{Giá thành thành phẩm} = \text{Dở dang đầu kỳ (154)} + \text{Chi phí phát sinh trong kỳ (621 + 622 + 627)} - \text{Dở dang cuối kỳ (154)}$$
   * Báo cáo tách bạch rõ ràng giữa khối lượng sản phẩm hoàn thành nhập kho và chi phí dở dang của các lệnh sản xuất chưa hoàn tất cuối kỳ.
3. **Báo cáo chi phí sản xuất theo Lệnh sản xuất (MO):**
   * Cho phép đối soát từng lệnh: Chi phí kế hoạch vs Chi phí thực tế vs Giá trị Odoo đã ghi nhận vào kho thành phẩm.

---

### 7.2. Kiến trúc MVC của `l10n_vn_mrp_reports`

```
┌────────────────────────────────────────────────────────────────────────┐
│                    KIẾN TRÚC MVC: l10n_vn_mrp_reports                  │
├────────────────────────────────────────────────────────────────────────┤
│ MODEL (M):                                                             │
│  • wizard/production_cost_wizard.py (vn.production.cost.wizard):       │
│    - Inherit vn.report.wizard.mixin                                    │
│    - Layout: 'product' (theo SP), 'order' (theo MO), 'cost_card' (S37) │
│    - Filter: product_ids, production_ids, date_from, date_to           │
│  • models/manufacturing_provider.py: Data provider trích xuất chi phí  │
│    từ mrp.production, stock.move, workorder                            │
│                                                                        │
│ VIEW (V):                                                              │
│  • views/production_cost_wizard_views.xml: Form lọc theo sản phẩm & MO │
│  • views/menus.xml: Đặt trong Kế toán -> Sổ chi tiết -> Báo cáo SX     │
│  • report/production_cost_templates.xml: QWeb Template cho Mẫu S37-DN  │
│                                                                        │
│ CONTROLLER / SERVICE (C):                                              │
│  • services/manufacturing_service.py:                                  │
│    - ProductionCostService: Bóc tách chi phí 3 khoản mục theo sản phẩm │
│    - CostCardService: Lập thẻ tính giá thành S37                       │
│  • report/vn_mrp_report_qweb.py: Controller sinh PDF và xem trước      │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 8. ĐIỂM SÁNG KỸ THUẬT (DESIGN PATTERNS & BEST PRACTICES)

Qua nghiên cứu sâu cấu trúc mã nguồn của tác giả Manh Nguyen, có thể thấy đây là một trong những bộ mã nguồn Odoo có chất lượng kiến trúc cao nhất trong cộng đồng Odoo Việt Nam:

```
┌────────────────────────────────────────────────────────────────────────┐
│               CLEAN ARCHITECTURE / DOMAIN-DRIVEN DESIGN                │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│    [ PRESENTATION LAYER (Views / Wizards / QWeb / XlsxWriter) ]        │
│                                 │                                      │
│                                 ▼ DTO Filters                          │
│                                                                        │
│    [ APPLICATION / SERVICE LAYER (Services / Facades) ]                │
│                                 │                                      │
│         ┌───────────────────────┴───────────────────────┐              │
│         ▼                                               ▼              │
│  [ DOMAIN LAYER (Pure Python) ]          [ INFRASTRUCTURE LAYER ]      │
│  • LedgerEngine                          • OdooLedgerRepository        │
│  • StatementEngine                       • OdooMappingRepository       │
│  • AST Formula Parser                    • vn.ledger.provider          │
│  (100% No Odoo Dependency)               (ORM & SQL Queries)           │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

1. **Clean Architecture & Separation of Concerns (Tách biệt mối quan tâm):**
   * Toàn bộ thuật toán cân đối tài khoản, tính luồng tiền, bóc tách giá thành nằm gọn trong `domain/`. Tầng này chỉ làm việc với Python `dataclasses` và `DTO`, **không hề import `odoo.models`**.
   * Nhờ đó, logic kế toán được bảo vệ nguyên vẹn, không bị ảnh hưởng mỗi khi Odoo nâng cấp phiên bản (từ Odoo 17, 18, 19 lên 20).
2. **Nói không với `eval()` - Sử dụng AST Parser:**
   * Trong nhiều module Odoo khác, người lập trình thường dùng hàm `eval()` để tính toán công thức. Điều này gây ra lỗ hổng bảo mật nghiêm trọng (Remote Code Execution - RCE).
   * Tác giả Manh Nguyen tự xây dựng một bộ phân tích cú pháp biểu thức an toàn (`core/utils/expression_parser.py`) dựa trên Abstract Syntax Tree (AST) của Python, chỉ cho phép các phép toán số học cơ bản.
3. **Repository Pattern & Provider Extension Point:**
   * Cung cấp class `vn.ledger.provider`. Nếu doanh nghiệp có một module custom quản lý kho riêng hoặc có quy tắc tính chi phí đặc thù, chỉ cần kế thừa provider này để trả về dữ liệu tương thích, toàn bộ hệ thống báo cáo bên trên sẽ tự động hoạt động mà không cần sửa code lõi.
4. **Nhất quán 3 kênh đầu ra (Tri-output Consistency):**
   * Cùng một bộ dữ liệu từ DTO: Màn hình tương tác On-screen, Bản in PDF (QWeb), và Tệp tin Excel (XlsxWriter) cho ra kết quả khớp nhau từng con số thập phân.

---

## 9. TỔNG KẾT & KHUYẾN NGHỊ TRIỂN KHAI

### Tóm tắt giá trị mang lại:
* Bộ 4 module của tác giả **Manh Nguyen** là **giải pháp toàn diện, chuẩn mực và hiện đại nhất hiện nay** cho bài toán Kế toán Việt Nam (VAS) trên **Odoo 20 Community**.
* Giải quyết triệt để vấn đề pháp lý doanh nghiệp: Tuân thủ đầy đủ Thông tư 200/2014, Thông tư 133/2016 và đón đầu Thông tư 99/2025 (áp dụng từ 2026).
* Khép kín chu trình tài chính: Từ **Kế toán tổng hợp/BCTC (`l10n_vn_vas_reports`)** -> **Kế toán kho (`l10n_vn_stock_reports`)** -> **Kế toán chi phí giá thành sản xuất (`l10n_vn_mrp_reports`)**, xây dựng trên nền tảng vững chắc của **`vn_core`**.

### Khuyến nghị cho Odoo Developer / Consultant khi triển khai:
1. **Thứ tự cài đặt khuyến nghị:**
   ```bash
   # Bước 1: Cài đặt Core
   odoo-bin -i vn_core
   
   # Bước 2: Cài đặt Kế toán tổng hợp
   odoo-bin -i l10n_vn_vas_reports
   
   # Bước 3: Nếu có quản lý kho hàng
   odoo-bin -i l10n_vn_stock_reports
   
   # Bước 4: Nếu có phân xưởng sản xuất
   odoo-bin -i l10n_vn_mrp_reports
   ```
2. **Cấu hình ban đầu:** Sau khi cài đặt, vào ngay `Cấu hình -> Công ty`, chọn đúng **Chế độ kế toán (TT200, TT133 hoặc TT99)** để hệ thống tự động nạp cấu trúc tài khoản và mẫu biểu tương ứng.
3. **Tận dụng bộ sinh dữ liệu mẫu (`vn_demo_generator`):** Trong môi trường test, hãy sử dụng tính năng sinh demo data có sẵn của module để tạo nhanh hàng chục bút toán, phiếu kho và lệnh sản xuất mẫu, giúp kế toán viên nghiệm thu và so sánh báo cáo tức thì.

