# -*- coding: utf-8 -*-

import time,pytz
import re
from datetime import datetime,timedelta,timezone,date
from email.policy import default
from markupsafe import Markup

from lxml import etree
from odoo import models, api, fields,_
# from odoo.addons.test_impex.models import field
from odoo.exceptions import UserError, ValidationError
import traceback,pdb,inspect

from odoo.tools import drop_view_if_exists
import logging
from googletrans import Translator
_logger = logging.getLogger(__name__)



class AttributeForm(models.Model):
     _inherit = 'product.attribute'
     _rec_name = 'name'

     display_type = fields.Selection(
          selection=[
               ('radio', 'Radio'),
               ('date', 'Date'),
               ('file', 'File'),
               ('identifier', 'Identifier'),
               ('image', 'Image'),
               # ('measurement', 'Measurement'),
               ('multi_select', 'Multi Select'),
               ('multi_checkbox', 'Multi Checkbox'),
               ('link', 'Link'),
               ('number', 'Integer'),
               ('price', 'Price'),
               ('ref_data_multi', 'Reference Data Multi Select'),
               ('ref_data_simple_select', 'Reference Data Simple Select'),
               ('simple_select', 'Simple Select'),
               ('text', 'Text'),
               ('textarea', 'Text Area'),
               ('yes_no', 'Checkbox'),
               ('pills', 'Pills'),
               ('select', 'Select'),
               ('color', 'Color'),
               ('multi', 'Multi-checkbox (option)'),
          ],
          required=True,
          help="The display type used in the Product Configurator.")
     attribute_group = fields.Many2one('attribute.group', string='Attribute Group', tracking=True)
     attribute_type_id = fields.Many2one('pim.attribute.type', string='PIM Attribute Type')
     is_mandatory = fields.Boolean(string='Mandatory', default=False)
     is_required_in_clone = fields.Boolean(string='Required in Clone', default=True)
     is_cloning = fields.Boolean(string='Cloning', default=True)
     is_completeness = fields.Boolean(string='Completeness')
     original_name = fields.Char('Previous Name')

     attribute_types = fields.Selection([('basic', 'Basic'),
                                         ('optional', 'Optional')], string='Attribute Type')
     attribute_types_id = fields.Many2one('pim.attribute.type', string='Attribute Type')
     completed_in_percent = fields.Float('Completed Progressbar',compute="_compute_completness")
     state = fields.Selection([('unpublish', 'Unpublish'), ('publish', 'Publish')], string='Status', default='unpublish')


     position_ref_field_id = fields.Many2one("ir.model.fields", string="Position After", domain="[('model_id.model','=','product.management')]")

     code = fields.Char(string='Code')

     unique_value = fields.Selection(
          [('yes', 'Yes'), ('no', 'No')],
          string='Unique Value',
     )

     value_per_channel = fields.Selection(
          [('yes', 'Yes'), ('no', 'No')],
          string='Value per channel',
     )

     value_per_locale = fields.Selection(
          [('yes', 'Yes'), ('no', 'No')],
          string='Value per locale',
     )

     usable_in_grid = fields.Selection(
          [('yes', 'Yes'), ('no', 'No')],
          string='Usable in grid',
     )

     locale_specific = fields.Selection(
          [('yes', 'Yes'), ('no', 'No')],
          string='Locale specific',
     )

     master_attribute_ids = fields.One2many(
          'product.attribute',
          'parent_id',
          compute='_compute_master_attribute_ids',
          string='Attributes'
     )

     parent_id = fields.Many2one(
          'product.attribute',
          string='Parent Group',
          ondelete='cascade',
     )

     label_transaltion = fields.Char(string='English', compute="_compute_label_attribute_translation")

     user_id = fields.Many2one('res.users', string="User", default=lambda self: self.env.user)

     history_log = fields.Text(string='', help="This field stores the history of changes.")

     old_name = fields.Char(string="Old Name", readonly=True)
     new_name = fields.Char(string="New Name", readonly=True)
     old_code = fields.Char(string="Old Code", readonly=True)
     new_code = fields.Char(string="New Code", readonly=True)

     @api.depends('name')
     def _compute_label_attribute_translation(self):
          translator = Translator()
          for record in self:
               if record.name:
                    try:
                         user_lang = self.env.user.lang
                         lang_rec = self.env['res.lang'].search([('code', '=', user_lang)], limit=1)
                         src_lang = lang_rec.url_code
                         translation = translator.translate(record.name, src=src_lang, dest='en')
                         record.label_transaltion = translation.text.capitalize()
                    except Exception as e:
                         record.label_transaltion = 'Error in translation'
               else:
                    record.label_transaltion = ''

     # this is for loading tree view in while click edit button
     def _compute_master_attribute_ids(self):
          for record in self:
               record.master_attribute_ids = self.env['product.attribute'].search([])

     def save_attributes(self):
          return {
               'type': 'ir.actions.act_window',
               'view_mode': 'form',
               'res_model': 'product.attribute',
               'view_id': self.env.ref('pim_ext.view_product_attribute_master_custom').id,
               'res_id': self.id,
               'context': {'no_breadcrumbs': True},
               'target': 'current',
          }

     # attribute master edit button
     def attribute_edit_open_form_view(self):
          self.ensure_one()
          return {
               'type': 'ir.actions.act_window',
               'name': 'Edit Attribute',
               'res_model': 'product.attribute',
               'view_mode': 'form',
               'view_id': self.env.ref('pim_ext.view_product_attribute_master_custom').id,
               'context': {'no_breadcrumbs': True},
               'res_id': self.id,
          }

     # delete button attribute
     def attribute_master_unlink(self):
          return {
               'name': 'Confirm Deletion',
               'type': 'ir.actions.act_window',
               'res_model': 'attribute.master.unlink.wizard',
               'view_mode': 'form',
               'target': 'new',
               'context': {'default_attribute_id': self.id},
          }

     def action_back_to_attribute_menu(self):
          menu_id = self.env.ref('pim_ext.menu_pim_attribute_action')
          return {
               'type': 'ir.actions.client',
               'tag': 'reload',
               'params': {
                    'menu_id': menu_id.id,
               },
          }


     def action_publish_attribute(self):
          for record in self:
               if not record.attribute_group:
                    raise ValidationError("Alert!! Please select the group of the '%s' attribute." % record.name)
               if record.state == 'unpublish':
                    if record.name:
                         field_name = f"x_{record.name.strip().replace(' ', '_').lower()}"
                         field_type = None
                         field_data = {}
                         if record.display_type == 'text':
                              field_type = 'char'
                         elif record.display_type == 'textarea':
                              field_type = 'text'
                         elif record.display_type == 'number':
                              field_type = 'integer'
                         elif record.display_type == 'file':
                              field_type = 'binary'
                         elif record.display_type == 'image':
                              field_type = 'binary'
                         elif record.display_type == 'simple_select':
                              field_type = 'selection'
                         elif record.display_type == 'date':
                              field_type = 'date'
                         if not field_type:
                              continue

                         field_data.update({
                              'name': field_name,
                              'field_description': record.name,
                              'ttype': field_type,
                              'model_id': self.env.ref('pim_ext.model_product_management').id,
                              'state': 'manual',
                         })
                         create_field = self.env['ir.model.fields'].create(field_data)
                         if field_type == 'selection' and record.value_ids:
                              for value in record.value_ids:
                                   sel_value = value.name.strip().replace(' ', '_').lower()
                                   sel_name = value.name
                                   self.env['ir.model.fields.selection'].create({
                                        'name': sel_name,
                                        'value': sel_value,
                                        'field_id': create_field.id
                                   })
                         view = self.env.ref('pim_ext.product_managemnt_form_view')
                         widget = "image" if record.display_type == "image" else ""
                         widget_attribute = f' widget="{widget}"' if widget else ""
                         new_field_xml = f'<field name="{field_name}"{widget_attribute}  required="False"/>'
                         arch_value = f"""
                         <xpath expr="//field[@name='{self.position_ref_field_id.name}']" position="after">
                             {new_field_xml}
                         </xpath>
                         """
                         self.env['ir.ui.view'].sudo().create({
                              'name': f'add_field_{field_name}_to_product_management',
                              'type': 'form',
                              'model': view.model,
                              'inherit_id': view.id,
                              'arch': arch_value,
                         })
                         group_line = self.env['attribute.group.lines'].search([
                              ('attr_group_id', '=', record.attribute_group.id),
                              ('product_attribute_id', '=', record.id)
                         ], limit=1)

                         if not group_line:
                              self.env['attribute.group.lines'].create({
                                   'attr_group_id': record.attribute_group.id,
                                   'product_attribute_id': record.id,
                                   'display_type': record.display_type,
                              })

                         record.write({'state': 'publish'})


     # def action_update_publish_attribute(self):
     #      for record in self:
     #           if not record.original_name:
     #                record.original_name = record.name
     #                print(record.original_name, 'originalllllllllllllll')
     #
     #           if record.name != record.original_name:
     #                field_name = f"x_{record.original_name.strip().replace(' ', '_').lower()}"
     #                ir_field = self.env['ir.model.fields'].sudo().search([
     #                     ('name', '=', field_name),
     #                     ('model_id', '=', self.env.ref('pim_ext.model_product_management').id)
     #                ], limit=1)
     #                if ir_field:
     #                     ir_field.write({
     #                          'field_description': record.name,
     #                     })
     #                     new_field_name = f"x_{record.name.strip().replace(' ', '_').lower()}"
     #                     self.env.cr.execute(f"""
     #                     ALTER TABLE product_management RENAME COLUMN {field_name} TO {new_field_name}
     #                 """)
     #                record.original_name = record.name
     #      return {
     #           'type': 'ir.actions.client',
     #           'tag': 'display_notification',
     #           'params': {
     #                'message': 'Attributes updated successfully, including related fields!',
     #                'type': 'success',
     #                'sticky': False,
     #           },
     #      }

     def _compute_completness(self):
          for rec in self:
               data = rec.search_read([('id','=',rec._origin.id)],fields=['attribute_type_id','display_type','attribute_types_id','attribute_types','attribute_group','is_mandatory','is_required_in_clone', 'is_cloning'])
               false_count = sum(1 for d in data for value in d.values() if value != False)
               rec.completed_in_percent = (false_count/7) * 100
               # raise ValidationError(false_count/8)

     def create_pim_attribute_type(self):
          # Return the action to open the product.attribute custom layout
          return {
               'type': 'ir.actions.act_window',
               'name': 'Create Attribute',
               'res_model': 'pim.attribute.type',
               'view_mode': 'form',
               'view_id': self.env.ref('pim_ext.view_product_attribute_custom').id,
               'target': 'current',
               'context': {
                    'default_attribute_ids': self.env['product.attribute'].search([]).ids,
               },
          }

     @api.constrains('name', 'value_ids')
     def check_attribute_name(self):
          pattern = "^(?=.*[a-zA-Z0-9])[A-Za-z0-9 ]+$"
          for rec in self:
               name_count = self.search_count([('name', '=ilike', rec.name)])
               if name_count > 1:
                    raise ValidationError("Attribute name already exist")
               if rec.name and not re.match(pattern, rec.name):
                    raise ValidationError("Attribute Name should be AlphaNumeric")
               if not rec.value_ids:
                    raise ValidationError("Please fill the Attribute values for dropdown")

     def write(self, vals):
          for rec in self:
               time_now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
               msg_string = ''
               msg_string2 = ''
               old_code = rec.code or 'N/A'
               new_code = vals.get('code', old_code)

               for key in vals:
                    if key in ['name', 'code', 'display_type', 'required_in_clone', 'mandatory', 'completeness']:
                         attribute = rec._fields[key].string
                         header = "• %s" % attribute
                         if key in ['display_type']:
                              selection_tuple = dict(rec._fields[key].selection)
                              old_value = selection_tuple.get(getattr(rec, key), 'N/A') if getattr(rec, key) else 'N/A'
                         else:
                              old_value = getattr(rec, key) or 'N/A'
                         new_value = vals[key] or 'N/A'
                         if key in ['name']:

                              msg_string += (
                                                 "Old value: %s               New Value: %s\n"
                                            ) % (old_value, new_value)
                              full_message = header + "\n" + msg_string
                              if rec.history_log:
                                   rec.history_log = full_message + "\n" + rec.history_log
                              else:
                                   rec.history_log = full_message
                         if key in ['code']:
                              code = rec._fields[key].string
                              header2 = "• %s" % code
                              msg_string2 += (
                                                 "Old value: %s               New Value: %s\n"
                                            ) % (old_code, new_code)
                              full_message2 = header2 + "\n" + msg_string2
                              if rec.history_log:
                                   rec.history_log = full_message2 + "\n" + rec.history_log
                              else:
                                   rec.history_log = full_message2
          res = super(AttributeForm, self).write(vals)
          return res


