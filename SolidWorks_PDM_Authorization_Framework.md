# BÁO CÁO KIẾN TRÚC & THIẾT KẾ PHÂN QUYỀN PDM THỰC THI (TAILORED PDM FRAMEWORK)
# HỆ THỐNG ACCESS TOKEN 180 NGÀY, CƠ CHẾ PHÂN QUYỀN 5 LỚP & TRANH CHẤP CHECK-IN CHO SOLIDWORKS 2022

> **Đơn vị tư vấn:** Principal PDM Consultant & Solution Architect  
> **Khách hàng / Doanh nghiệp:** Nhà máy Chế tạo Cơ khí / Mạng nội bộ LAN  
> **Hệ thống mục tiêu:** Odoo 20 (PostgreSQL `odoo20`) | OmniaSolutions OdooPLM | SolidWorks 2022 Desktop Add-in  
> **Trạng thái:** HOÀN THIỆN ĐẦY ĐỦ TOÀN BỘ SƠ ĐỒ AUTHORIZATION FLOW, TOKEN & MERMAID SPECIFICATION

---

## MỤC 1: TỔNG HỢP CẤU HÌNH DOANH NGHIỆP ĐÃ XÁC LẬP

Dựa trên yêu cầu vận hành thực tế tại doanh nghiệp, hệ thống được thiết lập theo bộ tham số cốt lõi sau:

| Mã quyết định | Hạng mục cấu hình | Phương án xác lập | Mô tả chi tiết hành vi hệ thống |
| :--- | :--- | :--- | :--- |
| **Q1.1** | **Thời hạn Token** | **Option A (Fixed 180 Days)** | Đúng 180 ngày kể từ lúc Login, token hết hạn cứng và bắt buộc đăng nhập lại. Không sử dụng hạn trượt (No Rolling Expiry). |
| **Q1.2** | **Ràng buộc Thiết bị** | **Multi-device Concurrent (Không Kick-out)** | Một kỹ sư được phép đăng nhập trên nhiều máy tính cùng lúc (Workstation, Laptop). Session trên các máy tính độc lập, không bị đăng xuất khi máy khác login. |
| **Q2.1** | **Tranh chấp Check-out & Chống ghi đè** | **FIFO Priority + Lock Handover + Anti-Overwrite** | - **Ưu tiên Check-out trước:** Kỹ sư nào Check-out trước sẽ nắm quyền ưu tiên Check-in (`Primary Lock Holder`).<br>- **Chuyển giao quyền:** Kỹ sư giữ quyền có thể chủ động bàn giao quyền Check-in cho kỹ sư đến sau.<br>- **Chống ghi đè:** Nếu 2 kỹ sư cùng tải về sửa, khi người thứ nhất Check-in bản mới lên Odoo, hệ thống **chặn đứng** người thứ hai Check-in, ép buộc phải tải bản vẽ mới nhất về máy để cập nhật, tuyệt đối không ghi đè. |
| **Q3** | **Quy trình Duyệt & Revision** | **Option B + C (2 Cấp + Đóng băng Rev A)** | - Kỹ sư vẽ nộp duyệt ➔ Trưởng nhóm (Lead/Checker) thẩm định và bấm **Released**.<br>- **Đóng băng Rev A:** Bản vẽ Rev A sau khi Released là bất biến (Read-only lịch sử).<br>- Muốn chỉnh sửa tiếp bắt buộc phải bấm **New Revision** để sinh ra **Rev B** độc lập. |
| **Q4.1** | **Môi trường Vận hành** | **LAN Intranet Only (Real-time ACID)** | Vận hành 100% trong mạng nội bộ công ty. Mọi thao tác CAD Add-in đều xác thực và đối chiếu thời gian thực (Real-time) qua Odoo Backend, loại bỏ rủi ro offline. |

---

## MỤC 2: QUY TRÌNH PHÂN QUYỀN TOÀN DIỆN (5-LAYER PDM AUTHORIZATION ENGINE)

Hệ thống phân quyền được xây dựng theo mô hình **Đánh giá Thẩm quyền 5 Lớp (5-Layer Authorization Filter)**. Bất kỳ thao tác nào từ SolidWorks (Check-out, Check-in, Submit Review, Release, New Revision, Delete) đều phải đi qua bộ lọc logic nghiêm ngặt này trước khi chạm vào cơ sở dữ liệu:

