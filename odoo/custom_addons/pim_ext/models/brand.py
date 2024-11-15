
from odoo import api, fields, models, _


class ProductBrand(models.Model):
    _name = 'product.brand'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Brand Information'
    _rec_name = 'name'



    name = fields.Char('Brand Name')
    brand_logo = fields.Image('Logo')
    description = fields.Text('Description')
    website = fields.Char("Website URL")