class AttributeMasterUnlinkWizard(models.TransientModel):
    _name = 'attribute.master.unlink.wizard'
    _description = 'Wizard to Confirm Deletion of Attribute master'

    attribute_id = fields.Many2one('product.attribute', string="Attribute Master")

    def confirm_unlink(self):
        menu_id = self.env['ir.ui.menu'].search([('name', '=', 'Attributes')])
        if self.attribute_id:
             self.attribute_id.unlink()
        return {
             'type': 'ir.actions.client',
             'tag': 'reload',
             'params': {
                  'menu_id': menu_id.id,
             },
        }

class Attributegroup(models.Model):
     _name = 'attribute.group'
     _inherit = ['mail.thread', 'mail.activity.mixin']

     name = fields.Char('Name', required=True,)
     description = fields.Text(string='Description')
     active = fields.Boolean('Active', default=True)
     attributes_ids = fields.One2many('product.attribute', 'attribute_group', string='Attributes', required=True, tracking=True, store=True)
     attribute_family_id = fields.Many2many('family.attribute', string='Attribute Family', required=True, tracking=True, store=True)
     attribute_group_line_ids = fields.One2many('attribute.group.lines', 'attr_group_id', string='Attribute group line')
     attribute_code = fields.Selection([('medias', 'Medias')], string="Code")
     attribute_code_rec = fields.Char(string='Code')
     attribute_label = fields.Char(string='English', compute="_compute_label_translation")
     parent_id = fields.Many2one(
          'attribute.group',
          string='Parent Group',
          ondelete='cascade',
     )
     child_ids = fields.One2many(
          'attribute.group',
          'parent_id',
          compute='_compute_child_ids',
          string='Sub-groups'
     )
     user_id = fields.Many2one('res.users', string="User", default=lambda self: self.env.user)

     history_log = fields.Text(string='', help="This field stores the history of changes.")

     old_name = fields.Char(string="Old Name", readonly=True)
     new_name = fields.Char(string="New Name", readonly=True)
     old_code = fields.Char(string="Old Code", readonly=True)
     new_code = fields.Char(string="New Code", readonly=True)

     is_create_mode = fields.Boolean(default=False, string='Create Mode')

     def write(self, vals):
          for rec in self:
               time_now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
               msg_string = ''
               msg_string2 = ''
               old_code = rec.attribute_code_rec or 'N/A'
               new_code = vals.get('attribute_code_rec', old_code)

               for key in vals:
                    if key in ['name', 'attribute_code_rec', 'display_type', 'required_in_clone', 'mandatory', 'completeness']:
                         attribute = rec._fields[key].string
                         header = "• %s" % attribute
                         if key in ['display_type']:
                              selection_tuple = dict(rec._fields[key].selection)
                              old_value = selection_tuple.get(getattr(rec, key), 'N/A') if getattr(rec, key) else 'N/A'
                         else:
                              old_value = getattr(rec, key) or 'N/A'
                         new_value = vals[key] or 'N/A'
                         if key in ['name']:

                              msg_string += (
                                                 "Old value: %s               New Value: %s\n"
                                            ) % (old_value, new_value)
                              full_message = header + "\n" + msg_string
                              if rec.history_log:
                                   rec.history_log = full_message + "\n" + rec.history_log
                              else:
                                   rec.history_log = full_message
                         if key in ['attribute_code_rec']:
                              code = rec._fields[key].string
                              header2 = "• %s" % code
                              msg_string2 += (
                                                 "Old value: %s              New Value: %s\n"
                                            ) % (old_code, new_code)
                              full_message2 = header2 + "\n" + msg_string2
                              if rec.history_log:
                                   rec.history_log = full_message2 + "\n" + rec.history_log
                              else:
                                   rec.history_log = full_message2
          res = super(Attributegroup, self).write(vals)
          return res

     @api.depends('name')
     def _compute_label_translation(self):
          translator = Translator()
          for record in self:
               if record.name:
                    try:
                         user_lang = self.env.user.lang
                         lang_rec = self.env['res.lang'].search([('code', '=', user_lang)], limit=1)
                         src_lang = lang_rec.url_code
                         translation = translator.translate(record.name, src=src_lang, dest='en')
                         record.attribute_label = translation.text.capitalize()
                    except Exception as e:
                         record.attribute_label = 'Error in translation'
               else:
                    record.attribute_label = ''

     # this is for loading tree view in while click edit button
     def _compute_child_ids(self):
          for record in self:
               record.child_ids = self.env['attribute.group'].search([])

     def attribute_group_unlink(self):
          print('deleteeeeeeeeeee')

     # attribute group edit button
     def attribute_group_open_form_view(self):
          all_attribute_group_ids = self.env['attribute.group'].search([]).ids
          self.ensure_one()
          return {
               'type': 'ir.actions.act_window',
               'name': 'Edit Attribute Group',
               'res_model': 'attribute.group',
               'view_mode': 'form',
               'view_id': self.env.ref('pim_ext.view_product_attribute_groups_custom').id,
               'context': {'no_breadcrumbs': True,
                           'default_is_create_mode': False,
                           },
               'res_id': self.id,
          }

     # delete button group
     def attribute_group_unlink(self):
          return {
               'name': 'Confirm Deletion',
               'type': 'ir.actions.act_window',
               'res_model': 'attribute.group.unlink.wizard',
               'view_mode': 'form',
               'target': 'new',
               'context': {'default_group_id': self.id},
          }


     def action_back_to_menu(self):
          menu_id = self.env.ref('pim_ext.menu_pim_attribute_action2')

          # return {
          #      'type': 'ir.actions.act_window',
          #      'res_model': 'attribute.group',
          #      'view_mode': 'list',
          #      'view_id': action_id,
          #      # 'context': {'no_breadcrumbs': True},
          #      'target': 'current',
          # }
          return {
               'type': 'ir.actions.client',
               'tag': 'reload',
               'params': {
                    'menu_id': menu_id.id,
               },
          }

     def save_attributes(self):
          for line in self.attribute_group_line_ids:
               if not line.product_attribute_id:
                    raise UserError(f"No product attribute linked in line {line.id}.")

               # Update the product.attribute if needed
               line.product_attribute_id.write({
                    'attribute_group': self.id,
               })
          return {
               'type': 'ir.actions.act_window',
               'view_mode': 'form',
               'res_model': 'attribute.group',
               'view_id': self.env.ref('pim_ext.view_product_attribute_groups_custom').id,
               'res_id': self.id,
               'context': {'no_breadcrumbs': True},
               'target': 'current',
          }

     # def attribute_group_unlink(self):
     #      print('dskjncccccccc')
     #      self.unlink()
     #      return {'type': 'ir.actions.client', 'tag': 'reload'}

     def create_pim_attribute_groups(self):

          return {
               'type': 'ir.actions.act_window',
               'name': 'Create Attribute group',
               'res_model': 'attribute.group',
               'view_mode': 'form',
               'view_id': self.env.ref('pim_ext.view_product_attribute_groups_custom').id,
               'target': 'current',
               'context': {
                    'default_is_create_mode': True,
                    'default_child_ids': self.env['attribute.group'].search([]).ids,
               },
          }

     # @api.model
     # def create(self, vals):
     #      print('fkdjfkdfd', vals)
     #      record = super(Attributegroup, self).create(vals)
     #      record._check_unique_attributes()
     #      return record
     #
     # @api.model
     # def write(self, vals):
     #      print('fko9444444444', vals)
     #      res = super(Attributegroup, self).write(vals)
     #      if 'attribute_group_line_ids' in vals:
     #           self._check_unique_attributes()
     #      return res
     #
     # @api.constrains('attribute_group_line_ids')
     # def _check_unique_attributes(self):
     #      for record in self:
     #           attributes_in_group = record.attribute_group_line_ids.mapped('product_attribute_id')
     #           for attribute in attributes_in_group:
     #                other_groups = self.env['attribute.group'].search([
     #                     ('id', '!=', record.id),
     #                     ('attribute_group_line_ids.product_attribute_id', '=', attribute.id)
     #                ])
     #                if other_groups:
     #                     raise ValidationError(
     #                          f"The attribute '{attribute.name}' is already assigned to another attribute group."
     #                     )


