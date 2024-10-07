# -*- coding: utf-8 -*-

from odoo import models, api, fields,_


class PIMAttributeType(models.Model):
     _name = 'pim.attribute.type'
     _description = 'PIM Attribute Type'
     _rec_name = 'name'

     name = fields.Char(string="Attribute Name", default='Type')

     def action_select_date(self):
          print('date')
          self.ensure_one()
          return {
               'type': 'ir.actions.act_window',
               'name': 'Date Attribute',
               'res_model': 'product.attribute',
               'view_mode': 'form',
               'context': {
                    'default_attribute_type_id': self.id,
                    'default_display_type': 'date',
                           },
          }

     def action_select_file(self):
          print('fileeeeeeee')
          self.ensure_one()
          return {
               'type': 'ir.actions.act_window',
               'name': 'File Attribute',
               'res_model': 'product.attribute',
               'view_mode': 'form',
               'context': {
                    'default_attribute_type_id': self.id,
                    'default_display_type': 'file',
               },
          }



     def action_select_identifier(self):
          print('identifierrrrrrrrrrr')
          self.ensure_one()
          return {
               'type': 'ir.actions.act_window',
               'name': 'Identifier Attribute',
               'res_model': 'product.attribute',
               'view_mode': 'form',
               'context': {
                    'default_attribute_type_id': self.id,
                    'default_display_type': 'identifier',
               },
          }

     def action_select_image(self):
          print('imageeeeeeeeeeeeee')

          self.ensure_one()
          return {
               'type': 'ir.actions.act_window',
               'name': 'Image Attribute',
               'res_model': 'product.attribute',
               'view_mode': 'form',
               'context': {
                    'default_attribute_type_id': self.id,
                    'default_display_type': 'image',
               },
          }

     def action_select_measurement(self):
          print('measurementttttttttttt')

          self.ensure_one()
          return {
               'type': 'ir.actions.act_window',
               'name': 'Measurement Attribute',
               'res_model': 'product.attribute',
               'view_mode': 'form',
               'context': {
                    'default_attribute_type_id': self.id,
                    'default_display_type': 'measurement',
               },
          }

     def action_select_multiselect(self):
          print('mutiselectttttttttttt')
          self.ensure_one()
          return {
               'type': 'ir.actions.act_window',
               'name': 'Multi Select Attribute',
               'res_model': 'product.attribute',
               'view_mode': 'form',
               'context': {
                    'default_attribute_type_id': self.id,
                    'default_display_type': 'multi_select',
               },
          }

     def action_select_number(self):
          print('numberrrrrrrrr')
          self.ensure_one()
          return {
               'type': 'ir.actions.act_window',
               'name': 'Number Attribute',
               'res_model': 'product.attribute',
               'view_mode': 'form',
               'context': {
                    'default_attribute_type_id': self.id,
                    'default_display_type': 'number',
               },
          }

     def action_select_price(self):
          print('priceeeeeeeeeeeeeee')
          self.ensure_one()
          return {
               'type': 'ir.actions.act_window',
               'name': 'Price Attribute',
               'res_model': 'product.attribute',
               'view_mode': 'form',
               'context': {
                    'default_attribute_type_id': self.id,
                    'default_display_type': 'price',
               },
          }

     def action_select_ref_data_multi(self):
          print('reference_data_multi_selecttttt')
          self.ensure_one()
          return {
               'type': 'ir.actions.act_window',
               'name': 'Ref Data Multi Select Attribute',
               'res_model': 'product.attribute',
               'view_mode': 'form',
               'context': {
                    'default_attribute_type_id': self.id,
                    'default_display_type': 'ref_data_multi',
               },
          }

     def action_select_ref_data_simple(self):
          print('Ref_data_simple_select')
          self.ensure_one()
          return {
               'type': 'ir.actions.act_window',
               'name': 'Ref Data Simple Select Attribute',
               'res_model': 'product.attribute',
               'view_mode': 'form',
               'context': {
                    'default_attribute_type_id': self.id,
                    'default_display_type': 'ref_data_simple_select',
               },
          }

     def action_select_simple(self):
          print('Simple_selecttttttttt')
          self.ensure_one()
          return {
               'type': 'ir.actions.act_window',
               'name': 'Simple Select Attribute',
               'res_model': 'product.attribute',
               'view_mode': 'form',
               'context': {
                    'default_attribute_type_id': self.id,
                    'default_display_type': 'simple_select',
               },
          }

     def action_select_text(self):
          print('texttttttttttt')
          self.ensure_one()
          return {
               'type': 'ir.actions.act_window',
               'name': 'Text Attribute',
               'res_model': 'product.attribute',
               'view_mode': 'form',
               'context': {
                    'default_attribute_type_id': self.id,
                    'default_display_type': 'text',
               },
          }

     def action_select_text_area(self):
          print('Text_areaaaaaaaaaaaa')
          self.ensure_one()
          return {
               'type': 'ir.actions.act_window',
               'name': 'TextArea Attribute',
               'res_model': 'product.attribute',
               'view_mode': 'form',
               'context': {
                    'default_attribute_type_id': self.id,
                    'default_display_type': 'textarea',
               },
          }

     def action_select_yes_no(self):
          print('Yes_noooooooooooooo')
          self.ensure_one()
          return {
               'type': 'ir.actions.act_window',
               'name': 'yes/No Attribute',
               'res_model': 'product.attribute',
               'view_mode': 'form',
               'context': {
                    'default_attribute_type_id': self.id,
                    'default_display_type': 'yes_no',
               },
          }

