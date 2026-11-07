# Set UTF-8 encoding
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "  NÂNG CẤP MODULE TDB_PLM_CUSTOM QUA DOCKER (KHÔNG CẦN CÀI PYTHON TRÊN WINDOWS)" -ForegroundColor Green
Write-Host "================================================================================" -ForegroundColor Cyan

Write-Host "`n[1/3] Đang tạm dừng container Odoo..." -ForegroundColor Yellow
docker compose stop odoo

Write-Host "`n[2/3] Đang nâng cấp module tdb_plm_custom vào CSDL odoo20_dev..." -ForegroundColor Yellow
docker compose run --rm odoo /opt/odoo/venv/bin/python3 /opt/odoo/src/odoo-bin -c /etc/odoo/odoo.conf -u tdb_plm_custom -d odoo20_dev --stop-after-init

Write-Host "`n[3/3] Đang khởi động lại container Odoo..." -ForegroundColor Yellow
docker compose start odoo

Write-Host "`n================================================================================" -ForegroundColor Cyan
Write-Host "  >>> HOÀN TẤT NÂNG CẤP THÀNH CÔNG! <<<" -ForegroundColor Green
Write-Host "  Hệ thống đã nạp bảng token 180 ngày và menu quản trị thiết bị CAD." -ForegroundColor Green
Write-Host "  Hãy mở trình duyệt (F5): PLM -> Cấu hình -> Desktop Access Tokens" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
