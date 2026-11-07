# Set UTF-8 encoding
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "  NANG CAP MODULE TDB_PLM_CUSTOM QUA DOCKER CHO TOAN BO CSDL" -ForegroundColor Green
Write-Host "================================================================================" -ForegroundColor Cyan

Write-Host "`n[1/3] Dang tam dung container Odoo..." -ForegroundColor Yellow
docker compose stop odoo

Write-Host "`n[2/3] Dang kiem tra va nang cap tren tat ca CSDL trong PostgreSQL..." -ForegroundColor Yellow
$dbs = docker compose exec -T db psql -U odoo -t -A -c "SELECT datname FROM pg_database WHERE datistemplate = false AND datname NOT IN ('postgres', 'template0', 'template1');"
foreach ($db in $dbs) {
    $dbName = $db.Trim()
    if ($dbName) {
        Write-Host "  -> Dang nang cap module cho CSDL: $dbName..." -ForegroundColor Green
        docker compose run --rm odoo /opt/odoo/venv/bin/python3 /opt/odoo/src/odoo-bin -c /etc/odoo/odoo.conf -u custom_home_menu,tdb_plm_custom -d $dbName --stop-after-init
    }
}

Write-Host "`n[3/3] Dang khoi dong lai container Odoo..." -ForegroundColor Yellow
docker compose start odoo

Write-Host "`n================================================================================" -ForegroundColor Cyan
Write-Host "  >>> HOAN TAT NANG CAP THANH CONG! <<<" -ForegroundColor Green
Write-Host "  1. Mo trinh duyet Odoo Web: Hay bam Ctrl + F5 de xoa cache menu." -ForegroundColor Cyan
Write-Host "  2. Hoac Dang xuat (Log out) roi Dang nhap lai." -ForegroundColor Cyan
Write-Host "  3. Menu se xuat hien ngay tren thanh cong cu PLM: PLM -> Desktop Access Tokens" -ForegroundColor Green
Write-Host "================================================================================" -ForegroundColor Cyan
