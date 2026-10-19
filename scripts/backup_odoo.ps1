# ================================================================================
# SCRIPT TU DONG SAO LUU (BACKUP) ODOO & POSTGRESQL NEN ZIP HANG NGAY
# ================================================================================
# - Tu dong nen toan bo Database PostgreSQL + Tep dinh kem (Filestore) thanh file .zip.
# - TUYET DOI KHONG XOA BAT KY BAN SAO LUU NAO (Giu lai lich su vinh vien).
# - Ho tro 2 che do thong minh:
#     1. Qua Odoo Web API neu Odoo dang mo.
#     2. Tu dong chay truc tiep bang pg_dump.exe + nen filestore neu Odoo dang tat.
# ================================================================================

param(
    [string]$DbName = "odoo20",
    [string]$MasterPwd = "MatKhauMoi",
    [string]$DbUser = "odoo20",
    [string]$DbPassword = "tdb@2026",
    [string]$DbHost = "localhost",
    [int]$DbPort = 5432,
    [string]$PgDumpPath = "C:\Program Files\PostgreSQL\15\bin\pg_dump.exe",
    [string]$DataDir = "C:\odoo20\data",
    [string]$OdooUrl = "http://127.0.0.1:8080",
    [string]$BackupDir = "C:\odoo_backups"
)

# 1. Khoi tao thu muc luu tru
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
Write-Log "User DB  : $DbUser"
Write-Log "File dich: $backupFile"
Write-Log "Chinh sach: GIU LAI TOAN BO BAN SAO LUU VINH VIEN"
Write-Log "================================================================================"

# 2. Cau hinh thong tin xac thuc cho PostgreSQL (tranh loi password authentication failed)
$env:PGUSER = $DbUser
$env:PGPASSWORD = $DbPassword
$env:PGHOST = $DbHost
$env:PGPORT = "$DbPort"

# Tu dong tao file pgpass.conf cho ca User hien tai va he thong
$pgpassContent = "localhost:" + $DbPort + ":*:" + $DbUser + ":" + $DbPassword + "`r`n127.0.0.1:" + $DbPort + ":*:" + $DbUser + ":" + $DbPassword + "`r`n*:" + $DbPort + ":*:" + $DbUser + ":" + $DbPassword
$pgpassPaths = @(
    "$env:APPDATA\postgresql\pgpass.conf",
    "$env:USERPROFILE\AppData\Roaming\postgresql\pgpass.conf",
    "C:\Windows\System32\config\systemprofile\AppData\Roaming\postgresql\pgpass.conf"
)
foreach ($p in $pgpassPaths) {
    try {
        $pDir = Split-Path -Parent $p
        if (-not (Test-Path $pDir)) { New-Item -ItemType Directory -Path $pDir -Force | Out-Null }
        Set-Content -Path $p -Value $pgpassContent -Encoding ASCII -Force
    } catch {}
}

# 3. Kiem tra xem co the sao luu truc tiep bang pg_dump.exe + Filestore khong (Cuc nhanh va on dinh 100%)
$backupSuccess = $false

# Tim duong dan pg_dump neu chua dung
if (-not (Test-Path $PgDumpPath)) {
    $found = Get-ChildItem "C:\Program Files\PostgreSQL" -Recurse -Filter "pg_dump.exe" -ErrorAction SilentlyContinue | Select-Object -ExpandProperty FullName -First 1
    if ($found) { $PgDumpPath = $found }
}

