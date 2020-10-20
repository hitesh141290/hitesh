from odoo import fields, models, api, _
from odoo.exceptions import UserError
import re


class EwayTransportation(models.Model):
    _name = 'eway.transportation'
    _inherit = ['mail.thread']

    name = fields.Char("Transpoter Name", track_visibility="onchange")
    transportation_mode = fields.Selection([('1', 'Road'),
                                            ('2', 'Rail'),
                                            ('3', 'Air'),
                                            ('4', 'Ship'), ], "Transportation Mode", track_visibility="onchange")
    transporter_date = fields.Date("Transportation Date", track_visibility="onchange")
    transporter_id = fields.Char("Transporter ID", track_visibility="onchange")
    transporter_doc_no = fields.Char("Transporter Document No.", track_visibility="onchange")
    email_id = fields.Char("Email ID", track_visibility="onchange")
    mobile_no = fields.Char("Mobile No", track_visibility="onchange")
    transporter_address1 = fields.Char("Street 1", track_visibility="onchange")
    transporter_address2 = fields.Char("Street 2", track_visibility="onchange")
    city = fields.Char("City", track_visibility="onchange")
    place = fields.Char("Place", track_visibility="onchange")
    zip = fields.Char("Zip", track_visibility="onchange")
    country_id = fields.Many2one('res.country', "Country", track_visibility="onchange")
    state_id = fields.Many2one('res.country.state', "State", track_visibility="onchange")

    @api.constrains('doc_date')
    def validate_transport_date(self):
        if len(self.mobile_no) != 10 and (self.mobile_no).isdigit() == False:
            raise UserError(_('Invalid Phone Number'))
        if self.email_id:
            match = re.match('^[_a-z0-9-]+(\.[_a-z0-9-]+)*@[a-z0-9-]+(\.[a-z0-9-]+)*(\.[a-z]{2,4})$', self.email_id)
            if not match:
                raise UserError(_('Invalid Email Id'))
        return True

    @api.onchange('state_id')
    def _onchange_state(self):
        if self.state_id:
            self.country_id = self.state_id.country_id.id
