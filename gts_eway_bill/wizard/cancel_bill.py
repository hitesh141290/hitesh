from odoo import fields, models, api, _
from odoo.exceptions import UserError
import json


class EbillCancel(models.Model):
    _name='ebill.cancel'

    reason = fields.Selection([('1', 'Due To Break Down'),
                               ('2', 'Due To Transhipment'),
                               ('3', 'Others'),
                               ('4', 'First time'), ], string='Reason')
    remark = fields.Text('Remark')

    @api.multi
    def cancel_bill(self):
        active_id = self.env.context.get('active_id')
        sale_order_id = self.env['sale.order'].browse(active_id)
        if sale_order_id.cancel_date:
            raise UserError(_('This Bill is already Cancelled'))
        if not sale_order_id.ewaybill_no:
            raise UserError(_('Eway Bill No Not Exits'))
        cancel_dic ={
            'ewbNo': sale_order_id.ewaybill_no,
            'cancelRsnCode': self.reason,
            'cancelRmrk': self.remark
        }
        configuration = self.env['eway.configuration'].search([])
        data_base64 = json.dumps(cancel_dic)
        response = configuration.generate_eway(data_base64, 'CANEWB')
        if response and response.status_code == 200:
            sale_order_id.cancel_date = (response.json().get('cancelDate'))
            sale_order_id.bill_status ='cancel'
        else:
            raise UserError(_(response.text))

