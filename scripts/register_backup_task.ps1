# ================================================================================
# SCRIPT ĐĂNG KÝ LỊCH TỰ ĐỘNG CHẠY BACKUP VÀO 21:00 (9H TỐI) HÀNG NGÀY TRÊN WINDOWS
# ================================================================================
# Chạy script này dưới quyền Run as Administrator để tạo Windows Scheduled Task.
# ================================================================================

$taskName = "Odoo_Daily_Backup_21h"
$scriptPath = "C:\Work\odoo20-docker\scripts\backup_odoo.ps1"

# Kiểm tra đường dẫn script thực tế
if (-not (Test-Path $scriptPath)) {
    # Nếu đang chạy từ thư mục khác, lấy đường dẫn cùng thư mục với script này
    $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
    $candidate = Join-Path $scriptDir "backup_odoo.ps1"
    if (Test-Path $candidate) {
        $scriptPath = $candidate
    }
}

Write-Host "Đường dẫn script backup: $scriptPath" -ForegroundColor Cyan

# 1. Định nghĩa hành động chạy PowerShell ngầm
$action = New-ScheduledTaskAction `
    -Execute "PowerShell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$scriptPath`""

# 2. Định nghĩa lịch kích hoạt: 21:00 hàng ngày (9h tối)
$trigger = New-ScheduledTaskTrigger -Daily -At 9:00PM

# 3. Chạy dưới quyền SYSTEM để luôn tự động chạy dù không có user đăng nhập
$principal = New-ScheduledTaskPrincipal `
    -UserId "SYSTEM" `
    -LogonType ServiceAccount `
    -RunLevel Highest

# 4. Thiết lập tùy chọn chạy (chạy lại nếu trễ, không giới hạn pin)
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Hours 3)

# 5. Đăng ký Task vào Windows Task Scheduler
try {
    Register-ScheduledTask `
        -TaskName $taskName `
        -Action $action `
        -Trigger $trigger `
        -Principal $principal `
        -Settings $settings `
        -Description "Tu dong sao luu database va filestore Odoo 20 nen ZIP hang ngay luc 21h00" `
        -Force | Out-Null

    Write-Host "`n>>> ĐÃ ĐĂNG KÝ TASK THÀNH CÔNG!" -ForegroundColor Green
    Write-Host "Task Name : $taskName"
    Write-Host "Thời gian : 21:00 (9h tối) hàng ngày"
    Write-Host "Tài khoản : SYSTEM (hoạt động 24/7 kể cả khi máy chủ đã logout)"
    Write-Host "Kiểm tra  : Gõ 'taskschd.msc' trong Run để xem Task Scheduler.`n"
} catch {
    Write-Host "`n[LỖI] Không thể tạo Task: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "LƯU Ý: Vui lòng mở PowerShell bằng quyền 'Run as Administrator' rồi chạy lại lệnh này!" -ForegroundColor Yellow
}
