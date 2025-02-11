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

     products_id = fields.Many2one('product.template', string='Products')

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
               old_code = rec.code or 'N/A'
               new_code = vals.get('code', old_code)
               old_active = rec.active
               new_active = vals.get('active', old_active)
               old_attribute_group = rec.attribute_group.display_name if rec.attribute_group else 'N/A'
               new_attribute_group = self.env['attribute.group'].browse(vals['attribute_group']).display_name if vals.get(
                    'attribute_group') else 'N/A'
               old_write_date = rec.write_date.strftime("%d/%m/%Y %H:%M:%S") if rec.write_date else 'N/A'
               new_write_date = fields.Datetime.now().strftime("%d/%m/%Y %H:%M:%S")
               old_write_uid = rec.write_uid.display_name if rec.write_uid else 'N/A'
               new_write_uid = self.env.user.display_name

               for key in vals:
                    if key in ['name', 'code', 'active', 'create_variant','sequence','attribute_group','display_type','attribute_type_id',
                               'is_mandatory','is_required_in_clone','is_cloning','is_completeness','original_name','attribute_types','attribute_types_id',
                               'completed_in_percent','state','position_ref_field_id','unique_value','value_per_channel','value_per_locale','usable_in_grid',
                               'locale_specific','master_attribute_ids','label_transaltion']:
                         attribute = rec._fields[key].string
                         header = "• %s" % attribute

                         if key == 'attribute_group':
                              old_value = old_attribute_group
                              new_value = new_attribute_group
                         else:
                              old_value = getattr(rec, key) or 'N/A'
                              new_value = vals[key] or 'N/A'

                         msg_string += ("Old value: %s | New Value: %s | Updated Date: %s | Updated By: %s\n") % (
                              old_value, new_value, old_write_date, old_write_uid
                         )
                         full_message = header + "\n" + msg_string
                         rec.history_log = full_message + "\n" + (rec.history_log or '')

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

               tracked_fields = ['name', 'attribute_code_rec', 'active', 'parent_id', 'description', 'attribute_code']
               tracked_group_line_fields = ['product_attribute_id', 'display_type', 'enable', 'value_per_channel',
                                            'value_per_locale']

               for key in vals:
                    if key in tracked_fields:
                         attribute = rec._fields[key].string
                         old_value = getattr(rec, key) or 'N/A'
                         new_value = vals[key] or 'N/A'

                         # Fetch display_name for Many2one fields
                         if key == 'parent_id':
                              old_value = rec.parent_id.display_name if rec.parent_id else 'N/A'
                              new_value = self.env['attribute.group'].browse(vals[key]).display_name if vals.get(
                                   key) else 'N/A'

                         msg_string += (
                              f"• {attribute}\nOld value: {old_value} | New Value: {new_value} | Updated Date: {time_now} | Updated By: {self.env.user.display_name}\n")

                    if key == 'attribute_group_line_ids':
                         for command in vals[key]:
                              if command[0] in [1, 4]:  # Update or Link existing records
                                   line_id = self.env['attribute.group.lines'].browse(command[1])
                                   for field in tracked_group_line_fields:
                                        if field in command[2]:
                                             old_value = getattr(line_id, field) or 'N/A'
                                             new_value = command[2][field] or 'N/A'

                                             # Fix: Fetch display_name for product_attribute_id
                                             if field == 'product_attribute_id':
                                                  old_value = line_id.product_attribute_id.display_name if line_id.product_attribute_id else 'N/A'
                                                  new_value = self.env['product.attribute'].browse(
                                                       new_value).display_name if new_value else 'N/A'

                                             msg_string += (
                                                  f"• {field}\nOld value: {old_value} | New Value: {new_value} | Updated Date: {time_now} | Updated By: {self.env.user.display_name}\n")

                              elif command[0] == 0:  # New record
                                   msg_string += "• New Attribute Group Line Added\n"
                              elif command[0] == 2:  # Deletion
                                   line_id = self.env['attribute.group.lines'].browse(command[1])
                                   msg_string += f"• Attribute Group Line Removed: {line_id.product_attribute_id.display_name if line_id.product_attribute_id else 'N/A'}\n"

               if msg_string:
                    rec.history_log = msg_string + "\n" + (rec.history_log or '')

          return super(Attributegroup, self).write(vals)

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
          help="The display type used in the Product Configurator.")

     related_display_type = fields.Selection(
          related='product_attribute_id.display_type',
          store=True,
          readonly=True
     )

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

               # Fields to track
               tracked_fields = ['name', 'description', 'supplier_id', 'brand_id', 'manufacture_id', 'availability',
                                 'swatch', 'gift']
               tracked_one2many_fields = {
                    'product_families_ids': ['product_id', 'attribute_id', 'attribute_group_id', 'completeness_percent',
                                             'product_id_stored'],
                    'variant_line_ids': ['variant_id', 'name', 'variant_ids'],
               }

               # Track direct field changes
               for key in vals:
                    if key in tracked_fields:
                         attribute = rec._fields[key].string  # Get field's display name
                         old_value = getattr(rec, key) or 'N/A'
                         new_value = vals[key] or 'N/A'

                         # Handle Many2one fields to show display_name
                         if isinstance(rec._fields[key], fields.Many2one):
                              old_value = old_value.display_name if old_value != 'N/A' else 'N/A'
                              new_value = self.env[rec._fields[key].comodel_name].browse(
                                   new_value).display_name if new_value != 'N/A' else 'N/A'

                         msg_string += (
                              f"• {attribute}\nOld Value: {old_value} | New Value: {new_value} | Updated Date: {time_now} | Updated By: {self.env.user.display_name}\n"
                         )

               # Track One2many field changes
               for field, subfields in tracked_one2many_fields.items():
                    if field in vals:
                         field_label = rec._fields[field].string  # Get One2many field's display name
                         for command in vals[field]:
                              if command[0] == 1:  # Update existing record
                                   line_id = rec[field].browse(command[1])  # Corrected browsing method
                                   for subfield in subfields:
                                        if subfield in command[2]:
                                             subfield_label = line_id._fields[
                                                  subfield].string  # Get field's display name
                                             old_value = getattr(line_id, subfield) or 'N/A'
                                             new_value = command[2][subfield] or 'N/A'

                                             msg_string += (
                                                  f"• {subfield_label} (in {field_label})\nOld Value: {old_value} | New Value: {new_value} | Updated Date: {time_now} | Updated By: {self.env.user.display_name}\n"
                                             )

                              elif command[0] == 0:  # New record added
                                   new_record_data = command[2]  # Data of new record
                                   msg_string += (
                                        f"• New record added to {field_label}\n"
                                        f"  Updated Date: {time_now} | Updated By: {self.env.user.display_name}\n"
                                   )
                              elif command[0] == 2:  # Deletion
                                   removed_record = rec[field].browse(command[1])  # Browse the One2many record
                                   removed_name = removed_record.display_name if removed_record else "Unknown"
                                   removed_write_date = removed_record.write_date.strftime(
                                        "%d/%m/%Y %H:%M:%S") if removed_record.write_date else "N/A"
                                   removed_write_uid = removed_record.write_uid.display_name if removed_record.write_uid else "Unknown"

                                   msg_string += (
                                        f"• Record removed from {field_label}: {removed_name}\n"
                                        f"  Updated Date: {removed_write_date} | Updated By: {removed_write_uid}\n"
                                   )

               if msg_string:
                    rec.history_log = msg_string + "\n" + (rec.history_log or '')

          return super(FamilyAttribute, self).write(vals)

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
     family_id = fields.Many2one('family.attribute', string='Family', readonly=True)
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

     product_parent_id = fields.Many2one(
          'product.template',
          string='Parent Group',
          ondelete='cascade',
     )
     product_tmplt_ids = fields.One2many(
          'product.template',
          'product_parent_id',
          compute='_compute_products_ids',
          string='Sub-groups'
     )

     is_update_from_attribute = fields.Boolean(string='Created from attribute')
     percentage_complete = fields.Float(string="Complete",
                                        compute='_compute_percentage_complete',
                                        help="Percentage of completion (0-100)")

     progress_state = fields.Selection([
          ('partially_completed', 'Partially Completed'),
          ('almost_completed', 'Almost Completed'),
          ('fully_completed', 'Fully Completed'),
          ('not_completed', 'Not Completed'),
          ('incomplete', 'Incomplete')
     ], string="Progress State")

     is_variant = fields.Boolean(string='Variant Product')
     variant_id = fields.Many2one('family.variant.line', string='Family Variant')
     is_variant_values_updated = fields.Boolean(default=False, string='Is Variant value updated')
     product_attr_values_id = fields.Many2many('product.attribute.value', 'attr_value_id', 'products_id', string='Attribute Values')
     product_attr_ids = fields.One2many('product.attribute', 'products_id', string='Attributes')
     is_variant_update = fields.Boolean(string='Variant updated', default=False)

     def _compute_products_ids(self):
          for record in self:
               record.product_tmplt_ids = self.env['product.template'].search([])

     def action_back_to_product_menu(self):
          print('fdfidofjdkfjd')
          return {
               'name': 'products',
               'res_model': 'product.template',
               'type': 'ir.actions.act_window',
               'view_id': self.env.ref('pim_ext.view_product_management_tree').id,
               'view_mode': 'list',
               'target': 'current',
               'context': {
                    'no_breadcrumbs': True,
               }
          }


     def _compute_percentage_complete(self):
          for product in self:
               filled_count = 0
               total_count = 0
               if product.family_id:
                    attributes = product.family_id.mapped('product_families_ids').mapped('attribute_id')
                    for attr_rec in attributes:
                         if attr_rec.is_completeness:
                              total_count += 1
                              field_name = f"x_{attr_rec.name.lower()}"
                              if field_name in product._fields:
                                   attribute_value = getattr(product, field_name, None)
                                   print(f"Checking field {field_name}: Value = {attribute_value}")
                                   if isinstance(product._fields[field_name], fields.Boolean):
                                        print('dsskdjskdjs')
                                        if attribute_value:
                                             filled_count += 1
                                   else:
                                        if attribute_value not in [False, None, ""]:
                                             filled_count += 1
                              else:
                                   print(f"Field {field_name} does not exist in product.template")
                    product.percentage_complete = (filled_count / total_count * 100) if total_count > 0 else 0
                    product._compute_progress_state(product.percentage_complete)
               else:
                    product.percentage_complete = 0

     def _compute_progress_state(self, percentage_complete):
          print('dskjskjdsk', percentage_complete)
          for product in self:
               if percentage_complete >= 70:
                    product.progress_state = 'fully_completed'
               elif percentage_complete >= 55 and percentage_complete < 70:
                    product.progress_state = 'almost_completed'
               elif percentage_complete >= 40 and percentage_complete < 55:
                    product.progress_state = 'partially_completed'
               elif percentage_complete >= 25 and percentage_complete < 40:
                    product.progress_state = 'not_completed'
               else:
                    product.progress_state = 'incomplete'

     def update_variant_values(self):
          print('dksjdksjd', self.variant_id.variant_ids, self.variant_id.variant_ids[:1])
          attribute_value = self.variant_id.variant_ids[:1]
          return {
               'type': 'ir.actions.act_window',
               'res_model': 'attribute.variant.values.wizard',
               'view_mode': 'form',
               'target': 'new',
               'context': {'default_attribute_family_id': self.family_id.id,
                           'default_product_id': self.id,
                           'default_variant_id': self.variant_id.id,
                           'default_attribute_id': attribute_value.id if attribute_value else False,
                           },
          }

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

     def save_product_rec(self):
          return {
               'type': 'ir.actions.act_window',
               'view_mode': 'form',
               'res_model': 'product.template',
               'view_id': self.env.ref('pim_ext.view_product_creation_split_view_custom').id,
               'res_id': self.id,
               'context': {'no_breadcrumbs': True},
               'target': 'current',
          }

     def custom_product_open_form_view(self):
          print('dksdjskdjs')

          return {
              'type': 'ir.actions.act_window',
              'name': 'Products',
              'res_model': 'product.template',
              'view_mode': 'form',
              'view_id': self.env.ref('pim_ext.view_product_creation_split_view_custom').id,
              'context': {'no_breadcrumbs': True,
                          },
              'res_id': self.id,
          }

     def custom_product_open_default_form_view(self):
          return {
               'type': 'ir.actions.act_window',
               'name': 'Products',
               'res_model': 'product.template',
               'view_mode': 'form',
               'view_id': self.env.ref('product.product_template_only_form_view').id,
               'context': {'no_breadcrumbs': True,
                           },
               'res_id': self.id,
               'target': 'new',
          }

     def custom_product_unlink(self):
          return {
               'name': 'Confirm Deletion',
               'type': 'ir.actions.act_window',
               'res_model': 'product.template.unlink.wizard',
               'view_mode': 'form',
               'target': 'new',
               'context': {'default_product_id': self.id},
          }


class ProductMasterUnlinkWizard(models.TransientModel):
    _name = 'product.template.unlink.wizard'
    _description = 'Wizard to Confirm Deletion of Product master'

    product_id = fields.Many2one('product.template', string="Product Master", readonly=True)

    def confirm_unlink(self):
        if self.product_id:
             self.product_id.unlink()
        return {
             'type': 'ir.actions.act_window',
             'name': 'Products',
             'res_model': 'product.template',
             'view_mode': 'list',
             'view_id': self.env.ref('pim_ext.view_product_management_tree').id,
             'context': {'no_breadcrumbs': True,
                         },
        }