### 1. Sơ đồ Cây Phán Quyết Phân Quyền (Authorization Flowchart)

```mermaid
flowchart TD
    START(["Kỹ sư kích hoạt Action trên SolidWorks<br>(Checkout / Checkin / Release / Revise / Save)"]) --> L1{"LỚP 1: TOKEN VALIDITY<br>Token còn hạn trong 180 ngày<br>& không bị thu hồi?"}
    
    L1 -- "Hết hạn / Không hợp lệ" --> ERR_401["401 UNAUTHORIZED<br>Hiển thị Dialog bắt buộc Login lại"]
    L1 -- "Hợp lệ" --> L2{"LỚP 2: RBAC PERMISSIONS<br>Vai trò của User có được phép<br>thực hiện Action này?"}
    
    L2 -- "Vi phạm Role (VD: Kỹ sư bấm Release)" --> ERR_403_ROLE["403 FORBIDDEN: INSUFFICIENT_ROLE<br>Chặn: 'Quyền duyệt bản vẽ chỉ thuộc về Lead/Checker'"]
    L2 -- "Đúng vai trò" --> L3{"LỚP 3: LIFECYCLE STATE<br>Trạng thái bản vẽ hiện tại là gì?"}
    
    L3 -- "Trạng thái: Released (Đã đóng băng)" --> CHK_REL{"Action yêu cầu là gì?"}
    CHK_REL -- "New Revision (Tạo Rev B)" --> ALLOW_REV["CHO PHÉP TÁCH NHÁNH REV B<br>Nhân bản bản ghi, giữ nguyên gốc Rev A"]
    CHK_REL -- "Sửa / Checkin đè" --> ERR_FROZEN["403 FORBIDDEN: REVISION_FROZEN<br>Chặn: 'Rev A đã phát hành và bị đóng băng vĩnh viễn'"]
    
    L3 -- "Trạng thái: Under Review" --> CHK_REV{"User có phải Checker/Lead?"}
    CHK_REV -- "Không (Là Designer)" --> ERR_REVIEW["403 FORBIDDEN: UNDER_REVIEW_LOCKED<br>Chặn: 'Bản vẽ đang chờ duyệt, tạm khóa chỉnh sửa'"]
    CHK_REV -- "Đúng là Lead" --> ALLOW_LEAD["CHO PHÉP LEAD: Phê duyệt (Release) hoặc Từ chối"]
    
    L3 -- "Trạng thái: Draft" --> L4{"LỚP 4: LOCK OWNERSHIP (FIFO)<br>Action là gì?"}
    
    L4 -- "Action: Check-out" --> EVAL_CKO["Đánh giá thứ tự đến:<br>- Đến đầu ➔ Cấp quyền Primary Lock<br>- Đến sau ➔ Cấp quyền Secondary Editor"]
    L4 -- "Action: Check-in" --> CHK_OWNER{"User có phải Primary Lock Holder<br>(Hoặc đã nhận Handover)?"}
    
    CHK_OWNER -- "Không phải người giữ quyền" --> ERR_NOT_PRIMARY["403 FORBIDDEN: NOT_PRIMARY_HOLDER<br>Chặn: 'Kỹ sư A đang giữ quyền Check-in chính'"]
    CHK_OWNER -- "Đúng người giữ quyền" --> L5{"LỚP 5: ANTI-OVERWRITE GUARD<br>Base Version Client == Server Version hiện tại?"}
    
    L5 -- "Khác nhau (Server đã có Ver mới)" --> ERR_409["409 CONFLICT: STALE_VERSION_OVERWRITE<br>Chặn: 'Server đã có phiên bản mới hơn. Bắt buộc tải về!'"]
    L5 -- "Khớp 100%" --> ALLOW_EXEC["200 OK: ACTION_AUTHORIZED<br>Thực thi ghi file & Nâng version bản vẽ"]

    classDef startNode fill:#e3f2fd,stroke:#1565c0,stroke-width:2px;
    classDef checkNode fill:#fff9c4,stroke:#fbc02d,stroke-width:2px;
    classDef errNode fill:#ffebee,stroke:#c62828,stroke-width:2px;
    classDef okNode fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px;

    class START startNode;
    class L1,L2,L3,L4,L5,CHK_REL,CHK_REV,CHK_OWNER checkNode;
    class ERR_401,ERR_403_ROLE,ERR_FROZEN,ERR_REVIEW,ERR_NOT_PRIMARY,ERR_409 errNode;
    class ALLOW_REV,ALLOW_LEAD,EVAL_CKO,ALLOW_EXEC okNode;
```

