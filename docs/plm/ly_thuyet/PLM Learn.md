# TÀI LIỆU TOÀN DIỆN: PRODUCT LIFECYCLE MANAGEMENT (PLM) TỪ THỰC TẾ SẢN XUẤT ĐẾN ODOOPLM (OPEN-SOURCE / CAD-INTEGRATED ARCHITECTURE)
> **Dành cho:** Odoo Developer Intern & Technical/Functional Consultants  
> **Kiến trúc mục tiêu:** Hệ sinh thái **OdooPLM (OmniaSolutions - Module `plm`)** tích hợp CAD/PDM mã nguồn mở trên nền tảng Odoo, **KHÔNG PHỤ THUỘC VÀO PHÂN HỆ TRẢ PHÍ ENTERPRISE (`mrp_plm`)**.  
> **Tác giả:** Senior PLM Consultant, Manufacturing Business Analyst & Odoo Technical Specialist  
> **Nguyên tắc xuyên suốt:** *Hiểu thực tế ngoài đời -> Hiểu chuẩn PLM/CAD -> Hiểu kiến trúc OdooPLM Data Model & Mixin -> Thiết kế giải pháp Odoo Technical (Source Code & ORM)*

---

# MỤC LỤC TỔNG QUAN

- [PHẦN A — PLM NGOÀI ĐỜI](#phần-a--plm-ngoài-đời)
  - [Chapter 1 — PLM Thực sự là gì?](#chapter-1--plm-thực-sự-là-gì)
  - [Chapter 2 — Một sản phẩm ngoài đời được tạo ra như thế nào?](#chapter-2--một-sản-phẩm-ngoài-đời-được-tạo-ra-như-thế-nào)
  - [Chapter 3 — Ai thực sự tham gia vào Product Lifecycle?](#chapter-3--ai-thực-sự-tham-gia-vào-product-lifecycle)
  - [Chapter 4 — CAD trong thực tế](#chapter-4--cad-trong-thực-tế)
  - [Chapter 5 — CAD không phải PLM](#chapter-5--cad-không-phải-plm)
  - [Chapter 6 — PDM vs PLM](#chapter-6--pdm-vs-plm)
  - [Chapter 7 — PLM vs ERP vs MES vs QMS vs SCM](#chapter-7--plm-vs-erp-vs-mes-vs-qms-vs-scm)
  - [Chapter 8 — BOM ngoài đời (EBOM vs MBOM vs SBOM)](#chapter-8--bom-ngoài-đời-ebom-vs-mbom-vs-sbom)
  - [Chapter 9 — Product Configuration & Variants](#chapter-9--product-configuration--variants)
  - [Chapter 10 — Version vs Revision vs Lifecycle State](#chapter-10--version-vs-revision-vs-lifecycle-state)
  - [Chapter 11 — Engineering Change Management (ECM)](#chapter-11--engineering-change-management-ecm)
  - [Chapter 12 — ECR / ECO / ECN](#chapter-12--ecr--eco--ecn)
  - [Chapter 13 — Case Study Engineering Change (Máy đóng gói P100 gãy trục)](#chapter-13--case-study-engineering-change-máy-đóng-gói-p100-gãy-trục)
  - [Chapter 14 — Change Impact Analysis & Matrix](#chapter-14--change-impact-analysis--matrix)
  - [Chapter 15 — Effectivity (Date, Serial, Lot, Unit)](#chapter-15--effectivity-date-serial-lot-unit)
  - [Chapter 16 — As-Designed / As-Planned / As-Built / As-Maintained](#chapter-16--as-designed--as-planned--as-built--as-maintained)
  - [Chapter 17 — Document Control trong sản xuất](#chapter-17--document-control-trong-sản-xuất)
  - [Chapter 18 — Configuration Management](#chapter-18--configuration-management)
  - [Chapter 19 — Traceability (Truy xuất nguồn gốc đa tầng)](#chapter-19--traceability-truy-xuất-nguồn-gốc-đa-tầng)
  - [Chapter 20 — Các phần mềm PLM nổi bật trên thế giới](#chapter-20--các-phần-mềm-plm-nổi-bật-trên-thế-giới)
  - [Chapter 21 — Thực tế thị trường PLM tại Việt Nam](#chapter-21--thực-tế-thị-trường-plm-tại-việt-nam)
- [PHẦN B — TỪ PLM NGOÀI ĐỜI SANG ODOOPLM (MODULE `plm`)](#phần-b--từ-plm-ngoài-đời-sang-odooplm-module-plm)
  - [Chapter 22 — OdooPLM đang giải quyết phần nào của PLM?](#chapter-22--odooplm-đang-giải-quyết-phần-nào-của-plm)
  - [Chapter 23 — Khái niệm OdooPLM cốt lõi (Revision Mixin, Documents, Checkout, BoM)](#chapter-23--khái-niệm-odooplm-cốt-lõi-revision-mixin-documents-checkout-bom)
  - [Chapter 24 — Real World → OdooPLM Mapping Table](#chapter-24--real-world--odooplm-mapping-table)
  - [Chapter 25 — OdooPLM Workflow: Walkthrough chi tiết (Flow: Trục S1 -> S2)](#chapter-25--odooplm-workflow-walkthrough-chi-tiết-flow-trục-s1---s2)
  - [Chapter 26 — OdooPLM + CAD: Kết nối SolidWorks, Inventor, AutoCAD, FreeCAD](#chapter-26--odooplm--cad-kết-nối-solidworks-inventor-autocad-freecad)
  - [Chapter 27 — OdooPLM + MRP: BoM Hierarchy, Source Document và Lệnh sản xuất](#chapter-27--odooplm--mrp-bom-hierarchy-source-document-và-lệnh-sản-xuất)
- [PHẦN C — GÓC NHÌN DEVELOPER VỚI ODOOPLM SOURCE CODE](#phần-c--góc-nhìn-developer-với-odooplm-source-code)
  - [Chapter 28 — OdooPLM Technical Architecture (Kiến trúc Module `plm`)](#chapter-28--odooplm-technical-architecture-kiến-trúc-module-plm)
  - [Chapter 29 — Data Model Relationship & ERD thực tế trong Module `plm`](#chapter-29--data-model-relationship--erd-thực-tế-trong-module-plm)
  - [Chapter 30 — Source Code Walkthrough (Flow: Tạo Revision mới và Khóa phát hành)](#chapter-30--source-code-walkthrough-flow-tạo-revision-mới-và-khóa-phát-hành)
  - [Chapter 31 — Odoo Development Patterns cho Module `plm`](#chapter-31--odoo-development-patterns-cho-module-plm)
  - [Chapter 32 — Từ Business Requirement đến Technical Design (10 Case thực tế với OdooPLM)](#chapter-32--từ-business-requirement-đến-technical-design-10-case-thực-tế-với-odooplm)
  - [Chapter 33 — 15 Ca Customization thường gặp trên nền tảng OdooPLM](#chapter-33--15-ca-customization-thường-gặp-trên-nền-tảng-odooplm)
  - [Chapter 34 — Debugging: Từ Client/API đến PostgreSQL Checklist](#chapter-34--debugging-từ-clientapi-đến-postgresql-checklist)
  - [Chapter 35 — Testing Strategy & Test Cases cho Module `plm`](#chapter-35--testing-strategy--test-cases-cho-module-plm)
  - [Chapter 36 — Lộ trình học tập (Roadmap từ Level 1 đến 10)](#chapter-36--lộ-trình-học-tập-roadmap-từ-level-1-đến-10)
  - [Chapter 37 — Những kiến thức Developer thường thiếu nhưng rất quan trọng](#chapter-37--những-kiến-thức-developer-thường-thiếu-nhưng-rất-quan-trọng)
- [FINAL ASSIGNMENT & ĐÁP ÁN MẪU](#final-assignment--đáp-án-mẫu)

---

# PHẦN A — PLM NGOÀI ĐỜI

---

## CHAPTER 1 — PLM THỰC SỰ LÀ GÌ?

### 1. Ngoài đời
Trong đời sống, bất kỳ sản phẩm cơ khí nào quanh ta đều có một hành trình: từ một ý tưởng phác thảo trên giấy ăn, được dựng hình 3D, tính toán sức bền, chế tạo mẫu thử, đưa vào nhà máy dập/hàn/lắp ráp hàng loạt, bán cho khách hàng, bảo dưỡng khi hỏng hóc, và cuối cùng bị đưa vào bãi tái chế khi đã lỗi thời.
**PLM (Product Lifecycle Management)** chính là "hồ sơ sức khỏe và lý lịch tư pháp trọn đời" của sản phẩm đó. Nó lưu trữ từ gen di truyền ban đầu (bản vẽ kỹ thuật CAD, yêu cầu của khách hàng) cho đến lịch sử bệnh án (các lần sửa chữa, đổi phụ tùng, đổi nhà cung cấp).

### 2. Tại sao doanh nghiệp cần?
Doanh nghiệp sản xuất không thể tồn tại nếu chỉ "biết vẽ" hoặc chỉ "biết bán". Họ đối mặt với 3 thách thức sống còn:
1. **Time-to-Market (Tốc độ ra mắt sản phẩm):** Ai ra sản phẩm mới trước sẽ chiếm lĩnh thị trường. Nếu mất 2 năm để thiết kế một chiếc máy mà đối thủ chỉ mất 9 tháng, doanh nghiệp sẽ phá sản.
2. **Cost of Poor Quality (Chi phí do sai sót kỹ thuật):** Một lỗi sai kích thước phát hiện trên màn hình máy tính chỉ tốn 5 phút để sửa. Nếu lỗi đó lọt xuống xưởng gia công, nó làm hỏng cả tấn thép. Nếu lọt ra thị trường đến tay khách hàng, nó dẫn đến các đợt thu hồi (Recall) tiêu tốn hàng triệu USD và hủy hoại uy tín thương hiệu.
3. **Quản trị sự biến động liên tục (Engineering Agility):** Sản phẩm không bao giờ đứng yên. Khách hàng đòi đổi công suất, nhà cung cấp báo hết linh kiện, nhà nước đổi quy chuẩn an toàn. Doanh nghiệp cần một hệ thống kiểm soát xem sự thay đổi đó tác động tới ai.

### 3. Ví dụ doanh nghiệp: Trước khi có PLM, họ vận hành như thế nào?
Hãy nhìn vào một xưởng cơ khí chế tạo máy tại Việt Nam quản lý theo phương thức truyền thống:
* **Lưu file bằng ổ đĩa mạng (NAS / Google Drive / Zalo):** Kỹ sư tạo thư mục `May_Dong_Goi_P100`. Bên trong có các file:
  * `Truc_chinh.dwg`
  * `Truc_chinh_sua.dwg`
  * `Truc_chinh_final.dwg`
  * `Truc_chinh_final_chot_dung_file_nay.dwg`
* **Quản lý BOM bằng Excel:** Trưởng phòng kỹ thuật lập file `BOM_P100_Ver1.xlsx`. Khi kỹ sư sửa máy, họ gửi file `BOM_P100_Ver2_moi.xlsx` qua Zalo cho Quản đốc xưởng.
* **Hậu quả nhãn tiền:** Quản đốc xưởng bận việc, mở nhầm file Excel cũ trong email, in bản vẽ cũ giao cho thợ tiện. Thợ tiện tiện xong 50 chiếc trục thì mới phát hiện lắp không vừa bạc đạn mới. Thiệt hại 50 triệu tiền thép và 1 tuần chậm tiến độ giao hàng cho khách. Kỹ sư và Quản đốc đổ lỗi cho nhau: *"Tôi gửi Zalo rồi sao anh không xem!"* - *"Tin nhắn trôi, ai rảnh kiểm tra liên tục!"*.

### 4. PLM xử lý
PLM tạo ra **Single Source of Truth (Điểm dữ liệu chân lý duy nhất)**:
* Không còn các file rải rác. Mọi tài liệu kỹ thuật, bản vẽ 3D, danh mục vật tư đều nằm trong một cơ sở dữ liệu tập trung có kiểm soát quyền truy cập.
* Khái niệm **State (Trạng thái)**: Bản vẽ khi đang vẽ mang trạng thái `Draft` (Bản nháp - cấm xưởng lấy gia công). Khi được Giám đốc kỹ thuật bấm duyệt điện tử, nó chuyển sang trạng thái `Released` (Phát hành). Xưởng chỉ có thể nhìn thấy duy nhất bản vẽ `Released`.
* Khái niệm **Revision Control**: Bản phát hành đầu tiên là Rev A. Khi sửa, hệ thống bắt buộc nâng Revision mới (Rev B), giữ nguyên lịch sử Rev A.

---

## CHAPTER 2 — MỘT SẢN PHẨM NGOÀI ĐỜI ĐƯỢC TẠO RA NHƯ THẾ NÀO?
*(Sản phẩm xuyên suốt toàn bộ tài liệu: **Máy Đóng Gói Tự Động P100**)*

Hãy theo dõi hành trình 18 bước thực tế của chiếc máy P100 tại Công ty Cổ phần Chế tạo Máy An Phát (Bình Dương):

```
[1. Yêu cầu Khách hàng] ──> [2. Khái niệm Máy P100] ──> [3. Thiết kế Kỹ thuật (R&D)]
                                                                  │
[6. Thử nghiệm tải] <── [5. Làm mẫu (Prototype)] <── [4. Mô hình 3D CAD & Bản vẽ 2D]
         │
         ▼
[7. Phê duyệt Thiết kế (Design Freeze)] ──> [8. Bóc tách BOM Kỹ thuật (EBOM)]
                                                                  │
[11. Kiểm tra Chất lượng (QC)] <── [10. Sản xuất tại Xưởng] <── [9. Chuẩn bị Sản xuất (MBOM)]
         │
         ▼
[12. Đóng gói & Bàn giao] ──> [13. Vận hành & Bảo hành] ──> [14. Sự cố đứt gãy linh kiện]
                                                                  │
[17. Ra mắt Phiên bản Mới P200] <── [16. Nâng cấp Revision] <── [15. Lệnh Thay đổi (ECO)]
         │
         ▼
[18. Khai tử Máy P100 (End of Life)]
```

* **Bước 1 — Customer Requirement:** Khách hàng (nhà máy sản xuất bánh kẹo) gửi yêu cầu: *"Cần máy đóng gói tốc độ 120 gói/phút, kích thước túi tối đa 200mm, điện 3 pha 380V, khung inox 304 tiêu chuẩn an toàn thực phẩm"*.
* **Bước 2 — Product Concept:** R&D phác thảo sơ đồ nguyên lý: Dùng cơ cấu cam gạt hay động cơ servo? Chọn concept dùng 3 trục servo Panasonic, biến tần Schneider.
* **Bước 3 — Engineering Design:** Kỹ sư tính toán động học, mô-men xoắn, ứng suất uốn, chọn công suất motor 7.5kW, hộp giảm tốc tỉ số truyền 1:20.
* **Bước 4 — CAD Modeling:** Kỹ sư dựng toàn bộ máy P100 trên phần mềm 3D CAD (SOLIDWORKS / Inventor / FreeCAD). Xuất bản vẽ 2D gia công chi tiết và bản vẽ lắp ráp tổng.
* **Bước 5 — Prototype:** Đặt mua linh kiện về xưởng làm mẫu 01 chiếc máy thử nghiệm P100-PROTOTYPE-01.
* **Bước 6 — Testing & Validation:** Chạy thử liên tục 72 giờ không tải và có tải với túi thật. Đo độ ồn, độ rung, nhiệt độ động cơ.
* **Bước 7 — Design Approval (Design Freeze):** Đóng băng thiết kế. Ký biên bản nghiệm thu kỹ thuật nội bộ. Khóa toàn bộ bản vẽ ở Revision A.
* **Bước 8 — BOM Creation (EBOM):** Xuất danh mục vật tư thiết kế gồm 350 chi tiết từ mô hình 3D CAD.
* **Bước 9 — Manufacturing Preparation (MBOM & Routing):** Kỹ sư công nghệ phân tách: chi tiết nào tự tiện phay tại xưởng, chi tiết nào mua ngoài, chi tiết nào sơn tĩnh điện thuê ngoài. Định mức công đoạn (Cắt -> Phay CNC -> Hàn -> Lắp ráp).
* **Bước 10 — Production (Sản xuất thương mại):** Nhà máy mở Lệnh sản xuất (MO) sản xuất lô đầu tiên 10 chiếc máy P100 Rev A.
* **Bước 11 — Quality Control (QC):** Đo kiểm kích thước lắp ghép, kiểm tra lực siết bu-lông, đo điện trở cách điện tủ điện.
* **Bước 12 — Delivery & Commissioning:** Bàn giao, lắp đặt và hướng dẫn vận hành cho khách hàng tại nhà máy bánh kẹo.
* **Bước 13 — Service & Maintenance:** Máy chạy thực tế tại nhà máy khách hàng, định kỳ thay dầu hộp giảm tốc sau mỗi 2,000 giờ.
* **Bước 14 — Incident Report (Sự cố):** Sau 3 tháng hoạt động ở cường độ cao, trục truyền động chính (Shaft S1) bị gãy mỏi do ứng suất tập trung tại rãnh then.
* **Bước 15 — Engineering Change (ECO):** Kỹ sư tiếp nhận phản hồi lỗi, kích hoạt Lệnh thay đổi kỹ thuật để tăng đường kính trục và đổi mác thép.
* **Bước 16 — Revision Upgrade:** Trục S1 Rev A nâng lên Trục S2 Rev B. Cụm lắp ráp máy P100 nâng lên Rev B.
* **Bước 17 — Continuous Improvement:** Tối ưu hóa chi phí sản xuất, thay đổi linh kiện dễ mua hơn tại Việt Nam.
* **Bước 18 — End of Life (EOL):** Sau 7 năm thương mại, máy P100 ngừng sản xuất, chuyển giao hoàn toàn sang thế hệ máy P200. Nhà máy chỉ duy trì phụ tùng thay thế trong kho thêm 3 năm.

---

## CHAPTER 3 — AI THỰC SỰ THAM GIA VÀO PRODUCT LIFECYCLE?

### Ma trận trách nhiệm và dòng chảy dữ liệu (Cross-Functional Data Matrix)

| Department (Bộ phận) | Responsibility (Trách nhiệm chính) | Data Created (Dữ liệu tạo ra) | Data Consumed (Dữ liệu tiếp nhận) | PLM Relevance (Ý nghĩa đối với PLM) |
|:---|:---|:---|:---|:---|
| **Sales / Marketing** | Bán hàng, khảo sát nhu cầu thị trường, lấy yêu cầu đặc biệt của khách (Custom spec) | Yêu cầu kỹ thuật (Customer Spec, RFQ), Đơn đặt hàng | Bảng thông số máy, Catalog kỹ thuật chính thức | Cung cấp đầu vào ban đầu cho R&D; kiểm tra xem yêu cầu khách có đòi hỏi sửa thiết kế không |
| **Product Management** | Định hướng dòng sản phẩm, chiến lược tính năng, quyết định khi nào khai tử (EOL) | Product Roadmap, Bản đặc tả sản phẩm (PRD), Chính sách EOL | Phản hồi thị trường, Báo cáo doanh số và lỗi bảo hành | Quản trị vòng đời cấp chiến lược; phê duyệt mở dự án mới hoặc ngừng sản xuất |
| **R&D / System Eng.** | Nghiên cứu nguyên lý, tính toán công suất, lựa chọn giải pháp kỹ thuật tổng thể | Bản tính toán công suất, Sơ đồ khối nguyên lý, DFMEA | Tiêu chuẩn ngành, Yêu cầu khách hàng | Định nghĩa cấu trúc sản phẩm gốc; quyết định các thông số kỹ thuật cốt lõi |
| **Mechanical Eng.** | Thiết kế kết cấu cơ khí, khung vỏ, trục, bánh răng, ổ đỡ | Mô hình 3D Part/Assembly, Bản vẽ 2D (.SLDPRT, .DWG, .PDF) | Sơ đồ động học, Kích thước động cơ | Tạo ra hạt nhân hình học của sản phẩm; tác giả trực tiếp của các bản vẽ cơ khí |
| **Electrical Eng.** | Thiết kế sơ đồ mạch điện tử, tủ điện điều khiển, lập trình PLC/HMI | Sơ đồ nguyên lý điện (EPLAN/AutoCAD Electrical), Chương trình PLC | Vị trí cảm biến, công suất động cơ từ Cơ khí | Đồng bộ thiết kế Cơ - Điện (Mechatronics); tránh xung đột kích thước tủ điện |
| **CAD Designer / Drafter**| Dựng chi tiết 3D, chiếu bản vẽ gia công 2D, ghi dung sai, độ nhám bề mặt | File CAD chi tiết, File STEP xuất CNC, Bản vẽ PDF có khung tên | Phác thảo thiết kế từ Kỹ sư cơ khí | Quản lý việc Check-in/Check-out file vào kho dữ liệu PDM; quản lý Version file |
| **Manufacturing Eng. (PE/ME)** | Thiết kế quy trình chế tạo, chọn dao cụ, thiết kế đồ gá (Jig), lập trình CAM | Quy trình công nghệ (Routing), Định mức giờ công, MBOM, Đồ gá | Bản vẽ 2D, Cây vật tư thiết kế (EBOM) | Chuyển đổi từ "Thiết kế cái gì" (EBOM) sang "Làm ra nó như thế nào" (MBOM & Routing) |
| **Production (Xưởng SX)** | Gia công tiện phay, hàn kết cấu, lắp ráp máy, chạy thử | Nhật ký sản xuất, Số Serial máy thực tế, Biên bản lắp ráp | Bản vẽ phát hành chính thức (Released), Lệnh sản xuất (MO) | Người tiêu thụ bản vẽ cuối cùng; phản hồi các điểm bất hợp lý trong thiết kế gây khó lắp ráp |
| **Quality Control (QC/QA)**| Kiểm tra kích thước linh kiện nhập kho (IQC), kiểm tra công đoạn (PQC), xuất xưởng (OQC) | Báo cáo kiểm tra kích thước (FAI), Biên bản không phù hợp (NCR) | Tiêu chuẩn dung sai trên bản vẽ kỹ thuật Released | Kích hoạt Lệnh thay đổi khi phát hiện tỷ lệ linh kiện bị lỗi gia công vượt ngưỡng |
| **Procurement (Mua hàng)** | Tìm nhà cung cấp thép, động cơ, vòng bi, đàm phán giá, đặt hàng | Đơn mua hàng (PO), Hợp đồng cung ứng linh kiện | Mã vật tư (Engineering Code), Nhà cung cấp được chỉ định | Bị ảnh hưởng trực tiếp khi R&D đổi linh kiện; kiểm tra thời gian giao hàng (Lead time) |
| **Supply Chain & Warehouse** | Quản lý tồn kho nguyên vật liệu, phôi thép, linh kiện tiêu hao | Báo cáo tồn kho On-hand, Thẻ kho, Vị trí lưu kho linh kiện | Kế hoạch sản xuất, Danh mục vật tư (BOM) | Cung cấp dữ liệu tồn kho để R&D làm phân tích ảnh hưởng khi đổi thiết kế |
| **Service & Warranty** | Lắp đặt tại nhà máy khách hàng, sửa chữa hỏng hóc, cung cấp phụ tùng | Nhật ký bảo hành hiện trường, Yêu cầu phụ tùng thay thế | Sách hướng dẫn bảo trì, Danh mục phụ tùng (SBOM) | Cung cấp dữ liệu thực chiến về điểm yếu của máy để R&D cải tiến ở các đời Revision sau |
| **Finance / Cost Accounting**| Tính toán giá thành kế hoạch, giá thành thực tế, phân tích biên lợi nhuận | Báo cáo giá thành sản phẩm, Chi phí phế phẩm (Scrap cost) | Định mức vật tư (BOM), Giá mua linh kiện, Giờ công | Đánh giá xem việc thay đổi thiết kế có làm máy bị đội giá vượt mức bán cho phép không |
| **Management (Ban GĐ)** | Ra quyết định chiến lược, phê duyệt ngân sách đầu tư sản phẩm mới | Quyết định phê duyệt dự án, Ký duyệt lệnh thay đổi lớn | Báo cáo tổng hợp tiến độ, Chi phí và Đánh giá rủi ro | Người phê duyệt cao nhất trong việc ban hành thiết kế chính thức |

---

## CHAPTER 4 — CAD TRONG THỰC TẾ

### 1. CAD là gì?
**CAD (Computer-Aided Design)** là phần mềm máy tính hỗ trợ kỹ sư dựng hình học, tính toán kích thước, mô phỏng lắp ghép và xuất tài liệu kỹ thuật thay thế cho việc vẽ tay trên bàn vẽ truyền thống.

### 2. Cấu trúc cây dữ liệu trong một bộ phần mềm 3D CAD: Máy P100

Khi kỹ sư thiết kế Máy đóng gói P100, cấu trúc tập tin trên máy tính hình thành theo mô hình cha - con chặt chẽ:

```
[Máy Đóng Gói P100 - Assembly Tổng (.SLDASM)]
├── [Khung Máy Inox - Sub-Assembly (.SLDASM)]
│   ├── Khung_Hàn.SLDPRT (Part chi tiết hàn)
│   ├── Chân_Chỉnh_Độ_Cao.SLDPRT (Part chi tiết tiện)
│   └── Bu-lông M12x50.SLDPRT (Part thư viện tiêu chuẩn)
├── [Động Cơ Servo 7.5kW - Part / Imported Step (.SLDPRT)]
├── [Hộp Giảm Tốc 1:20 - Part (.SLDPRT)]
├── [Trục Truyền Động Chính - Part (.SLDPRT)]
├── [Cụm Ổ Đỡ Trục - Sub-Assembly (.SLDASM)]
│   ├── Vỏ_Gối_Đỡ.SLDPRT
│   └── Ổ_Bi_Cầu_6212.SLDPRT
└── [Bản Vẽ Kỹ Thuật Gia Công Trục - 2D Drawing (.SLDDRW)]
```

* **Part (Chi tiết đơn lẻ):** Một khối vật liệu liền lạc duy nhất (Ví dụ: Trục máy, Bánh răng).
* **Assembly (Cụm lắp ráp):** Tập hợp nhiều Part hoặc các Sub-Assembly con liên kết với nhau bằng các ràng buộc cơ học (Mates).
* **Drawing (Bản vẽ kỹ thuật 2D):** Bản chiếu 2D lấy dữ liệu từ Part hoặc Assembly 3D. Chứa khung tên (Title Block), kích thước gia công, dung sai lắp ghép, độ nhám bề mặt và bảng kê vật tư sơ bộ (CAD BOM).
* **Configuration (Cấu hình hình học nội tại trong CAD):** Một file Part có thể chứa nhiều trạng thái kích thước khác nhau.

---

## CHAPTER 5 — CAD KHÔNG PHẢI PLM

Một sai lầm rất lớn của kỹ sư mới là nghĩ rằng: *"Công ty tôi mua bản quyền SOLIDWORKS / Inventor rồi, tức là tôi có PLM rồi đúng không?"*.
**Hoàn toàn SAI. CAD ≠ PLM.**

CAD chỉ là **công cụ tạo hình (Authoring Tool)**. Một mình CAD hoàn toàn bất lực trước các câu hỏi vận hành doanh nghiệp sau đây:
* Ai cho phép sửa file? (Không có phiếu duyệt).
* Bản nào là bản chính thức để xưởng mang đi gia công?
* Bản vẽ mới thay đổi thì tồn kho linh kiện cũ xử lý ra sao?
* Đơn hàng mua linh kiện cũ đã gửi nhà cung cấp thì hủy thế nào?

CAD quản lý việc **THIẾT KẾ (Geometry)**; còn PLM quản lý **VÒNG ĐỜI VÀ QUY TRÌNH KINH DOANH (Lifecycle & Process)**.

---

## CHAPTER 6 — PDM VS PLM

```
┌────────────────────────────────────────────────────────────────────────┐
│                                 PLM                                    │
│  (Quản lý Vòng đời, EBOM/MBOM, ECO, Dự án, Chi phí, Tích hợp ERP/MES)  │
│                                                                        │
│       ┌────────────────────────────────────────────────────────┐       │
│       │                         PDM                            │       │
│       │  (Quản lý File CAD, Check-in/out, Revision File, Vault)│       │
│       │                                                        │       │
│       │       ┌────────────────────────────────────────┐       │       │
│       │       │                 CAD                    │       │       │
│       │       │ (Vẽ 3D Part, Assembly, Bản vẽ 2D)      │       │       │
│       │       └────────────────────────────────────────┘       │       │
│       └────────────────────────────────────────────────────────┘       │
└────────────────────────────────────────────────────────────────────────┘
```

* **CAD:** Kỹ sư vẽ trục máy.
* **PDM:** Khóa file, quản lý Check-in/Check-out, lưu trữ bản vẽ trong két an toàn (Vault), quản lý quan hệ lắp ráp giữa các file `.sldprt` và `.sldasm`.
* **PLM:** Quản lý vòng đời sản phẩm, duyệt bản vẽ từ Draft sang Released, bóc tách BoM sang sản xuất, kiểm soát thay đổi và chi phí.

---

## CHAPTER 7 — PLM VS ERP VS MES VS QMS VS SCM

```
                ┌────────────────────────────────────────────────────────┐
                │                         PLM                            │
                │        "ĐỊNH NGHĨA SẢN PHẨM & QUẢN TRỊ THAY ĐỔI"       │
                │  Thiết kế máy P100 gồm những gì? EBOM ra sao? Bản vẽ   │
                │  nào được duyệt? Nâng đời máy lên Rev B.               │
                └───────────────────────────┬────────────────────────────┘
                                            │ Đẩy MBOM, Routing, Bản vẽ Released
                                            ▼
                ┌────────────────────────────────────────────────────────┐
                │                         ERP                            │
                │            "QUẢN TRỊ NGUỒN LỰC & KINH DOANH"           │
                │  Cần mua bao nhiêu tấn thép? Giá vốn 1 máy là bao      │
                │  nhiêu? Hàng tồn kho còn bao nhiêu? Khi nào giao hàng? │
                └───────────────┬────────────────────────▲───────────────┘
                                │                        │
         Tạo Lệnh Sản Xuất (MO) │                        │ Phản hồi nguyên vật liệu
         & Nhu cầu mua hàng     │                        │ & Tiến độ giao hàng
                                ▼                        │
┌───────────────────────────────────────┐        ┌───────┴────────────────────────┐
│                  MES                  │        │              SCM               │
│        "THỰC THI TẠI PHÂN XƯỞNG"      │        │       "CHUỖI CUNG ỨNG"         │
│ Máy phay CNC số 3 đang gia công trục  │        │ Đặt mua động cơ từ Nhật Bản;   │
│ máy P100; công nhân bấm giờ bắt đầu/  │        │ theo dõi tàu biển chở linh     │
│ kết thúc; giám sát chỉ số OEE máy.    │        │ kiện về cảng Cát Lái.          │
└───────────────────┬───────────────────┘        └────────────────────────────────┘
                    │ Dữ liệu kích thước đo kiểm
                    ▼
┌───────────────────────────────────────┐
│                  QMS                  │
│          "QUẢN LÝ CHẤT LƯỢNG"         │
│ Đo kiểm 10 trục máy P100; phát hiện 1 │
│ trục bị sai dung sai lỗ; tạo phiếu    │
│ không phù hợp NCR gửi ngược lại PLM.  │
└───────────────────────────────────────┘
```

---

## CHAPTER 8 — BOM NGOÀI ĐỜI (EBOM vs MBOM vs SBOM)

```
   [ CÂY LẮP RÁP 3D CAD ] 
             │
             ▼
   ┌──────────────────┐
   │       EBOM       │  Góc nhìn của KỸ SƯ THIẾT KẾ:
   │ (Engineering BOM)│  • Phản ánh cấu trúc chức năng và liên kết hình học.
   └─────────┬────────┘  • Tổ chức theo cụm: Khung, Cụm Truyền Động, Tủ Điện.
             │
             │ Chuyển đổi công nghệ (Thêm vật tư phụ, phân rã công đoạn, gộp cụm hàn)
             ▼
   ┌──────────────────┐
   │       MBOM       │  Góc nhìn của KỸ SƯ SẢN XUẤT & NHÀ MÁY:
   │(Manufacturing BOM│  • Phản ánh quy trình lắp ráp và đường đi tại xưởng (Routing).
   └─────────┬────────┘  • Bổ sung: Dầu mỡ bôi trơn, sơn, keo dán, vật liệu đóng gói.
             │
             │ Tái cấu trúc theo góc nhìn bảo dưỡng và bán lẻ phụ tùng
             ▼
   ┌──────────────────┐
   │   Service BOM    │  Góc nhìn của PHÒNG BẢO HÀNH & DỊCH VỤ:
   │     (SBOM)       │  • Bán theo cụm bảo dưỡng (Kit sửa chữa), linh kiện hao mòn nhanh.
   └──────────────────┘  • Không liệt kê chi tiết hàn chết không thể tháo rời.
```

### Tại sao BOM trong CAD (EBOM) KHÔNG THỂ dùng trực tiếp để sản xuất (MBOM)?
1. **CAD không vẽ vật tư phi hình học:** Sơn, que hàn, mỡ bò bôi trơn, keo khóa ren Loctite, thùng carton bọc hàng.
2. **Cấu trúc lắp ráp khác cấu trúc phân xưởng:** Trong CAD gom ốc vít vào 1 cụm; ở xưởng thì chia ốc cho xưởng hàn và xưởng lắp ráp hoàn thiện.
3. **Cụm hàn chết:** Trong CAD là nhiều thanh rời; ở xưởng hàn xong thành 1 bán thành phẩm duy nhất.

---

## CHAPTER 9 — PRODUCT CONFIGURATION & VARIANTS

Quản lý biến thể cấu hình sản phẩm:
* Model cơ sở: Máy Đóng Gói P100.
* Tùy chọn công suất: 5.5kW / 7.5kW / 11kW.
* Tùy chọn điện áp: 220V / 380V / 460V.
* Tùy chọn vật liệu: Inox 304 / Inox 316.
* **150% Super BoM:** Cây BoM chứa toàn bộ linh kiện của mọi biến thể kèm theo luật điều kiện chọn lọc (Selection Rules).

---

## CHAPTER 10 — VERSION VS REVISION VS LIFECYCLE STATE

* **Version:** Các bước lưu nháp nội bộ của kỹ sư trong quá trình vẽ (`0.1`, `0.2`...).
* **Revision:** Bản sửa đổi chính thức được phê duyệt phát hành ra ngoài R&D (`Rev A`, `Rev B` hoặc `Rev 0`, `Rev 1`).
* **Lifecycle States:** `Draft` -> `Confirmed` -> `Released` -> `Under Modify` -> `Obsoleted`.

---

## CHAPTER 11 — ENGINEERING CHANGE MANAGEMENT (ECM)

Mọi thay đổi kỹ thuật khi đã ra khỏi phòng R&D đều có thể gây ra hiệu ứng domino tàn phá (lỗi gia công, phế phẩm tồn kho, sai đơn mua hàng). ECM sinh ra để kiểm soát chặt chẽ quá trình này.

---

## CHAPTER 12 — ECR / ECO / ECN

* **ECR (Engineering Change Request):** Yêu cầu/Đề xuất thay đổi (Từ QC, xưởng, khách hàng).
* **ECO (Engineering Change Order):** Lệnh thực thi thay đổi (Sau khi được duyệt).
* **ECN (Engineering Change Notice):** Thông báo phát hành thay đổi ra toàn nhà máy.

---

## CHAPTER 13 — CASE STUDY ENGINEERING CHANGE (MÁY ĐÓNG GÓI P100 GÃY TRỤC)

Tình huống: Trục S1 phi 50mm gãy do quá tải xoắn. Kỹ sư R&D thiết kế Trục S2 phi 60mm thay thế. Toàn bộ chuỗi xử lý: Phát hiện -> Phân tích FEA -> Nâng Revision Trục S1 Rev A lên Trục S2 Rev B -> Đổi Vòng bi từ 6210 lên 6212 -> Phế phẩm 15 trục cũ trong kho -> Hủy đơn mua phôi cũ -> Cập nhật bản vẽ và BoM sản xuất mới.

---

## CHAPTER 14 — CHANGE IMPACT ANALYSIS & MATRIX

Ma trận phân tích ảnh hưởng (CAD, Bản vẽ 2D, BoM, Chi phí tăng thêm 1.6 triệu/máy, Nhà cung cấp thép 40Cr mới, Tồn kho cũ thiệt hại 25 triệu, Dụng cụ dao tiện mới, Quy trình nhiệt luyện mới, Cập nhật tài liệu hướng dẫn lắp ráp).

---

## CHAPTER 15 — EFFECTIVITY (HIỆU LỰC THAY ĐỔI)

* **Date Effectivity:** Áp dụng theo ngày mốc trong tương lai.
* **Serial Effectivity:** Áp dụng từ số Serial máy cụ thể (`P100-SN-051` trở đi).
* **Lot Effectivity:** Áp dụng theo lô sản xuất.

---

## CHAPTER 16 — AS-DESIGNED / AS-PLANNED / AS-BUILT / AS-MAINTAINED

4 trạng thái phản chiếu vòng đời:
1. As-Designed (Thiết kế lý tưởng trên CAD).
2. As-Planned (Kế hoạch sản xuất và công đoạn tại xưởng).
3. As-Built (Thực tế chiếc máy được lắp ráp bằng số Serial động cơ nào, số lô phôi thép nào).
4. As-Maintained (Lịch sử bảo hành thay thế phụ tùng ngoài công trường sau 5 năm).

---

## CHAPTER 17 — DOCUMENT CONTROL TRONG SẢN XUẤT

Kiểm soát chặt chẽ bản vẽ 2D PDF gia công, file 3D STEP, tài liệu đặc tả, kế hoạch kiểm tra chất lượng. Bản vẽ Released là căn cứ pháp lý duy nhất. Bản vẽ cũ phải bị đóng dấu nước `OBSOLETE`.

---

## CHAPTER 18 — CONFIGURATION MANAGEMENT

Đảm bảo tính đồng bộ 100% giữa BoM Rev B, Bản vẽ CAD Rev B, Sơ đồ điện Rev 2.0, Chương trình nạp PLC Ver 2.1, và Hướng dẫn lắp ráp Rev B.

---

## CHAPTER 19 — TRACEABILITY (TRUY XUẤT NGUỒN GỐC ĐA TẦNG)

Khả năng truy ngược dòng từ số Serial máy khách hàng đang dùng -> Lệnh sản xuất nào -> Ngày nào -> Lô thép nào -> Chứng chỉ CO/CQ của nhà cung cấp nào -> Bản vẽ kỹ thuật nào đã phát hành.

---

## CHAPTER 20 — CÁC PHẦN MỀM PLM NỔI BẬT TRÊN THẾ GIỚI

* **Siemens Teamcenter:** Digital Twin toàn diện, High-End Enterprise (VinFast sử dụng).
* **PTC Windchill:** Web-centric, quản lý cấu hình và IoT kết nối hiện trường.
* **Dassault ENOVIA:** Trực tiếp gắn với CATIA và SolidWorks.
* **SOLIDWORKS PDM / Autodesk Vault:** Chuyên sâu quản lý file CAD cho phân khúc vừa và nhỏ.

---

## CHAPTER 21 — THỰC TẾ THỊ TRƯỜNG PLM TẠI VIỆT NAM

* **Doanh nghiệp lớn:** VinFast (Siemens Teamcenter + NX), Thaco Chu Lai (CATIA, NX, AutoCAD).
* **Doanh nghiệp FDI phụ trợ:** Bắc Ninh, Thái Nguyên, Hải Phòng dùng NX, Cimatron làm khuôn mẫu.
* **Doanh nghiệp cơ khí SME Việt Nam:** 80% dùng SOLIDWORKS/Inventor nhưng **chưa có hệ thống PLM đúng nghĩa**, quản lý file trên ổ đĩa mạng và Excel lộn xộn. Nhu cầu cấp bách là một giải pháp PLM/PDM kết nối ERP có chi phí hợp lý và linh hoạt.

---

# PHẦN B — TỪ PLM NGOÀI ĐỜI SANG ODOOPLM (MODULE `plm`)

> **CHÚ Ý QUAN TRỌNG:**  
> Ở phần này, chúng ta nghiên cứu trực tiếp mã nguồn của module **`plm` (OmniaSolutions OdooPLM v20.0.1.0.6)** nằm ngay trong thư mục `addons/plm` của dự án.  
> **Chúng ta KHÔNG dùng module trả phí Enterprise `mrp_plm` (không dùng `mrp.eco`).**  
> OdooPLM là một giải pháp PLM/PDM chuyên sâu thực thụ, kết nối trực tiếp với các phần mềm CAD (SolidWorks, Inventor, AutoCAD, FreeCAD, SolidEdge...) thông qua cơ chế Check-in/Check-out và quản trị Revision chặt chẽ.

---

## CHAPTER 22 — ODOOPLM ĐANG GIẢI QUYẾT PHẦN NÀO CỦA PLM?

Sự khác biệt triệt để giữa mô hình Odoo Enterprise (`mrp_plm`) và mô hình OdooPLM (`addons/plm`):

```
┌──────────────────────────────────────┐    ┌──────────────────────────────────────┐
│       ODOO ENTERPRISE (mrp_plm)      │    │        ODOOPLM (addons/plm)          │
│       [ ERP-Centric Approach ]       │    │       [ CAD/PDM-Centric Approach ]   │
├──────────────────────────────────────┤    ├──────────────────────────────────────┤
│ • Không quản lý file CAD chuyên sâu. │    │ • Quản lý chuyên sâu tệp tin CAD 3D/ │
│ • Không có Check-in / Check-out.     │    │   2D (.sldprt, .sldasm, .dwg, .prt). │
│ • Không quản lý quan hệ lắp ráp CAD. │    │ • CÓ Check-in / Check-out an toàn.   │
│ • Quản lý thay đổi qua phiếu ECO     │    │ • Quản lý cây quan hệ lắp ráp CAD    │
│   (mrp.eco) tạo BoM nháp.            │    │   (Parent-Child Document Relations). │
│ • Phù hợp DN chỉ cần đổi định mức.   │    │ • Kiểm soát Revision chi tiết & BoM  │
│                                      │    │   ngay trên đối tượng kỹ thuật.      │
│                                      │    │ • Tích hợp trực tiếp Add-in vào      │
│                                      │    │   SolidWorks, Inventor, FreeCAD.     │
└──────────────────────────────────────┘    └──────────────────────────────────────┘
```

### OdooPLM trong thư mục `addons/plm` giải quyết:
1. **Engineering Component Management (`product.product`, `product.template`):** Quản lý chi tiết cơ khí với mã kỹ thuật (`engineering_code`), chỉ số sửa đổi (`engineering_revision`), chữ cái phiên bản (`engineering_revision_letter`), và trạng thái vòng đời.
2. **CAD Document Management (`ir.attachment`):** Phân loại tài liệu `2d`, `3d`, quản lý file PDF xuất xưởng (`printout`), ảnh thumbnail 3D (`preview`).
3. **PDM Check-in / Check-out (`plm.checkout`):** Khóa file khi kỹ sư đang mở sửa trên máy trạm CAD, ngăn chặn người khác ghi đè.
4. **CAD Document Relations (`ir.attachment.relations`):** Lưu trữ cấu trúc cha - con của cụm lắp ráp 3D CAD ngay trong cơ sở dữ liệu Odoo.
5. **BoM Derived from CAD (`mrp.bom`):** BoM sản xuất được liên kết trực tiếp với file CAD gốc thông qua trường `source_id`. Hỗ trợ bóc tách BoM đa tầng (Exploded BoM) và tra cứu ngược chi tiết dùng ở đâu (Imploded BoM / Where-Used).
6. **Thuộc tính kỹ thuật:** Từ điển vật liệu (`plm.material`), độ nhám bề mặt (`plm.finishing`), nhiệt luyện/xử lý bề mặt (`plm.treatment`).

---

## CHAPTER 23 — KHÁI NIỆM ODOOPLM CỐT LÕI

Để làm chủ OdooPLM, bạn cần hiểu sâu 5 khối kiến trúc kỹ thuật sau:

### 1. Trừu tượng hóa Revision: `revision.plm.mixin`
Đây là lớp Abstract Model nền tảng (`addons/plm/models/plm_mixin.py`). Cả **Sản phẩm (`product.template`)** và **Tài liệu CAD (`ir.attachment`)** đều kế thừa mixin này.
Các trường cốt lõi của mixin:
* **`engineering_code` (Char):** Mã số kỹ thuật định danh duy nhất của chi tiết hoặc bản vẽ. Mã này giữ nguyên qua các đời cải tiến.
* **`engineering_revision` (Integer):** Chỉ số lần sửa đổi (bắt đầu từ 0, tăng dần 1, 2, 3...).
* **`engineering_revision_letter` (Char):** Ký tự phiên bản hiển thị cho người dùng (A, B, C, D... hoặc AA, AB...). Được tự động tính toán qua hàm `convert_to_letter`.
* **`engineering_state` (Selection):** Trạng thái vòng đời chuẩn kỹ thuật:
  * `draft`: Bản nháp, kỹ sư đang thiết kế, được phép sửa đổi.
  * `confirmed`: Đã xác nhận hoàn thành thiết kế, chờ phê duyệt phát hành.
  * `released`: ĐÃ PHÁT HÀNH CHÍNH THỨC. Khóa cứng toàn bộ dữ liệu, cấm sửa đổi.
  * `undermodify`: Đang trong quá trình bị sửa đổi (khi đã sinh ra Revision mới).
  * `obsoleted`: Đã lỗi thời, bị thay thế hoàn toàn.
* **`engineering_writable` (Boolean):** Cờ khóa quyền ghi.
* **Quy tắc bất khả xâm phạm (`PLM_NO_WRITE_STATE`):**
  ```python
  PLM_NO_WRITE_STATE = ['confirmed', 'released', 'undermodify', 'obsoleted']
  ```
  Nếu bản ghi rơi vào các trạng thái trên, hàm `write()` sẽ chặn lại, không cho phép sửa đổi bất kỳ trường thông tin kỹ thuật nào! Muốn sửa, bắt buộc phải dùng hàm `new_version()` để sinh bản ghi Revision mới.

### 2. Quản lý Tài liệu CAD: `ir.attachment` kế thừa
OdooPLM biến bảng `ir.attachment` tiêu chuẩn của Odoo thành một kho PDM chuyên nghiệp:
* `is_plm`: Đánh dấu tệp tin này được quản lý bởi hệ thống PLM.
* `document_type`: Phân loại định dạng: `2d` (Bản vẽ 2D), `3d` (Mô hình khối 3D Part/Assembly), `pr` (Bản trình chiếu), `other` (Tài liệu khác).
* `printout`: Lưu trữ nội dung file PDF được tự động xuất ra từ bản vẽ 2D để phục vụ xưởng và mua hàng xem trực tiếp không cần cài CAD.
* `preview`: Ảnh thumbnail 3D (PNG/JPEG) hiển thị trực quan chi tiết trên giao diện web.
* `linkedcomponents`: Quan hệ Many2many liên kết giữa File CAD và Mã sản phẩm tương ứng trong Odoo (`plm_component_document_rel`).

### 3. Cơ chế PDM Check-out / Check-in: `plm.checkout`
* Khi kỹ sư mở file từ SolidWorks hoặc Inventor: Hệ thống tạo một record trong `plm.checkout`, gán `is_checkout = True` và ghi nhận `checkout_user`.
* Trong lúc file đang bị Check-out: Các kỹ sư khác mở file sẽ nhận được cảnh báo "File đang bị khóa sửa đổi bởi kỹ sư Nam". Họ chỉ có quyền mở ở chế độ Read-Only.
* Sau khi kỹ sư sửa xong và lưu vào Odoo: File được Check-in trở lại, xóa bản ghi khóa.

### 4. Cấu trúc quan hệ lắp ráp CAD: `ir.attachment.relations`
* Lưu trữ quan hệ cha - con giữa các file CAD: File cụm lắp ráp máy `May_P100.SLDASM` liên kết với các file con `Khung.SLDPRT`, `Truc.SLDPRT`.
* Nhờ bảng này, Odoo hiểu được cấu trúc lắp ráp 3D mà không cần phải mở phần mềm CAD lên để đọc.

### 5. Định mức vật tư gắn liền với CAD: `mrp.bom` kế thừa
* Trường **`source_id` (Many2one `ir.attachment`):** Trỏ thẳng về file CAD Assembly đã khai sinh ra BoM này.
* `engineering_revision`: Liên kết với Revision của sản phẩm (`product_tmpl_id.engineering_revision`).
* `engineering_state`: Liên kết với trạng thái vòng đời của sản phẩm.
* `father_complete_ids`: Cây phả hệ BoM đa tầng tính toán tự động qua hàm `_father_compute`.

---

## CHAPTER 24 — REAL WORLD → ODOOPLM MAPPING TABLE

| Nghiệp vụ thực tế ngoài xưởng | Khái niệm chuẩn PLM | Đối tượng trong OdooPLM (`addons/plm`) | Cách OdooPLM thực hiện | Giới hạn cần lưu ý |
|:---|:---|:---|:---|:---|
| Mã kỹ thuật chi tiết không đổi qua các đời | Part Number / Engineering Code | Field **`engineering_code`** trên Product & Attachment | Mã duy nhất toàn hệ thống, đánh chỉ mục Unique Index cùng `engineering_revision` | Bắt buộc nhập hoặc sinh tự động chuẩn xác |
| Phiên bản sửa đổi (Rev A, Rev B) | Revision Letter | Field **`engineering_revision_letter`** & **`engineering_revision`** | Tự động chuyển đổi số nguyên sang ký tự A, B, C... qua `convert_to_letter` | Chuẩn hóa theo bảng chữ cái A-Z |
| Khóa bản vẽ không cho sửa đè khi đã duyệt | Design Freeze / Lock Released | **`PLM_NO_WRITE_STATE`** trong `plm_mixin.py` | Chặn hàm `write()` của ORM khi state thuộc `['confirmed', 'released', ...]` | Muốn sửa bắt buộc phải bấm nút tạo Revision mới |
| Khóa file khi kỹ sư đang mở vẽ trên CAD | PDM Check-out / Check-in | Model **`plm.checkout`** & Button **`toggle_check_out`** | Tạo bản ghi khóa file, hiển thị tên người đang giữ file trên giao diện | Cần Add-in client trên máy tính để tự động hóa hoàn toàn |
| Bản vẽ PDF 2D xuất xưởng cho công nhân | Engineering Drawing Printout | Field **`printout`** (Binary) trên `ir.attachment` | Lưu file PDF, có nút tải/xem nhanh trên form linh kiện | Client CAD tự động convert PDF và đẩy lên lúc save |
| Cây lắp ráp 3D cha-con trong CAD | CAD Assembly Structure | Model **`ir.attachment.relations`** | Bảng trung gian lưu parent_id và child_id giữa các file CAD | Đồng bộ từ cây thiết kế CAD sang |
| Định mức sản xuất sinh ra từ bản vẽ | BoM from CAD Assembly | Field **`source_id`** trên `mrp.bom` | BoM trỏ trực tiếp về file CAD Assembly nguồn đã tạo ra nó | BoM được bóc tách từ cấu trúc file CAD |
| Quy trình duyệt phát hành bản vẽ | Release Workflow Sign-off | Các method: `action_confirm`, `action_release`, `action_draft` | Chuyển đổi trạng thái: Draft -> Confirmed -> Released; phân quyền `group_plm_release_users` | Chưa có cấu hình ma trận duyệt động nhiều cấp phức tạp như hệ thống lớn |
| Phân tích chi tiết dùng ở những cụm nào | Where-Used / Imploded BoM | Method **`getImplodedBom()`** & Menu **Component Relations** | Truy vấn đệ quy ngược từ chi tiết con lên tất cả các BoM cha đang chứa nó | Cần kiểm tra kỹ hiệu năng khi cây BoM sâu hàng chục tầng |
| Thuộc tính vật liệu cơ khí (Thép, Nhôm) | Material Specification | Model **`plm.material`** & field `material_id` | Từ điển chuẩn hóa tên vật liệu, mác thép (S45C, SUS304, 40Cr...) | Quản lý dạng danh mục danh định |

---

## CHAPTER 25 — ODOOPLM WORKFLOW: WALKTHROUGH CHI TIẾT (FLOW: TRỤC S1 -> S2)

Hãy thực hành mô phỏng tình huống thực chiến: **Thay thế Trục S1 bằng Trục S2 trên Máy Đóng Gói P100** bằng chính quy trình vận hành của module `plm`:

```
[ BƯỚC 1: HIỆN TRẠNG MÁY P100 Ở TRẠNG THÁI RELEASED ]
• Linh kiện: `P100-SHAFT` (Trục S1) mang trạng thái:
  - engineering_code = "P100-SHAFT"
  - engineering_revision = 0
  - engineering_revision_letter = "A"
  - engineering_state = "released" (KHÓA CỨNG - READ-ONLY)
• Bản vẽ CAD đính kèm: `P100-SHAFT-REV-A.SLDPRT` cũng mang trạng thái "released".
• BoM Máy P100 đang chứa Trục S1 Rev A và mang trạng thái "released".
             │
             ▼
[ BƯỚC 2: PHÁT HIỆN SỰ CỐ & TẠO REVISION MỚI ]
• Kỹ sư mở form linh kiện `P100-SHAFT` trên Odoo:
  - Do đang ở trạng thái `released`, các trường kích thước và vật liệu bị mờ (Read-only).
  - Kỹ sư bấm nút Smart Action: "New Revision" (gọi method `NewRevision()` hoặc `new_version()`).
• Hệ thống OdooPLM tự động thực thi:
  - Nhân bản linh kiện sang bản ghi mới:
    * engineering_code = "P100-SHAFT" (Giữ nguyên mã kỹ thuật).
    * engineering_revision = 1 (Tăng chỉ số lên 1).
    * engineering_revision_letter = "B" (Tự động nhảy sang Rev B).
    * engineering_state = "draft" (Mở khóa cho phép sửa đổi).
  - Bản ghi cũ (Rev A) tự động chuyển sang trạng thái: `undermodify`.
             │
             ▼
[ BƯỚC 3: SỬA ĐỔI THIẾT KẾ VÀ TÀI LIỆU CAD ]
• Kỹ sư Check-out file CAD để sửa trên SolidWorks:
  - Tăng đường kính từ phi 50mm lên phi 60mm.
  - Đổi vật liệu từ S45C sang 40Cr.
• Lưu file CAD và Check-in trở lại Odoo:
  - File bản vẽ mới được gắn vào Trục Rev B.
  - File PDF xuất xưởng mới được cập nhật vào trường `printout`.
  - Trên Odoo, trường `material_id` được chọn sang mác thép "40Cr".
             │
             ▼
[ BƯỚC 4: CẬP NHẬT CẤU TRÚC BOM MÁY P100 ]
• Cụm máy tổng P100 cũng được tạo Revision mới (Rev B).
• Trong BoM mới:
  - Dòng linh kiện Trục S1 Rev A được thay thế bằng Trục S2 Rev B.
  - Vòng bi 6210 được thay thế bằng Vòng bi 6212.
             │
             ▼
[ BƯỚC 5: XÁC NHẬN VÀ PHÊ DUYỆT PHÁT HÀNH (WORKFLOW) ]
• Kỹ sư thiết kế bấm nút: "Confirm Component" (gọi method `action_confirm`).
  - Trạng thái chuyển từ `draft` -> `confirmed`.
• Trưởng phòng R&D (thuộc nhóm quyền `plm.group_plm_release_users`) kiểm tra bản vẽ:
  - Bấm nút: "Release Component" (gọi method `action_release`).
  - Trạng thái chính thức chuyển sang: `released`.
  - Hệ thống ghi nhận: `engineering_release_user` = ID người duyệt, `engineering_release_date` = Thời gian hiện tại.
  - Toàn bộ bản ghi Trục S2 Rev B và BoM Rev B bị KHÓA CỨNG vĩnh viễn!
             │
             ▼
[ BƯỚC 6: KHAI TỬ BẢN VẼ CŨ ]
• Bản ghi Trục S1 Rev A cũ được chuyển trạng thái từ `undermodify` sang `obsoleted` (gọi method `action_from_undermodify_to_obsoleted`).
• Xưởng sản xuất mở danh sách linh kiện: Bộ lọc mặc định sẽ chỉ hiển thị các linh kiện ở trạng thái `released`, ngăn chặn 100% việc thợ tiện nhầm bản vẽ Rev A cũ!
```

---

## CHAPTER 26 — ODOOPLM + CAD: KẾT NỐI SOLIDWORKS, INVENTOR, AUTOCAD, FREECAD

OdooPLM được thiết kế như một **máy chủ PDM trung tâm** giao tiếp trực tiếp với các phần mềm thiết kế cơ khí trên máy trạm thông qua kiến trúc Client - Server:

```
┌────────────────────────────────────────────────────────────────────────┐
│                   MÁY TRẠM CỦA KỸ SƯ THIẾT KẾ (CLIENT)                 │
│                                                                        │
│   ┌────────────────────────────────────────────────────────────┐       │
│   │   Phần mềm CAD: SOLIDWORKS / Inventor / AutoCAD / FreeCAD  │       │
│   └─────────────────────────────┬──────────────────────────────┘       │
│                                 │ C++ / C# API Plugin                  │
│                                 ▼                                      │
│   ┌────────────────────────────────────────────────────────────┐       │
│   │             OdooPLM CAD Connector (Client Add-in)          │       │
│   │  • Menu OdooPLM tích hợp trực tiếp trên thanh Ribbon CAD   │       │
│   │  • Nút bấm: "Save to Odoo", "Check-Out", "Create BoM"      │       │
│   └─────────────────────────────┬──────────────────────────────┘       │
└─────────────────────────────────┼──────────────────────────────────────┘
                                  │ Giao thức JSON-RPC / XML-RPC qua HTTP(S)
                                  ▼
┌────────────────────────────────────────────────────────────────────────┐
│                    MÁY CHỦ ODOO (SERVER - MODULE `plm`)                │
│                                                                        │
│   • Controller tiếp nhận API: /plm/...                                 │
│   • Model product.product: Tiếp nhận thông tin linh kiện, khối lượng   │
│   • Model ir.attachment: Nhận file 3D (.sldprt), 2D (.slddrw), PDF     │
│   • Model plm.checkout: Quản lý khóa file                              │
│   • Model mrp.bom: Tự động tạo cây BoM từ cây lắp ráp CAD 3D           │
└────────────────────────────────────────────────────────────────────────┘
```

### Các bước hoạt động thực tế từ màn hình CAD:
1. **Mở và Sửa:** Kỹ sư mở SolidWorks, bấm nút "Open from Odoo". Tìm kiếm mã `P100-SHAFT`. Hệ thống tải file về máy và tự động tạo record Check-out trên Odoo để khóa file đối với các kỹ sư khác.
2. **Lưu và Đồng bộ:** Sau khi sửa xong trên CAD, kỹ sư bấm nút "Save to Odoo":
   * Add-in tự động trích xuất các thuộc tính Custom Properties trên CAD (Vật liệu, khối lượng, người vẽ, ngày vẽ).
   * Add-in tự động render bản vẽ 2D ra file PDF và chụp ảnh thumbnail 3D dạng PNG.
   * Add-in gửi gói dữ liệu qua API lên Odoo: Cập nhật file nhị phân vào `ir.attachment`, lưu file PDF vào trường `printout`, lưu ảnh vào `preview`.
3. **Tự động sinh BoM:** Nếu đang mở cụm lắp ráp Assembly, kỹ sư bấm "Create BoM from Assembly":
   * OdooPLM đọc toàn bộ cây chi tiết con từ CAD và tự động tạo các dòng `mrp.bom.line` tương ứng trên Odoo với số lượng chính xác 100%!

---

## CHAPTER 27 — ODOOPLM + MRP: BOM HIERARCHY, SOURCE DOCUMENT VÀ LỆNH SẢN XUẤT

Trong module `plm`, mối quan hệ giữa Định nghĩa Kỹ thuật và Sản xuất được xây dựng vô cùng chặt chẽ:

### 1. Nguồn gốc của BoM (`source_id`)
* Khác với Odoo tiêu chuẩn (nơi BoM được người dùng tự gõ tay linh kiện vào bảng), trong OdooPLM, mỗi BoM mang một trường **`source_id`** trỏ thẳng đến bản ghi `ir.attachment` của file CAD Assembly gốc.
* *Ý nghĩa:* Đảm bảo tính toàn vẹn dữ liệu. Bất kỳ ai nhìn vào BoM đều biết chính xác: BoM này được bóc tách từ file bản vẽ nào, Revision nào.

### 2. Cây cấu trúc BoM đa tầng (`father_complete_ids`)
* OdooPLM tính toán cấu trúc cha - con của toàn bộ cây sản phẩm thông qua method `_father_compute`:
  * Cho phép người dùng đứng ở bất kỳ linh kiện con nào (Ví dụ: Trục S2) xem được ngay danh sách tất cả các cụm máy cha đang sử dụng nó (Tra cứu Where-Used).
* Báo cáo in ấn chuyên dụng: Module cung cấp sẵn các báo cáo **Exploded BoM Report** (Bóc tách chi tiết toàn bộ các tầng từ trên xuống dưới) và **Imploded BoM Report** (Tổng hợp gom nhóm vật tư phục vụ mua hàng).

### 3. Tương tác với Lệnh sản xuất (Manufacturing Orders - MO)
* Khi một linh kiện chuyển trạng thái sang `released`, BoM liên kết với nó trở thành BoM chính thức có hiệu lực.
* Trên form sản phẩm của OdooPLM có Smart Button `action_view_mos` cho phép kỹ sư R&D nhảy ngay sang xem danh sách các Lệnh sản xuất đang thực hiện của linh kiện đó để đánh giá mức độ ảnh hưởng trước khi bấm tạo Revision mới.

---

# PHẦN C — GÓC NHÌN DEVELOPER VỚI ODOOPLM SOURCE CODE

---

## CHAPTER 28 — ODOOPLM TECHNICAL ARCHITECTURE (KIẾN TRÚC MODULE `plm`)

Hãy cùng mổ xẻ mã nguồn thực tế của thư mục `c:\Work\odoo20-docker\addons\plm`:

### 1. Khai báo Manifest (`__manifest__.py`)
* **Tên module:** `plm`
* **Phiên bản:** `20.0.1.0.6`
* **Tác giả:** OmniaSolutions
* **Dependencies:** `["base", "board", "product", "mrp", "stock_account", "web_hierarchy"]`
  *(Lưu ý: Không hề phụ thuộc vào `mrp_plm` của Enterprise! Module chạy hoàn hảo trên nền tảng Odoo Community).*

### 2. Danh sách các Python Model Files quan trọng trong `addons/plm/models/`:

| Tên File | Các Model định nghĩa bên trong | Vai trò kiến trúc trong hệ thống |
|:---|:---|:---|
| **`plm_mixin.py`** | `revision.plm.mixin` | Abstract Model chứa toàn bộ logic quản trị Revision, Sequence chữ cái, State workflow, khóa ghi dữ liệu. |
| **`product_template.py`**| `product.template` | Kế thừa `revision.plm.mixin`, bổ sung các trường kỹ thuật và nút bấm tra cứu Revision. |
| **`product_product.py`** | `product.product` | Xử lý logic nhân bản Revision (`NewRevision`, `reviseCompAndDoc`), bóc tách BoM CAD, giao tiếp với CAD client. |
| **`ir_attachment.py`** | `ir.attachment` | Kế thừa `revision.plm.mixin`, biến attachment thành PLM Document (2D/3D, printout PDF, preview image). |
| **`plm_checkout.py`** | `plm.checkout` | Quản lý việc Check-out/Check-in tài liệu CAD, khóa file chống ghi đè đồng thời. |
| **`ir_attachment_relations.py`**| `ir.attachment.relations` | Lưu trữ cấu trúc cây lắp ráp cha-con giữa các file CAD 3D. |
| **`mrp_bom.py`** | `mrp.bom`, `mrp.bom.line` | Bổ sung `source_id`, `weight_net`, tính toán cây BoM cha `father_complete_ids`, đồng bộ Revision theo sản phẩm. |
| **`plm_material.py`** | `plm.material` | Danh mục mác vật liệu cơ khí (S45C, SUS304, CT3...). |
| **`plm_finishing.py`** | `plm.finishing` | Danh mục độ nhám và gia công bề mặt (Ra 0.8, Ra 1.6...). |
| **`plm_treatment.py`** | `plm.treatment` | Danh mục nhiệt luyện và xử lý bề mặt (Tôi cao tần, Mạ kẽm, Thấm cacbon...). |

---

## CHAPTER 29 — DATA MODEL RELATIONSHIP & ERD THỰC TẾ TRONG MODULE `plm`

Sơ đồ quan hệ thực thể (ERD) chính xác giữa các bảng dữ liệu của module `plm`:

```
                 ┌────────────────────────────────────────────────────────┐
                 │                 revision.plm.mixin                     │
                 │   (engineering_code, engineering_revision,             │
                 │    engineering_revision_letter, engineering_state)     │
                 └───────────┬────────────────────────────────┬───────────┘
                             │ Kế thừa trừu tượng             │ Kế thừa trừu tượng
                             ▼                                ▼
┌─────────────────────────────────────────┐      ┌─────────────────────────────────────────┐
│             product.product             │      │              ir.attachment              │
│            (Engineering Part)           │      │             (PLM Document)              │
│                                         │      │  • document_type: 2d / 3d               │
│  • material_id (plm.material)           │      │  • printout: PDF Content                │
│  • finishing_id (plm.finishing)         │      │  • preview: 3D Image                    │
│  • treatment_id (plm.treatment)         │      │  • is_plm: True                         │
└────────────────────┬────────────────────┘      └────────────┬───────────────┬────────────┘
                     │                                        │ 1             │
                     │ n                                    1 │               │
                     │         plm_component_document_rel     │               │
                     └───────────────────┬────────────────────┘               │
                                         │ Many2many                          │
                                         ▼                                    │
                     ┌────────────────────────────────────────┐               │
                     │          linkedcomponents              │               │
                     │   (Chi tiết gắn với file bản vẽ CAD)   │               │
                     └────────────────────────────────────────┘               │
                                                                              │
                                                                              │ 1
       ┌──────────────────────────────────────────────────────────┐           │
       │                         mrp.bom                          │           │
       │                   (Engineering BoM)                      │           │
       │                                                          │           │
       │ • source_id (Many2one ir.attachment) ────────────────────┼───────────┘
       │ • engineering_revision (related product_tmpl_id)         │ Trỏ về file CAD gốc
       │ • father_complete_ids (Hierarchy compute)                │
       └─────────────────────────┬────────────────────────────────┘
                                 │ 1
                                 │ n
       ┌─────────────────────────▼────────────────────────────────┐
       │                       mrp.bom.line                       │
       │  • product_id (Trỏ về product.product)                   │
       │  • product_qty (Số lượng chi tiết trong cụm)             │
       └──────────────────────────────────────────────────────────┘
```

---

## CHAPTER 30 — SOURCE CODE WALKTHROUGH (FLOW: TẠO REVISION MỚI VÀ KHÓA PHÁT HÀNH)

Hãy cùng truy vết 2 luồng xử lý mã nguồn quan trọng nhất trong OdooPLM:

### Luồng 1: Cơ chế Khóa Ghi Dữ Liệu Khi Đã Phát Hành (Hard Write Protection)
Mở file `addons/plm/models/plm_mixin.py`:

```python
# Trích xuất đoạn code kiểm soát ghi trong revision.plm.mixin:
PLM_NO_WRITE_STATE = [
    CONFIRMED_STATUS,   # 'confirmed'
    RELEASED_STATUS,    # 'released'
    UNDER_MODIFY_STATUS,# 'undermodify'
    OBSOLATED_STATUS,   # 'obsoleted'
]

def write(self, vals):
    # Nếu bản ghi không ở trạng thái 'draft', hệ thống kiểm tra quyền can thiệp
    for rec in self:
        if rec.engineering_state in PLM_NO_WRITE_STATE:
            # Danh sách các trường kỹ thuật cấm tuyệt đối không được sửa:
            forbidden_fields = ['engineering_code', 'engineering_revision', 'name', 'standard_price']
            for f in forbidden_fields:
                if f in vals and vals[f] != getattr(rec, f):
                    raise UserError(_(
                        "Bản ghi '%s' đang ở trạng thái '%s' (Đã khóa kỹ thuật)!\n"
                        "Bạn không thể sửa trực tiếp. Bắt buộc phải tạo Revision mới (New Revision)."
                    ) % (rec.display_name, rec.engineering_state))
    return super(RevisionBaseMixin, self).write(vals)
```

### Luồng 2: Cơ chế Nhân Bản Tạo Revision Mới (`_new_version`)
Khi người dùng bấm nút tạo Revision mới:

```python
# Trích xuất logic trong revision.plm.mixin:
def _new_version(self, extra_values=None):
    self.ensure_one()
    # 1. Kiểm tra: Tài liệu có đang bị Check-out không? Nếu có thì cấm nhân bản!
    self._refuse_revision_chain_if_checked_out()

    # 2. Chuẩn bị giá trị cho bản ghi Revision mới:
    vals = {
        'engineering_revision': self.engineering_revision + 1, # Tăng chỉ số: 0 -> 1 -> 2
        'engineering_revision_letter': self.get_revision_letter(self.engineering_revision + 1), # 'A' -> 'B'
        'engineering_state': START_STATUS, # Đưa về trạng thái 'draft' để kỹ sư sửa
        'engineering_revision_user': self.env.user.id,
        'engineering_revision_date': fields.Datetime.now(),
        'engineering_writable': True,
    }
    if extra_values:
        vals.update(extra_values)

    # 3. Chuyển trạng thái bản ghi hiện tại sang 'undermodify'
    self.write({'engineering_state': UNDER_MODIFY_STATUS})

    # 4. Thực hiện copy tạo bản ghi mới (ORM copy)
    new_record = self.copy(default=vals)

    # 5. Thiết lập liên kết lịch sử giữa bản cũ và bản mới
    return new_record
```

---

## CHAPTER 31 — ODOO DEVELOPMENT PATTERNS CHO MODULE `plm`

Khi bạn phát triển các tính năng mở rộng cho module `plm`, bạn phải tuân thủ các pattern thiết kế sau:

### Pattern 1: Kế thừa bổ sung trường thuộc tính vào Linh kiện kỹ thuật
* **Requirement:** Thêm trường `hardness` (Độ cứng nhiệt luyện sau gia công, ví dụ: "50-55 HRC") vào sản phẩm.
* **Quy tắc:** Dùng `_inherit = 'product.template'` hoặc `product.product`.
* **Code triển khai:**
```python
# custom_plm/models/product_product.py
from odoo import models, fields

class ProductProduct(models.Model):
    _inherit = 'product.product'

    hardness = fields.Char(
        string="Độ Cứng Nhiệt Luyện",
        help="Độ cứng theo thang đo Rockwell C (HRC) hoặc Brinell (HB) sau khi nhiệt luyện.",
        tracking=True
    )
```

### Pattern 2: Bổ sung hành động kiểm tra khi Phê duyệt Phát hành (`action_release`)
* **Requirement:** Chặn không cho Release linh kiện nếu chưa nhập mác vật liệu (`material_id`).
* **Quy tắc:** Override method `action_from_confirmed_to_released` hoặc `action_release` trong `product.product`.
* **Code triển khai:**
```python
# custom_plm/models/product_product.py
from odoo import models, _
from odoo.exceptions import ValidationError

class ProductProduct(models.Model):
    _inherit = 'product.product'

    def action_release(self):
        for rec in self:
            if not rec.material_id:
                raise ValidationError(_(
                    "KHÔNG THỂ PHÁT HÀNH CHI TIẾT '%s':\n"
                    "Bắt buộc phải chỉ định Mác Vật Liệu (Material) trước khi ký duyệt phát hành!"
                ) % rec.display_name)
        return super(ProductProduct, self).action_release()
```

---

## CHAPTER 32 — TỪ BUSINESS REQUIREMENT ĐẾN TECHNICAL DESIGN (10 CASE THỰC TẾ VỚI ODOOPLM)

Dưới đây là 10 tình huống thiết kế kỹ thuật thực chiến trên nền tảng module `plm`:

### Case 1: Bắt buộc phải có file PDF Printout trước khi Release linh kiện
* **Business:** Bản vẽ xuất xưởng cho công nhân phải có sẵn file PDF. Không được release nếu chưa có file PDF đính kèm.
* **Technical Design:**
  * Model: `product.product`
  * Method: `action_release`
  * Logic: Kiểm tra `rec.linkeddocuments`. Quét xem có document nào có `document_type == '2d'` và trường `printout` không rỗng không. Nếu không có thì raise `ValidationError`.

### Case 2: Tự động khóa bản ghi file CAD khi chi tiết chuyển sang Released
* **Business:** Khi kỹ sư trưởng bấm duyệt linh kiện, toàn bộ file CAD đính kèm liên quan phải tự động chuyển sang `released` để đồng bộ.
* **Technical Design:**
  * Model: `product.product`, override `action_release`:
    ```python
    for doc in self.linkeddocuments:
        if doc.engineering_state != 'released':
            doc.action_release()
    ```

### Case 3: Chặn xóa chi tiết nếu đang nằm trong một BoM đã Released
* **Business:** Ngăn chặn việc vô tình xóa mất chi tiết con khi máy tổng đã đi vào sản xuất thương mại.
* **Technical Design:**
  * Model: `product.product`, override method `unlink()`:
    ```python
    def unlink(self):
        for rec in self:
            boms = self.env['mrp.bom.line'].search([
                ('product_id', '=', rec.id),
                ('bom_id.engineering_state', '=', 'released')
            ])
            if boms:
                raise UserError(_("Không thể xóa chi tiết '%s' vì đang nằm trong BoM đã phát hành!") % rec.name)
        return super().unlink()
    ```

### Case 4: Cảnh báo khi tạo Revision mới mà kho vẫn còn tồn linh kiện cũ
* **Business:** Nhắc nhở kỹ sư biết số lượng tồn kho của bản vẽ cũ trước khi quyết định thay đổi hình học.
* **Technical Design:**
  * Kế thừa hàm `NewRevision()`, lấy `self.qty_available`. Nếu > 0, bắn một notification popup (dạng `display_notification` warning) nhắc nhở kỹ sư.

### Case 5: Đồng bộ khối lượng tịnh (`weight_net`) từ mô hình 3D CAD vào BoM
* **Business:** Kỹ sư thiết kế trong CAD tính được chính xác trọng lượng khối kim loại. BoM phải tự cập nhật trọng lượng này để tính chi phí vận chuyển.
* **Technical Design:**
  * Khi client lưu CAD Assembly lên Odoo, gọi method cập nhật trường `weight_net` trên `mrp.bom` bằng tổng `weight` của các chi tiết con.

### Case 6: Kiểm tra quyền phê duyệt theo Nhóm người dùng chuyên biệt
* **Business:** Chỉ có Trưởng phòng R&D mới có quyền bấm nút "Release Component".
* **Technical Design:**
  * Trong `views/product_product.xml`, gán thuộc tính: `groups="plm.group_plm_release_users"` cho button `action_release`.

### Case 7: Tự động đánh dấu `obsoleted` cho Revision cũ khi Revision mới Released
* **Business:** Tránh việc hai bản vẽ cùng hiển thị là đang có hiệu lực.
* **Technical Design:**
  * Khi bản Revision B được bấm `action_release`, tìm bản Revision A trước đó (qua `engineering_code` và `engineering_revision == B - 1`), tự động gọi method `action_from_undermodify_to_obsoleted()`.

### Case 8: Quản lý nhà sản xuất chế tạo phôi (Manufacturer Part Number - MPN)
* **Business:** Quản lý mã vòng bi của hãng NSK, SKF tương ứng với mã chi tiết nội bộ.
* **Technical Design:**
  * Bổ sung bảng quan hệ hoặc trường `mpn_code`, `manufacturer_id` vào `product.product`.

### Case 9: Tích hợp mã màu kiểm tra trạng thái trên Kanban
* **Business:** Trên màn hình Kanban chi tiết linh kiện: Màu xanh = Released, Màu vàng = Draft, Màu đỏ = Obsoleted.
* **Technical Design:**
  * Trong file XML view `product_product_kanban.xml`, sử dụng attribute `color` kết hợp với trường `engineering_state`.

### Case 10: Tự động gửi email thông báo khi linh kiện hoàn thành phát hành
* **Business:** Bắn thông báo cho phòng Mua hàng và Xưởng khi có chi tiết mới Released.
* **Technical Design:**
  * Trong hàm `action_release`, gọi `self.message_post(body=..., partner_ids=...)` gửi qua hệ thống Mail Thread của Odoo.

---

## CHAPTER 33 — 15 CA CUSTOMIZATION THƯỜNG GẶP TRÊN NỀN TẢNG ODOOPLM

| STT | Yêu cầu nghiệp vụ | Standard OdooPLM (`addons/plm`) | Giải pháp Technical của Developer |
|:---|:---|:---|:---|
| **1** | Thêm trường "Lý do sửa đổi" (Design Change Reason) | Đã có sẵn trường `desc_modify` trên Attachment | Mở rộng thêm trường `change_reason_id` trên `product.product`. |
| **2** | Thêm danh mục Tiêu chuẩn áp dụng (ISO, DIN, JIS) | Chưa có | Tạo model mới `plm.standard`, gắn Many2one vào `product.product`. |
| **3** | Bắt buộc phải Check-in file CAD trước khi Confirm linh kiện | Có sẵn logic kiểm tra | Kiểm tra `is_checkout == False` trong hàm `action_confirm`. |
| **4** | Phân quyền chỉ cho phép nhóm Admin tạo Revision nhánh (`new_branch`) | Logic có sẵn trong mixin | Phân quyền button `new_branch` cho nhóm `plm.group_plm_admin`. |
| **5** | Đính kèm file mô phỏng ứng suất CAE/FEA (.STEP, .IGES) | Hỗ trợ qua `ir.attachment` | Cấu hình thêm định dạng trong Selection `document_type`. |
| **6** | Tự động tính toán tổng diện tích bề mặt để tính lượng sơn mạ | Chưa có | Bổ sung trường `surface_area`, nhân định mức sơn trong BoM. |
| **7** | Tự động sinh mã `engineering_code` theo quy tắc Sequence doanh nghiệp | Có sẵn cơ chế normalize | Kế thừa hàm `create()`, gọi `self.env['ir.sequence'].next_by_code()`. |
| **8** | Chặn xóa file bản vẽ PDF nếu linh kiện đã ở trạng thái Released | Có sẵn `PLM_NO_WRITE_STATE` | Mixin tự động chặn xóa bản ghi khi không phải Draft. |
| **9** | Hiển thị bảng so sánh hai phiên bản BoM (Diff Report) | Có wizard báo cáo BoM | Xây dựng wizard so sánh 2 record `mrp.bom` của Rev A và Rev B. |
| **10** | Quản lý phụ tùng thay thế thương mại (Spare Parts BoM) | Có sẵn model `plm.spare.bom` | Cấu hình cây phụ tùng trong menu Component Relations. |
| **11** | Tự động đóng dấu Watermark "RELEASED" lên file PDF bản vẽ | Chưa có | Viết hàm xử lý binary PDF bằng thư viện `pypdf` khi bấm release. |
| **12** | Xuất danh mục vật tư ra file Excel theo mẫu chuẩn của nhà máy | Có báo cáo PDF chuẩn | Viết action xuất file Excel qua thư viện `xlsxwriter`. |
| **13** | Quản lý tuổi thọ và số chu kỳ hoạt động của chi tiết hao mòn | Chưa có | Thêm trường `lifecycle_cycles`, tích hợp với module `maintenance`. |
| **14** | Tích hợp Webhook bắn thông báo sang Microsoft Teams / Telegram | Chưa có | Kế thừa `action_release`, gọi thư viện `requests.post()` tới Webhook URL. |
| **15** | Tự động cập nhật BoM mới vào các Lệnh sản xuất MO đang ở trạng thái Draft | Chưa có | Trong `action_release`, tìm các MO Draft và cập nhật lại `bom_id`. |

---

## CHAPTER 34 — DEBUGGING: TỪ CLIENT/API ĐẾN POSTGRESQL CHECKLIST

Khi làm việc với OdooPLM, bạn sẽ thường xuyên xử lý các lỗi liên quan đến Check-out locks và ràng buộc Unique Index. Hãy làm theo checklist 8 bước sau:

1. **Lỗi `This Engineering Code and Revision combination already exists`:**
   * *Nguyên nhân:* Do ràng buộc `@api.constrains('engineering_code', 'engineering_revision')` hoặc Unique Index trong PostgreSQL.
   * *Cách xử lý:* Kiểm tra xem có bản ghi nào bị lưu trữ (Archive / `active=False`) nhưng vẫn đang chiếm giữ cặp mã và revision đó không.
2. **Lỗi `Cannot modify a record in non-draft state`:**
   * *Nguyên nhân:* Code của bạn đang cố gọi `.write()` lên một linh kiện hoặc attachment đang mang trạng thái `confirmed` hoặc `released`.
   * *Cách xử lý:* Kiểm tra xem nghiệp vụ đó có đòi hỏi tạo Revision mới trước khi sửa hay không.
3. **Lỗi File bị kẹt Check-out (`Document is checked out`):**
   * *Nguyên nhân:* Kỹ sư tắt máy tính đột ngột khi CAD chưa kịp gửi gói Check-in trả về.
   * *Cách xử lý:* Đăng nhập bằng tài khoản Quản trị viên PLM (`plm.group_plm_admin`), vào menu **Documents -> Search on Checked-Out Documents**, bấm nút ép mở khóa (Force Check-in).
4. **Lỗi API Client từ SolidWorks/Inventor không kết nối được:**
   * *Cách xử lý:* Kiểm tra log server Odoo. Xem URL XML-RPC/JSON-RPC có bị chặn bởi Reverse Proxy Nginx không (chú ý cấu hình `client_max_body_size 500M` để tải file CAD nặng).

---

## CHAPTER 35 — TESTING STRATEGY & TEST CASES CHO MODULE `plm`

File kiểm thử tự động mẫu viết cho OdooPLM (`tests/test_plm_lifecycle.py`):

```python
from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError, ValidationError

class TestPlmLifecycle(TransactionCase):

    def setUp(self):
        super(TestPlmLifecycle, self).setUp()
        self.plm_release_group = self.env.ref('plm.group_plm_release_users')
        self.env.user.groups_id |= self.plm_release_group

        # 1. Khởi tạo linh kiện kỹ thuật ban đầu (Trục S1)
        self.component_shaft = self.env['product.product'].create({
            'name': 'Trục Truyền Động P100',
            'engineering_code': 'P100-SHAFT-TEST',
            'engineering_revision': 0,
            'engineering_revision_letter': 'A',
            'engineering_state': 'draft',
        })

    def test_01_lifecycle_workflow_success(self):
        """Test luồng duyệt linh kiện: Draft -> Confirmed -> Released"""
        # Bước 1: Confirm chi tiết
        self.component_shaft.action_confirm()
        self.assertEqual(self.component_shaft.engineering_state, 'confirmed')

        # Bước 2: Release chi tiết
        self.component_shaft.action_release()
        self.assertEqual(self.component_shaft.engineering_state, 'released')
        self.assertTrue(self.component_shaft.engineering_release_date)

        # Bước 3: Kiểm tra cơ chế khóa ghi (Cấm sửa khi đã Released)
        with self.assertRaises(UserError):
            self.component_shaft.write({'name': 'Tên mới sửa trộm'})

    def test_02_new_revision_creation(self):
        """Test cơ chế tạo Revision mới từ bản ghi đã phát hành"""
        self.component_shaft.action_confirm()
        self.component_shaft.action_release()

        # Tạo Revision mới (Rev B)
        new_rev = self.component_shaft._new_version()

        self.assertEqual(new_rev.engineering_code, 'P100-SHAFT-TEST')
        self.assertEqual(new_rev.engineering_revision, 1)
        self.assertEqual(new_rev.engineering_revision_letter, 'B')
        self.assertEqual(new_rev.engineering_state, 'draft')
        self.assertEqual(self.component_shaft.engineering_state, 'undermodify')
```

---

## CHAPTER 36 — LỘ TRÌNH HỌC TẬP (ROADMAP TỪ LEVEL 1 ĐẾN 10)

```
[ LEVEL 1: NỀN TẢNG SẢN XUẤT CƠ KHÍ ] ──> Hiểu phôi thép, tiện, phay, dung sai, hàn kết cấu.
                 │
                 ▼
[ LEVEL 2: NỀN TẢNG 3D CAD ]          ──> Biết mở file Part, Assembly, xuất bản vẽ 2D PDF trên CAD.
                 │
                 ▼
[ LEVEL 3: LÀM CHỦ BẢN CHẤT BOM ]     ──> Phân biệt thuần thục EBOM thiết kế và MBOM sản xuất.
                 │
                 ▼
[ LEVEL 4: BẢN CHẤT PDM ]              ──> Nắm vững Check-in/Check-out, kiểm soát xung đột ghi đè file.
                 │
                 ▼
[ LEVEL 5: VÒNG ĐỜI KỸ THUẬT ]        ──> Hiểu 5 trạng thái: Draft -> Confirmed -> Released -> Obsoleted.
                 │
                 ▼
[ LEVEL 6: ODOOPLM FUNCTIONAL ]       ──> Cài đặt module plm, thao tác quản lý Component, Document, BoM.
                 │
                 ▼
[ LEVEL 7: ODOOPLM TECHNICAL CORE ]   ──> Đọc hiểu sâu `plm_mixin.py`, `ir_attachment.py`, `product_product.py`.
                 │
                 ▼
[ LEVEL 8: KỸ NĂNG CUSTOMIZATION ]    ──> Kế thừa module plm, viết validation rules, thêm thuộc tính kỹ thuật.
                 │
                 ▼
[ LEVEL 9: QUẢN TRỊ BOM & MRP ]        ──> Tự động đồng bộ BoM từ bản vẽ CAD sang Lệnh sản xuất MO.
                 │
                 ▼
[ LEVEL 10: TÍCH HỢP CAD CLIENT ]     ──> Nắm vững giao thức API JSON-RPC kết nối SolidWorks/Inventor với Odoo.
```

---

## CHAPTER 37 — NHỮNG KIẾN THỨC DEVELOPER THƯỜNG THIẾU NHƯNG RẤT QUAN TRỌNG

1. **Hiểu bản chất của Ký tự Revision (Letter Index):** Nhiều bạn viết code tăng revision bằng cách cộng chuỗi `chr(ord(letter) + 1)`. Cách này sẽ bị crash khi revision vượt quá chữ 'Z' (phải nhảy sang 'AA', 'AB'...). Hãy luôn dùng hàm chuẩn `convert_to_letter` có sẵn trong `plm_mixin.py`.
2. **Quy tắc FFF (Form - Fit - Function):** Nếu kích thước lắp ghép thay đổi (như trục to lên không vừa gối đỡ cũ), bạn bắt buộc phải tạo mã `engineering_code` mới hoàn toàn, không được phép dùng chung mã cũ để tăng Revision!
3. **Cẩn trọng với Database Constraint:** Bảng `product_template` và `ir_attachment` trong OdooPLM có Unique Index đánh trên cặp `(engineering_code, engineering_revision)`. Bất kỳ script import dữ liệu Excel nào tạo trùng cặp giá trị này sẽ làm sập Database Transaction ngay lập tức.

---

# FINAL ASSIGNMENT & ĐÁP ÁN MẪU

---

## ĐỀ BÀI (BUSINESS REQUIREMENT TỪ NHÀ MÁY TÂN HƯNG)

**Khách hàng:** Công ty Cổ phần Chế tạo Cơ khí Chính xác Tân Hưng (Bình Dương).  
**Hệ thống:** Odoo 20 cài đặt module mã nguồn mở **`plm` (OmniaSolutions OdooPLM)**.  
**Yêu cầu chuyển giao:** Phát triển một module custom mở rộng đặt tên là **`tanhung_plm_custom`** (phụ thuộc vào module `plm` và `mrp`) giải quyết 3 yêu cầu khắt khe sau:
1. **Kiểm soát An toàn Phát hành Bản vẽ:**
   * Khi người dùng bấm nút "Release Component" (`action_release`): Hệ thống bắt buộc phải kiểm tra xem chi tiết đó đã có ít nhất một tài liệu đính kèm (`linkeddocuments`) thuộc loại bản vẽ 2D (`document_type == '2d'`) và đã có nội dung file PDF (`printout` không rỗng) hay chưa. Nếu thiếu, chặn lại và hiển thị thông báo lỗi.
2. **Cảnh báo Tài chính khi tạo Revision mới:**
   * Bổ sung trường `scrap_cost` (Chi phí ước tính thiệt hại phôi cũ) vào linh kiện.
   * Nếu `scrap_cost > 20.000.000 VNĐ`, bắt buộc người dùng thuộc nhóm Quản đốc Nhà máy (`mrp.group_mrp_manager`) xác nhận thì mới cho phép tạo Revision mới.
3. **Tự động Cập nhật BoM vào Lệnh Sản Xuất:**
   * Khi một linh kiện BoM tổng được bấm Release thành công: Tự động quét toàn bộ các Lệnh sản xuất (`mrp.production`) đang ở trạng thái `draft` của sản phẩm đó để gán lại BoM mới phát hành.

---

## ĐÁP ÁN MẪU TỪ SENIOR ODOO DEVELOPER

### Cấu trúc Module Custom:
```
custom_addons/tanhung_plm_custom/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   └── product_product.py
└── views/
    └── product_product_views.xml
```

#### 1. File `__manifest__.py`:
```python
{
    'name': 'Tan Hung PLM Customization (OdooPLM Extension)',
    'version': '20.0.1.0.0',
    'summary': 'Mở rộng quy trình quản lý vòng đời và kiểm soát phát hành cho OdooPLM',
    'author': 'Senior Odoo Consultant',
    'category': 'Manufacturing/PLM',
    'depends': ['plm', 'mrp'],
    'data': [
        'views/product_product_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
```

#### 2. File `models/product_product.py`:
```python
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

class ProductProduct(models.Model):
    _inherit = 'product.product'

    scrap_cost = fields.Monetary(
        string="Chi Phí Thiệt Hại Phôi Cũ Dự Kiến",
        currency_field='currency_id',
        tracking=True,
        help="Tổng thiệt hại tài chính do loại bỏ phôi cũ khi nâng Revision chi tiết này."
    )

    def action_release(self):
        """Override method phê duyệt phát hành chi tiết kỹ thuật."""
        for rec in self:
            # 1. Ràng buộc an toàn: Bắt buộc phải có bản vẽ 2D kèm file PDF Printout
            has_valid_pdf_drawing = False
            for doc in rec.linkeddocuments:
                if doc.document_type == '2d' and doc.printout:
                    has_valid_pdf_drawing = True
                    break

            if not has_valid_pdf_drawing:
                raise ValidationError(_(
                    "VI PHẠM QUY TRÌNH KỸ THUẬT NHÀ MÁY:\n"
                    "Linh kiện '%s' (Mã: %s - Rev %s) không thể Phát Hành (Release) "
                    "vì chưa đính kèm bản vẽ 2D có tệp tin PDF xuất xưởng (Printout Content)!\n"
                    "Vui lòng kiểm tra lại tài liệu đính kèm trước khi ký duyệt."
                ) % (rec.name, rec.engineering_code, rec.engineering_revision_letter))

        # Thực thi logic release chuẩn của OdooPLM (chuyển state sang 'released')
        res = super(ProductProduct, self).action_release()

        # 2. Tự động quét và cập nhật BoM mới cho các Lệnh sản xuất đang ở trạng thái Nháp (Draft MO)
        for rec in self:
            # Tìm BoM mới nhất của sản phẩm này đang ở trạng thái released
            latest_bom = self.env['mrp.bom'].search([
                ('product_tmpl_id', '=', rec.product_tmpl_id.id),
                ('engineering_state', '=', 'released')
            ], limit=1, order='create_date desc')

            if latest_bom:
                draft_mos = self.env['mrp.production'].search([
                    ('product_id', '=', rec.id),
                    ('state', '=', 'draft')
                ])
                if draft_mos:
                    draft_mos.write({'bom_id': latest_bom.id})
                    rec.message_post(body=_(
                        "Hệ thống đã tự động đồng bộ BoM phát hành mới nhất vào %s Lệnh sản xuất đang ở trạng thái Nháp."
                    ) % len(draft_mos))

        return res

    def NewRevision(self):
        """Override method tạo Revision mới với ràng buộc chi phí phế phẩm cao."""
        for rec in self:
            if rec.scrap_cost > 20000000:
                # Kiểm tra quyền: Bắt buộc người thực hiện phải thuộc nhóm Quản đốc Nhà máy
                if not self.env.user.has_group('mrp.group_mrp_manager'):
                    raise UserError(_(
                        "CẢNH BÁO TÀI CHÍNH:\n"
                        "Chi phí thiệt hại phôi cũ dự kiến là %s %s (vượt mức cho phép 20 triệu VNĐ).\n"
                        "Chỉ có Quản đốc Nhà máy (Manufacturing Manager) mới có thẩm quyền kích hoạt tạo Revision mới!"
                    ) % (rec.scrap_cost, rec.currency_id.symbol))

        return super(ProductProduct, self).NewRevision()
```

#### 3. File `views/product_product_views.xml`:
```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <record id="view_product_product_form_inherit_tanhung" model="ir.ui.view">
        <field name="name">product.product.form.inherit.tanhung</field>
        <field name="model">product.product</field>
        <field name="inherit_id" ref="plm.view_product_client_workflow"/>
        <field name="arch" type="xml">
            <!-- Thêm trường chi phí thiệt hại phôi cũ vào form linh kiện kỹ thuật -->
            <xpath expr="//header" position="after">
                <div class="alert alert-warning text-center" 
                     role="alert" 
                     invisible="scrap_cost &lt;= 20000000 or engineering_state == 'released'">
                    <strong>Cảnh báo tài chính:</strong> Chi phí hủy phôi cũ vượt mức 20 triệu VNĐ. Yêu cầu Quản đốc phê duyệt!
                </div>
            </xpath>
            <xpath expr="//field[@name='engineering_state']" position="before">
                <field name="currency_id" invisible="1"/>
                <field name="scrap_cost" widget="monetary" readonly="engineering_state != 'draft'"/>
            </xpath>
        </field>
    </record>
</odoo>
```

---

# LỜI KẾT
Tài liệu này đã trang bị cho bạn tư duy và kiến thức thực chiến chính xác nhất về **Product Lifecycle Management (PLM)** gắn liền với kiến trúc mã nguồn mở **OdooPLM (Module `plm`)**. Bạn hoàn toàn làm chủ được cả hai thế giới: hiểu sâu sắc nhu cầu cơ khí của kỹ sư thiết kế CAD tại nhà máy và biến chúng thành các giải pháp kỹ thuật thanh lịch, an toàn và tối ưu trong Odoo ORM.
