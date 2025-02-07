# -*- coding: utf-8 -*-

from odoo import _, api, fields, models


class AttributeVariantWizard(models.TransientModel):
    _name = 'attribute.variant.wizard'
    _description = 'Attribute Variant'

    name = fields.Char(string='Label')
    variant_ids = fields.Many2many(
        'product.attribute',
        string='Variants',
        relation='custom_product_line_variant_rels',
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
                'variant_familiy_id': family_id,
            })]
        })
        return True


class AttributeVariantValuesWizard(models.TransientModel):
    _name = 'attribute.variant.values.wizard'
    _description = 'Attribute Variant Values'

    variant_value_ids = fields.Many2many('product.attribute.value', 'product_attribute_value_rel', 'attribute_variant_value_id', 'values_id',  string='Variant values')
    product_id = fields.Many2one('product.template', string='Product')
    attribute_family_id = fields.Many2one('family.attribute', string='Families')
    variant_id = fields.Many2one('family.variant.line', string='Variant')

    def update_variant_value_rec(self):
        for rec in self:
            print('hi')
            model_id = self.env['ir.model'].search([('model', '=', 'product.template')])
            print('Model ID:', model_id)
            view_name = 'sku_field_add_attribute_custom_' + self.attribute_family_id.name.lower().replace(' ', '_')
            print('View Name:', view_name)

            view_exist = self.env['ir.ui.view'].search([
                ('name', '=', view_name),
                ('model_id', '=', model_id.id)
            ], limit=1)

            print('View Found:', view_exist)
            if not view_exist:
                print(f"View '{view_name}' not found!")
                return
            arch_tree = view_exist.arch
            print("Existing View XML:", arch_tree[:500])  # Print only first 500 characters to avoid large output
            product_variant_page = ""
            if rec.variant_id:
                for variant_rec in rec.variant_id.variant_ids:
                    variant_name = variant_rec.name
                    field_name = f"x_{variant_name.replace(' ', '_').lower()}"

                    print('Processing Variant:', variant_name)
                    print('Generated Field Name:', field_name)
                    variant_values = rec.variant_value_ids.filtered(lambda v: v.attribute_id == variant_rec)
                    print('dksjdskjds', variant_values)
                    variant_values_str = ", ".join(
                        variant_values.mapped('name'))
                    print('dksjdskjds', variant_values_str)

                    if f'name="{field_name}_page"' in arch_tree:
                        print(f"Page '{field_name}_page' found, modifying...")
                        product_variant_page += f"""
                            <xpath expr="//notebook/page[@name='{field_name}_page']" position="inside">
                                <div>
                                    <strong>Variant Values:</strong> {variant_values_str if variant_values_str else 'No values selected'}
                                </div>
                            </xpath>
                        """
                        print('dsdksjdskjds', product_variant_page)
                    else:
                        print(f"Page '{field_name}_page' NOT found in view XML, skipping...")

            if product_variant_page:
                view_exist.write({'arch': f"""<data>{arch_tree}{product_variant_page}</data>"""})
                print(" View Updated Successfully!")
                rec.product_id.write({'is_variant_values_updated': True})
                return {
                    'type': 'ir.actions.act_window',
                    'res_model': 'product.template',
                    'view_mode': 'form',
                    'res_id': rec.product_id.id,
                    'view_id': self.env.ref('pim_ext.view_product_creation_split_view_custom').id,
                    'target': 'current',
                    'context': {'no_breadcrumbs': True},
                }
            else:
                print("No valid pages found to modify. No update applied.")
        # working code
    # def update_variant_value_rec(self):
    #     for rec in self:
    #         print('hi')
    #
    #         # Get the model ID for 'product.template'
    #         model_id = self.env['ir.model'].search([('model', '=', 'product.template')])
    #         print('Model ID:', model_id)
    #
    #         # Generate the dynamic view name
    #         view_name = 'sku_field_add_attribute_custom_' + self.attribute_family_id.name.lower().replace(' ', '_')
    #         print('View Name:', view_name)
    #
    #         # Search for the existing view
    #         view_exist = self.env['ir.ui.view'].search([
    #             ('name', '=', view_name),
    #             ('model_id', '=', model_id.id)
    #         ], limit=1)
    #
    #         print('View Found:', view_exist)
    #
    #         if not view_exist:
    #             print(f"View '{view_name}' not found!")
    #             return
    #
    #         # Extract the current XML architecture
    #         arch_tree = view_exist.arch
    #         print("Existing View XML:", arch_tree[:500])  # Print only first 500 characters to avoid large output
    #
    #         # Start with an empty update XML
    #         product_variant_page = ""
    #
    #         if rec.variant_id:
    #             for variant_rec in rec.variant_id.variant_ids:
    #                 variant_name = variant_rec.name
    #                 field_name = f"x_{variant_name.replace(' ', '_').lower()}"
    #
    #                 print('Processing Variant:', variant_name)
    #                 print('Generated Field Name:', field_name)
    #
    #                 # Check if the variant page exists in the XML
    #                 if f'name="{field_name}_page"' in arch_tree:
    #                     print(f"✅ Page '{field_name}_page' found, modifying...")
    #
    #                     # Append only the needed XPath modification
    #                     product_variant_page += f"""
    #                         <xpath expr="//notebook/page[@name='{field_name}_page']" position="inside">
    #                             <div>
    #                                 <span>hello</span>
    #                             </div>
    #                         </xpath>
    #                     """
    #                 else:
    #                     print(f"Page '{field_name}_page' NOT found in view XML, skipping...")
    #
    #         # Apply changes ONLY if we have valid pages
    #         print('dksjdkjfd0933', arch_tree, product_variant_page)
    #         if product_variant_page:
    #             print('dskjhdjfhd')
    #             view_exist.write({'arch': f"""<data>{arch_tree}{product_variant_page}</data>"""})
    #             print("View Updated Successfully!")
    #
    #         else:
    #             print(" No valid pages found to modify. No update applied.")