class AttributeGroupLine(models.Model):
     _name = 'attribute.group.lines'

     attr_group_id = fields.Many2one('attribute.group', string='Attribute Group')
     used_attribute_ids = fields.Many2many(
          'product.attribute',
          compute='_compute_used_attribute_ids',
          string='Used Attributes',
          store=False
     )
     product_attribute_id = fields.Many2one('product.attribute', string='Product Attribute')
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

     enable = fields.Boolean(string="Enable", default=True)
     value_per_channel = fields.Boolean(string="Value per channel", default=False)
     value_per_locale = fields.Boolean(string="Value per locale", default=False)

     @api.depends('attr_group_id', 'product_attribute_id')
     def _compute_used_attribute_ids(self):
          """Compute all attributes already assigned to groups."""
          all_used_attributes = self.env['attribute.group.lines'].search([]).mapped('product_attribute_id')
          for line in self:
               line.used_attribute_ids = all_used_attributes

     @api.onchange('enable')
     def _onchange_enable(self):
          if self.product_attribute_id:
               attribute_name = f"x_{self.product_attribute_id.name.lower().replace(' ', '_')}"
               name = f"add_field_{attribute_name}_to_product_management"
               attribute_view_exist = self.env['ir.ui.view'].search(
                    [('name', '=ilike', name), ('active', '!=', None)])
               arch = self._arch(attribute_name,self.enable)
               if attribute_view_exist.arch:
                    attribute_view_exist.arch = arch

     def _arch(self,attribute_name,active):
          if active == False:
               new_field_xml = f'<field name="{attribute_name}" invisible="True"/>'
          else:
               new_field_xml = f'<field name="{attribute_name}"/>'
          arch = f"""
                       <xpath expr="//field[@name='{self.product_attribute_id.position_ref_field_id.name}']" position="after">
                                                          %s
                                                  </xpath>""" % new_field_xml
          return arch


