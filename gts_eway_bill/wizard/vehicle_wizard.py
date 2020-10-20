from odoo import api, models, fields, _
import json


class UpdatevehicleNO(models.TransientModel):
    _name='update.vehicle.no'

    vehicle_no = fields.Char('vehicle No')
    reason = fields.Selection([('1', 'Due To Break Down'),
                                   ('2', 'Due To Transhipment'),
                                   ('3', 'Others'),
                                   ('4', 'First time'),], string='Reason')
    remark = fields.Text('Remark')


    @api.multi
    def update_vehicle(self):
        active_id = self.env.context.get('active_id')
        sale_order = self.env['sale.order'].browse(active_id)

        if sale_order.ewaybill_no:
            vehicle_dic = {
              'ewbNo': sale_order.ewaybill_no,
              'vehicleNo': sale_order.vehicle_no,
              'fromPlace': 'BANGALORE',
              'fromState': 29,
               'reasonCode': self.reason,
              'reasonRem': self.remark,
              'transDocNo ': sale_order.trans_id,
              'transDocDate ': sale_order.doc_date,
               'transMode': sale_order.transportation_mode,
               'vehicleType':sale_order.vehicle_type
            }
            data_base64 = json.dumps(vehicle_dic)
            configuration = self.env['eway.configuration'].search([])
            if configuration:
                response = configuration.generate_eway(data_base64, 'VEHEWB')
                sale_order.message_post(body=_("Vehicle Details valid from "+ response.json().get('validUpto')+ ' to'+ response.json().get('vehUpdDate')))

