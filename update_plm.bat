@echo off
echo ================================================================================
echo   NANG CAP MODULE TDB_PLM_CUSTOM CHO ODOO 20 (CSDL: ODOO20)
echo ================================================================================

echo.
echo [1/3] Dang cap nhat code moi nhat tu Git (origin/main)...
git fetch origin main
git reset --hard origin/main

echo.
echo [2/3] Tam dung container Odoo de tranh lock...
docker compose stop odoo 2>nul

echo.
echo [*] Dang nang cap module tdb_plm_custom vao CSDL odoo20...
docker compose run --rm odoo /opt/odoo/venv/bin/python3 /opt/odoo/src/odoo-bin -c /etc/odoo/odoo.conf -u tdb_plm_custom -i tdb_plm_custom -d odoo20 --stop-after-init

REM Nang cap du phong cho odoo20_dev neu co
docker compose run --rm odoo /opt/odoo/venv/bin/python3 /opt/odoo/src/odoo-bin -c /etc/odoo/odoo.conf -u tdb_plm_custom -i tdb_plm_custom -d odoo20_dev --stop-after-init 2>nul

echo.
echo [3/3] Dang khoi dong lai container Odoo...
docker compose start odoo 2>nul

echo.
echo ================================================================================
echo   >>> HOAN TAT NANG CAP THANH CONG CHO CSDL ODOO20! <<<
echo   1. Mo trinh duyet Web: Dang xuat (Log out) roi Dang nhap lai (hoac Ctrl + F5).
echo   2. Tai khoan Ky su (A, B) se hoan toan KHONG con thay Desktop Access Tokens.
echo   3. Tai khoan Sếp / Administrator se thay menu Desktop Access Tokens truc tiep tren Top Bar va trong Cau hinh.
echo ================================================================================
pause
