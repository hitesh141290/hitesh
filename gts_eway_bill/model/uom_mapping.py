from odoo import fields, models, api


class UomMapping(models.Model):
    _name = 'uom.mapping'

    product_uom_id= fields.Many2one('product.uom',"Uom Code")
    unit_code_id= fields.Many2one('unit.quantity.code',"Unit Quanity Code")