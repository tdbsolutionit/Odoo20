@echo off
chcp 65001 >nul
echo ================================================================================
echo   TDB SOLUTION - NANG CAP MODULE TDB_PLM_CUSTOM CHO ODOO 20
echo ================================================================================

echo.
echo [1/4] Dang cap nhat ma nguon moi nhat tu Git (origin/main)...
REM Sao luu file cau hinh rieng cua may cuc bo neu co (tranh bi de khi pull/reset)
if exist config\odoo.conf copy /Y config\odoo.conf config\odoo.conf.local_backup >nul

git fetch origin main
git reset --hard origin/main

REM Khoi phuc lai dung file cau hinh cua may nay
if exist config\odoo.conf.local_backup (
    copy /Y config\odoo.conf.local_backup config\odoo.conf >nul
    del config\odoo.conf.local_backup >nul
)

echo.
echo [2/4] Dang giai phong rang buoc unique cu va chuan hoa du lieu Database...
REM Gỡ bỏ ràng buộc unique 1 người cũ plm_checkout_documentid để cho phép nhiều kỹ sư cùng Check-out
docker compose exec -T db psql -U odoo -d odoo20 -c "ALTER TABLE plm_checkout DROP CONSTRAINT IF EXISTS plm_checkout_documentid; ALTER TABLE plm_checkout DROP CONSTRAINT IF EXISTS plm_checkout__documentid; ALTER TABLE plm_checkout DROP CONSTRAINT IF EXISTS plm_checkout_documentid_uniq; CREATE UNIQUE INDEX IF NOT EXISTS plm_checkout_doc_user_uniq ON plm_checkout (documentid, userid);" 2>nul
docker compose exec -T db psql -U odoo -d odoo20_dev -c "ALTER TABLE plm_checkout DROP CONSTRAINT IF EXISTS plm_checkout_documentid; ALTER TABLE plm_checkout DROP CONSTRAINT IF EXISTS plm_checkout__documentid; ALTER TABLE plm_checkout DROP CONSTRAINT IF EXISTS plm_checkout_documentid_uniq; CREATE UNIQUE INDEX IF NOT EXISTS plm_checkout_doc_user_uniq ON plm_checkout (documentid, userid);" 2>nul

REM Chuẩn hóa ghi chú Snapshot cũ trong lịch sử phiên bản thành thuật ngữ cơ khí trực quan
docker compose exec -T db psql -U odoo -d odoo20 -c "UPDATE plm_document_history SET description = REPLACE(REPLACE(REPLACE(REPLACE(description, 'Snapshot lưu tại thời điểm Check-in từ SolidWorks CAD', 'Check-in từ SolidWorks CAD'), 'Snapshot lưu tại thời điểm Check-in', 'Lưu khi Check-in bản vẽ'), 'Snapshot lưu trước khi chuyển giao Key cho', 'Lưu dự phòng trước khi chuyển Key cho'), 'Snapshot', 'Bản vẽ') WHERE description LIKE '%%Snapshot%%';" 2>nul
docker compose exec -T db psql -U odoo -d odoo20_dev -c "UPDATE plm_document_history SET description = REPLACE(REPLACE(REPLACE(REPLACE(description, 'Snapshot lưu tại thời điểm Check-in từ SolidWorks CAD', 'Check-in từ SolidWorks CAD'), 'Snapshot lưu tại thời điểm Check-in', 'Lưu khi Check-in bản vẽ'), 'Snapshot lưu trước khi chuyển giao Key cho', 'Lưu dự phòng trước khi chuyển Key cho'), 'Snapshot', 'Bản vẽ') WHERE description LIKE '%%Snapshot%%';" 2>nul

echo.
echo [3/4] Tam dung container Odoo va tien hanh nang cap module tdb_plm_custom...
docker compose stop odoo 2>nul

echo [*] Dang nang cap module vao CSDL odoo20...
docker compose run --rm odoo /opt/odoo/venv/bin/python3 /opt/odoo/src/odoo-bin -c /etc/odoo/odoo.conf -u tdb_plm_custom -i tdb_plm_custom -d odoo20 --stop-after-init

REM Nang cap du phong cho CSDL odoo20_dev neu co
echo [*] Dang nang cap module vao CSDL odoo20_dev...
docker compose run --rm odoo /opt/odoo/venv/bin/python3 /opt/odoo/src/odoo-bin -c /etc/odoo/odoo.conf -u tdb_plm_custom -i tdb_plm_custom -d odoo20_dev --stop-after-init 2>nul

echo.
echo [4/4] Dang khoi dong lai container Odoo...
docker compose start odoo 2>nul

echo.
echo ================================================================================
echo   >>> NANG CAP THANH CONG TOAN BO TINH NANG PLM MOI NHAT! <<<
echo ================================================================================
echo   1. Multi-user Check-out: Da go bo loi 'documentid must be unique'. Nhieu ky su
echo      co the cung bam Check-out tai lieu de tham chieu ban ve.
echo   2. Nut Check-out: Luon hien thi cho moi ky su chua check-out. Khi da check-out
echo      se xuat hien nut 'Huy Check-out' de giai phong tai lieu khi xem xong.
echo   3. Dieu huong chuan: Bam nut link chi tiet con hoac Assembly cha se luon mo
echo      Form view PLM day du (co anh 3D, Banner Nguoi giu Key, cac tab ky thuat).
echo   4. Lich su phien ban: Chuan hoa toan bo ghi chu 'Snapshot' cu thanh ngon ngu
echo      co khi truc quan ('Luu khi Check-in ban ve', 'Luu du phong...').
echo   5. Tai file lich su: Da dang ky duoi file CAD chuan SolidWorks (.sldprt, .sldasm).
echo   6. Ban giao / Thu hoi Key: Khong bat buoc nhap ly do.
echo ================================================================================
pause
