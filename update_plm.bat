@echo off
echo ================================================================================
echo   NANG CAP MODULE TDB_PLM_CUSTOM QUA DOCKER (KHONG CAN PYTHON TREN WINDOWS)
echo ================================================================================

echo.
echo [1/3] Tam dung container Odoo...
docker compose stop odoo

echo.
echo [2/3] Dang nang cap module tdb_plm_custom vao CSDL odoo20_dev...
docker compose run --rm odoo /opt/odoo/venv/bin/python3 /opt/odoo/src/odoo-bin -c /etc/odoo/odoo.conf -u tdb_plm_custom -d odoo20_dev --stop-after-init

echo.
echo [3/3] Dang khoi dong lai container Odoo...
docker compose start odoo

echo.
echo ================================================================================
echo   HOAN TAT NANG CAP THANH CONG!
echo   Vui long mo trinh duyet (F5) kiem tra: PLM -^> Cau hinh -^> Desktop Access Tokens
echo ================================================================================
pause
