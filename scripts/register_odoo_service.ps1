# ================================================================================
# SCRIPT DANG KY ODOO CHAY NGAM 24/7 TREN WINDOWS SERVER
# ================================================================================
# - Tu dong chay ngay khi mo may (khong can dang nhap Remote Desktop).
# - Chay ngam vinh vien (ExecutionTimeLimit = 0).
# - Tu dong bat lai ngay lap tuc neu bi crash hoac tat dot ngot.
# ================================================================================

param(
    [string]$OdooDir = "C:\odoo20\odoo",
    [string]$PythonExe = "",
    [string]$ConfigFile = "",
    [string]$TaskName = "Odoo_Server_24_7"
)

# 1. Tu dong xac dinh duong dan Python va odoo.conf
if (-not $PythonExe) {
    $venvPy = Join-Path $OdooDir ".venv\Scripts\python.exe"
    if (Test-Path $venvPy) {
        $PythonExe = $venvPy
    } else {
        $foundPy = Get-Command "python.exe" -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source -First 1
        $PythonExe = if ($foundPy) { $foundPy } else { "python.exe" }
    }
}

if (-not $ConfigFile) {
    $cfg = Join-Path $OdooDir "odoo.conf"
    $ConfigFile = if (Test-Path $cfg) { $cfg } else { "odoo.conf" }
}

$odooBin = Join-Path $OdooDir "odoo-bin"

Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "CAU HINH TIEN TRINH ODOO 24/7 WINDOWS SERVER" -ForegroundColor Cyan
Write-Host "Thu muc Odoo : $OdooDir"
Write-Host "Python       : $PythonExe"
Write-Host "Odoo Bin     : $odooBin"
Write-Host "Config       : $ConfigFile"
Write-Host "Task Name    : $TaskName"
Write-Host "================================================================================"

# 2. Dinh nghia hanh dong chay Odoo
$action = New-ScheduledTaskAction `
    -Execute $PythonExe `
    -Argument "`"$odooBin`" -c `"$ConfigFile`"" `
    -WorkingDirectory $OdooDir

# 3. Kich hoat khi he dieu hanh khoi dong (At Startup)
$trigger = New-ScheduledTaskTrigger -AtStartup

# 4. Chay duoi quyen he thong SYSTEM (hoat dong 24/7 khong can login RDP)
$principal = New-ScheduledTaskPrincipal `
    -UserId "SYSTEM" `
    -LogonType ServiceAccount `
    -RunLevel Highest

# 5. Thiet lap dac biet:
# - ExecutionTimeLimit = Zero (Chay vinh vien khong bao gio bi Windows ngat sau 3 ngay)
# - RestartCount = 999 (Tu dong khoi dong lai neu bi crash)
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -RestartCount 999 `
    -RestartInterval (New-TimeSpan -Minutes 1) `
    -ExecutionTimeLimit ([TimeSpan]::Zero) `
    -MultipleInstances IgnoreNew

# 6. Dang ky hoac cap nhat vao Windows Task Scheduler
try {
    # Neu task da ton tai, dung truoc khi cap nhat
    Stop-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue

    Register-ScheduledTask `
        -TaskName $TaskName `
        -Action $action `
        -Trigger $trigger `
        -Principal $principal `
        -Settings $settings `
        -Description "Dich vu tu dong duy tri Odoo 20 chay ngam 24/7 tren Windows Server" `
        -Force | Out-Null

    Write-Host "`n>>> DANG KY DICH VU ODOO 24/7 THANH CONG!" -ForegroundColor Green

    # Khoi dong task luon
    Start-ScheduledTask -TaskName $TaskName
    Start-Sleep -Seconds 2

    $taskInfo = Get-ScheduledTask -TaskName $TaskName
    Write-Host "Trang thai hien tai: $($taskInfo.State)" -ForegroundColor Yellow
    Write-Host "`n[HUONG DAN QUAN LY ODOO 24/7]:" -ForegroundColor Cyan
    Write-Host "- Khoi dong Odoo  : Start-ScheduledTask -TaskName `"$TaskName`""
    Write-Host "- Dung Odoo        : Stop-ScheduledTask -TaskName `"$TaskName`""
    Write-Host "- Xem trang thai   : Get-ScheduledTask -TaskName `"$TaskName`""
    Write-Host "- Mo Task Scheduler: Go 'taskschd.msc' trong Hop thoai Run.`n"
} catch {
    Write-Host "`n[LOI]: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Vui long mo PowerShell bang quyen 'Run as Administrator' roi chay lai!" -ForegroundColor Yellow
}
