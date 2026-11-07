# Set UTF-8 encoding
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "  NANG CAP MODULE TDB_PLM_CUSTOM QUA DOCKER (CSDL: ODOO20)" -ForegroundColor Green
Write-Host "================================================================================" -ForegroundColor Cyan

Write-Host "`n[1/3] Dang tam dung container Odoo..." -ForegroundColor Yellow
docker compose stop odoo

Write-Host "`n[2/3] Dang nang cap module tdb_plm_custom vao CSDL odoo20..." -ForegroundColor Yellow
docker compose run --rm odoo /opt/odoo/venv/bin/python3 /opt/odoo/src/odoo-bin -c /etc/odoo/odoo.conf -u tdb_plm_custom -i tdb_plm_custom -d odoo20 --stop-after-init

# Du phong cho odoo20_dev
docker compose run --rm odoo /opt/odoo/venv/bin/python3 /opt/odoo/src/odoo-bin -c /etc/odoo/odoo.conf -u tdb_plm_custom -i tdb_plm_custom -d odoo20_dev --stop-after-init 2>$null

Write-Host "`n[3/3] Dang khoi dong lai container Odoo..." -ForegroundColor Yellow
docker compose start odoo

Write-Host "`n================================================================================" -ForegroundColor Cyan
Write-Host "  >>> HOAN TAT NANG CAP THANH CONG CHO CSDL ODOO20! <<<" -ForegroundColor Green
Write-Host "  1. Mo trinh duyet Odoo Web: Hay bam Ctrl + F5 de xoa cache menu." -ForegroundColor Cyan
Write-Host "  2. Hoac Dang xuat (Log out) roi Dang nhap lai." -ForegroundColor Cyan
Write-Host "  3. Menu se xuat hien ngay tren thanh cong cu PLM: PLM -> Desktop Access Tokens" -ForegroundColor Green
Write-Host "================================================================================" -ForegroundColor Cyan
