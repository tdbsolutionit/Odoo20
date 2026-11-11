@echo off
echo ================================================================================
echo   NANG CAP MODULE TDB_PLM_CUSTOM CHO ODOO 20 (CSDL: ODOO20)
echo ================================================================================

echo.
echo [1/4] Dang cap nhat code moi nhat tu Git (origin/main)...
git pull origin main

echo.
echo [2/4] Tam dung container Odoo de tranh lock...
docker compose stop odoo 2>nul

echo.
echo [3/4] Dang nang cap module tdb_plm_custom vao CSDL odoo20...
docker compose run --rm odoo /opt/odoo/venv/bin/python3 /opt/odoo/src/odoo-bin -c /etc/odoo/odoo.conf -u tdb_plm_custom -i tdb_plm_custom -d odoo20 --stop-after-init

REM Nang cap du phong cho odoo20_dev neu co
docker compose run --rm odoo /opt/odoo/venv/bin/python3 /opt/odoo/src/odoo-bin -c /etc/odoo/odoo.conf -u tdb_plm_custom -i tdb_plm_custom -d odoo20_dev --stop-after-init 2>nul

echo.
echo [4/4] Dang khoi dong lai container Odoo...
docker compose start odoo 2>nul

echo.
echo ================================================================================
echo   >>> HOAN TAT NANG CAP THANH CONG CHO CSDL ODOO20! <<<
echo   1. Mo trinh duyet Web va bam Ctrl + F5 (hoac Dang xuat roi Dang nhap lai).
echo   2. Thao tac Check-out va Check-in: lich su phien ban se tu dong xuat hien!
echo ================================================================================
pause