class AttributeGroupUnlinkWizard(models.TransientModel):
    _name = 'attribute.group.unlink.wizard'
    _description = 'Wizard to Confirm Deletion of Attribute Group'

    group_id = fields.Many2one('attribute.group', string="Attribute Group")

    def confirm_unlink(self):
        menu_id = self.env['ir.ui.menu'].search([('name', '=', 'Attributes Groups')])
        if self.group_id:
             self.group_id.unlink()
        return {
             'type': 'ir.actions.client',
             'tag': 'reload',
             'params': {
                  'menu_id': menu_id.id,
             },
        }


class ManufacturerAttribute(models.Model):
     _name = 'manufacturer.attribute'
     _inherit = ['mail.thread', 'mail.activity.mixin']

     name = fields.Char('Name', required=True, tracking=True)

class BrandAttribute(models.Model):
     _name = 'brand.attribute'
     _inherit = ['mail.thread', 'mail.activity.mixin']

     name = fields.Char('Name', required=True, tracking=True)

      
class FamilyProducts(models.Model):
     _name = 'family.products'

     product_id = fields.Many2one('product.template', 'Product', required=True)
     default_code = fields.Char('SKU #')
     family_id = fields.Many2one('family.attribute','Family')
     mpn_number = fields.Char('MPN')
     status = fields.Selection([('active','Active'),('inactive','In Active')],'Status')
     origin = fields.Char('Origin')
     po_min = fields.Integer('PO Min')
     po_max = fields.Integer('PO Max')
     p65 = fields.Char('P65')
     attribute1_id = fields.Many2one('product.attribute1','',related='family_id.attribute1_id',)
     attribute1_val = fields.Char('Attribute 1')
     attribute2_id = fields.Many2one('product.attribute2','',related='family_id.attribute2_id',)
     attribute2_val = fields.Char('Attribute 2')
     attribute3_id = fields.Many2one('product.attribute3','',related='family_id.attribute3_id',)
     attribute3_val = fields.Char('Attribute 3')
     attribute4_id = fields.Many2one('product.attribute4','',related='family_id.attribute4_id',)
     attribute4_val = fields.Char('Attribute 4')
     select_sku = fields.Boolean('Select')


