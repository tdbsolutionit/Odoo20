# -*- coding: utf-8 -*-
from odoo import api, models


class IrActionsActions(models.Model):
    _inherit = 'ir.actions.actions'

    @api.model
    def get_bindings(self, model_name):
        res = super().get_bindings(model_name)
        if model_name == 'sale.order' and isinstance(res, dict) and 'report' in res:
            filtered_reports = []
            for r in res['report']:
                r_name = str(r.get('name') or '')
                r_xml_id = str(r.get('xml_id') or '')
                # Loại bỏ hoàn toàn báo cáo mẫu gốc của Odoo (chỉ giữ lại Báo giá đơn hàng TDB)
                if r_xml_id == 'sale.action_report_saleorder':
                    continue
                if ('báo giá' in r_name.lower() or 'quotation' in r_name.lower()) and 'tdb' not in r_name.lower():
                    continue
                filtered_reports.append(r)
            res['report'] = filtered_reports
        return res
