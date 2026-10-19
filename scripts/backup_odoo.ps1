# ================================================================================
# SCRIPT TU DONG SAO LUU (BACKUP) ODOO & POSTGRESQL NEN ZIP HANG NGAY
# ================================================================================
# - Tu dong nen toan bo Database + Tep dinh kem (Filestore) thanh file .zip chuan Odoo.
# - Tu dong dat ten theo ngay gio: odoo20_backup_yyyyMMdd_HHmmss.zip.
# - Tu dong xoa cac ban sao luu cu qua 30 ngay de tiet kiem dung luong o cung.
# - Tu dong ghi nhat ky (log) theo ngay de quan tri vien de dang theo doi.
# ================================================================================

param(
    [string]$DbName = "odoo20",                 # Ten co so du lieu Odoo can backup
    [string]$MasterPwd = "admin",               # Master password quan tri (xem trong config/odoo.conf)
    [string]$OdooUrl = "http://127.0.0.1:8080", # Cong Odoo dang chay (8080 hoac 8069)
    [string]$BackupDir = "C:\odoo_backups",      # Thu muc luu file backup tren server
    [int]$RetentionDays = 30                     # So ngay luu tru (sau 30 ngay se tu xoa file cu)
)

# 1. Khoi tao thu muc luu tru va thu muc logs
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
Write-Log "BAT DAU SAO LUU HE THONG ODOO (DATABASE & FILESTORE)"
Write-Log "Database : $DbName"
Write-Log "Odoo URL : $OdooUrl"
Write-Log "File dich: $backupFile"
Write-Log "================================================================================"

# 2. Goi API Odoo Database Manager de nen toan bo CSDL + Filestore thanh file .ZIP
try {
    $backupUrl = "$OdooUrl/web/database/backup"
    $body = @{
        master_pwd = $MasterPwd
        name = $DbName
        backup_format = "zip"
    }

    Write-Log "Dang gui yeu cau nen va tai du lieu tu Odoo... (Vui long doi vai phut tuy dung luong tep)"
    
    # Goi WebRequest voi thoi gian timeout len den 2 gio (7200 giay)
    $response = Invoke-WebRequest -Uri $backupUrl -Method Post -Body $body -OutFile $backupFile -TimeoutSec 7200

    if (Test-Path $backupFile) {
        $fileSizeMB = [math]::Round((Get-Item $backupFile).Length / 1MB, 2)
        if ($fileSizeMB -gt 0.05) {
            Write-Log ">>> SAO LUU THANH CONG! Dung luong file nen: $fileSizeMB MB." "SUCCESS"
        } else {
            Write-Log "CANH BAO: File sao luu tao ra qua nho ($fileSizeMB MB). Vui long kiem tra lai Master Password hoac Database Name!" "ERROR"
        }
    } else {
        Write-Log "LOI: Khong tim thay file sao luu sau khi thuc hien!" "ERROR"
    }
} catch {
    Write-Log "LOI NGOAI LE TRONG KHI SAO LUU: $($_.Exception.Message)" "ERROR"
}

# 3. Tu dong don dep cac ban backup cu hon $RetentionDays ngay
try {
    Write-Log "Kiem tra va don dep cac ban sao luu cu hon $RetentionDays ngay..."
    $cutoffDate = (Get-Date).AddDays(-$RetentionDays)
    $oldFiles = Get-ChildItem -Path $BackupDir -Filter "*.zip" | Where-Object { $_.LastWriteTime -lt $cutoffDate }
    
    $deletedCount = 0
    foreach ($file in $oldFiles) {
        Write-Log "Xoa ban sao luu cu: $($file.Name) (Tao luc: $($file.LastWriteTime))"
        Remove-Item $file.FullName -Force
        $deletedCount++
    }
    Write-Log "Da don dep $deletedCount ban sao luu cu."
} catch {
    Write-Log "Loi khi don dep file cu: $($_.Exception.Message)" "WARNING"
}

Write-Log "HOAN TAT TIEN TRINH SAO LUU HANG NGAY.`n"
