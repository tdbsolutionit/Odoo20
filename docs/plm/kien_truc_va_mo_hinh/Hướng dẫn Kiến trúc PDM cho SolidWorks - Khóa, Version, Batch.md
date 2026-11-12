# HƯỚNG DẪN KIẾN TRÚC PDM CHO SOLIDWORKS
## CHECK-IN / CHECK-OUT TRÊN ODOOPLM: KHÓA — VERSION — BATCH

> **Đối tượng người đọc:** Ban Giám đốc, Kỹ sư thiết kế CAD, Đội ngũ Lập trình viên Odoo & CAD Add-in  
> **Hệ sinh thái:** Odoo 20 Community / Enterprise | OmniaSolutions OdooPLM (`addons/plm`) | SolidWorks 2022 Desktop Add-in  
> **Tư tưởng chủ đạo:** **"Khóa, Không Phải Merge" (Pessimistic Locking, Not Merging)** — Chuẩn hóa dữ liệu theo 3 trụ cột: **Khóa (Lock) — Phiên bản (Version) — Giao dịch Khối (Batch)**.

---

## MỤC LỤC
1. [TƯ DUY CỐT LÕI: KHÓA, KHÔNG PHẢI MERGE](#1-tư-duy-cốt-lõi-khóa-không-phải-merge)
2. [VÒNG ĐỜI KHÓA CỦA MỘT TỆP CAD (STATE MACHINE)](#2-vòng-đời-khóa-của-một-tệp-cad-state-machine)
3. [LUỒNG TƯƠNG TÁC KỸ THUẬT: ADD-IN ↔ ODOO ↔ DATABASE](#3-luồng-tương-tác-kỹ-thuật-add-in--odoo--database)
4. [GIẢI QUYẾT 3 BÀI TOÁN SẢN XUẤT THỰC TẾ](#4-giải-quyết-3-bài-toán-sản-xuất-thực-tế)
   - [Bài toán 1: Hai người bấm Check-out cùng lúc (Race Condition tại t=0)](#bài-toán-1-hai-người-bấm-check-out-cùng-lúc-race-condition-tại-t0)
   - [Bài toán 2: Cụm Assembly & Giao dịch Khối (Atomic Batch Transaction)](#bài-toán-2-cụm-assembly--giao-dịch-khối-atomic-batch-transaction)
   - [Bài toán 3: Đồng bộ Local ↔ Server & Bảo vệ thuộc tính File](#bài-toán-3-đồng-bộ-local--server--bảo-vệ-thuộc-tính-file)
5. [KẾ HOẠCH TRIỂN KHAI 6 GIAI ĐOẠN (ROADMAP CHO DEV)](#5-kế-hoạch-triển-khai-6-giai-đoạn-roadmap-cho-dev)

---

## 1. TƯ DUY CỐT LÕI: KHÓA, KHÔNG PHẢI MERGE

Trong phát triển phần mềm, các lập trình viên sử dụng Git để sửa song song trên cùng một file mã nguồn dạng văn bản (text), sau đó ghép lại (merge). Tuy nhiên, **trong kỹ thuật cơ khí 3D, tư duy đó hoàn toàn không thể áp dụng**:

```mermaid
flowchart TD
    subgraph GIT["MÔ HÌNH GIT (File Text Mã Nguồn)"]
        direction TB
        G_DEV["Kỹ sư A & Kỹ sư B\n(Cùng sửa song song)"] --> G_MERGE["TỰ ĐỘNG MERGE\nGhép các dòng code (A + B)"]
        G_NOTE["Sửa song song, ghép sau"]
    end

    subgraph PDM["MÔ HÌNH PDM (File CAD 3D Nhị Phân)"]
        direction TB
        P_A["Kỹ sư A: Lấy khóa trước"] --> P_LOCK["SLDPRT (Đang bị khóa)"]
        P_B["Kỹ sư B: Đến sau"] -.->|"Bị chặn (X)"| P_LOCK
        P_NOTE["Ai lấy khóa trước thì sửa"]
    end

    classDef gitBox fill:#f1f8e9,stroke:#558b2f,stroke-width:2px;
    classDef pdmBox fill:#e3f2fd,stroke:#1565c0,stroke-width:2px;
    classDef lockBox fill:#fff3e0,stroke:#e65100,stroke-width:2px;

    class GIT,G_DEV,G_MERGE gitBox;
    class PDM,P_A,P_B pdmBox;
    class P_LOCK lockBox;
```

| Tiêu chí | MÔ HÌNH GIT (Code Phần Mềm) | MÔ HÌNH PDM (Bản Vẽ CAD 3D) |
| :--- | :--- | :--- |
| **Định dạng dữ liệu** | Dạng văn bản (Text / Lines of code). | Tệp nhị phân độc quyền (Binary Blobs: `.sldprt`, `.sldasm`). |
| **Cơ chế cộng tác** | **Sửa song song, ghép sau:** Nhiều người sửa cùng lúc, Git tự động merge dòng text. | **Khóa độc quyền (Pessimistic Lock):** Ai lấy khóa trước thì sửa, người đến sau chỉ được đọc. |
| **Khả năng Merge** | Có thể tự động giải quyết conflict theo dòng. | **Tuyệt đối không thể Merge** (sẽ làm hỏng cây tính năng Feature Tree và hình học Parasolid). |

### Tại sao file CAD không thể Merge?
* Tệp SolidWorks (`.sldprt`, `.sldasm`, `.slddrw`) là **tệp nhị phân độc quyền (Binary Blobs)** chứa cây lịch sử tính năng (Feature Tree), tham số hình học nhân Parasolid và các ràng buộc lắp ghép (Mate Constraints).
* Không có bất kỳ công cụ nào có thể tự động ghép 2 thay đổi hình học độc lập (ví dụ: A đổi lỗ ren M8, B vát mép cạnh đáy) mà không làm rách lưới đa giác hoặc làm hỏng mô hình tham số.
* **Quy tắc vàng của PDM cơ khí:** 
  > **Chỉ duy nhất một người được phép sửa một tệp CAD tại một thời điểm (Exclusive Lock). Ai đến trước thì lấy khóa sửa; ai đến sau thì chỉ được mở xem dưới chế độ Chỉ-Đọc (Read-only).**

---

## 2. VÒNG ĐỜI KHÓA CỦA MỘT TỆP CAD (STATE MACHINE)

Một tệp CAD trong kho PDM luôn vận hành xoay quanh 2 trạng thái vật lý và **3 ngả đường** giải phóng khóa:

```mermaid
stateDiagram-v2
    [*] --> Checked_In: Bản vẽ lưu trong kho Server
    
    state Checked_In {
        ReadOnly_Server: Thuộc tính trên máy trạm = READ-ONLY
    }

    Checked_In --> Checked_Out: Check-out (Cấp khóa ghi độc quyền)

    state Checked_Out {
        Writable_Local: Thuộc tính trên máy trạm = GHI ĐƯỢC
    }

    Checked_Out --> Checked_In: Đường 1: Check-in (Version + 1, Upload file mới)
    Checked_Out --> Checked_In: Đường 2: Undo Check-out (Hủy sửa, giữ nguyên Version)
    Checked_Out --> Checked_In: Đường 3: Force Unlock (Trưởng phòng cưỡng chế mở khóa)
```

### Chi tiết 3 ngả đường giải phóng khóa:
1. **Đường 1 — `Check-in` (Hoàn tất chỉnh sửa):**
   * Kỹ sư hoàn thành việc sửa bản vẽ $\rightarrow$ Bấm Check-in từ Add-in.
   * File nhị phân mới được đẩy lên Server Odoo $\rightarrow$ Số **Version tự động tăng +1** (ví dụ: v1 lên v2) $\rightarrow$ Server xóa bản ghi khóa.
   * File trên máy trạm tự động khóa lại thành **Read-only**.
2. **Đường 2 — `Undo Check-out` (Hủy bỏ thao tác):**
   * Kỹ sư mở ra sửa thử nhưng không đạt, muốn hủy bỏ thay đổi.
   * Add-in gửi yêu cầu hủy $\rightarrow$ Server xóa bản ghi khóa mà **không cập nhật file mới**, **giữ nguyên version cũ** $\rightarrow$ File local hoàn nguyên về bản vẽ gốc.
3. **Đường 3 — `Force Unlock` (Cưỡng chế mở khóa / Phá khóa):**
   * Kỹ sư giữ khóa nhưng đột xuất nghỉ việc, đi công tác, hoặc máy tính bị hỏng.
   * Trưởng phòng kỹ thuật (Admin) có thẩm quyền bấm nút phá khóa trên Odoo $\rightarrow$ Server xóa bản ghi khóa, ghi nhận log kiểm toán (audit log) $\rightarrow$ File trở về trạng thái sẵn sàng để người khác tiếp quản.

---

## 3. LUỒNG TƯƠNG TÁC KỸ THUẬT: ADD-IN ↔ ODOO ↔ DATABASE

Quá trình giao tiếp giữa máy trạm SolidWorks, Odoo API Gateway và Cơ sở dữ liệu PostgreSQL diễn ra theo một chu trình 6 bước khép kín và an toàn:

```mermaid
sequenceDiagram
    autonumber
    actor Dev as Kỹ sư SolidWorks
    participant Addin as SolidWorks Add-in
    participant Odoo as Odoo API Gateway
    participant DB as PostgreSQL Database

    Dev->>Addin: Bấm "Check-out File"
    Addin->>Odoo: Gửi API check_out(file_id)
    Odoo->>DB: Thực thi: SELECT * FROM plm_checkout FOR UPDATE NOWAIT
    DB-->>Odoo: Cấp khóa thành công (Lock Granted)
    Odoo-->>Addin: Phản hồi: Token phiên khóa + Base Version hiện tại
    Note over Addin: Gỡ thuộc tính Read-Only<br/>Chuyển sang GHI ĐƯỢC (Writable)
    
    Dev->>Addin: Chỉnh sửa hình học 3D trên SolidWorks
    Dev->>Addin: Bấm "Check-in"
    Addin->>Odoo: Gửi API check_in(batch_files, token)
    
    rect rgb(240, 248, 255)
        Note over Odoo,DB: GIAO DỊCH NGUYÊN TỬ (ATOMIC TRANSACTION)
        Odoo->>DB: BEGIN TRANSACTION
        Odoo->>DB: Ghi file nhị phân mới vào Filestore
        Odoo->>DB: Cập nhật Version = Version + 1
        Odoo->>DB: Xóa bản ghi plm_checkout
        Odoo->>DB: COMMIT TRANSACTION (hoặc ROLLBACK nếu có lỗi)
    end
    
    Odoo-->>Addin: Phản hồi OK: Version + 1, Đã nhả khóa
    Note over Addin: Đặt lại thuộc tính file = READ-ONLY
```

---

## 4. GIẢI QUYẾT 3 BÀI TOÁN SẢN XUẤT THỰC TẾ

---

### Bài toán 1: Hai người bấm Check-out cùng lúc (Race Condition tại t=0)

* **Tình huống:** Kỹ sư **An** và Kỹ sư **Bình** cùng mở một chi tiết và cùng bấm Check-out vào đúng mili-giây $t=0$.
* **Hậu quả nếu xử lý sai:** Cả hai cùng nghĩ mình đang giữ khóa, cùng sửa và người bấm lưu sau sẽ xóa sạch công sức của người bấm trước.
* **Giải pháp dứt điểm:** Sử dụng cơ chế **`FOR UPDATE NOWAIT`** của PostgreSQL.

```mermaid
flowchart LR
    A["Kỹ sư An (t = 0)"] --> PG{"POSTGRESQL\nFOR UPDATE NOWAIT"}
    B["Kỹ sư Bình (t = 0)"] --> PG
    
    PG -->|"Đến trước (Microsecond)"| OK["An ĐƯỢC CẤP KHÓA\n(Bắt đầu chỉnh sửa)"]
    PG -->|"Đến sau (Đụng khóa)"| REJECT["Bình BỊ TỪ CHỐI NGAY\n'An đang giữ khóa, không chờ!'"]

    classDef ok fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px;
    classDef reject fill:#ffebee,stroke:#c62828,stroke-width:2px;
    class OK ok;
    class REJECT reject;
```

* **Nguyên lý hoạt động:**
  1. Giao dịch của An đến cơ sở dữ liệu trước một phần triệu giây $\rightarrow$ PostgreSQL cấp khóa độc quyền cho An.
  2. Giao dịch của Bình đến sau lập tức đụng cờ `NOWAIT` $\rightarrow$ Cơ sở dữ liệu **từ chối ngay mà không treo ứng dụng** (không bắt Bình phải chờ timeout).
  3. Odoo bắt lỗi và trả về ngay thông báo cho Bình: *"Chi tiết đang được sửa bởi An (bắt đầu lúc 08:30). Bạn chỉ có quyền đọc (Read-only)."*

---

### Bài toán 2: Cụm Assembly & Giao dịch Khối (Atomic Batch Transaction)

Trong cơ khí, hiếm khi kỹ sư làm việc với 1 chi tiết đơn lẻ mà thường làm việc với cả một cụm máy (**Assembly**) gồm hàng chục Part con.

```mermaid
flowchart TD
    ASM["CỤM LẮP RÁP: ASM"] --> PA["Part A: Rảnh"]
    ASM --> PB["Part B: Đang bị người khác khóa!"]
    ASM --> PC["Part C: Rảnh"]

    PB --> DECISION{"Kiểm tra Batch"}
    DECISION -->|"Có 1 chi tiết kẹt khóa"| RB["ROLLBACK TOÀN BỘ\n(Hủy giao dịch, không lưu nửa vời)"]
    DECISION -->|"Tất cả chi tiết hợp lệ"| CM["COMMIT TOÀN BỘ\n(Cả cụm đồng loạt lên Version +1)"]

    classDef fail fill:#ffebee,stroke:#c62828,stroke-width:2px;
    classDef pass fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px;
    class PB,RB fail;
    class CM pass;
```

* Khi thực hiện Check-in / Check-out theo lô (Batch):
  * **Toàn bộ linh kiện thành công:** Odoo mới ghi nhận `COMMIT`. Tất cả chi tiết đồng loạt lên Version mới.
  * **Chỉ cần 1 linh kiện bị lỗi:** Odoo lập tức kích hoạt `ROLLBACK` toàn bộ giao dịch. Trả thông báo lỗi rõ ràng: *"Giao dịch hủy bỏ vì Part B đang bị Kỹ sư Tuấn khóa"*. Không để lại bất kỳ rác dữ liệu nào.

---

### Bài toán 3: Đồng bộ Local ↔ Server & Bảo vệ thuộc tính File

Xung đột phổ biến nhất tại các phòng thiết kế là kỹ sư sửa file ở máy tính cá nhân nhưng không biết trên Server đã có bản mới hơn do đồng nghiệp vừa tải lên.

```mermaid
flowchart LR
    SRV["Server Odoo:\nBản v3 (Mới nhất)"] <-->|"So sánh Version"| LOC["Máy trạm Local:\nBản v2 (Đã cũ)"]
    LOC --> WARN["CẢNH BÁO TAM GIÁC VÀNG !\n'Bắt buộc tải bản v3 trước khi sửa'"]

    classDef srv fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px;
    classDef loc fill:#fff3e0,stroke:#f57c00,stroke-width:2px;
    classDef warn fill:#ffebee,stroke:#c62828,stroke-width:2px;
    class SRV srv;
    class LOC loc;
    class WARN warn;
```

* **Cơ chế 2 lớp bảo vệ:**
  1. **Lớp 1 — Khóa thuộc tính File hệ điều hành Windows (OS File Attributes):**
     * Khi file chưa được Check-out: Add-in tự động đặt thuộc tính file trên ổ cứng máy trạm là **`Read-Only`**. Kỹ sư mở trên SolidWorks chỉ có thể xem, nếu bấm `Ctrl + S` SolidWorks sẽ báo lỗi cấm ghi.
     * Khi Check-out thành công: Add-in mới gỡ thuộc tính Read-Only, cho phép ghi bình thường.
  2. **Lớp 2 — Cảnh báo lệch Version (Stale Cache Detection):**
     * Trước khi mở file hoặc Check-out, Add-in luôn đối chiếu Version giữa Local và Server.
     * Nếu phát hiện Server đang là bản `v3` mà Local chỉ có bản `v2` $\rightarrow$ Hiển thị **Cảnh báo màu vàng** và ép buộc kỹ sư tải bản mới nhất về đè lên bản cũ trước khi thực hiện bất kỳ thao tác nào.

---

## 5. KẾ HOẠCH TRIỂN KHAI 6 GIAI ĐOẠN (ROADMAP CHO DEV)

Lộ trình triển khai được chia thành 6 giai đoạn rõ ràng, có thể kiểm thử và bàn giao độc lập từng bước:

```mermaid
flowchart LR
    P0["0. AUDIT\nTìm lỗi luồng cũ"] --> P1["1. KHÓA SERVER\nChống trùng với NOWAIT"]
    P1 --> P2["2. VERSION\nTăng +1 & Lưu lịch sử"]
    P2 --> P3["3. ASSEMBLY BATCH\nGiao dịch All-or-Nothing"]
    P3 --> P4["4. CLIENT READ-ONLY\nKhóa file trên Windows"]
    P4 --> P5["5. VẬN HÀNH\nCảnh báo lệch & Force Unlock"]

    classDef done fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px;
    classDef curr fill:#fff3e0,stroke:#f57c00,stroke-width:2px;
    classDef next fill:#e1f5fe,stroke:#0288d1,stroke-width:2px;

    class P0 done;
    class P1,P2 curr;
    class P3,P4,P5 next;
```

### Chi tiết nhiệm vụ kỹ thuật cho từng giai đoạn:

| Giai đoạn | Tên Giai Đoạn | Nhiệm vụ chính của Lập trình viên Odoo (Backend) | Nhiệm vụ chính của Lập trình viên Add-in (Client) |
| :-: | :--- | :--- | :--- |
| **0** | **Audit (Tìm lỗi)** | Rà soát toàn bộ code [`plm_checkout.py`](file:///c:/Work/odoo20-docker/addons/plm/models/plm_checkout.py) và các controller upload hiện tại để phát hiện các kịch bản nghẽn mạng hoặc kẹt session. | Kiểm tra các hàm bắt sự kiện Save/Open trong mã nguồn C# của SolidWorks Add-in. |
| **1** | **Khóa Server không trùng** | Bổ sung ràng buộc `unique (documentid)` và áp dụng câu lệnh `FOR UPDATE NOWAIT` vào API `check-out`. Đảm bảo trả về mã lỗi ngay khi có xung đột. | Bắt mã lỗi từ chối của Server và hiển thị Popup: *"File đang được giữ khóa bởi [Tên người giữ]"*. |
| **2** | **Version có lịch sử** | Kế thừa [`revision.plm.mixin`](file:///c:/Work/odoo20-docker/addons/plm/models/plm_mixin.py) để tự động tăng Version +1 sau khi Check-in. Kích hoạt [`plm.backupdoc`](file:///c:/Work/odoo20-docker/addons/plm/models/plm_backup_document.py) lưu trữ tệp nhị phân cũ vào kho lịch sử. | Hiển thị số Version hiện tại của chi tiết trực tiếp trên cây thư mục FeatureTree của SolidWorks. |
| **3** | **Assembly Batch** | Xây dựng API tiếp nhận danh sách file theo mảng (Array). Bọc toàn bộ quá trình xử lý trong khối `with cr.savepoint():` để tự động Rollback nếu 1 chi tiết thất bại. | Thu thập toàn bộ cây phụ thuộc của cụm máy và đóng gói gửi lên Server trong một request duy nhất. |
| **4** | **Client Read-only** | Cung cấp API trả về trạng thái khóa nhanh (`get_checkout_snapshot`) để Client tra cứu. | Viết code can thiệp thuộc tính Windows File System (`FileInfo.IsReadOnly = true/false`) tương ứng theo trạng thái Check-out. |
| **5** | **Vận hành & Cảnh báo** | Xây dựng nút bấm **"Force Unlock"** trên giao diện Odoo có phân quyền cho Trưởng phòng, bắt buộc nhập lý do và ghi vào Chatter kiểm toán. | Viết logic so sánh $v_{server} \neq v_{local}$, bật cảnh báo và nút "Get Latest Version" khi phát hiện file local bị cũ. |

---

## 6. KẾT LUẬN

Bộ quy chuẩn **"Khóa — Version — Batch"** này là nền tảng sống còn của một hệ thống PDM thực thụ:
* **Đơn giản:** Không làm phức tạp hóa hệ thống bằng các cơ chế rẽ nhánh/merge phần mềm không tương thích với CAD.
* **Chính xác tuyệt đối:** Bảo vệ hình học 3D, loại bỏ nguy cơ ghi đè mất dữ liệu.
* **Ổn định:** Cơ chế `NOWAIT` và `Atomic Batch` triệt tiêu hoàn toàn lỗi treo phần mềm và lỗi gãy cụm lắp ráp.

