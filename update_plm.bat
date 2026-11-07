@echo off
echo ================================================================================
echo   NANG CAP MODULE TDB_PLM_CUSTOM QUA DOCKER CHO TOAN BO CSDL
echo ================================================================================

echo.
echo [1/3] Tam dung container Odoo de tranh lock...
docker compose stop odoo

echo.
echo [2/3] Dang kiem tra va nang cap tren tat ca CSDL trong he thong...

REM Quet va nang cap tat ca database co trong PostgreSQL container
FOR /F "tokens=*" %%D IN ('docker compose exec -T db psql -U odoo -t -A -c "SELECT datname FROM pg_database WHERE datistemplate = false AND datname NOT IN ('postgres', 'template0', 'template1');"') DO (
    echo   - Dang nang cap module cho CSDL: %%D...
    docker compose run --rm odoo /opt/odoo/venv/bin/python3 /opt/odoo/src/odoo-bin -c /etc/odoo/odoo.conf -u custom_home_menu,tdb_plm_custom -d %%D --stop-after-init
)

echo.
echo [3/3] Dang khoi dong lai container Odoo...
docker compose start odoo

echo.
echo ================================================================================
echo   >>> HOAN TAT NANG CAP THANH CONG TREN TOAN BO CSDL! <<<
echo   1. Mo trinh duyet Odoo Web: Hay bam Ctrl + F5 de xoa cache menu.
echo   2. Hoac Dang xuat (Log out) roi Dang nhap lai.
echo   3. Menu se xuat hien ngay tren thanh cong cu PLM:
echo      PLM -^> Desktop Access Tokens
echo ================================================================================
pause
