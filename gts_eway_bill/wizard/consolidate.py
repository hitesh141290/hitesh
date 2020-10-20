from odoo import api, models, fields, _
import json
from datetime import datetime
from odoo.exceptions import UserError


class UpdatevehicleNO(models.Model):
    _name='consolidate.bill'

    transportation_mode = fields.Selection([('1', 'Road'),
                                            ('2', 'Rail'),
                                            ('3', 'Air'),
                                            ('4', 'Ship'),
                                            ], string="Transportation Mode", default='1')
    transporter_id = fields.Many2one('eway.transportation', string="Transporter")
    trans_id = fields.Char("Transporter ID")
    state_id = fields.Many2one('res.country.state', "State")
    city = fields.Char("Place")
    vehicle_no = fields.Char("Vehicle No")
    ewaybills_order_ids = fields.Many2many('sale.order', 'rel_sale_consolidate', 'sale_id', 'consolidate_id',  string="Consolidate Bill")

    @api.multi
    def generate_bill(self):
        active_id = self.env.context.get('active_id')
        sale_list =[]
        line_data =[]
        time2 = datetime.strptime(self.transporter_id.transporter_date, "%Y-%m-%d")
        consolidate_dic = {
            'fromPlace': self.city,
            'fromState': self.state_id.port_code,
            'vehicleNo': self.vehicle_no,
            'transMode': self.transportation_mode,
            'transDocN': self.trans_id,
            'transDocDate': time2.strftime('%d/%m/%Y')
        }
        for line in self.ewaybills_order_ids:
            line_dic = {
                'ewbNo': line.ewaybill_no
            }
            line_data.append(line_dic)
            sale_list.append(line.id)
        consolidate_dic.update({'tripSheetEwbBills': line_data})
        configuration = self.env['eway.configuration'].search([])
        data_base64 = json.dumps(consolidate_dic)
        print(data_base64)
        response = configuration.generate_eway(data_base64, 'GENCEWB')
        if response and response.status_code == 200:
            for sale in sale_list:
                sale_order = self.env['sale.order'].browse(sale)
                sale_order.consolidate_eway = (response.json()).get('cEwbNo')
                sale_order.conslidate_ebill_date = (response.json()).get('cEwbDate')
        else:
            raise UserError(_(response.text))