class ProductAttribute(models.Model):
     _name = 'product.attribute1'

     name = fields.Char('Name', required=True)


class ProductAttribute2(models.Model):
     _name = 'product.attribute2'

     name = fields.Char('Name', required=True)


class ProductAttribute3(models.Model):
     _name = 'product.attribute3'

     name = fields.Char('Name', required=True)
     
class ProductAttribute4(models.Model):
     _name = 'product.attribute4'

     name = fields.Char('Name', required=True)


class FamilyAttribute(models.Model):
     _name = 'family.attribute'
     _inherit = ['mail.thread', 'mail.activity.mixin']
     _description = 'Family'

     code = fields.Char(string="Code",required=True,
                          readonly=True, default=lambda self: _('New'))
     description = fields.Text(string="Description")

     name = fields.Char('Name', required=True, tracking=True)
     description = fields.Text(string="Description")

     supplier_id = fields.Many2one('res.partner','Supplier')
     brand_id = fields.Many2one('brand.attribute','Brand')
     manufacture_id = fields.Many2one('manufacturer.attribute','Manufacturer')
     attributes_group_ids = fields.Many2many('attribute.group', string='Attributes Groups', tracking=True, domain=[('active', '=', True)])
     taxonomy_ids = fields.Many2many('product.public.category', string="Taxonomy")
     attch_ids = fields.Many2many('ir.attachment', 'ir_attach_rel',  'record_relation_id', 'attachment_id', string="Attachments")
     complementary_categ_ids = fields.Many2many('product.public.category','custom_categ_rel','family_id','cteg_id', string="Complementary Categories")
     product_family_ids = fields.One2many('family.products','family_id','Products')
     product_image = fields.Image(string="Image",copy=False, attachment=True, max_width=1024, max_height=1024)
     buyer_id = fields.Many2one('res.partner','Buyer')
     availability = fields.Selection([('all','All Channel')],'Availability')
     swatch = fields.Selection([('yes','Yes'),('no','No')],'Swatch')
     gift = fields.Selection([('yes','Yes'),('no','No')],'Gift')
     attribute1_id = fields.Many2one('product.attribute1','Attribute 1')
     attribute2_id = fields.Many2one('product.attribute2','Attribute 2')
     attribute3_id = fields.Many2one('product.attribute3','Attribute 3')
     attribute4_id = fields.Many2one('product.attribute4','Attribute 4')
     asn_description = fields.Html('ASN Description')
     product_families_ids = fields.One2many('family.products.line', 'families_id', 'SKU', readonly=False)
     variant_line_ids = fields.One2many('family.variant.line', 'variant_familiy_id', 'Variants', readonly=False)

     attribute_label = fields.Char(string='English', compute="_compute_family_label_translation")

     parent_id = fields.Many2one(
          'family.attribute',
          string='Parent Group',
          ondelete='cascade',
     )
     family_ids = fields.One2many(
          'family.attribute',
          'parent_id',
          compute='_compute_family_ids',
          string='Sub-groups'
     )

     user_id = fields.Many2one('res.users', string="User", default=lambda self: self.env.user)

     history_log = fields.Text(string='', help="This field stores the history of changes.")

     old_name = fields.Char(string="Old Name", readonly=True)
     new_name = fields.Char(string="New Name", readonly=True)
     old_code = fields.Char(string="Old Code", readonly=True)
     new_code = fields.Char(string="New Code", readonly=True)

     is_create_mode = fields.Boolean(default=False, string='Create Mode')

     def write(self, vals):
          for rec in self:
               time_now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
               msg_string = ''
               msg_string2 = ''
               old_code = rec.code or 'N/A'
               new_code = vals.get('code', old_code)

               for key in vals:
                    if key in ['name', 'code', 'display_type', 'required_in_clone', 'mandatory', 'completeness']:
                         attribute = rec._fields[key].string
                         header = "• %s" % attribute
                         if key in ['display_type']:
                              selection_tuple = dict(rec._fields[key].selection)
                              old_value = selection_tuple.get(getattr(rec, key), 'N/A') if getattr(rec, key) else 'N/A'
                         else:
                              old_value = getattr(rec, key) or 'N/A'
                         new_value = vals[key] or 'N/A'
                         if key in ['name']:

                              msg_string += (
                                                 "Old value: %s               New Value: %s\n"
                                            ) % (old_value, new_value)
                              full_message = header + "\n" + msg_string
                              if rec.history_log:
                                   rec.history_log = full_message + "\n" + rec.history_log
                              else:
                                   rec.history_log = full_message
                         if key in ['code']:
                              code = rec._fields[key].string
                              header2 = "• %s" % code
                              msg_string2 += (
                                                 "Old value: %s               New Value: %s\n"
                                            ) % (old_code, new_code)
                              full_message2 = header2 + "\n" + msg_string2
                              if rec.history_log:
                                   rec.history_log = full_message2 + "\n" + rec.history_log
                              else:
                                   rec.history_log = full_message2
          res = super(FamilyAttribute, self).write(vals)
          return res

     @api.depends('name')
     def _compute_family_label_translation(self):
          translator = Translator()
          for record in self:
               if record.name:
                    try:
                         user_lang = self.env.user.lang
                         lang_rec = self.env['res.lang'].search([('code', '=', user_lang)], limit=1)
                         src_lang = lang_rec.url_code
                         translation = translator.translate(record.name, src=src_lang, dest='en')
                         record.attribute_label = translation.text.capitalize()
                    except Exception as e:
                         record.attribute_label = 'Error in translation'
               else:
                    record.attribute_label = ''

     def _compute_family_ids(self):
          for record in self:
               record.family_ids = self.env['family.attribute'].search([])

     def attribute_family_open_form_view(self):
          self.ensure_one()
          return {
               'type': 'ir.actions.act_window',
               'name': 'Edit Family',
               'res_model': 'family.attribute',
               'view_mode': 'form',
               'view_id': self.env.ref('pim_ext.view_split_family_view_custom').id,
               'context': {'no_breadcrumbs': True,
                           'default_is_create_mode': False,
                           },
               'res_id': self.id,
          }

     # delete Family
     def attribute_family_unlink(self):
          return {
               'name': 'Confirm Deletion',
               'type': 'ir.actions.act_window',
               'res_model': 'attribute.family.unlink.wizard',
               'view_mode': 'form',
               'target': 'new',
               'context': {'default_family_id': self.id},
          }

     def save_family(self):
          return {
               'type': 'ir.actions.act_window',
               'view_mode': 'form',
               'res_model': 'family.attribute',
               'view_id': self.env.ref('pim_ext.view_split_family_view_custom').id,
               'res_id': self.id,
               'context': {'no_breadcrumbs': True},
               'target': 'current',
          }

     def action_back_to_menu(self):
          menu_id = self.env['ir.ui.menu'].search([('name', '=', 'Families')])
          return {
               'type': 'ir.actions.client',
               'tag': 'reload',
               'params': {
                    'menu_id': menu_id.id,
               },
          }

     @api.model
     def create(self, vals):
          vals['code'] = self.env['ir.sequence'].next_by_code(
               'family.attribute') or None
          res = super(FamilyAttribute, self).create(vals)
          return res
     
     def edit_family(self):
          pass

     def delete_family(self):

          return {
               'type': 'ir.actions.act_window',
               'res_model': 'delete.family.wizard',
               'view_mode': 'form',
               'target': 'new',
               'context': {
                    'default_current_family_id': self.id,
                    'default_current_family' : self._origin.id,
                    },
          }

     def action_update(self):
          attribute_group = self.env['attribute.group'].search([("attribute_family_id", "in", self.id)])
          for record in attribute_group:
               self.attributes_group_ids = [(4, record.id)]

     def mass_edit(self):
         res=[]
         return res

     def create_pim_attribute_family(self):
          return {
               'type': 'ir.actions.act_window',
               'name': 'Family',
               'res_model': 'family.attribute',
               'view_mode': 'form',
               'view_id': self.env.ref('pim_ext.view_split_family_view_custom').id,
               'target': 'current',
               'context': {
                    'default_family_ids': self.env['family.attribute'].search([]).ids,
                    'default_is_create_mode': True,
               },
          }
          # return {
          #      'name':_('Create Family'),
          #      'type':'ir.actions.act_window',
          #      'view_mode':'form',
          #      'res_model':'family.attribute',
          # }

     def action_open_attribute_group_wizard(self):
          return {
               'type': 'ir.actions.act_window',
               'res_model': 'attribute.group.wizard',
               'view_mode': 'form',
               'target': 'new',
               'context': {'default_attribute_family_id': self.id},
          }

     def action_open_add_attribute_wizard(self):
          return {
               'type': 'ir.actions.act_window',
               'res_model': 'add.attribute.wizard',
               'view_mode': 'form',
               'target': 'new',
               'context': {'default_attribute_family_id': self.id},
          }

     def action__add_variant_wizard(self):
          return {
               'type': 'ir.actions.act_window',
               'res_model': 'attribute.variant.wizard',
               'view_mode': 'form',
               'target': 'new',
               'context': {'default_attribute_family_id': self.id},
          }


