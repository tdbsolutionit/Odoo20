-- ================================================================================
-- KỊCH BẢN TẠO CƠ SỞ DỮ LIỆU TEAMCENTER 12 (TCDB12) VÀ TÀI KHOẢN INFODBA
-- HỆ QUẢN TRỊ CSDL: MICROSOFT SQL SERVER
-- ================================================================================
-- LƯU Ý QUAN TRỌNG:
-- 1. Đảm bảo thư mục 'C:\Siemens' đã được tạo sẵn trên ổ C trước khi chạy.
-- 2. Chạy với tài khoản có quyền 'sysadmin' (ví dụ tài khoản 'sa' hoặc Windows Admin).
-- ================================================================================

USE [master]
GO

-- 1. Xóa Database cũ nếu đã tồn tại
IF EXISTS (SELECT name FROM master.dbo.sysdatabases WHERE name = N'TCDB12')
    DROP DATABASE [TCDB12]
GO

-- 2. Tạo Database TCDB12 theo chuẩn cấu hình Siemens Teamcenter
/* Do not specify a size and use the default size which matches model database */
CREATE DATABASE [TCDB12] ON (NAME = N'TC_Data', FILENAME = N'C:\Siemens\TC_Data.MDF' , FILEGROWTH = 10%),
FILEGROUP [ILOG]
( NAME = N'TC_ilog', FILENAME = N'C:\Siemens\TC_ilog.ndf' , FILEGROWTH = 10%)
 LOG ON 
(NAME = N'TC_Log', FILENAME = N'C:\Siemens\TC_Log.LDF' , FILEGROWTH = 10%)
 COLLATE Latin1_General_BIN
GO

-- 3. Cấu hình các tham số môi trường Database
ALTER DATABASE [TCDB12] SET ANSI_NULL_DEFAULT OFF 
GO
ALTER DATABASE [TCDB12] SET ANSI_NULLS OFF 
GO
ALTER DATABASE [TCDB12] SET ANSI_PADDING OFF 
GO
ALTER DATABASE [TCDB12] SET ANSI_WARNINGS OFF 
GO
ALTER DATABASE [TCDB12] SET ARITHABORT ON 
GO
ALTER DATABASE [TCDB12] SET AUTO_CLOSE OFF 
GO
ALTER DATABASE [TCDB12] SET AUTO_CREATE_STATISTICS ON 
GO
ALTER DATABASE [TCDB12] SET AUTO_SHRINK OFF 
GO
ALTER DATABASE [TCDB12] SET AUTO_UPDATE_STATISTICS ON 
GO
ALTER DATABASE [TCDB12] SET CURSOR_CLOSE_ON_COMMIT OFF 
GO
ALTER DATABASE [TCDB12] SET CURSOR_DEFAULT GLOBAL 
GO
ALTER DATABASE [TCDB12] SET CONCAT_NULL_YIELDS_NULL OFF 
GO
ALTER DATABASE [TCDB12] SET NUMERIC_ROUNDABORT OFF 
GO
ALTER DATABASE [TCDB12] SET QUOTED_IDENTIFIER ON 
GO
ALTER DATABASE [TCDB12] SET RECURSIVE_TRIGGERS OFF 
GO
ALTER DATABASE [TCDB12] SET AUTO_UPDATE_STATISTICS_ASYNC ON 
GO
ALTER DATABASE [TCDB12] SET DATE_CORRELATION_OPTIMIZATION OFF 
GO
ALTER DATABASE [TCDB12] SET PARAMETERIZATION SIMPLE 
GO
ALTER DATABASE [TCDB12] SET READ_WRITE 
GO
ALTER DATABASE [TCDB12] SET RECOVERY FULL 
GO
ALTER DATABASE [TCDB12] SET MULTI_USER 
GO
ALTER DATABASE [TCDB12] SET PAGE_VERIFY TORN_PAGE_DETECTION 
GO
ALTER DATABASE [TCDB12] SET READ_COMMITTED_SNAPSHOT ON 
GO

-- 4. Chuyển sang CSDL vừa tạo và tạo Login/User 'infodba'
USE [TCDB12]
GO

/****** Object:  Login infodba  ******/
IF NOT EXISTS (SELECT * FROM master.dbo.syslogins WHERE loginname = N'infodba')
BEGIN
    DECLARE @logindb nvarchar(132), @loginlang nvarchar(132) SELECT @logindb = N'TC', @loginlang = N'@LANGUAGE@'
    IF @logindb IS NULL OR NOT EXISTS (SELECT * FROM master.dbo.sysdatabases WHERE name = @logindb)
        SELECT @logindb = N'master'
    IF @loginlang IS NULL OR (NOT EXISTS (SELECT * FROM master.dbo.syslanguages WHERE name = @loginlang) AND @loginlang <> N'us_english')
        SELECT @loginlang = @@language
    CREATE LOGIN [infodba] WITH PASSWORD = 'infodba', CHECK_POLICY = OFF
END
GO

-- 5. Gán Server Roles cho user 'infodba'
EXEC sp_addsrvrolemember N'infodba', sysadmin
GO
EXEC sp_addsrvrolemember N'infodba', securityadmin
GO
EXEC sp_addsrvrolemember N'infodba', serveradmin
GO
EXEC sp_addsrvrolemember N'infodba', setupadmin
GO
EXEC sp_addsrvrolemember N'infodba', processadmin
GO
EXEC sp_addsrvrolemember N'infodba', diskadmin
GO
EXEC sp_addsrvrolemember N'infodba', dbcreator
GO
EXEC sp_addsrvrolemember N'infodba', bulkadmin
GO

-- 6. Gán quyền truy cập Database và Database Roles cho 'infodba'
IF NOT EXISTS (SELECT * FROM dbo.sysusers WHERE name = N'infodba' AND uid < 16382)
    EXEC sp_grantdbaccess N'infodba', N'infodba'
GO

EXEC sp_addrolemember N'db_accessadmin', N'infodba'
GO
EXEC sp_addrolemember N'db_backupoperator', N'infodba'
GO
EXEC sp_addrolemember N'db_datareader', N'infodba'
GO
EXEC sp_addrolemember N'db_datawriter', N'infodba'
GO
EXEC sp_addrolemember N'db_ddladmin', N'infodba'
GO
EXEC sp_addrolemember N'db_denydatareader', N'infodba'
GO
EXEC sp_addrolemember N'db_denydatawriter', N'infodba'
GO
EXEC sp_addrolemember N'db_owner', N'infodba'
GO
EXEC sp_addrolemember N'db_securityadmin', N'infodba'
GO
