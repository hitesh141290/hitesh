from odoo import fields, models, api, _
from odoo.exceptions import UserError
from datetime import datetime
import requests
import json


class EwayConfiguration(models.Model):
    _name = 'eway.configuration'

    eway_url = fields.Char("Eway URL", track_visibility="onchange")
    active = fields.Boolean("Active", default=True)
    active_production = fields.Boolean("Production Active", default=False)
    asp_id = fields.Char("ASP ID", track_visibility="onchange")
    asp_password = fields.Char("Password", track_visibility="onchange")
    gstin = fields.Char("GSTIN", track_visibility="onchange")
    user_name = fields.Char("User Name", track_visibility="onchange")
    ewb_password = fields.Char("Ewb Password", track_visibility="onchange")
    access_token = fields.Char("Access Token", track_visibility="onchange")
    access_date = fields.Datetime("Access Date", track_visibility="onchange")
    action_name = fields.Char('Action Name', track_visibility="onchange")
    distance_key = fields.Char("Distance API Key")

    @api.constrains('active')
    def validate_email(self):
        active_ids = self.env['eway.configuration'].search([])
        if not len(active_ids) ==1:
            raise UserError(_('Cannot Have Multiple active Configuration'))
        return True

    @api.multi
    def toggle_active(self):
        """ Inverse the value of the field ``active`` on the records in ``self``. """
        for record in self:
            record.active = not record.active

    @api.multi
    def toggle_production(self):
        for record in self:
            record.active_production = not record.active_production


    @api.multi
    def generate_token(self, url):
        resp = requests.get(url)
        print('resp...', resp.json())
        if resp.json().get('status') == '1':
            self.access_token = resp.json().get('authtoken')
            self.access_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    @api.multi
    def generate_eway(self, data_base64=False, action_name=False):
        url = self.eway_url + 'authenticate?action=ACCESSTOKEN&aspid=' + self.asp_id + '&password=' +\
              self.asp_password + '&gstin=' + self.gstin + '&username=' + self.user_name +\
              '&ewbpwd=' + self.ewb_password
        if self.access_date:
            time1 = datetime.strptime(self.access_date, "%Y-%m-%d %H:%M:%S")
            time2 = datetime.strptime(datetime.now().strftime('%Y-%m-%d %H:%M:%S'), "%Y-%m-%d %H:%M:%S")
            diff = time2 - time1
            if diff.seconds >= 21600:
                self.generate_token(url)
        print('self.access_token...', self.access_token)
        if not self.access_token:
            self.generate_token(url)
        print('self.access_token...', self.access_token)
        resp = requests.post(self.eway_url + 'ewayapi?action=' + action_name + '&aspid=' + self.asp_id +
                             '&password=' + self.asp_password + '&gstin=' + self.gstin + '&username=' +
                             self.user_name + '&authtoken=' + self.access_token, data=data_base64)
        print('resp.......', resp, resp.json())
        return resp
