# ================================================================================
# SCRIPT TỰ ĐỘNG SAO LƯU (BACKUP) ODOO & POSTGRESQL NÉN ZIP HÀNG NGÀY
# ================================================================================
# - Tự động nén toàn bộ Database + Tệp đính kèm (Filestore) thành file .zip chuẩn Odoo.
# - Tự động đặt tên theo ngày giờ: odoo20_backup_yyyyMMdd_HHmmss.zip.
# - Tự động xóa các bản sao lưu cũ quá 30 ngày để tiết kiệm dung lượng ổ cứng.
# - Tự động ghi nhật ký (log) theo ngày để quản trị viên dễ dàng theo dõi.
# ================================================================================

param(
    [string]$DbName = "odoo20",                 # Tên cơ sở dữ liệu Odoo cần backup
    [string]$MasterPwd = "admin",               # Master password quản trị (xem trong config/odoo.conf)
    [string]$OdooUrl = "http://127.0.0.1:8080", # Cổng Odoo đang chạy (8080 hoặc 8069)
    [string]$BackupDir = "C:\odoo_backups",      # Thư mục lưu file backup trên server
    [int]$RetentionDays = 30                     # Số ngày lưu trữ (sau 30 ngày sẽ tự xóa file cũ)
)

# 1. Khởi tạo thư mục lưu trữ và thư mục logs
if (-not (Test-Path $BackupDir)) {
    New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null
}
$logDir = Join-Path $BackupDir "logs"
if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$logFile = Join-Path $logDir "backup_$(Get-Date -Format 'yyyyMMdd').log"
$backupFile = Join-Path $BackupDir "${DbName}_backup_${timestamp}.zip"

function Write-Log {
    param([string]$message, [string]$level = "INFO")
    $logMsg = "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] [$level] $message"
    Write-Host $logMsg
    Add-Content -Path $logFile -Value $logMsg
}

Write-Log "================================================================================"
Write-Log "BẮT ĐẦU SAO LƯU HỆ THỐNG ODOO (DATABASE & FILESTORE)"
Write-Log "Database : $DbName"
Write-Log "Odoo URL : $OdooUrl"
Write-Log "File đích: $backupFile"
Write-Log "================================================================================"

# 2. Gọi API Odoo Database Manager để nén toàn bộ CSDL + Filestore thành file .ZIP
try {
    $backupUrl = "$OdooUrl/web/database/backup"
    $body = @{
        master_pwd = $MasterPwd
        name = $DbName
        backup_format = "zip"
    }

    Write-Log "Đang gửi yêu cầu nén và tải dữ liệu từ Odoo... (Vui lòng đợi vài phút tùy dung lượng tệp)"
    
    # Gọi WebRequest với thời gian timeout lên đến 2 giờ (7200 giây)
    $response = Invoke-WebRequest -Uri $backupUrl -Method Post -Body $body -OutFile $backupFile -TimeoutSec 7200

    if (Test-Path $backupFile) {
        $fileSizeMB = [math]::Round((Get-Item $backupFile).Length / 1MB, 2)
        if ($fileSizeMB -gt 0.05) {
            Write-Log ">>> SAO LƯU THÀNH CÔNG! Dung lượng file nén: $fileSizeMB MB." "SUCCESS"
        } else {
            Write-Log "CẢNH BÁO: File sao lưu tạo ra quá nhỏ ($fileSizeMB MB). Vui lòng kiểm tra lại Master Password hoặc Database Name!" "ERROR"
        }
    } else {
        Write-Log "LỖI: Không tìm thấy file sao lưu sau khi thực hiện!" "ERROR"
    }
} catch {
    Write-Log "LỖI NGOẠI LỆ TRONG KHI SAO LƯU: $($_.Exception.Message)" "ERROR"
}

# 3. Tự động dọn dẹp các bản backup cũ hơn $RetentionDays ngày
try {
    Write-Log "Kiểm tra và dọn dẹp các bản sao lưu cũ hơn $RetentionDays ngày..."
    $cutoffDate = (Get-Date).AddDays(-$RetentionDays)
    $oldFiles = Get-ChildItem -Path $BackupDir -Filter "*.zip" | Where-Object { $_.LastWriteTime -lt $cutoffDate }
    
    $deletedCount = 0
    foreach ($file in $oldFiles) {
        Write-Log "Xóa bản sao lưu cũ: $($file.Name) (Tạo lúc: $($file.LastWriteTime))"
        Remove-Item $file.FullName -Force
        $deletedCount++
    }
    Write-Log "Đã dọn dẹp $deletedCount bản sao lưu cũ."
} catch {
    Write-Log "Lỗi khi dọn dẹp file cũ: $($_.Exception.Message)" "WARNING"
}

Write-Log "HOÀN TẤT TIẾN TRÌNH SAO LƯU HÀNG NGÀY.`n"
