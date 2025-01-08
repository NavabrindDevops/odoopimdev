# -*- coding: utf-8 -*-

from odoo import _, api, fields, models


class AttributeVariantWizard(models.TransientModel):
    _name = 'attribute.variant.wizard'
    _description = 'Attribute Variant'

    name = fields.Char(string='Label')
    variant_ids = fields.Many2many(
        'product.product',
        string='Product Variants',
        relation='custom_product_line_variant_rel',
        column1='custom_line_id',
        column2='variant_id',
    )
    attribute_family_id = fields.Many2one('family.attribute', string='Families')

    # def add_attributes_variant_to_family(self):
    #     print('dkfodkf')
    #     family_id = self.attribute_family_id.id
    #     print('dw33333', family_id)
    #     family = self.env['family.attribute'].browse(family_id)
    #     print('22222222', family)
    #
    #     for variant in self.variant_ids:
    #         print('variantwwwwww', variant)
    #         family.write({
    #             'variant_line_ids': [(0, 0, {
    #                 'variant_id': variant.id,
    #             })]
    #         })

    def add_attributes_variant_to_family(self):
        print('dkfodkf')
        family_id = self.attribute_family_id.id
        print('Selected Family ID:', family_id)

        family = self.env['family.attribute'].browse(family_id)
        print('Family Record:', family)
        variants_to_add = [(4, variant.id) for variant in self.variant_ids]
        print('Variants to Add:', variants_to_add)
        family.write({
            'variant_line_ids': [(0, 0, {
                'name': self.name,
                'variant_ids': variants_to_add,
            })]
        })
        return True