if (Test-Path $PgDumpPath) {
    Write-Log "Su dung phuong thuc sao luu truc tiep (Native pg_dump + Filestore) voi: $PgDumpPath"
    $tempDir = Join-Path $env:TEMP "odoo_backup_$timestamp"
    try {
        New-Item -ItemType Directory -Path $tempDir -Force | Out-Null
        $dumpSqlPath = Join-Path $tempDir "dump.sql"

        Write-Log "Dang xuat du lieu Database bang pg_dump..."
        $procArgs = @(
            "-h", $DbHost,
            "-p", "$DbPort",
            "-U", $DbUser,
            "--no-owner",
            "-f", $dumpSqlPath,
            $DbName
        )
        $pInfo = New-Object System.Diagnostics.ProcessStartInfo
        $pInfo.FileName = $PgDumpPath
        $pInfo.Arguments = ($procArgs -join " ")
        $pInfo.EnvironmentVariables["PGPASSWORD"] = $DbPassword
        $pInfo.EnvironmentVariables["PGUSER"] = $DbUser
        $pInfo.UseShellExecute = $false
        $pInfo.RedirectStandardError = $true
        $pInfo.CreateNoWindow = $true

        $process = [System.Diagnostics.Process]::Start($pInfo)
        $stdErr = $process.StandardError.ReadToEnd()
        $process.WaitForExit()

        if ($process.ExitCode -eq 0 -and (Test-Path $dumpSqlPath)) {
            Write-Log "Xuat CSDL PostgreSQL thanh cong! Dang dong goi Filestore..."
            
            # Chep thu muc filestore vao ban backup neu ton tai
            $filestoreDir = Join-Path $DataDir "filestore\$DbName"
            if (-not (Test-Path $filestoreDir)) {
                # Thu kiem tra o AppData mac dinh
                $altFs = "$env:LOCALAPPDATA\Odoo\filestore\$DbName"
                if (Test-Path $altFs) { $filestoreDir = $altFs }
            }

            if (Test-Path $filestoreDir) {
                Write-Log "Chep tep dinh kem tu: $filestoreDir"
                $destFs = Join-Path $tempDir "filestore"
                Copy-Item -Path $filestoreDir -Destination $destFs -Recurse -Force
            }

            # Tao file manifest.json chuan Odoo
            $manifest = @{
                "odoo_dump" = "1"
                "db_name" = $DbName
                "version" = "20.0"
                "modules" = @{}
            } | ConvertTo-Json
            Set-Content -Path (Join-Path $tempDir "manifest.json") -Value $manifest -Encoding ASCII

            # Nen toan bo thu muc thanh file .zip
            Write-Log "Dang nen toan bo thanh file .ZIP..."
            if (Test-Path $backupFile) { Remove-Item $backupFile -Force }
            Compress-Archive -Path "$tempDir\*" -DestinationPath $backupFile -CompressionLevel Optimal

            if (Test-Path $backupFile) {
                $fileSizeMB = [math]::Round((Get-Item $backupFile).Length / 1MB, 2)
                Write-Log ">>> SAO LUU THANH CONG! Dung luong file: $fileSizeMB MB" "SUCCESS"
                Write-Log "File luu tai: $backupFile" "SUCCESS"
                $backupSuccess = $true
            }
        } else {
            Write-Log "Loi khi chay pg_dump: $stdErr" "WARNING"
        }
    } catch {
        Write-Log "Loi tien trinh sao luu truc tiep: $($_.Exception.Message)" "WARNING"
    } finally {
        if (Test-Path $tempDir) {
            Remove-Item -Path $tempDir -Recurse -Force -ErrorAction SilentlyContinue
        }
    }
}

# 4. Neu sao luu truc tiep chua thanh cong, thu tiep qua Odoo Web API
if (-not $backupSuccess) {
    Write-Log "Chuyen sang thu sao luu qua Odoo Web API..."
    try {
        $backupUrl = "$OdooUrl/web/database/backup"
        $body = @{
            master_pwd = $MasterPwd
            name = $DbName
            backup_format = "zip"
        }
        $response = Invoke-WebRequest -UseBasicParsing -Uri $backupUrl -Method Post -Body $body -OutFile $backupFile -TimeoutSec 7200
        if (Test-Path $backupFile) {
            $fileSizeMB = [math]::Round((Get-Item $backupFile).Length / 1MB, 2)
            if ($fileSizeMB -gt 0.05) {
                Write-Log ">>> SAO LUU QUA ODOO WEB THANH CONG! Dung luong file: $fileSizeMB MB." "SUCCESS"
                Write-Log "File luu tai: $backupFile" "SUCCESS"
                $backupSuccess = $true
            }
        }
    } catch {
        Write-Log "Loi sao luu qua Odoo Web API: $($_.Exception.Message)" "ERROR"
    }
}

Write-Log "HOAN TAT TIEN TRINH SAO LUU HANG NGAY.`n"
