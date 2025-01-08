# -*- coding: utf-8 -*-

from odoo import _, api, fields, models


class AttributeGroupWizard(models.TransientModel):
    _name = 'attribute.group.wizard'
    _description = 'Attribute Group Wizard'

    attribute_group_ids = fields.Many2many('attribute.group', string='Attribute Groups', required=True)
    attribute_family_id = fields.Many2one('family.attribute', string='Families')

    def apply_group_attributes(self):
        print('dkfodkf')
        family_id = self.attribute_family_id.id
        print('famileeeeeee', family_id)
        family = self.env['family.attribute'].browse(family_id)
        print('dsdsdsd', family)

        for group in self.attribute_group_ids:
            for attribute in group.attribute_group_line_ids:
                print('dlkdlfd', attribute)
                family.write({
                    'product_families_ids': [(0, 0, {
                        'attribute_id': attribute.product_attribute_id.id,
                        # 'value_ids': [(6, 0, attribute.value_ids.ids)]
                    })]
                })