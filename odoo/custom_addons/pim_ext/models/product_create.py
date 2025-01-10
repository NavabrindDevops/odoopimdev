# -*- coding: utf-8 -*-
import xml.etree.ElementTree as xee
from lxml import etree as xee
from odoo import models, fields, api, _
from odoo.exceptions import UserError

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

    family_id = fields.Many2one('family.attribute', string='Family')
    sku = fields.Char(string='SKU')

    def product_save(self):
        print('Saving product and creating dynamic fields...')
        # Step 1: Retrieve the view and parse it with lxml
        view_id = self.env.ref('pim_ext.view_product_template_form_inherit')
        print('Form View ID:', view_id)

        view_arch = view_id.arch_base
        print('dj333333333333', view_arch)# The XML structure of the view
        doc = xee.fromstring(view_arch)  # Parse with lxml
        print('Parsed XML Document:', doc)
        field_name = "x_test_field"
        self._create_dynamic_field(field_name)

        # Step 2: Locate the group where dynamic fields should be added
        print('dkjfkdjfkfj', doc.xpath)
        print('455555555555555', doc.xpath("//page[1]/group"))
        dynamic_fields_group = doc.xpath("//group[@name='dynamic_attributes']")
        print('Dynamic Fields Group:', dynamic_fields_group)

        if dynamic_fields_group:
            container = dynamic_fields_group[0]
            print('Dynamic Fields Container:', container)

            # Example: Adding a test field (replace with actual logic)
            field_name = "x_test_field"
            field_element = xee.Element('field', {'name': field_name})
            container.append(field_element)
            print(f"Field '{field_name}' added to the container.")

            # Save the updated XML back to the view
            view_id.write({'arch': xee.tostring(doc, pretty_print=True, encoding='unicode')})
            print('Updated Form View XML Saved.')

        return {'type': 'ir.actions.act_window', 'tag': 'reload'}

    def _create_dynamic_field(self, field_name):
        """ Creates a dynamic field in product.template if it doesn't already exist """
        # Check if the field exists in product.template
        existing_field = self.env['ir.model.fields'].search([
            ('name', '=', field_name),
            ('model', '=', 'product.template')
        ])

        if not existing_field:
            # Create the field dynamically in product.template model
            self.env['ir.model.fields'].create({
                'name': field_name,
                'model': 'product.template',
                'field_description': f"Dynamic field {field_name}",
                'ttype': 'char',  # Change the field type as needed (e.g., 'float', 'text', etc.)
                'store': True,  # Field is stored in the database
            })
            print(f"Field '{field_name}' created dynamically in product.template.")
        else:
            print(f"Field '{field_name}' already exists in product.template.")



    def product_cancel(self):
        pass