---

### 2. Sơ đồ Tuần tự Luồng Thẩm Quyền Thời Gian Thực (Authorization Flow Sequence)
Sơ đồ thể hiện cách SolidWorks Desktop Add-in gửi yêu cầu xác thực thẩm quyền trước mỗi hành vi:

```mermaid
sequenceDiagram
    autonumber
    actor User as Kỹ sư / Lead
    participant SW as SolidWorks Ribbon / Taskpane
    participant Gatekeeper as Odoo Authorization Gatekeeper
    participant TokenService as plm.desktop.token
    participant LockService as plm.checkout.lock
    participant StateService as ir.attachment (PLM Document)

    User->>SW: Nhấp chuột vào nút "Check-in Bản vẽ"
    SW->>SW: Đọc Local Token (Cache 180 ngày) & Local Hash
    SW->>Gatekeeper: POST /api/desktop/pdm/check_action<br>{Token, action='checkin', file_id=501, base_ver=1}

    Note over Gatekeeper, TokenService: LỚP 1: KIỂM TRA ACCESS TOKEN
    Gatekeeper->>TokenService: verify_token(Token)
    TokenService-->>Gatekeeper: Token Valid (User: Kỹ sư Nam, ID: 12)

    Note over Gatekeeper, StateService: LỚP 2 & 3: KIỂM TRA ROLE & TRẠNG THÁI BẢN VẼ
    Gatekeeper->>StateService: get_document_state(file_id=501)
    StateService-->>Gatekeeper: State: 'draft', Group: 'group_plm_designer'
    Gatekeeper->>Gatekeeper: Validate: State là Draft và User có quyền Designer (Hợp lệ)

    Note over Gatekeeper, LockService: LỚP 4: KIỂM TRA QUYỀN SỞ HỮU KHÓA (FIFO)
    Gatekeeper->>LockService: check_lock_ownership(file_id=501, user_id=12)
    alt Không phải người giữ quyền Check-in
        LockService-->>Gatekeeper: False (Primary Holder là Kỹ sư Hùng)
        Gatekeeper-->>SW: 403 Forbidden (NOT_PRIMARY_HOLDER)
        SW-->>User: Hiện thông báo: "Kỹ sư Hùng đang giữ quyền Check-in!"
    else Đúng là người giữ quyền Check-in (hoặc được Handover)
        LockService-->>Gatekeeper: True (Primary Lock Holder Valid)

        Note over Gatekeeper, StateService: LỚP 5: BẢO VỆ CHỐNG GHI ĐÈ PHIÊN BẢN (ANTI-OVERWRITE)
        Gatekeeper->>StateService: compare_version(file_id=501, client_base_ver=1)
        alt Server đã lên Version 2
            StateService-->>Gatekeeper: Conflict (Current Server Version = 2)
            Gatekeeper-->>SW: 409 Conflict (STALE_VERSION_OVERWRITE_PREVENTED)
            SW-->>User: Chặn ghi đè: "Bản vẽ đã có Ver 2 trên server. Tải bản mới về!"
        else Phiên bản hoàn toàn khớp
            StateService-->>Gatekeeper: Version Match (Current Server Version = 1)
            Gatekeeper-->>SW: 200 OK (ACTION_AUTHORIZED)
            SW->>Gatekeeper: Tiến hành truyền dữ liệu file CAD lên Odoo!
        end
    end
```

---

### 3. Ma Trận Quyền Hạn Theo Vai Trò & Vòng Đời (RBAC & State Permission Matrix)

