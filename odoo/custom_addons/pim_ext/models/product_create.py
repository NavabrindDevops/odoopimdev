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

    master_products_ids = fields.One2many(
        'product.template',
        'product_master_id',
        string='Products'
    )

    is_invisible = fields.Boolean(default=False, string='Invisible Types')
    is_product_model_invisible = fields.Boolean(default=False, string='Invisible Types')
    is_product_grouped = fields.Boolean(default=False, string='Is Bundle')
    is_product_bundle = fields.Boolean(default=False, string='Is Grouped')

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
        print('Saving product and creating dynamic fields...')
        view_id = self.env.ref('pim_ext.view_product_template_form_inherit')
        print('viewelkflfkdf', view_id)
        view_arch = view_id.arch_base
        print('dioviewarchhhhhhhh', view_arch)
        doc = xee.fromstring(view_arch)
        print('docccccc---------->>>>>..', doc)

        attributes = self.family_id.mapped('product_families_ids').mapped('attribute_id')
        print('atributessssss-------->>>>', attributes)
        if not attributes:
            print("No attributes found for the family.")
            return

        # Group attributes by attribute group
        grouped_attributes = {}
        for attribute in attributes:
            print('dksjdhshds', attribute)
            print('ffffffffffff', attribute.attribute_group)
            group = attribute.attribute_group.name if attribute.attribute_group else "Ungrouped"
            print('groupdddddddddddddd', group)

            grouped_attributes.setdefault(group, []).append(attribute)
            print('apeendddddddddddd', grouped_attributes)

        # Locate the dynamic attributes container
        dynamic_fields_group = doc.xpath("//group[@name='dynamic_attributes']")
        print('dgyeeeeeeeeeeee', dynamic_fields_group)
        if dynamic_fields_group:
            print('fhrrrrrrrrrr')
            container = dynamic_fields_group[0]
            print('conttttttttttttaaaaaaaaa', container)

            for group_name, group_attributes in grouped_attributes.items():
                print('dkjkdjfd333333333', group_name)
                print('fjeeeeeeeeeeeeeeeeee', group_attributes)
                # Create a collapsible group for each attribute group
                collapsible_group = xee.SubElement(
                    container,
                    'group',
                    {'string': group_name, 'name': f"{group_name.replace(' ', '_').lower()}_group",
                     'collapsable': 'true'}
                )
                print('dkecolaaaaaaaaapseeeeeee', collapsible_group)
                group_invisible_condition = []
                for attribute in group_attributes:
                    print('dopatrrrrrrrrro94444444', attribute)
                    field_name = f"x_{attribute.name.replace(' ', '_').lower()}"
                    print('dkf4fieldsnameeeeeee', field_name)
                    existing_field = collapsible_group.xpath(f"./field[@name='{field_name}']")
                    print('existinffffffffff', existing_field)
                    display_type = attribute.display_type
                    print('dsdjsdhsjdhs',display_type)
                    associated_family_id = self.family_id.id
                    print('dijdkjfd', associated_family_id)
                    if associated_family_id not in group_invisible_condition:
                        group_invisible_condition.append(associated_family_id)
                    if not existing_field:
                        field_element = xee.Element('field', {'name': field_name,
                                                              'invisible': f"1 if family_id != {associated_family_id} else 0"
                                                              })
                        print('gkhhhhhhhhhhh', field_element)
                        collapsible_group.append(field_element)
                        print('or90rrrrrrrrrrrrrrrrrrrr', collapsible_group)

                    # Ensure dynamic fields are created in the model
                    self._create_dynamic_field(field_name, display_type)
            if group_invisible_condition:
                group_invisible_expr = " and ".join(
                    [f"family_id != {family_id}" for family_id in group_invisible_condition])
                collapsible_group.attrib['invisible'] = f"1 if {group_invisible_expr} else 0"
                print('Group Invisible Condition:', collapsible_group.attrib['invisible'])

            # Update the form view with the modified XML
            view_id.write({'arch': xee.tostring(doc, pretty_print=True, encoding='unicode')})
            print('Updated Form View XML Saved2222222.', view_id)
            print('archaaaaadksdsdsssssssss.', view_id.arch)

        # Create the product template
        new_product = self.env['product.template'].create({
            'name': self.sku if self.sku else 'Test',
            'default_code': self.sku if self.sku else 'Test',
            'categ_id': 1,
            'sku': self.sku,
            'family_id': self.family_id.id,
        })
        print(f"New Product Created: {new_product.name} (ID: {new_product.id})")

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'product.template',
            'view_mode': 'form',
            'res_id': new_product.id,
            'context': {'no_breadcrumbs': True,
                        'default_family_id': self.family_id.id,
                        },
            'target': 'current',
        }

    def _create_dynamic_field(self, field_name, display_type):
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
            display_type = 'float'
        if display_type == 'radio':
            print('radiooooooo')
            display_type = 'boolean'
        if display_type == 'file':
            print('fileeeeeee')
            display_type = 'binary'
        if display_type == 'image':
            print('imageeeeeeeeeeee')
            display_type = 'binary'
        if display_type == 'textarea':
            print('textareasssssss')
            display_type = 'text'
        if display_type == 'link':
            print('linkssssss')
            display_type = 'char'

        if not existing_field:
            print('fkjfdkjfdkfjd', field_name)
            print('djijdsiijds', self.env['ir.model']._get('product.template').id)
            print('44444444444444', field_name.replace('x_', ''), )
            self.env['ir.model.fields'].create({
                'name': field_name,
                'model_id': self.env['ir.model']._get('product.template').id,
                'field_description': field_name.replace('x_', ''),
                'ttype': display_type,
                'store': True,
            })
            print('ddddddddddddddd')
            print(f"Field '{field_name}' created dynamically in product.template.")
        else:
            print(f"Field '{field_name}' already exists in product.template.")

    def product_cancel(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Products',
            'res_model': 'product.template',
            'view_mode': 'kanban',
            'view_id': self.env.ref('pim_ext.view_product_management_kanban').id,
            'context': {'no_breadcrumbs': True},

        }

