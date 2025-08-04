# -*- coding: utf-8 -*-

import time,pytz
import re
from datetime import datetime,timedelta,timezone,date
from email.policy import default
from markupsafe import Markup
import pytz
import colorsys

from lxml import etree
from odoo import models, api, fields,_, tools
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
          selection_add=[
               ('date', 'Date'),
               ('file', 'File'),
               ('image', 'Image'),
               ('measurement', 'Measurement'),
               ('number', 'Integer'),
               ('price', 'Price'),
               ('text', 'Text'),
               ('textarea', 'Text Area'),
               ('yes_no', 'Checkbox'),
               ('table', 'Table'),
               ('multi_select', 'Multi Select'),
               ('simple_select', 'Simple Select'),
          ],
          ondelete={
               'date': 'cascade',
               'file': 'cascade',
               'image': 'cascade',
               'measurement': 'cascade',
               'number': 'cascade',
               'price': 'cascade',
               'text': 'cascade',
               'textarea': 'cascade',
               'yes_no': 'cascade',
               'table': 'cascade',
               'multi_select': 'cascade',
               'simple_select': 'cascade',
          },
     )
     attribute_group = fields.Many2many('attribute.group', string='Attribute Group', tracking=True)
     attribute_type_id = fields.Many2one('pim.attribute.type', string='PIM Attribute Type')
     parent_attribute_id = fields.Many2one('product.attribute', string='Attribute')
     is_mandatory = fields.Boolean(string='Mandatory', default=False)
     is_required_in_clone = fields.Boolean(string='Required in Clone', default=True)
     is_cloning = fields.Boolean(string='Cloning', default=True)
     is_completeness = fields.Boolean(string='Completeness')
     attribute_types = fields.Selection([('basic', 'Basic'),
                                         ('optional', 'Optional')], string='Attribute Type')
     attribute_types_id = fields.Many2one('pim.attribute.type', string='Attribute Type')
     completed_in_percent = fields.Float('Completed Progressbar')
     state = fields.Selection([('unpublish', 'Unpublish'), ('publish', 'Publish')], string='Status', default='unpublish')


     position_ref_field_id = fields.Many2one("ir.model.fields", string="Position After", domain="[('model_id.model','=','product.management')]")

     code = fields.Char(string='Code', readonly=True)

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

     sub_attribute_ids = fields.One2many(
          'product.attribute',
          'parent_id',
          string='Table Attributes'
     )

     label_transaltion = fields.Char(string='English', compute="_compute_label_attribute_translation")

     user_id = fields.Many2one('res.users', string="User", default=lambda self: self.env.user)

     history_log = fields.Html(string='History Log', help="This field stores the history of changes.")

     products_id = fields.Many2one('product.template', string='Products')

     original_name = fields.Char('Field Names')

     widget = fields.Char("Widget")
     max_value = fields.Char("Max Length")
     alpha_numeric_value = fields.Boolean("Alpha Numeric Validation")
     company_id = fields.Many2one('res.company', required=True, readonly=True, default=lambda self: self.env.company)

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

     def sanitize_field_name(self, name):
          name = name.lower()
          name = name.replace(' #', '_1')
          name = re.sub(r'[^a-z0-9_]', '_', name)
          name = re.sub(r'_+', '_', name)
          name = name.strip('_')
          name = f'x_{name}'
          if not name[0].isalpha():
               name = 'x_' + name
          return name[:63]

     def get_create_vals(self, vals, model_id, d_type):
          if d_type in ['select', 'color']:
               d_type = 'selection'
          elif d_type in ['text']:
               d_type = 'char'
          elif d_type in ['textarea']:
               d_type = 'text'
          elif d_type in ['date']:
               d_type = 'date'
          elif d_type in ['number']:
               d_type = 'integer'
          elif d_type in ['link', 'file', 'image']:
               d_type = 'binary'
          elif d_type in ['yes_no']:
               d_type = 'boolean'
          elif d_type in ['simple_select']:
               d_type = 'many2one'
          elif d_type in ['multi_select']:
               d_type = 'many2many'
          elif d_type in ['price']:
               d_type = 'monetary'
          elif d_type in ['table']:
               d_type = 'one2many'

          base_vals = {
               'name': vals.original_name,
               'field_description': vals.name,
               'model_id': model_id.id,
          }

          if d_type in ['many2one']:
               base_vals.update({
                    'ttype': d_type,
                    'model': model_id.model,  # only required for backward compatibility
                    'relation': 'product.attribute.value',
                    'domain': '[("attribute_id", "=", %d)]' % vals.id,
               })
          elif d_type in ['measurement']:
               uom_model_id = self.env['ir.model'].sudo().search([('model', '=', 'uom.uom')])
               base_vals.update({
                    'model': uom_model_id.model,  # only required for backward compatibility
                    'relation': 'uom.uom',
                    'ttype': 'many2one',
               })
          elif d_type in ['many2many']:
               base_vals.update({
                    'ttype': d_type,
                    'model': model_id.model,  # only required for backward compatibility
                    'relation': 'product.attribute.value',
                    'relation_table': 'x_%s_rel' % vals.original_name.replace('.', '_'),
                    'column1': 'attribute_id',
                    'column2': '%s_id' % vals.original_name,
                    'domain': '[("attribute_id", "=", %d)]' % vals.id,
               })
          elif d_type in ['one2many']:
               base_vals.update({
                    'ttype': d_type,
                    'model': model_id.model,  # only required for backward compatibility
                    'relation': 'product.attribute',
                    'relation_field': 'parent_attribute_id',
                  #  'domain': '[("parent_attribute_id", "=", %d)]' % vals.id,
               })
          else:
               base_vals.update({
                    'ttype': d_type,
               })
          return base_vals

     def create_attributes(self):
          print("create_attributes ========== product attribute")
          self.ensure_one()
          model_id = self.env['ir.model'].sudo().search([('model', '=', 'product.template')])

          for vals in self:
               vals.original_name = self.sanitize_field_name(vals.name)

               create_vals = self.get_create_vals(vals, model_id, vals.display_type)


               print("create_vals === ", create_vals)
               create_field = self.env['ir.model.fields'].sudo().create(create_vals)
               print(" create_field  === ", create_field)
               # creates a filename field for binary field
               if vals.display_type in ['link', 'file', 'image']:
                    file_name = vals.original_name + '_file_name'
                    create_vals_file = {'name': file_name,
                                        'field_description': vals.name,
                                        'model': model_id.model,
                                        'model_id': model_id.id,
                                        'ttype': 'char',
                                        }
                    create_field_file_name = self.env['ir.model.fields'].sudo().create(create_vals_file)

               if vals.display_type == 'table' and vals.sub_attribute_ids:
                    for rec in vals.sub_attribute_ids:
                         rec.original_name = rec.sanitize_field_name(rec.name)
                         sub_create_vals = self.get_create_vals(rec, model_id, rec.display_type)
                         print(" sub_create_vals  === ",sub_create_vals)
                         sel_val = self.env['ir.model.fields'].sudo().create(sub_create_vals)
                         print(" sel_val  === ", sel_val)

          # # Check if an existing attribute exists
          # existing_attribute = attribute.search([('name', '=', self.name)], limit=1)
          #
          # if existing_attribute:
          #      # Update existing attribute
          #      existing_attribute.write(attribute_vals)
          #      attribute = existing_attribute
          # else:
          #      # Create new attribute
          #      attribute = attribute.create(attribute_vals)
          #
          # # Ensure attribute group lines are updated
          # if self.attribute_group:
          #      group_line = self.env['attribute.group.lines'].search([
          #           ('attr_group_id', '=', self.attribute_group.id),
          #           ('product_attribute_id', '=', attribute.id),
          #      ], limit=1)
          #
          #      if not group_line:
          #           self.env['attribute.group.lines'].create({
          #                'attr_group_id': self.attribute_group.id,
          #                'product_attribute_id': attribute.id,
          #           })
          # for record in self:
          #      if record.display_type in ['simple_select', 'radio', 'pills', 'color',
          #                                 'multi_select'] and not record.value_ids:
          #           raise ValidationError(
          #                "Please fill the Attribute values for dropdown.")
          #
          # menu_id = self.env.ref('pim_ext.menu_pim_attribute_action')
          # return {
          #      'type': 'ir.actions.client',
          #      'tag': 'reload',
          #      'params': {
          #           'menu_id': menu_id.id,
          #      },
          # }

     def create_pim_attribute_type(self):
          return {
               'type': 'ir.actions.act_window',
               'name': 'Create Attribute',
               'res_model': 'pim.attribute.type',
               'view_mode': 'form',
               'view_id': self.env.ref('pim_ext.view_product_attribute_custom').id,
               'target': 'current',
          }

     @api.constrains('name', 'value_ids')
     def check_attribute_name(self):
          print("check_attribute_name -------------------------")
          pattern = "^(?=.*[a-zA-Z0-9])[A-Za-z0-9 ]+$"
          for rec in self:
               name_count2 = self.search([('name', '=ilike', rec.name)])
               name_count = self.search_count([('name', '=ilike', rec.name)])
               print("name_count ------------------ ", name_count)
               print("name_count2 ------------------ ", name_count2)
               if name_count > 1:
                    raise ValidationError("Attribute name already exist")
               if rec.name and not re.match(pattern, rec.name):
                    raise ValidationError("Attribute Name should be AlphaNumeric")

     def _log_changes(self, rec, vals, action):
          # Get the current time in UTC
          updated_write_date_utc = fields.Datetime.now()
          # Convert to the user's timezone
          user_tz = self.env.user.tz or 'UTC'  # Default to UTC if no timezone is set
          updated_write_date = updated_write_date_utc.astimezone(pytz.timezone(user_tz)).strftime("%d/%m/%Y %H:%M:%S")
          new_write_uid = self.env.user.display_name

          changes = []  # Store changes in list

          for key in vals:
               if key in ['name', 'code', 'active', 'create_variant', 'sequence', 'attribute_group',
                          'display_type', 'attribute_type_id', 'is_mandatory', 'is_required_in_clone',
                          'is_cloning', 'is_completeness', 'original_name', 'attribute_types',
                          'attribute_types_id', 'state', 'position_ref_field_id',
                          'unique_value', 'value_per_channel', 'value_per_locale', 'usable_in_grid',
                          'locale_specific', 'master_attribute_ids', 'label_transaltion','max_value','alpha_numeric_value']:

                    attribute = rec._fields[key].string

                    if key == 'attribute_group':
                         old_value = ', '.join(rec.attribute_group.mapped('display_name')) or 'N/A'

                         # Extract only the IDs from the command tuples (e.g., (4, id))
                         command_list = vals.get(key, [])
                         group_ids = []
                         for command in command_list:
                              if isinstance(command, (list, tuple)) and command[0] in [4, 6]:
                                   if command[0] == 4:
                                        group_ids.append(command[1])
                                   elif command[0] == 6 and isinstance(command[1], list):
                                        group_ids.extend(command[1])
                         new_value_recs = self.env['attribute.group'].browse(group_ids)
                         new_value = ', '.join(new_value_recs.mapped('display_name')) or 'N/A'
                    # if key == 'attribute_group':
                    #      old_value = rec.attribute_group.display_name if rec.attribute_group else 'N/A'
                    #      new_value = self.env['attribute.group'].browse(vals[key]).display_name if vals.get(
                    #           key) else 'N/A'
                    else:
                         # Set old_value to 'N/A' if creating a new record
                         old_value = getattr(rec, key, 'N/A') if action == "update" else 'N/A'
                         new_value = vals[key] or 'N/A'

                    # Formatting Old & New values on the same line with space
                    change_entry = f"""
                  <li>
                      <strong>{attribute}</strong><br>
                      <span style='color: red;'>Old value:</span> {old_value}  
                      &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
                      <span style='color: green;'>New value:</span> {new_value}
                  </li>
                  """
                    changes.append(change_entry)

          if changes:
               action_text = "Created by" if action == "create" else "Updated by"
               user_info = f"<small>{action_text} <strong>{new_write_uid}</strong> on {updated_write_date}</small>"

               full_message = f"""
              <div style="border-left: 3px solid #6C757D; padding-left: 10px; margin-bottom: 15px;">
                  {user_info}
                  <ul style="list-style-type: none; padding-left: 0;">{''.join(changes)}</ul>
              </div>
              """

               rec.history_log = tools.html_sanitize(full_message) + (rec.history_log or '')
    
     @api.model_create_multi
     def create(self, vals):
          rec = super(AttributeForm, self).create(vals)

          # # If attribute_group is set during creation
          # if vals.get('attribute_group'):
          #      for group in rec.attribute_group:
          #           existing_line = group.attribute_group_line_ids.filtered(
          #                lambda l: l.product_attribute_id == rec.id)
          #           if not existing_line:
          #                rec.env['attribute.group.lines'].create({
          #                     'attr_group_id': group.id,
          #                     'product_attribute_id': rec.id
          #                })
          self._log_changes(rec, vals, action="create")

          return rec

     def write(self, vals):
          for rec in self:
               rec._log_changes(rec, vals, action="update")
               original_groups = rec.attribute_group
               result = super(AttributeForm, rec).write(vals)

               if 'attribute_group' in vals:
                    updated_groups = rec.attribute_group
                    removed_groups = original_groups - updated_groups

                    for group in removed_groups:
                         if rec in group.attributes_ids:
                              group.attributes_ids = [(3, rec.id)]

                         lines_to_remove = group.attribute_group_line_ids.filtered(
                              lambda l: l.product_attribute_id == rec.id)
                         lines_to_remove.unlink()

               return result

          return super(AttributeForm, self).write(vals)

     def sort_colors(self):
          for record in self:
               colors_rgb = [tuple(int(rec.html_color[i:i + 2], 16) for i in (1, 3, 5)) for rec in record.value_ids]
               colors_hsv = [colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0) for r, g, b in colors_rgb]
               sorted_colors_hsv = sorted(colors_hsv, key=lambda x: (x[0], x[1], x[2]))
               sorted_colors_rgb = [colorsys.hsv_to_rgb(h, s, v) for h, s, v in sorted_colors_hsv]
               sorted_colors_rgb = [(round(r * 255), round(g * 255), round(b * 255)) for r, g, b in sorted_colors_rgb]
               # # Clear existing sorted colors
               vals_list = []
               for r, g, b in sorted_colors_rgb:
                    color = '#{:02x}{:02x}{:02x}'.format(r, g, b)
                    record_name = self.env['product.attribute.value'].search([('html_color', '=', color),
                                                                              ('attribute_id', '=', record.id)],
                                                                             order="id", limit=1)
                    vals_list.append((0, 0, {
                         'name': record_name.name,
                         'html_color': color,
                         'attribute_id': record.id,
                         'image': record_name.image
                    }))
               record.value_ids.unlink()
               record.value_ids = vals_list

     def unlink(self):
          for rec in self:
               field_val = self.env['ir.model.fields'].sudo().search([('name', '=ilike', rec.original_name)])
               field_val.unlink()

               if rec.display_type in ['link', 'file', 'image']:
                    field_file_name = rec.original_name + '_file_name'
                    field_val_binary = self.env['ir.model.fields'].sudo().search([('name', '=ilike', field_file_name)])
                    field_val_binary.unlink()

          result = super(AttributeForm, self).unlink()
          return result


class AttributeMasterUnlinkWizard(models.TransientModel):
    _name = 'attribute.master.unlink.wizard'
    _description = 'Wizard to Confirm Deletion of Attribute master'

    attribute_id = fields.Many2one('product.attribute', string="Attribute Master")

    def confirm_unlink(self):
        if self.attribute_id:
             self.attribute_id.unlink()
        return {
             'type': 'ir.actions.client',
             'tag': 'reload',
             }