class AttributeFamilyUnlinkWizard(models.TransientModel):
    _name = 'attribute.family.unlink.wizard'
    _description = 'Wizard to Confirm Deletion of family'

    family_id = fields.Many2one('family.attribute', string="Family")

    def confirm_unlink(self):
        menu_id = self.env['ir.ui.menu'].search([('name', '=', 'Families')])
        if self.family_id:
             self.family_id.unlink()
        return {
             'type': 'ir.actions.client',
             'tag': 'reload',
             'params': {
                  'menu_id': menu_id.id,
             },
        }


class ProductProduct(models.Model):
     _inherit = 'product.product'

     attribute_group_ids = fields.Many2many('attribute.group', string='Attribute Group', compute='_compute_attribute_group_ids', store=True)
     attribute_family_ids = fields.Many2many('family.attribute', string='Family Attribute', compute='_compute_attribute_group_ids', store=True)
     hs_code = fields.Char('HS Code')
     
     @api.depends('product_template_attribute_value_ids')
     def _compute_attribute_group_ids(self):
          self.attribute_group_ids = self.product_template_attribute_value_ids.attribute_id.attribute_group
          self.attribute_family_ids = self.product_template_attribute_value_ids.attribute_id.attribute_group.attribute_family_id


class ProductTemplate(models.Model):
     _inherit = 'product.template'

     hs_code = fields.Char('HS Code')
     mpn_number = fields.Char('MPN')
     status = fields.Selection([('active','Active'),('inactive','In Active')],'Status')
     origin = fields.Char('Origin')
     po_min = fields.Integer('PO Min')
     po_max = fields.Integer('PO Max')
     p65 = fields.Char('P65')
     attribute1_id = fields.Many2one('product.attribute1','Attribute 1')
     attribute1_val = fields.Char('Value 1')
     attribute2_id = fields.Many2one('product.attribute2','Attribute 2')
     attribute2_val = fields.Char('Value 2')
     attribute3_id = fields.Many2one('product.attribute3','Attribute 3')
     attribute3_val = fields.Char('Value 3')
     attribute4_id = fields.Many2one('product.attribute4','Attribute 4')
     attribute4_val = fields.Char('Value 4')
     family_id = fields.Many2one('family.attribute','Product Family')
     active_label = fields.Char(string="Status", compute="_compute_active_label")

     readable_variant_names = fields.Char(string="Variants", compute="_compute_readable_variant_names")
     family_id = fields.Many2one('family.attribute', string='Family')
     sku = fields.Char(string='SKU')
     brand_id = fields.Many2one('product.brand', string='Brand')

     parent_id = fields.Many2one(
          'product.create',
          string='Parent Group',
          ondelete='cascade',
     )

     product_master_id = fields.Many2one(
          'product.create.master',
          string='Parent Group',
          ondelete='cascade',
     )

     @api.depends('product_variant_ids')
     def _compute_readable_variant_names(self):
          for template in self:
               if template.product_variant_ids:
                    template.readable_variant_names = ', '.join(template.product_variant_ids.mapped('name'))
               else:
                    template.readable_variant_names = "N/A"

     def _compute_active_label(self):
          for record in self:
               record.active_label = "ENABLED" if record.active else "DISABLED"

     def create_pim_products(self):
          all_product_ids = self.env['product.template'].search([], order='create_date desc').ids
          return {
               'type': 'ir.actions.act_window',
               'name': 'CREATE PRODUCT',
               'res_model': 'product.create',
               'view_mode': 'form',
               'view_id': self.env.ref('pim_ext.view_product_template_custom_form').id,
               'context': {'no_breadcrumbs': True,
                           'default_master_products_ids': all_product_ids,
                           },
               'target': 'current',
          }

     # this is for dynamic product creation
     @api.model
     def get_views(self, views, options=None):
          active_id = self.env.context.get('active_id')
          # Get the view's XML and the type of the view (form, tree, etc.)
          res = super(ProductTemplate, self).get_views(views, options)
          family_id = self.env.context.get('default_family_id') or self.family_id.id
          active_id = self.env.context.get('active_id')
          form_views = [view for view in views if view[1] == 'form']

          # Check if we're dealing with a form view and if the family is selected
          for view_id, view_type in form_views:
               if view_type == 'form' and self.family_id:
                    doc = etree.XML(res['arch'])  # Parse the XML of the form view

                    # Look for the dynamic fields container (group where we will add dynamic fields)
                    dynamic_fields_container = doc.xpath("//group[@name='dynamic_attributes']")
                    print('dkskkkwwwwww', dynamic_fields_container)
                    if dynamic_fields_container:
                         print('do0333333333333')
                         container = dynamic_fields_container[0]
                         print('djd2222222222', container)

                         # Get the attributes related to the selected family
                         attributes = self.family_id.mapped('attributes_group_ids.attributes_ids')
                         print('atrrrrrrrrrrrrrriiiiii', attributes)

                         # Loop through each attribute and add it as a field in the form
                         for attribute in attributes:
                              print('dop333333333', attribute)
                              field_name = f"x_attr_{attribute.id}"
                              print('dksdjkjkjf', field_name)

                              # Add the field dynamically to the form view
                              field_element = etree.Element('field', {'name': field_name})
                              print('sdkfdkfl3333333333', field_element)
                              container.append(field_element)
                              print('dopcvvvvvvvvvvvvvvvv', container)

                              # Dynamically create the field on the model
                              self._add_dynamic_field(attribute, field_name)

                    # Save the updated XML to be returned
                    res['arch'] = etree.tostring(doc, pretty_print=True)

          return res

     def _add_dynamic_field(self, attribute, field_name):
          print('2222222222222222222')
          """Dynamically adds a field to the model for each attribute"""
          field_type_mapping = {
               'char': fields.Char,
               'text': fields.Text,
               'integer': fields.Integer,
               'boolean': fields.Boolean,
               'selection': fields.Selection,
          }
          print('sopwwwwwwww', field_type_mapping)

          field_type = field_type_mapping.get(attribute.field_type, fields.Char)
          print('dskfdddddddddddd', field_type)
          field_params = {}

          if attribute.field_type == 'selection' and attribute.selection_options:
               print('9303333333333')
               field_params['selection'] = [(opt.strip(), opt.strip()) for opt in
                                            attribute.selection_options.split(',')]
               print('fipf55555555555', field_params)

          # Add the field to the model dynamically
          self._add_field_to_model(field_name, field_type, field_params)

     def _add_field_to_model(self, field_name, field_type, field_params):
          print('d9333333333333')
          """Dynamically adds a field to the product template model"""
          if field_name not in self._fields:
               print('dopweeeeeeeeeeeee')
               self._add_to_class(field_name, field_type, field_params)

     def _add_to_class(self, name, field_type, field_params):
          print('ds349333333333333')
          """Dynamically add the field to the model class"""
          field = field_type(string=name, **field_params)
          print('skdskfjdkfdk', field)
          self._add_to_fields(name, field)

     def _add_to_fields(self, name, field):
          print('dksjdskjdskdjskd')
          """Helper method to add the field"""
          self._fields[name] = field


