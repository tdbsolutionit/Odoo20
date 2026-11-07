@echo off
echo ================================================================================
echo   NANG CAP MODULE TDB_PLM_CUSTOM QUA DOCKER (CSDL: ODOO20)
echo ================================================================================

echo.
echo [1/3] Tam dung container Odoo de tranh lock...
docker compose stop odoo

echo.
echo [2/3] Dang nang cap module tdb_plm_custom vao CSDL odoo20...
docker compose run --rm odoo /opt/odoo/venv/bin/python3 /opt/odoo/src/odoo-bin -c /etc/odoo/odoo.conf -u tdb_plm_custom -i tdb_plm_custom -d odoo20 --stop-after-init

REM Nâng cấp dự phòng cho odoo20_dev nếu có
docker compose run --rm odoo /opt/odoo/venv/bin/python3 /opt/odoo/src/odoo-bin -c /etc/odoo/odoo.conf -u tdb_plm_custom -i tdb_plm_custom -d odoo20_dev --stop-after-init 2>nul

echo.
echo [3/3] Dang khoi dong lai container Odoo...
docker compose start odoo

echo.
echo ================================================================================
echo   >>> HOAN TAT NANG CAP THANH CONG CHO CSDL ODOO20! <<<
echo   1. Mo trinh duyet Web va bam Ctrl + F5 (hoac Dang xuat roi Dang nhap lai).
echo   2. Menu se xuat hien ngay tren thanh cong cu PLM:
echo      PLM ^> Desktop Access Tokens
echo ================================================================================
pause

