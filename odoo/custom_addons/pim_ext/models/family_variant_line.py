# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class FamilyVariantLine(models.Model):
    _name = 'family.variant.line'
    _description = 'Family Variants'

    variant_familiy_id = fields.Many2one('family.attribute', string='Family')

    variant_id = fields.Many2one('product.product', "Product Variant", index=True, ondelete='cascade')
    name = fields.Char(string='Label')
    variant_ids = fields.Many2many('product.product', string='Variants')