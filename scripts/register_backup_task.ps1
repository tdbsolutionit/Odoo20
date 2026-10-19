# ================================================================================
# SCRIPT DANG KY LICH TU DONG CHAY BACKUP VAO 21:00 (9H TOI) HANG NGAY TREN WINDOWS
# ================================================================================
# Chay script nay duoi quyen Run as Administrator de tao Windows Scheduled Task.
# ================================================================================

$taskName = "Odoo_Daily_Backup_21h"

# Tu dong xac dinh duong dan file backup_odoo.ps1 cung thu muc
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not $scriptDir) {
    $scriptDir = (Get-Location).Path
}
$scriptPath = Join-Path $scriptDir "backup_odoo.ps1"

if (-not (Test-Path $scriptPath)) {
    # Thu kiem tra o thu muc con scripts
    $subPath = Join-Path $scriptDir "scripts\backup_odoo.ps1"
    if (Test-Path $subPath) {
        $scriptPath = $subPath
    }
}

Write-Host "Duong dan script backup: $scriptPath" -ForegroundColor Cyan

# 1. Dinh nghia hanh dong chay PowerShell ngam
$action = New-ScheduledTaskAction `
    -Execute "PowerShell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$scriptPath`""

# 2. Dinh nghia lich kich hoat: 21:00 hang ngay (9h toi)
$trigger = New-ScheduledTaskTrigger -Daily -At 9:00PM

# 3. Chay duoi quyen SYSTEM de luon tu dong chay du khong co user dang nhap
$principal = New-ScheduledTaskPrincipal `
    -UserId "SYSTEM" `
    -LogonType ServiceAccount `
    -RunLevel Highest

# 4. Thiet lap tuy chon chay (chay lai neu tre, khong gioi han pin)
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Hours 3)

# 5. Dang ky Task vao Windows Task Scheduler
try {
    Register-ScheduledTask `
        -TaskName $taskName `
        -Action $action `
        -Trigger $trigger `
        -Principal $principal `
        -Settings $settings `
        -Description "Tu dong sao luu database va filestore Odoo 20 nen ZIP hang ngay luc 21h00" `
        -Force | Out-Null

    Write-Host "`n>>> DA DANG KY TASK THANH CONG!" -ForegroundColor Green
    Write-Host "Task Name : $taskName"
    Write-Host "Thoi gian : 21:00 (9h toi) hang ngay"
    Write-Host "Tai khoan : SYSTEM (hoat dong 24/7 ke ca khi may chu da logout)"
    Write-Host "Kiem tra  : Go 'taskschd.msc' trong Run de xem Task Scheduler.`n"
} catch {
    Write-Host "`n[LOI] Khong the tao Task: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "LUU Y: Vui long mo PowerShell bang quyen 'Run as Administrator' roi chay lai lenh nay!" -ForegroundColor Yellow
}
