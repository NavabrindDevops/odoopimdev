# -*- coding: utf-8 -*-

from odoo import _, api, fields, models


class AddAttributeWizard(models.TransientModel):
    _name = 'add.attribute.wizard'
    _description = 'Attribute Wizard'

    attribute_ids = fields.Many2many('product.attribute', string='Attributes', required=True)
    attribute_family_id = fields.Many2one('family.attribute', string='Families')

    def add_attributes_to_family(self):
        print('dkfodkf')
        family_id = self.attribute_family_id.id
        print('famileeeeeee', family_id)
        family = self.env['family.attribute'].browse(family_id)
        print('dsdsdsd', family)

        for attribute in self.attribute_ids:
            print('dlkdlfd', attribute)
            family.write({
                'product_families_ids': [(0, 0, {
                    'attribute_id': attribute.id,
                })]
            })