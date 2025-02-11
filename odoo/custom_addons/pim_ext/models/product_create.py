# -*- coding: utf-8 -*-
import xml.etree.ElementTree as xee
from lxml import etree as xee
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import json

class ProductCreate(models.Model):
    _name = 'product.create'
    _rec_name = 'name'

    name = fields.Char(string='Name')

    master_products_ids = fields.One2many(
        'product.template',
        'parent_id',
        string='Products'
    )

    is_invisible = fields.Boolean(default=False, string='Invisible Types')

    def action_back_to_product_menu(self):
        menu_id = self.env.ref('pim_ext.product_creation_menu')
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
            'params': {
                'menu_id': menu_id.id,
            },
        }

    def create_product_rec(self):
        all_product_ids = self.env['product.template'].search([], order='create_date desc').ids
        return {
            'name': 'Product create',
            'type': 'ir.actions.act_window',
            'res_model': 'product.create.master',
            'view_mode': 'form',
            'context': {'no_breadcrumbs': True,
                        'default_master_products_ids': all_product_ids,
                        'default_is_product_model_invisible': True,
                        },
            'view_id': self.env.ref('pim_ext.view_product_template_create_master_custom_form').id,
        }

    def create_product_model(self):
        all_product_ids = self.env['product.template'].search([], order='create_date desc').ids
        return {
            'name': 'Create a Product model',
            'type': 'ir.actions.act_window',
            'res_model': 'product.create.master',
            'view_mode': 'form',
            'context': {'no_breadcrumbs': True,
                        'default_master_products_ids': all_product_ids,
                        'default_is_invisible': True,
                        },
            'view_id': self.env.ref('pim_ext.view_product_template_create_master_custom_form').id,
        }

    def create_bundle_product(self):
        all_product_ids = self.env['product.template'].search([], order='create_date desc').ids
        return {
            'name': 'Create a Bundle product',
            'type': 'ir.actions.act_window',
            'res_model': 'product.create.master',
            'view_mode': 'form',
            'context': {'no_breadcrumbs': True,
                        'default_master_products_ids': all_product_ids,
                        'default_is_product_bundle': True,
                        },
            'view_id': self.env.ref('pim_ext.view_product_template_create_master_custom_form').id,
        }

    def create_grouped_product(self):
        all_product_ids = self.env['product.template'].search([], order='create_date desc').ids
        return {
            'name': 'Create a Grouped product',
            'type': 'ir.actions.act_window',
            'res_model': 'product.create.master',
            'view_mode': 'form',
            'context': {'no_breadcrumbs': True,
                        'default_master_products_ids': all_product_ids,
                        'default_is_product_grouped': True,
                        },
            'view_id': self.env.ref('pim_ext.view_product_template_create_master_custom_form').id,
        }

    def create_product_rec_model(self):
        pass