| Thao tác trên SolidWorks | Trạng thái Bản vẽ: DRAFT | Trạng thái Bản vẽ: UNDER REVIEW | Trạng thái Bản vẽ: RELEASED (Đóng Băng) |
| :--- | :---: | :---: | :---: |
| **Download / View 3D** | ✅ Mọi Kỹ sư | ✅ Mọi Kỹ sư | ✅ Mọi Kỹ sư (Kể cả Mua hàng/Sản xuất) |
| **Check-out (Lấy quyền Primary)**| ✅ Kỹ sư đến trước (FIFO) | ❌ Khóa tạm thời | ❌ Bị cấm tuyệt đối |
| **Check-in (Ghi đè file)** | ✅ Chỉ Primary Lock Holder | ❌ Khóa tạm thời | ❌ Bị cấm tuyệt đối |
| **Bàn giao quyền (Handover)** | ✅ Primary Holder giao cho người khác | ❌ Không áp dụng | ❌ Không áp dụng |
| **Nộp duyệt (Submit Review)** | ✅ Kỹ sư dựng hình (Designer) | ❌ Đã nộp rồi | ❌ Đã duyệt xong |
| **Phê duyệt (Release)** | ❌ Chưa được duyệt | ✅ **Chỉ Trưởng nhóm (Lead/Checker)** | ❌ Đã phát hành rồi |
| **Từ chối duyệt (Reject to Draft)**| ❌ Không áp dụng | ✅ **Chỉ Trưởng nhóm (Lead/Checker)** | ❌ Không áp dụng |
| **Tạo New Revision (Tách Rev B)** | ❌ Đang là bản thảo | ❌ Phải chờ duyệt xong hoặc reject | ✅ **Mọi Kỹ sư thiết kế** |

---

## MỤC 3: SƠ ĐỒ KIẾN TRÚC TỔNG THỂ HỆ THỐNG (ARCHITECTURE FLOWCHART)

Sơ đồ thể hiện luồng tương tác giữa máy trạm SolidWorks 2022 và máy chủ Odoo 20 qua mạng LAN nội bộ:

```mermaid
flowchart TD
    subgraph LAN["MẠNG NỘI BỘ DOANH NGHIỆP (INTRANET LAN)"]
        subgraph CAD_WS1["MÁY TRẠM 1 (KỸ SƯ A)"]
            SW1["SolidWorks 2022 Add-in"]
            CACHE1["Local CAD Workspace A"]
        end

        subgraph CAD_WS2["MÁY TRẠM 2 (KỸ SƯ B)"]
            SW2["SolidWorks 2022 Add-in"]
            CACHE2["Local CAD Workspace B"]
        end

        subgraph ODOO_SERVER["MÁY CHỦ ODOO 20 & PDM GATEWAY"]
            ROUTER["HTTP / REST API Dispatcher"]
            AUTH_MGR["plm.desktop.token<br>(Fixed 180 Days Multi-Session)"]
            GATEKEEPER["plm.action.gatekeeper<br>(FIFO Lock & Conflict Guard)"]
            REV_MGR["ir.attachment / plm.document<br>(Revision Freeze Engine)"]
            POSTGRES[("PostgreSQL 'odoo20'")]
        end
    end

    SW1 <-->|"REST API / LAN"| ROUTER
    SW2 <-->|"REST API / LAN"| ROUTER
    ROUTER --> AUTH_MGR
    ROUTER --> GATEKEEPER
    ROUTER --> REV_MGR
    AUTH_MGR --> POSTGRES
    GATEKEEPER --> POSTGRES
    REV_MGR --> POSTGRES

    classDef cadNode fill:#e1f5fe,stroke:#0288d1,stroke-width:2px;
    classDef serverNode fill:#e8f5e9,stroke:#388e3c,stroke-width:2px;
    classDef dbNode fill:#fff3e0,stroke:#f57c00,stroke-width:2px;

    class SW1,SW2,CACHE1,CACHE2 cadNode;
    class ROUTER,AUTH_MGR,GATEKEEPER,REV_MGR serverNode;
    class POSTGRES dbNode;
```

---

## MỤC 4: THIẾT KẾ BACKEND ODOO 20 CHI TIẾT

### 1. Model Quản lý Token Đa thiết bị 180 ngày: `plm.desktop.token`
Mỗi thiết bị khi đăng nhập sẽ tạo một bản ghi token độc lập. Không xóa các token cũ của user trên máy tính khác:

