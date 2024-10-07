# -*- coding: utf-8 -*-

from odoo import _, api, fields, models


class AttributeGroupWizard(models.TransientModel):
    _name = 'attribute.group.wizard'
    _description = 'Attribute Group Wizard'

    attribute_group_ids = fields.Many2many('attribute.group', string='Attribute Groups', required=True)
    attribute_family_id = fields.Many2one('family.attribute', string='Families')

    def apply_group_attributes(self):
        print('dkfodkf')