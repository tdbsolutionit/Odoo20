@echo off
echo ================================================================================
echo   NANG CAP MODULE TDB_PLM_CUSTOM CHO ODOO 20 (CSDL: ODOO20)
echo ================================================================================

echo.
echo [1/4] Dang cap nhat code moi nhat tu Git (origin/main)...
git fetch origin main
git reset --hard origin/main

echo.
echo [2/4] Tam dung container Odoo de tranh lock...
docker compose stop odoo 2>nul

echo.
echo [*] Don dep ghost menu Desktop Access Tokens tren Top Bar trong CSDL truoc khi nang cap...
docker compose exec -T db psql -U odoo -d odoo20 -c "DELETE FROM ir_ui_menu_group_rel WHERE menu_id IN (SELECT id FROM ir_ui_menu WHERE parent_id IN (SELECT res_id FROM ir_model_data WHERE module = 'plm' AND name = 'plm_menu') AND (name::text ILIKE '%%desktop%%token%%' OR name::text ILIKE '%%quản lý thiết bị%%')); DELETE FROM ir_ui_menu WHERE parent_id IN (SELECT res_id FROM ir_model_data WHERE module = 'plm' AND name = 'plm_menu') AND (name::text ILIKE '%%desktop%%token%%' OR name::text ILIKE '%%quản lý thiết bị%%'); DELETE FROM ir_model_data WHERE module = 'tdb_plm_custom' AND name = 'menu_plm_desktop_token_top';"
docker compose exec -T db psql -U odoo -d odoo20_dev -c "DELETE FROM ir_ui_menu_group_rel WHERE menu_id IN (SELECT id FROM ir_ui_menu WHERE parent_id IN (SELECT res_id FROM ir_model_data WHERE module = 'plm' AND name = 'plm_menu') AND (name::text ILIKE '%%desktop%%token%%' OR name::text ILIKE '%%quản lý thiết bị%%')); DELETE FROM ir_ui_menu WHERE parent_id IN (SELECT res_id FROM ir_model_data WHERE module = 'plm' AND name = 'plm_menu') AND (name::text ILIKE '%%desktop%%token%%' OR name::text ILIKE '%%quản lý thiết bị%%'); DELETE FROM ir_model_data WHERE module = 'tdb_plm_custom' AND name = 'menu_plm_desktop_token_top';" 2>nul

echo.
echo [3/4] Dang nang cap module tdb_plm_custom vao CSDL odoo20...
docker compose run --rm odoo /opt/odoo/venv/bin/python3 /opt/odoo/src/odoo-bin -c /etc/odoo/odoo.conf -u tdb_plm_custom -i tdb_plm_custom -d odoo20 --stop-after-init

REM Nang cap du phong cho odoo20_dev neu co
docker compose run --rm odoo /opt/odoo/venv/bin/python3 /opt/odoo/src/odoo-bin -c /etc/odoo/odoo.conf -u tdb_plm_custom -i tdb_plm_custom -d odoo20_dev --stop-after-init 2>nul

echo.
echo [*] Xac nhan don dep sau nang cap...
docker compose exec -T db psql -U odoo -d odoo20 -c "DELETE FROM ir_ui_menu_group_rel WHERE menu_id IN (SELECT id FROM ir_ui_menu WHERE parent_id IN (SELECT res_id FROM ir_model_data WHERE module = 'plm' AND name = 'plm_menu') AND (name::text ILIKE '%%desktop%%token%%' OR name::text ILIKE '%%quản lý thiết bị%%')); DELETE FROM ir_ui_menu WHERE parent_id IN (SELECT res_id FROM ir_model_data WHERE module = 'plm' AND name = 'plm_menu') AND (name::text ILIKE '%%desktop%%token%%' OR name::text ILIKE '%%quản lý thiết bị%%'); DELETE FROM ir_model_data WHERE module = 'tdb_plm_custom' AND name = 'menu_plm_desktop_token_top';"
docker compose exec -T db psql -U odoo -d odoo20_dev -c "DELETE FROM ir_ui_menu_group_rel WHERE menu_id IN (SELECT id FROM ir_ui_menu WHERE parent_id IN (SELECT res_id FROM ir_model_data WHERE module = 'plm' AND name = 'plm_menu') AND (name::text ILIKE '%%desktop%%token%%' OR name::text ILIKE '%%quản lý thiết bị%%')); DELETE FROM ir_ui_menu WHERE parent_id IN (SELECT res_id FROM ir_model_data WHERE module = 'plm' AND name = 'plm_menu') AND (name::text ILIKE '%%desktop%%token%%' OR name::text ILIKE '%%quản lý thiết bị%%'); DELETE FROM ir_model_data WHERE module = 'tdb_plm_custom' AND name = 'menu_plm_desktop_token_top';" 2>nul

echo.
echo [4/4] Dang khoi dong lai container Odoo...
docker compose start odoo 2>nul

echo.
echo ================================================================================
echo   >>> HOAN TAT NANG CAP THANH CONG CHO CSDL ODOO20! <<<
echo   1. Mo trinh duyet Web: Dang xuat (Log out) roi Dang nhap lai (hoac Ctrl + F5).
echo   2. Tai khoan Ky su se hoan toan khong con thay menu Desktop Access Tokens!
echo   3. Chi duy nhat tai khoan Administrator moi thay menu tai: PLM -> Cau hinh.
echo ================================================================================
pause