```python
# -*- coding: utf-8 -*-
from datetime import timedelta
import secrets
from odoo import api, fields, models

class PlmDesktopToken(models.Model):
    _name = 'plm.desktop.token'
    _description = 'SolidWorks Multi-device Fixed 180-day Token'
    _order = 'issued_at desc, id desc'

    name = fields.Char(string='Token Hash', required=True, index=True, readonly=True)
    user_id = fields.Many2one('res.users', string='Kỹ sư', required=True, ondelete='cascade', index=True)
    machine_uuid = fields.Char(string='Machine UUID', required=True, index=True)
    machine_name = fields.Char(string='Tên máy tính CAD')
    client_ip = fields.Char(string='IP LAN')
    cad_version = fields.Char(string='Phiên bản CAD', default='SolidWorks 2022')
    
    issued_at = fields.Datetime(string='Ngày cấp', default=fields.Datetime.now, readonly=True)
    expires_at = fields.Datetime(string='Hạn chót 180 ngày', required=True, index=True)
    is_revoked = fields.Boolean(string='Bị thu hồi thủ công', default=False)

    is_active = fields.Boolean(string='Còn hiệu lực', compute='_compute_is_active', store=True)

    @api.depends('expires_at', 'is_revoked')
    def _compute_is_active(self):
        now = fields.Datetime.now()
        for rec in self:
            rec.is_active = (not rec.is_revoked) and (rec.expires_at > now)

    @api.model
    def authenticate_device(self, user_id, machine_uuid, machine_name, client_ip, cad_version):
        """Cấp token 180 ngày cố định. Không hủy token trên các thiết bị khác của User."""
        raw_token = secrets.token_urlsafe(48)
        now = fields.Datetime.now()
        expires_at = now + timedelta(days=180)

        token_rec = self.create({
            'name': raw_token,
            'user_id': user_id,
            'machine_uuid': machine_uuid,
            'machine_name': machine_name,
            'client_ip': client_ip,
            'cad_version': cad_version,
            'issued_at': now,
            'expires_at': expires_at,
        })
        return token_rec, raw_token
```

---

### 2. Model Quản lý Khóa Tranh chấp & Chống ghi đè: `plm.checkout.lock`
Quản lý trạng thái khóa FIFO, chuyển giao quyền (Handover) và băm SHA-1 bảo vệ phiên bản:

```python
# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError

class PlmCheckoutLock(models.Model):
    _name = 'plm.checkout.lock'
    _description = 'PDM Checkout FIFO Priority & Handover Engine'
    _rec_name = 'attachment_id'

    attachment_id = fields.Many2one('ir.attachment', string='Bản vẽ CAD', required=True, ondelete='cascade', index=True)
    primary_user_id = fields.Many2one('res.users', string='Kỹ sư giữ quyền Check-in (FIFO)', required=True)
    primary_machine_uuid = fields.Char(string='Máy trạm giữ quyền')
    lock_time = fields.Datetime(string='Thời điểm khóa', default=fields.Datetime.now)
    
    base_file_hash = fields.Char(string='SHA-1 Hash gốc khi tải về', required=True)
    base_version_number = fields.Integer(string='Version gốc khi tải về', default=1)
    
    # Danh sách kỹ sư tải về sau (Secondary/Concurrent Editors)
    secondary_user_ids = fields.Many2many('res.users', string='Kỹ sư đang cùng sửa cục bộ')

    def action_handover_lock(self, new_user_id, new_machine_uuid):
        """Kỹ sư thứ nhất bàn giao quyền Check-in cho kỹ sư thứ hai"""
        self.ensure_one()
        self.write({
            'primary_user_id': new_user_id.id,
            'primary_machine_uuid': new_machine_uuid,
            'lock_time': fields.Datetime.now()
        })
```

---

## MỤC 5: CÁC SƠ ĐỒ TUẦN TỰ MERMAID CHI TIẾT (SEQUENCE DIAGRAMS)

### SƠ ĐỒ 1: ĐĂNG NHẬP ĐA THIẾT BỊ VỚI TOKEN CỐ ĐỊNH 180 NGÀY (Q1.1 & Q1.2)
Kỹ sư Hùng có thể đăng nhập đồng thời trên máy trạm Workstation tại công ty và máy trạm phụ mà không bị kick-out:

