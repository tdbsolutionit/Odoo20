# -*- coding: utf-8 -*-
# Copyright 2026 TDB Solution Co., Ltd.
"""
Module tùy biến phân hệ PLM (Product Lifecycle Management) cho TDB Solution.
Chuẩn hóa giao diện danh sách, tiêu đề song ngữ Anh - Việt và căn lề đồng đều.
"""
import mimetypes

# Đăng ký các định dạng tệp CAD phổ biến vào hệ thống mimetypes của Python
# Giúp Odoo và trình duyệt nhận diện chính xác đuôi tệp CAD, không bị đổi thành .bin
CAD_MIMETYPES = {
    '.sldprt': 'application/vnd.solidworks.part',
    '.sldasm': 'application/vnd.solidworks.assembly',
    '.slddrw': 'application/vnd.solidworks.drawing',
    '.prt': 'application/x-prt',
    '.asm': 'application/x-asm',
    '.drw': 'application/x-drw',
    '.step': 'application/step',
    '.stp': 'application/step',
    '.iges': 'application/iges',
    '.igs': 'application/iges',
    '.dxf': 'image/vnd.dxf',
    '.dwg': 'image/vnd.dwg',
    '.ipt': 'application/vnd.autodesk.inventor.part',
    '.iam': 'application/vnd.autodesk.inventor.assembly',
    '.idw': 'application/vnd.autodesk.inventor.drawing',
    '.pdf': 'application/pdf',
}
for ext, mime in CAD_MIMETYPES.items():
    mimetypes.add_type(mime, ext)
    mimetypes.add_type(mime, ext.upper())

from . import models
from . import controllers
from . import wizard
