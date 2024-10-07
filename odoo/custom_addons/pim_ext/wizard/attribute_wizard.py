# -*- coding: utf-8 -*-

from odoo import _, api, fields, models


class AddAttributeWizard(models.TransientModel):
    _name = 'add.attribute.wizard'
    _description = 'Attribute Wizard'

    attribute_ids = fields.Many2many('product.attribute', string='Attributes', required=True)
    attribute_family_id = fields.Many2one('family.attribute', string='Families')

    def add_attributes_to_family(self):
        print('dkfodkf')