```mermaid
sequenceDiagram
    autonumber
    actor Engineer as Kỹ sư (Hùng)
    participant WS1 as SolidWorks (Máy Trạm 1)
    participant WS2 as SolidWorks (Máy Trạm 2)
    participant OdooAPI as Odoo 20 REST API
    participant DB as PostgreSQL 'odoo20'

    Note over Engineer, WS1: ĐĂNG NHẬP MÁY TRẠM 1 (CÔNG TY)
    Engineer->>WS1: Nhập Login / Password
    WS1->>OdooAPI: POST /api/desktop/auth/login<br>(Machine_UUID_1, WS-RND-01)
    OdooAPI->>DB: Xác thực mật khẩu & Tạo Token 1
    DB-->>OdooAPI: Token_1 (Hạn: Bây giờ + 180 ngày)
    OdooAPI-->>WS1: 200 OK (Token_1, Expires: +180 Days)
    WS1-->>Engineer: Đăng nhập thành công trên Máy 1

    Note over Engineer, WS2: ĐĂNG NHẬP THÊM MÁY TRẠM 2 (KHÔNG KICK MÁY 1)
    Engineer->>WS2: Nhập Login / Password
    WS2->>OdooAPI: POST /api/desktop/auth/login<br>(Machine_UUID_2, WS-RND-02)
    OdooAPI->>DB: Tạo thêm Token 2 (Không hủy Token 1)
    DB-->>OdooAPI: Token_2 (Hạn: Bây giờ + 180 ngày)
    OdooAPI-->>WS2: 200 OK (Token_2, Expires: +180 Days)
    WS2-->>Engineer: Đăng nhập thành công trên Máy 2

    Note over WS1, WS2: CẢ 2 THIẾT BỊ HOẠT ĐỘNG SONG SONG 180 NGÀY
```

---

### SƠ ĐỒ 2: TRANH CHẤP CHECK-OUT (FIFO), CHUYỂN QUYỀN VÀ CHỐNG GHI ĐÈ (Q2.1)
Thể hiện tình huống: Kỹ sư A và B cùng sửa bản vẽ. Kỹ sư A Check-in trước, Kỹ sư B bị chặn đứng và buộc phải tải bản mới:

```mermaid
sequenceDiagram
    autonumber
    actor EngA as Kỹ sư A (Đến trước)
    actor EngB as Kỹ sư B (Đến sau)
    participant SWA as SolidWorks Add-in A
    participant SWB as SolidWorks Add-in B
    participant PDM as Odoo PDM Gatekeeper
    participant FileRepo as Kho Bản Vẽ (odoo20)

    Note over EngA, PDM: BƯỚC 1: KỸ SƯ A CHECK-OUT TRƯỚC (NẮM QUYỀN PRIMARY)
    EngA->>SWA: Bấm "Check-out Bản vẽ FRAME.SLDASM"
    SWA->>PDM: POST /api/desktop/pdm/check_action (checkout, file_id=101)
    PDM->>PDM: Kiểm tra trạng thái: File đang tự do
    PDM->>FileRepo: Đăng ký Primary Lock = Kỹ sư A (Base Ver: 1)
    PDM-->>SWA: 200 OK (Quyền: PRIMARY_LOCK_HOLDER, Hash: 8a9f2...)
    SWA-->>EngA: Mở bản vẽ ở chế độ ĐƯỢC PHÉP CHECK-IN

    Note over EngB, PDM: BƯỚC 2: KỸ SƯ B CHECK-OUT SAU (CHỈ ĐƯỢC SỬA CỤC BỘ)
    EngB->>SWB: Bấm "Check-out Bản vẽ FRAME.SLDASM"
    SWB->>PDM: POST /api/desktop/pdm/check_action (checkout, file_id=101)
    PDM-->>SWB: 200 OK (Cảnh báo: SECONDARY_LOCK, Kỹ sư A đang giữ quyền)
    SWB-->>EngB: Mở bản vẽ kèm thông báo: "Kỹ sư A đang giữ quyền Check-in!"

    alt TRƯỜNG HỢP 2A: KỸ SƯ A BÀN GIAO QUYỀN CHO B (LOCK HANDOVER)
        EngA->>SWA: Bấm "Chuyển giao quyền Check-in cho Kỹ sư B"
        SWA->>PDM: POST /api/desktop/pdm/handover_lock (to_user=EngB)
        PDM->>FileRepo: Cập nhật Primary Lock = Kỹ sư B
        PDM-->>SWA: 200 OK (Đã nhượng quyền)
        PDM-->>SWB: Notify: Kỹ sư B đã trở thành Primary Lock Holder!
    else TRƯỜNG HỢP 2B: KỸ SƯ A CHECK-IN TRƯỚC ➔ B BỊ CHẶN GHI ĐÈ
        EngA->>SWA: Bấm "Check-in Bản vẽ"
        SWA->>PDM: POST /api/desktop/pdm/checkin (File mới, Base Ver: 1)
        PDM->>FileRepo: Lưu file mới ➔ Cập nhật Version lên Ver: 2 (SHA: c41b7...)
        PDM->>FileRepo: Xóa Primary Lock của Kỹ sư A
        PDM-->>SWA: Check-in Thành công (Version 2 Published)

        Note over EngB, PDM: KỸ SƯ B CỐ TÌNH CHECK-IN SAU
        EngB->>SWB: Bấm "Check-in Bản vẽ"
        SWB->>PDM: POST /api/desktop/pdm/checkin (File của B, Base Ver: 1)
        PDM->>PDM: Đối chiếu Version: Base Ver 1 != Current Server Ver 2!
        PDM-->>SWB: 409 CONFLICT: STALE_VERSION_OVERWRITE_PREVENTED
        SWB-->>EngB: HỘP THOẠI CẢNH BÁO:<br>"Kỹ sư A đã cập nhật Ver 2 lên Server.<br>Bạn bị CHẶN GHI ĐÈ!<br>Vui lòng bấm 'Tải Bản Mới' để Merge."
    end
```

