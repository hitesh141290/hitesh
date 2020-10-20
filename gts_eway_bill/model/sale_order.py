from odoo import fields, models, api, _, tools
from odoo.exceptions import UserError
from datetime import datetime
import json
import requests
import logging

_logger = logging.getLogger(__name__)


def geo_query_address(street=None, zip=None, city=None, state=None, country=None):
    if country and ',' in country and (country.endswith(' of') or country.endswith(' of the')):
        # put country qualifier in front, otherwise GMap gives wrong results,
        # e.g. 'Congo, Democratic Republic of the' => 'Democratic Republic of the Congo'
        country = '{1} {0}'.format(*country.split(',', 1))
    return tools.ustr(', '.join(filter(None, [street,
                                              ("%s %s" % (zip or '', city or '')).strip(),
                                              state,
                                              country])))


class ResPartner(models.Model):
    _inherit = 'sale.order'

    generate_ewaybill = fields.Boolean("Generate E-Way Bill")
    eway_source = fields.Many2one('res.country.state', "Source")
    eway_destination = fields.Many2one('res.country.state', "Destination")
    supply_type = fields.Selection([('I', 'Inward'),
                                    ('O', 'Outward')], string="Supply Type", track_visibility="onchange")
    vehicle_type = fields.Selection([('R', 'Regular'),
                                     ('O', 'ODC')], string="Vechicle Type", track_visibility="onchange")

    sub_supply_type = fields.Selection([('1', 'Supply'),
                                        ('2', 'Import'),
                                        ('3', 'Export'),
                                        ('4', 'Job Work'),
                                        ('5', 'For Own Use'),
                                        ('6', 'Job Work Return'),
                                        ('7', 'Sale Return'),
                                        ('8', 'Other'),
                                        ('9', 'SKD/CDK'),
                                        ('10', 'Line Sales'),
                                        ('11', 'Recipient Not Known'),
                                        ('12', 'Exhibiation or Fairs'),
                                        ], string="Sub Supply Type", copy=False, track_visibility="onchange")
    transportation_mode = fields.Selection([('1', 'Road'),
                                            ('2', 'Rail'),
                                            ('3', 'Air'),
                                            ('4', 'Ship'),
                                            ], string="Transportation Mode", copy=False, track_visibility="onchange")
    transporter_id = fields.Many2one('eway.transportation', string="Transporter", track_visibility="onchange")
    transportation_distance = fields.Float("Distance(Km)", track_visibility="onchange")
    trans_id = fields.Char("Transporter ID", track_visibility="onchange")
    ewaybill_no = fields.Char("Eway Bill No", copy=False, track_visibility="onchange")
    vehicle_no = fields.Char("Vehicle No", track_visibility="onchange")
    document_type = fields.Selection([('INV', 'Tax Invoice'),
                                      ('BIL', 'Bill of Supply'),
                                      ('BOE', 'Bill of Entry'),
                                      ('CHL', 'Delivery Challan'),
                                      ('OTH', 'Others')], string="Document Type", copy=False,
                                     track_visibility="onchange")
    doc_date = fields.Date("Document Date", track_visibility="onchange")
    transporter_doc_no = fields.Char("Transporter Document No.", size=16, track_visibility="onchange")
    transportation_date = fields.Date('Transport Date', size=10, track_visibility="onchange")
    consolidate_id = fields.Many2one('consolidate.bill', string="Consolidate Bill", track_visibility="onchange")
    sub_type_desc = fields.Text('Sub Type Description', track_visibility="onchange")
    bill_status = fields.Selection([('not', 'Not Generated'),
                                    ('generate', 'Generated'),
                                    ('cancel', 'Cancel')], string="Bill Status", default='not',
                                   track_visibility="onchange")
    logs_details = fields.Char("Log Details", copy=False, track_visibility="onchange")

    consolidate_eway = fields.Char("Consolidate Eway-Bill No", copy=False, track_visibility="onchange")
    cancel_date = fields.Char("E-Bill Cancel Date", copy=False)
    eway_bill_date = fields.Char("Eway-Bill date", copy=False)
    valid_ebill_date = fields.Char("Eway-ValidUp", copy=False)
    conslidate_ebill_date = fields.Char("Consolidate Ebill Date", copy=False)

    @api.constrains('doc_date')
    def validate_document_date(self):
        if self.doc_date:
            if self.doc_date and datetime.strptime(self.doc_date, "%Y-%m-%d").date() > datetime.now().date():
                raise UserError(_('Document Date Cannot be greater then today'))
            return True

    @api.multi
    def update_vichel_no(self):
        return True

    @api.onchange('transporter_id')
    def _onchange_transporter_id(self):
        if self.transporter_id:
            self.trans_id = self.transporter_id.transporter_id
            self.transportation_date = self.transporter_id.transporter_date
        if self.doc_date and datetime.strptime(self.transporter_id.transporter_date,
                                               "%Y-%m-%d").date() < datetime.now().date():
            raise UserError(_('transportor Date Cannot be less then today'))

    @api.multi
    def generate_eway(self):
        line_data = []
        total_cgst = total_igst = total_sgst = 0.0
        port_other_country = self.env['res.country.state'].search([('name', 'ilike', 'OTHER COUNTRIES')])
        if self.ewaybill_no:
            raise UserError(_('You are not allow to Re-generate the Eway bill Again'))
        order_dic = {
            'supplyType': self.supply_type,
            'subSupplyType': self.sub_supply_type,
            'subSupplyDesc': ' ',
            'docType': 'INV',
            'docNo': self.name,
            'docDate': '15/12/2017',
            'fromGstin': "05AAACG1625Q1ZK",
            'fromTrdName': self.company_id.partner_id.name,
            'fromAddr1': self.company_id.partner_id.street,
            'fromAddr2': self.company_id.partner_id.street2,
            'fromPlace': self.company_id.partner_id.city,
            'fromPincode': self.company_id.partner_id.zip,
            'actFromStateCode': self.company_id.partner_id.state_id.port_code,
            'fromStateCode': self.company_id.partner_id.state_id.port_code,
            'toGstin': self.company_id.vat,
            'toTrdName': self.partner_id.name,
            'toAddr1': self.partner_id.street,
            'toAddr2': self.partner_id.street2,
            'toPlace': self.partner_id.city,
            'toPincode': self.partner_id.zip,
            'actToStateCode': self.partner_id.state_id.port_code,
            'toStateCode': self.partner_id.state_id.port_code,
            'transactionType': self.transportation_mode,
            'dispatchFromGSTIN': self.company_id.vat,
            'dispatchFromTradeName': self.company_id.partner_id.name,
            'shipToGSTIN': self.partner_shipping_id.vat,
            'shipToTradeName': self.partner_shipping_id.name,
            'otherValue': 0,
            'totalValue': self.amount_untaxed,
            'cessValue': 0,
            'cessNonAdvolValue': 0,
            'totInvValue': self.amount_total,
            'transporterId': self.transporter_id.name or '',
            'transporterName': self.transporter_id.name or '',
            'transDocNo': '',
            'transMode': self.transportation_mode,
            # 'transDistance': '656',
            'transDocDate': '',
            'vehicleNo': self.vehicle_no,
            'vehicleType': self.vehicle_type,
        }
        if self.order_line:
            for line in self.order_line:
                line_dic = {
                    'productName': line.product_id.name,
                    'productDesc': line.name,
                    'hsnCode': line.hsn_id.name,
                    'quantity': line.product_uom_qty,
                    'qtyUnit': 'BOX',
                    'cgstRate': line.cgst,
                    'sgstRate': line.sgst,
                    'igstRate': 3,
                    'cessRate': 0,
                    'cessNonAdvol': 0,
                    'taxableAmount': line.price_subtotal
                }
                total_cgst += line.cgst
                total_igst += line.igst
                total_sgst += line.sgst
                line_data.append(line_dic)
            order_dic.update(
                {'cgstValue': total_cgst, 'sgstValue': total_sgst, 'igstValue': total_igst, 'itemList': line_data})
        print('order_dic...', order_dic)
        order_dic.update({'itemList': line_data})
        configuration = self.env['eway.configuration'].search([])
        search = geo_query_address(street=self.company_id.partner_id.street, zip=self.partner_id.zip,
                                   city=self.partner_id.city, state=self.company_id.partner_id.state_id.port_code,
                                   country=self.company_id.partner_id.country_id.name)

        if configuration:
            # distance calculation
            if configuration.distance_key and self.company_id.partner_id.zip and self.partner_id.zip:

                url = "https://maps.googleapis.com/maps/api/distancematrix/json?units=imperial&origins=" + self.company_id.partner_id.zip + "&destinations=" + self.partner_id.zip + "&key=" + configuration.distance_key
                try:
                    response = requests.get(url, timeout=20.000).json()
                    if (response['status'] == 'OK'):
                        result = response.get('rows')
                        if result:
                            elements_list = response.get('rows')[0].get('elements')
                            if elements_list:
                                pre_final_list = elements_list[0]
                                if (pre_final_list.get('status') == 'OK'):
                                    final_list = (pre_final_list.get('distance')).get('value')

                                    if final_list > 1:
                                        distance_km = round(final_list * 0.001)
                                        order_dic.update(
                                            {'transDistance': distance_km})
                        else:
                            raise Warning(
                                _('Invalid JSon for th Distance:\n%s') % result)

                except Exception as e:
                    _logger.info("Exception in fetching end address: %s", e.args)

            else:
                raise UserError(_('Invalid configuration for the Distance API'))
            # for Outward
            if self.supply_type == 'O' and self.document_type == 'INV':
                if self.sub_supply_type == '1' or self.sub_supply_type == '9':
                    order_dic.update({'fromGstin': configuration.gstin,
                                      'docType': self.document_type})

                elif self.sub_supply_type == '3' and port_other_country:
                    order_dic.update({'fromGstin': configuration.gstin, 'actToStateCode': port_other_country.code,
                                      'toStateCode': port_other_country.code})

            elif self.supply_type == 'O' and self.document_type == 'BIL':
                if self.sub_supply_type == '1':
                    order_dic.update({'fromGstin': configuration.gstin,
                                      'docType': self.document_type})
                elif self.sub_supply_type == '3':
                    order_dic.update({'fromGstin': configuration.gstin, 'actToStateCode': port_other_country.code,
                                      'toStateCode': port_other_country.code,
                                      'docType': self.document_type})
                elif self.sub_supply_type == '9':
                    order_dic.update({'fromGstin': configuration.gstin, 'actToStateCode': port_other_country.code,
                                      'toStateCode': port_other_country.code,
                                      'docType': self.document_type})

            elif self.supply_type == 'O' and self.document_type == 'CHL':
                if self.sub_supply_type == '9' or self.sub_supply_type == '10' or self.sub_supply_type == '4' or self.sub_supply_type == '11':
                    order_dic.update({'fromGstin': configuration.gstin,
                                      'docType': self.document_type})
                elif self.sub_supply_type == '5':
                    order_dic.update({'fromGstin': configuration.gstin,
                                      'cgstValue': 0.0, 'sgstValue': 0.0, 'igstValue': 0.0, })
                elif self.sub_supply_type == '3' and port_other_country:
                    order_dic.update(
                        {'fromGstin': configuration.gstin, 'actToStateCode': port_other_country.code,
                         'toStateCode': port_other_country.code})

            elif self.supply_type == 'O' and self.document_type == 'OTH':
                if self.sub_supply_type == '11':
                    order_dic.update({'fromGstin': configuration.gstin,
                                      'docType': self.document_type})
                elif self.sub_supply_type == '9':

                    order_dic.update({'fromGstin': configuration.gstin,
                                      'docType': self.document_type,
                                      'subSupplyDesc': self.sub_type_desc, })

            # FOR iNWARD PROCESS

            if self.supply_type == 'I' and self.document_type == 'INV':
                if self.sub_supply_type == '1':
                    order_dic.update({'fromGstin': self.company_id.vat, 'toGstin': configuration.gstin})
                elif self.sub_supply_type == '9':
                    order_dic.update({'fromGstin': self.company_id.vat, 'toGstin': configuration.gstin})
            elif self.supply_type == 'I' and self.document_type == 'BIL':
                if self.sub_supply_type == '1':
                    order_dic.update({'fromGstin': self.company_id.vat, 'toGstin': configuration.gstin})
                elif self.sub_supply_type == '2' and port_other_country:
                    order_dic.update({'toGstin': configuration.gstin, 'fromStateCode': port_other_country.code,
                                      'actFromStateCode': port_other_country.code,
                                      'fromGstin': self.company_id.vat,
                                      'docType': self.document_type})
                elif self.sub_supply_type == '9':
                    order_dic.update({'fromGstin': self.company_id.vat, 'toGstin': configuration.gstin})
            elif self.supply_type == 'I' and self.document_type == 'BIL':
                if self.sub_supply_type == '2' and port_other_country:
                    order_dic.update({'toGstin': configuration.gstin, 'fromStateCode': port_other_country.code,
                                      'actFromStateCode': port_other_country.code, 'fromGstin': self.company_id.vat,
                                      'docType': self.document_type})
            elif self.supply_type == 'I' and self.document_type == 'OTH':
                if self.sub_supply_type == '8':
                    order_dic.update({'fromGstin': self.company_id.vat, 'toGstin': configuration.gstin,
                                      'docType': self.document_type,
                                      'subSupplyDesc': self.sub_type_desc,
                                      })
            if self.supply_type == 'I' and self.document_type == 'CHL':
                if self.sub_supply_type == '12':
                    order_dic.update({'fromGstin': self.company_id.vat, 'toGstin': configuration.gstin,
                                      'docType': self.document_type,
                                      })
                elif self.sub_supply_type == '9':
                    order_dic.update({'fromGstin': self.company_id.vat, 'toGstin': configuration.gstin})

                elif self.sub_supply_type == '6' or self.sub_supply_type == '7' or self.sub_supply_type == '5':
                    order_dic.update({'fromGstin': self.company_id.vat,
                                      'toGstin': configuration.gstin,
                                      'docType': self.document_type
                                      })
            if self.supply_type == 'I' and self.document_type == 'BOE':
                if self.sub_supply_type == '2' and port_other_country:
                    order_dic.update({'fromGstin': self.company_id.vat,
                                      'actFromStateCode': port_other_country.code,
                                      'fromStateCode': port_other_country.code, 'toGstin': configuration.gstin,
                                      'docType': self.document_type
                                      })
                elif self.sub_supply_type == '9' and port_other_country:
                    order_dic.update({'fromGstin': self.company_id.vat,
                                      'actFromStateCode': port_other_country.code,
                                      'fromStateCode': port_other_country.code, 'toGstin': configuration.gstin,
                                      'docType': self.document_type
                                      })
            print('order_dic final..+++++++++++++++++++++++++..', order_dic)
            data_base64 = json.dumps(order_dic)
            response = configuration.generate_eway(data_base64, 'GENEWAYBILL')
            if response.status_code == 200:
                self.ewaybill_no = response.json().get('ewayBillNo')
                self.eway_bill_date = response.json().get('ewayBillDate')
                self.valid_ebill_date = response.json().get('validUpto')
                self.bill_status = 'generate'
                self.logs_details = ""
            else:
                self.logs_details = (response.json().get('error')).get('message')
