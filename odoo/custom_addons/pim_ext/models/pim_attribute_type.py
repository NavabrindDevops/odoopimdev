# -*- coding: utf-8 -*-

from odoo import models, api, fields,_


class PIMAttributeType(models.Model):
     _name = 'pim.attribute.type'
     _description = 'PIM Attribute Type'
     _rec_name = 'name'

     name = fields.Char(string="Attribute Name", default=' ')
     type_name = fields.Char(string="Attribute Type Name")
     attribute_ids = fields.One2many('product.attribute', 'attribute_types_id', string='Attributes')
     is_invisible=fields.Boolean(default=False, string='Invisible Types')
     attribute_group = fields.Many2one('attribute.group', string='Attribute Group', tracking=True)

     display_type = fields.Selection(
          selection=[
               ('radio', 'Radio'),
               ('date', 'Date'),
               ('file', 'File'),
               ('identifier', 'Identifier'),
               ('image', 'Image'),
               ('measurement', 'Measurement'),
               ('multi_select', 'Multi Select'),
               ('number', 'Number'),
               ('price', 'Price'),
               ('ref_data_multi', 'Reference Data Multi Select'),
               ('ref_data_simple_select', 'Reference Data Simple Select'),
               ('simple_select', 'Simple Select'),
               ('text', 'Text'),
               ('textarea', 'Text Area'),
               ('yes_no', 'Yes/No'),
               ('pills', 'Pills'),
               ('select', 'Select'),
               ('color', 'Color'),
               ('multi', 'Multi-checkbox (option)'),
          ],
          help="The display type used in the Product Configurator.")

     def create_attributes(self):
          for rec in self:
               res = self.env['product.attribute'].create({
                    'name': rec.name,
                    'display_type': rec.display_type,
                    'attribute_group': rec.attribute_group.id,
                    'value_ids': [(0, 0, {
                         'name': 'test',
                    })]
               })
          return{
               'type': 'ir.actions.act_window',
               'res_model': 'product.attribute',
               'view_mode':'tree,form',
               'target': 'current',
               'context': {'no_breadcrumbs': True},
          }


     def action_select_date(self):
          self.ensure_one()
          return {
               'type': 'ir.actions.act_window',
               'name': 'Date Attribute',
               'res_model': 'pim.attribute.type',
               'view_id': self.env.ref('pim_ext.view_product_attribute_custom').id,
               'view_mode': 'form',
               'context': {
                    # 'default_attribute_type_id': self.id,
                    'default_attribute_ids': self.env['product.attribute'].search([]).ids,
                    'default_display_type': 'date',
                    'default_is_invisible': True,
                    'default_type_name': 'Date',
                           },
          }

     def action_select_file(self):
          self.ensure_one()
          return {
               'type': 'ir.actions.act_window',
               'name': 'File Attribute',
               'res_model': 'pim.attribute.type',
               'view_id': self.env.ref('pim_ext.view_product_attribute_custom').id,
               'view_mode': 'form',
               'context': {
                    'default_attribute_ids': self.env['product.attribute'].search([]).ids,
                    'default_is_invisible': True,
                    'default_display_type': 'file',
                    'default_type_name': 'File',

               },
          }



     def action_select_identifier(self):
          self.ensure_one()
          return {
               'type': 'ir.actions.act_window',
               'name': 'Identifier Attribute',
               'res_model': 'pim.attribute.type',
               'view_id': self.env.ref('pim_ext.view_product_attribute_custom').id,
               'view_mode': 'form',
               'context': {
                    'default_attribute_ids': self.env['product.attribute'].search([]).ids,
                    'default_is_invisible': True,
                    'default_display_type': 'identifier',
                    'default_type_name': 'Identifier',
               },
          }

     def action_select_image(self):
          self.ensure_one()
          return {
               'type': 'ir.actions.act_window',
               'name': 'Image Attribute',
               'res_model': 'pim.attribute.type',
               'view_id': self.env.ref('pim_ext.view_product_attribute_custom').id,
               'view_mode': 'form',
               'context': {
                    'default_attribute_ids': self.env['product.attribute'].search([]).ids,
                    'default_is_invisible': True,
                    'default_display_type': 'image',
                    'default_type_name': 'Image',
               },
          }

     def action_select_measurement(self):
          self.ensure_one()
          return {
               'type': 'ir.actions.act_window',
               'name': 'Measurement Attribute',
               'res_model': 'pim.attribute.type',
               'view_id': self.env.ref('pim_ext.view_product_attribute_custom').id,
               'view_mode': 'form',
               'context': {
                    'default_attribute_ids': self.env['product.attribute'].search([]).ids,
                    'default_is_invisible': True,
                    'default_display_type': 'measurement',
                    'default_type_name': 'Measurement',
               },
          }

     def action_select_multiselect(self):
          self.ensure_one()
          return {
               'type': 'ir.actions.act_window',
               'name': 'Multi Select Attribute',
               'res_model': 'pim.attribute.type',
               'view_id': self.env.ref('pim_ext.view_product_attribute_custom').id,
               'view_mode': 'form',
               'context': {
                    'default_attribute_ids': self.env['product.attribute'].search([]).ids,
                    'default_is_invisible': True,
                    'default_display_type': 'multi_select',
                    'default_type_name': 'Multi_select',
               },
          }

     def action_select_number(self):
          self.ensure_one()
          return {
               'type': 'ir.actions.act_window',
               'name': 'Number Attribute',
               'res_model': 'pim.attribute.type',
               'view_id': self.env.ref('pim_ext.view_product_attribute_custom').id,
               'view_mode': 'form',
               'context': {
                    'default_attribute_ids': self.env['product.attribute'].search([]).ids,
                    'default_is_invisible': True,
                    'default_display_type': 'number',
                    'default_type_name': 'Number',
               },
          }

     def action_select_price(self):
          self.ensure_one()
          return {
               'type': 'ir.actions.act_window',
               'name': 'Price Attribute',
               'res_model': 'pim.attribute.type',
               'view_id': self.env.ref('pim_ext.view_product_attribute_custom').id,
               'view_mode': 'form',
               'context': {
                    'default_attribute_ids': self.env['product.attribute'].search([]).ids,
                    'default_is_invisible': True,
                    'default_display_type': 'price',
                    'default_type_name': 'Price',
               },
          }

     def action_select_ref_data_multi(self):
          self.ensure_one()
          return {
               'type': 'ir.actions.act_window',
               'name': 'Ref Data Multi Select Attribute',
               'res_model': 'pim.attribute.type',
               'view_id': self.env.ref('pim_ext.view_product_attribute_custom').id,
               'view_mode': 'form',
               'context': {
                    'default_attribute_ids': self.env['product.attribute'].search([]).ids,
                    'default_is_invisible': True,
                    'default_display_type': 'ref_data_multi',
                    'default_type_name': 'Ref Data Multi Select Attribute',
               },
          }

     def action_select_ref_data_simple(self):
          self.ensure_one()
          return {
               'type': 'ir.actions.act_window',
               'name': 'Ref Data Simple Select Attribute',
               'res_model': 'pim.attribute.type',
               'view_id': self.env.ref('pim_ext.view_product_attribute_custom').id,
               'view_mode': 'form',
               'context': {
                    'default_attribute_ids': self.env['product.attribute'].search([]).ids,
                    'default_is_invisible': True,
                    'default_display_type': 'ref_data_simple_select',
                    'default_type_name': 'Ref Data Simple Select Attribute',
               },
          }

     def action_select_simple(self):
          self.ensure_one()
          return {
               'type': 'ir.actions.act_window',
               'name': 'Simple Select Attribute',
               'res_model': 'pim.attribute.type',
               'view_id': self.env.ref('pim_ext.view_product_attribute_custom').id,
               'view_mode': 'form',
               'context': {
                    'default_attribute_ids': self.env['product.attribute'].search([]).ids,
                    'default_is_invisible': True,
                    'default_display_type': 'simple_select',
                    'default_type_name': 'Simple Select Attribute',
               },
          }

     def action_select_text(self):
          self.ensure_one()
          return {
               'type': 'ir.actions.act_window',
               'name': 'Text Attribute',
               'res_model': 'pim.attribute.type',
               'view_id': self.env.ref('pim_ext.view_product_attribute_custom').id,
               'view_mode': 'form',
               'context': {
                    'default_attribute_ids': self.env['product.attribute'].search([]).ids,
                    'default_is_invisible': True,
                    'default_display_type': 'text',
                    'default_type_name': 'Text Attribute',
               },
          }

     def action_select_text_area(self):
          self.ensure_one()
          return {
               'type': 'ir.actions.act_window',
               'name': 'TextArea Attribute',
               'res_model': 'pim.attribute.type',
               'view_id': self.env.ref('pim_ext.view_product_attribute_custom').id,
               'view_mode': 'form',
               'context': {
                    'default_attribute_ids': self.env['product.attribute'].search([]).ids,
                    'default_is_invisible': True,
                    'default_display_type': 'textarea',
                    'default_type_name': 'TextArea',
               },
          }

     def action_select_yes_no(self):
          self.ensure_one()
          return {
               'type': 'ir.actions.act_window',
               'name': 'yes/No Attribute',
               'res_model': 'pim.attribute.type',
               'view_id': self.env.ref('pim_ext.view_product_attribute_custom').id,
               'view_mode': 'form',
               'context': {
                    'default_attribute_ids': self.env['product.attribute'].search([]).ids,
                    'default_is_invisible': True,
                    'default_display_type': 'yes_no',
                    'default_type_name': 'yes/No',
               },
          }