---

### SƠ ĐỒ 3: QUY TRÌNH DUYỆT 2 CẤP, ĐÓNG BĂNG REV A & TÁCH REV B (Q3)
Sau khi Trưởng nhóm duyệt **Released**, Rev A trở thành bất biến. Khi cần nâng cấp, hệ thống tự động sinh nhánh **Rev B**:

```mermaid
sequenceDiagram
    autonumber
    actor Designer as Kỹ sư Thiết kế
    actor Checker as Trưởng nhóm (Checker/Lead)
    participant SW as SolidWorks Taskpane
    participant OdooPLM as Odoo 20 PLM Engine
    participant DB as CSDL PostgreSQL

    Note over Designer, OdooPLM: GIAI ĐOẠN 1: KỸ SƯ VẼ & NỘP DUYỆT
    Designer->>SW: Hoàn thành 3D/2D Bản vẽ Rev A
    Designer->>SW: Bấm "Submit for Review" (Nộp thẩm định)
    SW->>OdooPLM: POST /api/desktop/pdm/submit_review (file_id=200, rev='A')
    OdooPLM->>DB: Đổi State: 'draft' ➔ 'under_review'
    OdooPLM-->>SW: Thông báo đã nộp duyệt thành công

    Note over Checker, OdooPLM: GIAI ĐOẠN 2: TRƯỞNG NHÓM PHÊ DUYỆT (RELEASE)
    Checker->>OdooPLM: Mở phiếu thẩm định bản vẽ Rev A
    Checker->>OdooPLM: Bấm nút "Phê duyệt & Release"
    OdooPLM->>DB: Đổi State: 'under_review' ➔ 'released'
    OdooPLM->>DB: ĐÓNG BĂNG DỮ LIỆU REV A (Is_Frozen = True, Read-Only)
    OdooPLM-->>SW: Thông báo: Bản vẽ Rev A đã chính thức Released!

    Note over Designer, OdooPLM: GIAI ĐOẠN 3: PHÁT SINH CẢI TIẾN ➔ TỰ TẠO REV B
    Designer->>SW: Mở bản vẽ Rev A để sửa kích thước
    SW->>OdooPLM: POST /api/desktop/pdm/check_action (action='edit', file_id=200)
    OdooPLM-->>SW: CHẶN: "Rev A đã Released và bị đóng băng! Bạn phải tạo New Revision."
    
    Designer->>SW: Bấm nút "New Revision (Tạo Rev B)"
    SW->>OdooPLM: POST /api/desktop/pdm/new_revision (source_id=200)
    OdooPLM->>DB: Tạo bản ghi mới Clone từ Rev A:<br>- Revision = 'B'<br>- State = 'draft'<br>- Parent_Rev_Id = Rev A (Id: 200)
    OdooPLM-->>SW: 200 OK (Đã tạo Rev B, mở khóa quyền sửa trên Rev B)
    SW-->>Designer: SolidWorks chuyển sang lưu trên nhánh Rev B (Rev A giữ nguyên vẹn!)
```

