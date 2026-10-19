# ================================================================================
# SCRIPT TU DONG SAO LUU (BACKUP) ODOO & POSTGRESQL NEN ZIP HANG NGAY
# ================================================================================
# - Tu dong nen toan bo Database + Tep dinh kem (Filestore) thanh file .zip chuan Odoo.
# - Tu dong dat ten theo ngay gio: odoo20_backup_yyyyMMdd_HHmmss.zip.
# - TUYET DOI KHONG XOA BAN SAO LUU NAO (Giu nguyen toan bo lich su backup vinh vien).
# - Tu dong do tim cong dang chay (8080, 8069, localhost, 127.0.0.1).
# ================================================================================

param(
    [string]$DbName = "odoo20",                 # Ten co so du lieu Odoo can backup
    [string]$MasterPwd = "admin",               # Master password quan tri (xem trong config/odoo.conf)
    [string]$OdooUrl = "http://127.0.0.1:8080", # Cong Odoo dang chay
    [string]$BackupDir = "C:\odoo_backups"      # Thu muc luu file backup tren server
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
Write-Log "File dich: $backupFile"
Write-Log "Chinh sach: GIU LAI TOAN BO BAN SAO LUU (KHONG XOA FILE CU)"
Write-Log "================================================================================"

# 2. Tu dong do tim URL Odoo dang hoat dong
$candidateUrls = @(
    $OdooUrl,
    "http://127.0.0.1:8080",
    "http://localhost:8080",
    "http://127.0.0.1:8069",
    "http://localhost:8069",
    "http://192.168.103.8:8080",
    "http://192.168.103.8:8069"
) | Select-Object -Unique

$activeUrl = $null
foreach ($url in $candidateUrls) {
    try {
        $testReq = Invoke-WebRequest -UseBasicParsing -Uri "$url/web/health" -Method Get -TimeoutSec 3 -ErrorAction SilentlyContinue
        $activeUrl = $url
        break
    } catch {
        try {
            $testReq = Invoke-WebRequest -UseBasicParsing -Uri "$url/web/login" -Method Get -TimeoutSec 3 -ErrorAction SilentlyContinue
            $activeUrl = $url
            break
        } catch {}
    }
}

if (-not $activeUrl) {
    # Thu kiem tra thang cong backup mac dinh
    $activeUrl = $OdooUrl
    Write-Log "Canh bao: Chua ket noi duoc truoc, se thu gui truc tiep den: $activeUrl" "WARNING"
} else {
    Write-Log "Da ket noi thanh cong den Odoo tai: $activeUrl" "INFO"
}

# 3. Goi API Odoo Database Manager de nen toan bo CSDL + Filestore thanh file .ZIP
try {
    $backupUrl = "$activeUrl/web/database/backup"
    $body = @{
        master_pwd = $MasterPwd
        name = $DbName
        backup_format = "zip"
    }

    Write-Log "Dang gui yeu cau nen va tai du lieu tu Odoo... (Vui long doi vai phut tuy dung luong tep)"
    
    $response = Invoke-WebRequest -UseBasicParsing -Uri $backupUrl -Method Post -Body $body -OutFile $backupFile -TimeoutSec 7200

    if (Test-Path $backupFile) {
        $fileSizeMB = [math]::Round((Get-Item $backupFile).Length / 1MB, 2)
        if ($fileSizeMB -gt 0.05) {
            Write-Log ">>> SAO LUU THANH CONG! Dung luong file nen: $fileSizeMB MB." "SUCCESS"
            Write-Log "File luu tai: $backupFile" "SUCCESS"
        } else {
            Write-Log "CANH BAO: File sao luu tao ra qua nho ($fileSizeMB MB). Vui long kiem tra lai Master Password ($MasterPwd) hoac Database Name ($DbName)!" "ERROR"
        }
    } else {
        Write-Log "LOI: Khong tim thay file sao luu sau khi thuc hien!" "ERROR"
    }
} catch {
    Write-Log "LOI NGOAI LE TRONG KHI SAO LUU: $($_.Exception.Message)" "ERROR"
    if ($_.Exception.Response) {
        try {
            $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
            $errDetail = $reader.ReadToEnd()
            if ($errDetail) {
                Write-Log "Chi tiet nguyen nhan tu Odoo: $errDetail" "ERROR"
            }
        } catch {}
    }
    Write-Log "Goi y kiem tra: Hay kiem tra Master Password (-MasterPwd) va xem log tren cua so chay Odoo!" "WARNING"
}

Write-Log "HOAN TAT TIEN TRINH SAO LUU HANG NGAY.`n"