class ProductCreateMaster(models.Model):
    _name='product.create.master'
    _description='Product creation page'
    _rec_name = 'sku'

    family_id = fields.Many2one('family.attribute', string='Family')
    sku = fields.Char(string='SKU')
    name = fields.Char(string='Name')
    image = fields.Binary("Product Image", attachment=True)

    master_products_ids = fields.One2many(
        'product.template',
        'product_master_id',
        string='Products'
    )

    is_invisible = fields.Boolean(default=False, string='Invisible Types')
    is_product_model_invisible = fields.Boolean(default=False, string='Invisible Types')
    is_product_grouped = fields.Boolean(default=False, string='Is Bundle')
    is_product_bundle = fields.Boolean(default=False, string='Is Grouped')
    variant_id = fields.Many2one('family.variant.line', string='Variants',domain="[('variant_familiy_id', '=', family_id)]")



    def action_back_to_product_menu(self):
        menu_id = self.env.ref('pim_ext.product_creation_menu')
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
            'params': {
                'menu_id': menu_id.id,
            },
        }

    def product_save(self):
        for rec in self:
            family_name = rec.family_id.name
            attributes_list = []
            new_field_xml = ''

            # Get the attributes related to the current product's family (family_id)
            attributes = rec.family_id.mapped('product_families_ids').mapped('attribute_id')

            # Group attributes by their attribute_group (optional but can be helpful for UI)
            attribute_groups = {}  # This will store attributes grouped by their attribute_group.
            for attribute in attributes:
                attribute_group = attribute.attribute_group.name if attribute.attribute_group else 'Uncategorized'
                if attribute_group not in attribute_groups:
                    attribute_groups[attribute_group] = []
                attribute_groups[attribute_group].append(attribute)
                associated_family_id = rec.family_id.id  # Use the current product's family_id

            # Generate XML for each attribute group
            for group_name, group_attributes in attribute_groups.items():
                # Check if group should be invisible for the current family
                group_visible_condition = f'invisible="1 if family_id != {rec.family_id.id} else 0"'

                new_field_xml += f'<group name="{group_name}" string="{group_name}" collapsible="1" expanded="1" >'

                for attribute in group_attributes:
                    field_mandatory = attribute.is_mandatory
                    print('dskjdskjdskj', field_mandatory)
                    field_name = f"x_{attribute.name.replace(' ', '_').lower()}"
                    display_type = attribute.display_type

                    self._create_dynamic_field(field_name, field_mandatory, display_type)

                    # Add field to product template dynamically
                    attributes_list.append(field_name)

                    # Generate field XML for inclusion in the view
                    print('dskdjsdkjdsk', rec.family_id.id)
                    field_name_xml = f'<field name="{field_name}"/>'
                    new_field_xml += field_name_xml

                new_field_xml += '</group>'

            variant_notebook_xml = ''
            if rec.variant_id:
                print('dskdjskjdkf')
                variant_lines = rec.variant_id.filtered(lambda v: v.variant_familiy_id == rec.family_id)

                for variant in variant_lines:
                    for variant_rec in variant.variant_ids:
                        variant_name = variant_rec.name
                        field_name = f"x_{variant_name.replace(' ', '_').lower()}"
                        #
                        # self._create_dynamic_field(field_name, False, 'many2many')

                        # Create a notebook page for each variant
                        print('dsjhdsjhds', variant_name)
                        # variant_visible_condition = f'invisible="1 if is_variant != True else 0"'
                        variant_visible_condition = f'invisible="1 if is_variant != True or family_id != {rec.family_id.id} else 0"'
                        # variant_notebook_xml += f"""
                        #         <page string="{variant_name}" name="{field_name}_page">
                        #             <field name="attribute_line_ids">
                        #
                        #             </field>
                        #         </page>
                        # """

                        print('dkjfjfkdjfd')
                        variant_invisible_rec = f'invisible="1 if is_variant_update != True else 0"'
                        variant_notebook_xml += f"""
                                        <page string="{variant_name}" name="{field_name}_page" {variant_visible_condition}>
                                            <form>
                                                <field name="is_variant_update" invisible="1"/>
                                                <header>
                                                    <button name = "update_variant_values" string = "Add values" icon="fa-plus " type = "object" class ="btn btn-success"/>
                                                </header>                                                
                                                <sheet>
                                                    <group>
                                                        <group>
                                                            <field name="product_attr_values_id" string=""  {variant_invisible_rec} widget="many2many_tags"/>
                                                        </group>
                                                    </group>
                                                </sheet>
                                            </form>
                                            
                                        </page>
                                """
            if variant_notebook_xml:
                print('iffffffffff')
                dynamic_notebook_xml = f"""
                        <xpath expr="//notebook/page[1]" position="before">
                            <page string="Attributes" name="attributes_page" {group_visible_condition}>
                                {new_field_xml}
                            </page>
                            {variant_notebook_xml}
                        </xpath>
                    """
            else:
                print('delseeeeeee')
                dynamic_notebook_xml = f"""
                            <xpath expr="//notebook/page[1]" position="before">
                                <page string="Attributes" name="attributes_page" {group_visible_condition}>
                                    {new_field_xml}
                                </page>
                            </xpath>
                        """

            # Apply to the Default Product View
            default_view_id = self.env.ref('product.product_template_only_form_view').id
            self._update_or_create_view('sku_field_add_attribute_' + family_name.lower().replace(' ', '_'),
                                        'product.template', default_view_id, dynamic_notebook_xml)

            # Apply to the Custom Split View
            custom_view_id = self.env.ref('pim_ext.view_product_creation_split_view_custom').id
            self._update_or_create_view('sku_field_add_attribute_custom_' + family_name.lower().replace(' ', '_'),
                                        'product.template', custom_view_id, dynamic_notebook_xml)

            # Create the product record
            new_product = self.env['product.template'].create({
                'name': self.name if self.name else 'Product',
                'default_code': self.sku if self.sku else 'SKU',
                'categ_id': 1,
                'sku': self.sku,
                'is_variant': True if rec.variant_id else False,
                'variant_id': rec.variant_id.id,
                'is_update_from_attribute': True,
                'image_1920': self.image,
                'family_id': rec.family_id.id,
                # 'attribute_line_ids': [(0, 0, {
                #         'attribute_id':
                # })]
            })


            return {
                'type': 'ir.actions.act_window',
                'res_model': 'product.template',
                'view_mode': 'form',
                'res_id': new_product.id,
                'view_id': self.env.ref('pim_ext.view_product_creation_split_view_custom').id,
                'context': {'no_breadcrumbs': True, 'default_family_id': rec.family_id.id},
                'target': 'current',
            }

    def _create_dynamic_field(self, field_name, field_mandatory, display_type):
        print('dskskdjskd', field_name)
        print('dk333333333333333333', display_type)
        """ Creates a dynamic field in product.template if it doesn't already exist """
        # Check if the field exists in product.template
        existing_field = self.env['ir.model.fields'].search([
            ('name', '=', field_name),
            ('model', '=', 'product.template')
        ])
        print('djkdjfdkjfd', existing_field)
        if display_type == 'number':
            print('numberrrrrrrr')
            display_type = 'integer'
        if display_type == 'radio':
            print('radiooooooo')
            display_type = 'boolean'
        if display_type == 'file':
            print('fileeeeeee')
            display_type = 'binary'
        if display_type == 'image':
            print('imageeeeeeeeeeee')
            display_type = 'binary'

        if display_type == 'link':
            print('linkssssss')
            display_type = 'char'
        if display_type == 'identifier':
            print('identifierrrrrrr')
            display_type = 'integer'
        if display_type == 'measurement':
            print('measureeeeeeeeee')
            display_type = 'float'
        if display_type == 'multi_select':
            print('multi_selectccccccccc')
            display_type = 'many2many'
        if display_type == 'price':
            print('priceeeeeeee')
            display_type = 'float'
        if display_type == 'ref_data_multi':
            print('ref_data_multiref_data_multi')
            display_type = 'many2many'
        if display_type == 'ref_data_simple_select':
            print('ref_data_simple_selectref_data_simple_select')
            display_type = 'many2many'
        if display_type == 'simple_select':
            print('simple_selectsimple_select')
            display_type = 'many2one'
        if display_type == 'text':
            print('testttttttttttttt')
            display_type = 'char'
        if display_type == 'textarea':
            print('textareasssssss')
            display_type = 'text'
        if display_type == 'yes_no':
            print('yes_noyes_no')
            display_type = 'boolean'
        if display_type == 'pills':
            print('pillspills')
            display_type = 'many2many'
        if display_type == 'select':
            print('selectselect')
            display_type = 'selection'
        if display_type == 'color':
            print('colorcolor')
            display_type = 'char'
        if display_type == 'multi':
            print('multimulti')
            display_type = 'many2many'

        if not existing_field:
            print('fkjfdkjfdkfjd', field_name)
            print('djijdsiijds', self.env['ir.model']._get('product.template').id)
            print('44444444444444', field_name.replace('x_', ''), )
            # field_values = {
            #     'name': field_name,
            #     'model_id': self.env['ir.model']._get('product.template').id,
            #     'field_description': field_name.replace('x_', ''),  # Set field label
            #     'ttype': display_type,  # Dynamic field type
            #     'store': True,
            #     'required': field_mandatory,
            # }
            self.env['ir.model.fields'].create({
                'name': field_name,
                'model_id': self.env['ir.model']._get('product.template').id,
                'field_description': field_name.replace('x_', ''),
                'ttype': display_type,
                'store': True,
                'required': True if field_mandatory else False,
            })
            print('ddddddddddddddd')
            print(f"Field '{field_name}' created dynamically in product.template.")
        else:
            print(f"Field '{field_name}' already exists in product.template.")

    def _update_or_create_view(self, view_name, model_name, inherit_view_id, arch_value):
        model_id = self.env['ir.model'].search([('model', '=', model_name)])

        view_exist = self.env['ir.ui.view'].search([
            ('name', '=ilike', view_name),
            ('model_id', '=', model_id.id),
            ('active', 'in', [True, False])
        ])

        if view_exist:
            print('dkjkfjdkfjdj3333333')
            view_exist.arch = arch_value
        else:
            print('9033333333333333')
            self.env['ir.ui.view'].sudo().create({
                'name': view_name,
                'type': 'form',
                'model': model_name,
                'inherit_id': inherit_view_id,
                'active': True,
                'arch': arch_value,
            })

    def product_cancel(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Products',
            'res_model': 'product.template',
            'view_mode': 'kanban',
            'view_id': self.env.ref('pim_ext.view_product_management_kanban').id,
            'context': {'no_breadcrumbs': True},

        }