---

## MỤC 6: ĐẶC TẢ 3 REST API CỐT LÕI CHO SOLIDWORKS DESKTOP ADD-IN

### API 1: Đăng nhập Đa thiết bị & Cấp Token 180 ngày Cố định
* **Method & URL:** `POST /api/desktop/auth/login`
* **Request Body:**
  ```json
  {
    "db": "odoo20",
    "login": "hung.cad@congty.vn",
    "password": "MatKhauChinhXac123",
    "machine_uuid": "BFEBFBFF000906EA-DELL-WS01",
    "machine_name": "WS-RND-HUNG",
    "cad_version": "SolidWorks 2022 SP5"
  }
  ```
* **Response Body (200 OK):**
  ```json
  {
    "status": "success",
    "token": "dGhpcyBpcyBhIHNlY3VyZSAxODBkYXkgdG9rZW4gZXhhbXBsZQ...",
    "issued_at": "2026-11-05T14:30:00Z",
    "expires_at": "2027-05-04T14:30:00Z",
    "duration_days": 180,
    "user": {
      "id": 14,
      "name": "Nguyễn Văn Hùng",
      "email": "hung.cad@congty.vn",
      "role": "cad_designer"
    }
  }
  ```

---

### API 2: Cổng Phán quyết Tranh chấp Check-out (FIFO & Handover)
* **Method & URL:** `POST /api/desktop/pdm/check_action`
* **Headers:** `Authorization: Bearer <TOKEN>`
* **Request Body (Khi Kỹ sư B bấm Check-out):**
  ```json
  {
    "action": "checkout",
    "document_id": 5012,
    "file_name": "ROBOT_ARM_BASE.SLDPRT",
    "machine_uuid": "BFEBFBFF000906EA-DELL-WS02"
  }
  ```
* **Response Body (Trường hợp B đến sau - 200 OK):**
  ```json
  {
    "allowed": true,
    "lock_role": "secondary_editor",
    "can_checkin_direct": false,
    "primary_holder": {
      "user_name": "Nguyễn Văn Hùng",
      "machine_name": "WS-RND-HUNG",
      "locked_at": "2026-11-05T08:15:00Z"
    },
    "dialog_title": "Cảnh Báo Quyền Check-In",
    "message_vn": "Kỹ sư Nguyễn Văn Hùng đã Check-out trước và đang giữ quyền Check-in chính. Bạn được phép sửa cục bộ, nhưng không thể Check-in đè trước Hùng trừ khi được bàn giao quyền."
  }
  ```

---

### API 3: Kiểm tra Chống ghi đè khi Check-in (Anti-Overwrite Conflict Guard)
* **Method & URL:** `POST /api/desktop/pdm/checkin`
* **Headers:** `Authorization: Bearer <TOKEN>`
* **Request Body:**
  ```json
  {
    "document_id": 5012,
    "base_version": 1,
    "base_hash": "8a9f2d1e7c5b...",
    "new_hash": "3f1a9c4e2d8a...",
    "machine_uuid": "BFEBFBFF000906EA-DELL-WS02"
  }
  ```
* **Response Body (Bị chặn do Kỹ sư A đã Check-in Ver 2 trước - 409 Conflict):**
  ```json
  {
    "status": "error",
    "error_code": "STALE_VERSION_OVERWRITE_PREVENTED",
    "dialog_title": "Chặn Ghi Đè Bản Vẽ",
    "message_vn": "Bản vẽ trên máy chủ đã được Kỹ sư Nguyễn Văn Hùng cập nhật lên Version 2 lúc 14:15. Phiên bản bạn đang sửa dựa trên Version 1 cũ. Để đảm bảo không làm mất dữ liệu của đồng nghiệp, hệ thống đã CHẶN thao tác này. Vui lòng bấm 'Tải Bản Mới' về để cập nhật!",
    "server_current_version": 2,
    "updated_by": "Nguyễn Văn Hùng",
    "updated_at": "2026-11-05T14:15:22Z"
  }
  ```
