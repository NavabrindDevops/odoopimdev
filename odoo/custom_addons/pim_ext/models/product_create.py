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

    def create_product_rec(self):
        return {
            'name': 'Product create',
            'type': 'ir.actions.act_window',
            'res_model': 'product.create.master',
            'view_mode': 'form',
            'context': {'no_breadcrumbs': True},
            'view_id': self.env.ref('pim_ext.product_creation_view_master').id,
        }

    def create_product_rec_model(self):
        pass


class ProductCreateMaster(models.Model):
    _name='product.create.master'
    _description='Product creation page'
    _rec_name = 'sku'

    family_id = fields.Many2one('family.attribute', string='Family')
    sku = fields.Char(string='SKU')

    def product_save(self):
        print('Saving product and creating dynamic fields...')
        view_id = self.env.ref('pim_ext.view_product_template_form_inherit')
        view_arch = view_id.arch_base
        doc = xee.fromstring(view_arch)

        attributes = self.family_id.mapped('product_families_ids').mapped('attribute_id')
        if not attributes:
            print("No attributes found for the family.")
            return

        # Group attributes by attribute group
        grouped_attributes = {}
        for attribute in attributes:
            print('dksjdhshds', attribute)
            print('ffffffffffff', attribute.attribute_group)
            group = attribute.attribute_group.name if attribute.attribute_group else "Ungrouped"

            grouped_attributes.setdefault(group, []).append(attribute)

        # Locate the dynamic attributes container
        dynamic_fields_group = doc.xpath("//group[@name='dynamic_attributes']")
        if dynamic_fields_group:
            container = dynamic_fields_group[0]

            for group_name, group_attributes in grouped_attributes.items():
                # Create a collapsible group for each attribute group
                collapsible_group = xee.SubElement(
                    container,
                    'group',
                    {'string': group_name, 'name': f"{group_name.replace(' ', '_').lower()}_group",
                     'collapsable': 'true'}
                )

                for attribute in group_attributes:
                    field_name = f"x_{attribute.name.replace(' ', '_').lower()}"
                    existing_field = collapsible_group.xpath(f"./field[@name='{field_name}']")
                    if not existing_field:
                        field_element = xee.Element('field', {'name': field_name})
                        collapsible_group.append(field_element)

                    # Ensure dynamic fields are created in the model
                    self._create_dynamic_field(field_name)

            # Update the form view with the modified XML
            view_id.write({'arch': xee.tostring(doc, pretty_print=True, encoding='unicode')})
            print('Updated Form View XML Saved.')

        # Create the product template
        new_product = self.env['product.template'].create({
            'name': self.sku,
            'default_code': self.sku,
            'categ_id': 1,
            'family_id': self.family_id.id,
        })
        print(f"New Product Created: {new_product.name} (ID: {new_product.id})")

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'product.template',
            'view_mode': 'form',
            'res_id': new_product.id,
            'target': 'current',
        }

    def _create_dynamic_field(self, field_name):
        """ Creates a dynamic field in product.template if it doesn't already exist """
        # Check if the field exists in product.template
        existing_field = self.env['ir.model.fields'].search([
            ('name', '=', field_name),
            ('model', '=', 'product.template')
        ])
        print('djkdjfdkjfd', existing_field)

        if not existing_field:
            print('fkjfdkjfdkfjd', field_name)
            print('djijdsiijds', self.env['ir.model']._get('product.template').id)
            print('44444444444444', field_name.replace('x_', ''), )
            self.env['ir.model.fields'].create({
                'name': field_name,
                'model_id': self.env['ir.model']._get('product.template').id,
                'field_description': field_name.replace('x_', ''),
                'ttype': 'char',
                'store': True,
            })
            print('ddddddddddddddd')
            print(f"Field '{field_name}' created dynamically in product.template.")
        else:
            print(f"Field '{field_name}' already exists in product.template.")

    def product_cancel(self):
        pass

