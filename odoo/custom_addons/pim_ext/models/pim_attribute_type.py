# -*- coding: utf-8 -*-
from random import randint
from odoo import models, api, fields,_,tools
import pytz
import colorsys
from odoo.exceptions import ValidationError

class PIMAttributeType(models.Model):
     _name = 'pim.attribute.type'
     _description = 'PIM Attribute Type'
     _rec_name = 'name'

     name = fields.Char(string="Attribute Name", default=' ')
     type_name = fields.Char(string="Attribute Type Name")
     attribute_types_id = fields.Many2one('pim.attribute.type', string='Parent Attributes', index=True, ondelete="cascade")
     attribute_ids = fields.One2many('pim.attribute.type', 'attribute_types_id', string='Attributes',  compute='_compute_attribute_ids')
     is_invisible=fields.Boolean(default=False, string='Invisible Types')
     attribute_group = fields.Many2one('attribute.group', string='Attribute Group', tracking=True)
     attribute_types = fields.Selection([('basic', 'Basic'), ('optional', 'Optional')], string='Attribute Type')
     is_mandatory = fields.Boolean(string='Mandatory', default=False)
     is_required_in_clone = fields.Boolean(string='Required in Clone', default=True)
     is_cloning = fields.Boolean(string='Cloning', default=True)
     is_completeness = fields.Boolean(string='Completeness')
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

     code = fields.Char(string='Code', readonly=True)

     unique_value = fields.Selection(
          [('yes', 'Yes'), ('no', 'No')],
          string='Unique Value',
          default='no'
     )

     value_per_channel = fields.Selection(
          [('yes', 'Yes'), ('no', 'No')],
          string='Value per channel',
          default='no'
     )

     value_per_locale = fields.Selection(
          [('yes', 'Yes'), ('no', 'No')],
          string='Value per locale',
          default='no'
     )

     usable_in_grid = fields.Selection(
          [('yes', 'Yes'), ('no', 'No')],
          string='Usable in grid',
          default='no'
     )

     locale_specific = fields.Selection(
          [('yes', 'Yes'), ('no', 'No')],
          string='Locale specific',
          default='no'
     )
     value_ids = fields.One2many(
          comodel_name='pim.attribute.value',
          inverse_name='attribute_type_id',
          string="Values", copy=True)

     history_log = fields.Html(string='History Log', help="This field stores the history of changes.")

     def _compute_attribute_ids(self):
          for record in self:
               record.attribute_ids = self.env['pim.attribute.type'].search([])

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
                    record_name = self.env['pim.attribute.value'].search([('html_color', '=', color),
                                                                              ('attribute_type_id', '=', record.id)],
                                                                             order="id", limit=1)
                    vals_list.append((0, 0, {
                         'name': record_name.name,
                         'html_color': color,
                         'attribute_type_id': record.id,
                         'image': record_name.image
                    }))
               record.value_ids.unlink()
               record.value_ids = vals_list

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
                          'attribute_types_id', 'completed_in_percent', 'state', 'position_ref_field_id',
                          'unique_value', 'value_per_channel', 'value_per_locale', 'usable_in_grid',
                          'locale_specific', 'master_attribute_ids', 'label_transaltion']:

                    attribute = rec._fields[key].string

                    if key == 'attribute_group':
                         old_value = rec.attribute_group.display_name if rec.attribute_group else 'N/A'
                         new_value = self.env['attribute.group'].browse(vals[key]).display_name if vals.get(
                              key) else 'N/A'
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

     def write(self, vals):
          res = super(PIMAttributeType, self).write(vals)

          # Fields that need to be updated in product.attribute
          fields_to_update = [
               'is_mandatory', 'is_required_in_clone', 'is_cloning', 'is_completeness'
          ]

          # Check if any of these fields were modified
          update_needed = any(field in vals for field in fields_to_update)

          if update_needed:
               for record in self:
                    product_attr = self.env['product.attribute'].search([('name', '=', record.name)], limit=1)
                    if product_attr:
                         update_vals = {field: record[field] for field in fields_to_update if field in vals}
                         product_attr.write(update_vals)

          # Log changes (existing functionality)
          for rec in self:
               self._log_changes(rec, vals, action="update")

          return res

     def create(self, vals):
          vals['code'] = self.env['ir.sequence'].next_by_code(
               'pim.attribute.type') or None
          record = super(PIMAttributeType, self).create(vals)
          self._log_changes(record, vals, action="create")
          return record

     def attribute_edit_open_form_view(self):
          self.ensure_one()
          return {
               'type': 'ir.actions.act_window',
               'name': 'Edit Attribute',
               # 'res_model': 'product.attribute',
               'view_mode': 'form',
               'res_model': 'pim.attribute.type',
               'view_id': self.env.ref('pim_ext.view_product_attribute_custom').id,
               'context': {'no_breadcrumbs': True},
               'res_id': self.id,
          }

     def attribute_master_unlink(self):
          return {
               'name': 'Confirm Deletion',
               'type': 'ir.actions.act_window',
               'res_model': 'attribute.master.unlink.wizard',
               'view_mode': 'form',
               'target': 'new',
               'context': {'default_attribute_types_id': self.id},
          }
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
                    'default_attribute_ids': self.env['pim.attribute.type'].search([]).ids,
               },
          }

     def create_attributes(self):
          self.ensure_one()
          attribute = self.env['product.attribute']

          values_list = []
          for value in self.value_ids:
               values_list.append([0, 0, {'name': value.name}])

          attribute_vals = {
               'name': self.name,
               'display_type': self.display_type,
               'attribute_group': self.attribute_group.id,
               'code': self.code,
               'is_mandatory': self.is_mandatory,
               'unique_value': self.unique_value,
               'value_per_channel': self.value_per_channel,
               'value_per_locale': self.value_per_locale,
               'usable_in_grid': self.usable_in_grid,
               'locale_specific': self.locale_specific,
               'is_required_in_clone': self.is_required_in_clone,
               'is_cloning': self.is_cloning,
               'is_completeness': self.is_completeness,
               # 'value_ids': values_list if values_list else [(0, 0, {
               #      'name': self.display_type.replace('_', ' '),
               # })]
          }

          # Check if an existing attribute exists
          existing_attribute = attribute.search([('name', '=', self.name)], limit=1)

          if existing_attribute:
               # Update existing attribute
               existing_attribute.write(attribute_vals)
               attribute = existing_attribute
          else:
               # Create new attribute
               attribute = attribute.create(attribute_vals)

          # Ensure attribute group lines are updated
          if self.attribute_group:
               group_line = self.env['attribute.group.lines'].search([
                    ('attr_group_id', '=', self.attribute_group.id),
                    ('product_attribute_id', '=', attribute.id),
               ], limit=1)

               if not group_line:
                    self.env['attribute.group.lines'].create({
                         'attr_group_id': self.attribute_group.id,
                         'product_attribute_id': attribute.id,
                    })
          for record in self:
               if record.display_type in ['simple_select', 'radio', 'pills', 'color',
                                          'multi_select'] and not record.value_ids:
                    raise ValidationError(
                         "Please fill the Attribute values for dropdown.")

          menu_id = self.env.ref('pim_ext.menu_pim_attribute_action')
          # return {
          #      'type': 'ir.actions.client',
          #      'tag': 'reload',
          #      'params': {
          #           'menu_id': menu_id.id,
          #      },
          # }


     # def cancel_attributes(self):
     #      return{
     #           'type': 'ir.actions.act_window',
     #           'res_model': 'product.attribute',
     #           'view_mode':'tree,form',
     #           'target': 'current',
     #           'context': {'no_breadcrumbs': True},
     #      }

     # def action_back_to_menu_attribute(self):
     #      menu_id = self.env.ref('pim_ext.menu_pim_attribute_action')
     #      return {
     #           'type': 'ir.actions.client',
     #           'tag': 'reload',
     #           'params': {
     #                'menu_id': menu_id.id,
     #           },
     #      }

     def action_back_to_menu_attribute(self):
          self.ensure_one()
          menu_id = self.env.ref('pim_ext.menu_pim_attribute_action')
          if not self.name or self.name.strip() == '' and not self.display_type:
               self._cr.execute("DELETE FROM pim_attribute_type WHERE id = %s", (self._origin.id,))
               self._cr.commit()
               return {
                    'type': 'ir.actions.client',
                    'tag': 'reload',
                    'params': {
                         'menu_id': menu_id.id,
                    },
               }
          elif self.display_type and self.name.strip() == '':
               raise ValidationError("You should fill the attribute name.")
          return {
               'type': 'ir.actions.client',
               'tag': 'reload',
               'params': {
                    'menu_id': menu_id.id,
               },
          }

     def action_select_date(self):
          self.ensure_one()
          empty_record = self.env['pim.attribute.type'].search([
               ('type_name', '=', False),
               ('create_uid', '=', self.env.user.id),
          ], order='create_date desc', limit=1)

          if empty_record:
               empty_record.write({
                    'attribute_ids': [(6, 0, self.env['pim.attribute.type'].search([]).ids)],
                    'is_invisible': True,
                    'display_type': 'date',
                    'type_name': 'Date',
               })
               return {
                    'type': 'ir.actions.act_window',
                    'name': 'Date Attribute',
                    'res_model': 'pim.attribute.type',
                    'view_id': self.env.ref('pim_ext.view_product_attribute_custom').id,
                    'view_mode': 'form',
                    'res_id': empty_record.id,
               }
          else:
               new_record = self.env['pim.attribute.type'].create({
                    'attribute_ids': [(6, 0, self.env['pim.attribute.type'].search([]).ids)],
                    'is_invisible': True,
                    'display_type': 'date',
                    'type_name': 'Date',
               })
               return {
                    'type': 'ir.actions.act_window',
                    'name': 'Date Attribute',
                    'res_model': 'pim.attribute.type',
                    'view_id': self.env.ref('pim_ext.view_product_attribute_custom').id,
                    'view_mode': 'form',
                    'res_id': new_record.id,
               }

     def action_select_file(self):
          self.ensure_one()
          empty_record = self.env['pim.attribute.type'].search([
               ('type_name', '=', False),
               ('create_uid', '=', self.env.user.id),
          ], order='create_date desc', limit=1)

          if empty_record:
               empty_record.write({
                    'attribute_ids': [(6, 0, self.env['pim.attribute.type'].search([]).ids)],
                    'is_invisible': True,
                    'display_type': 'file',
                    'type_name': 'File',
               })
               return {
                    'type': 'ir.actions.act_window',
                    'name': 'File Attribute',
                    'res_model': 'pim.attribute.type',
                    'view_id': self.env.ref('pim_ext.view_product_attribute_custom').id,
                    'view_mode': 'form',
                    'res_id': empty_record.id,
               }
          else:
               new_record = self.env['pim.attribute.type'].create({
                    'attribute_ids': [(6, 0, self.env['pim.attribute.type'].search([]).ids)],
                    'is_invisible': True,
                    'display_type': 'file',
                    'type_name': 'File',
               })
               return {
                    'type': 'ir.actions.act_window',
                    'name': 'File Attribute',
                    'res_model': 'pim.attribute.type',
                    'view_id': self.env.ref('pim_ext.view_product_attribute_custom').id,
                    'view_mode': 'form',
                    'res_id': new_record.id,
               }

     def action_select_identifier(self):
          self.ensure_one()
          empty_record = self.env['pim.attribute.type'].search([
               ('type_name', '=', False),
               ('create_uid', '=', self.env.user.id),
          ], order='create_date desc', limit=1)

          if empty_record:
               empty_record.write({
                    'attribute_ids': [(6, 0, self.env['pim.attribute.type'].search([]).ids)],
                    'is_invisible': True,
                    'display_type': 'identifier',
                    'type_name': 'Identifier',
               })
               return {
                    'type': 'ir.actions.act_window',
                    'name': 'Identifier Attribute',
                    'res_model': 'pim.attribute.type',
                    'view_id': self.env.ref('pim_ext.view_product_attribute_custom').id,
                    'view_mode': 'form',
                    'res_id': empty_record.id,
               }
          else:
               new_record = self.env['pim.attribute.type'].create({
                    'attribute_ids': [(6, 0, self.env['pim.attribute.type'].search([]).ids)],
                    'is_invisible': True,
                    'display_type': 'identifier',
                    'type_name': 'Identifier',
               })
               return {
                    'type': 'ir.actions.act_window',
                    'name': 'Identifier Attribute',
                    'res_model': 'pim.attribute.type',
                    'view_id': self.env.ref('pim_ext.view_product_attribute_custom').id,
                    'view_mode': 'form',
                    'res_id': new_record.id,
               }

     def action_select_image(self):
          self.ensure_one()
          empty_record = self.env['pim.attribute.type'].search([
               ('type_name', '=', False),
               ('create_uid', '=', self.env.user.id),
          ], order='create_date desc', limit=1)

          if empty_record:
               empty_record.write({
                    'attribute_ids': [(6, 0, self.env['pim.attribute.type'].search([]).ids)],
                    'is_invisible': True,
                    'display_type': 'image',
                    'type_name': 'Image',
               })
               return {
                    'type': 'ir.actions.act_window',
                    'name': 'Image Attribute',
                    'res_model': 'pim.attribute.type',
                    'view_id': self.env.ref('pim_ext.view_product_attribute_custom').id,
                    'view_mode': 'form',
                    'res_id': empty_record.id,
               }
          else:
               new_record = self.env['pim.attribute.type'].create({
                    'attribute_ids': [(6, 0, self.env['pim.attribute.type'].search([]).ids)],
                    'is_invisible': True,
                    'display_type': 'image',
                    'type_name': 'Image',
               })
               return {
                    'type': 'ir.actions.act_window',
                    'name': 'Image Attribute',
                    'res_model': 'pim.attribute.type',
                    'view_id': self.env.ref('pim_ext.view_product_attribute_custom').id,
                    'view_mode': 'form',
                    'res_id': new_record.id,
               }

     # def action_select_measurement(self):
     #      self.ensure_one()
     #      return {
     #           'type': 'ir.actions.act_window',
     #           'name': 'Measurement Attribute',
     #           'res_model': 'pim.attribute.type',
     #           'view_id': self.env.ref('pim_ext.view_product_attribute_custom').id,
     #           'view_mode': 'form',
     #           'context': {
     #                'default_attribute_ids': self.env['product.attribute'].search([]).ids,
     #                'default_is_invisible': True,
     #                'default_display_type': 'measurement',
     #                'default_type_name': 'Measurement',
     #           },
     #      }

     def action_select_link(self):
          self.ensure_one()
          empty_record = self.env['pim.attribute.type'].search([
               ('type_name', '=', False),
               ('create_uid', '=', self.env.user.id),
          ], order='create_date desc', limit=1)

          if empty_record:
               empty_record.write({
                    'attribute_ids': [(6, 0, self.env['pim.attribute.type'].search([]).ids)],
                    'is_invisible': True,
                    'display_type': 'link',
                    'type_name': 'Link',
               })
               return {
                    'type': 'ir.actions.act_window',
                    'name': 'Link',
                    'res_model': 'pim.attribute.type',
                    'view_id': self.env.ref('pim_ext.view_product_attribute_custom').id,
                    'view_mode': 'form',
                    'res_id': empty_record.id,
               }
          else:
               new_record = self.env['pim.attribute.type'].create({
                    'attribute_ids': [(6, 0, self.env['pim.attribute.type'].search([]).ids)],
                    'is_invisible': True,
                    'display_type': 'link',
                    'type_name': 'Link',
               })
               return {
                    'type': 'ir.actions.act_window',
                    'name': 'Link',
                    'res_model': 'pim.attribute.type',
                    'view_id': self.env.ref('pim_ext.view_product_attribute_custom').id,
                    'view_mode': 'form',
                    'res_id': new_record.id,
               }

     def action_select_multiselect(self):
          self.ensure_one()
          empty_record = self.env['pim.attribute.type'].search([
               ('type_name', '=', False),
               ('create_uid', '=', self.env.user.id),
          ], order='create_date desc', limit=1)

          if empty_record:
               empty_record.write({
                    'attribute_ids': [(6, 0, self.env['pim.attribute.type'].search([]).ids)],
                    'is_invisible': True,
                    'display_type': 'multi_select',
                    'type_name': 'Multi_select',
               })
               return {
                    'type': 'ir.actions.act_window',
                    'name': 'Multi Select Attribute',
                    'res_model': 'pim.attribute.type',
                    'view_id': self.env.ref('pim_ext.view_product_attribute_custom').id,
                    'view_mode': 'form',
                    'res_id': empty_record.id,
               }
          else:
               new_record = self.env['pim.attribute.type'].create({
                    'attribute_ids': [(6, 0, self.env['pim.attribute.type'].search([]).ids)],
                    'is_invisible': True,
                    'display_type': 'multi_select',
                    'type_name': 'Multi_select',
               })
               return {
                    'type': 'ir.actions.act_window',
                    'name': 'Multi Select Attribute',
                    'res_model': 'pim.attribute.type',
                    'view_id': self.env.ref('pim_ext.view_product_attribute_custom').id,
                    'view_mode': 'form',
                    'res_id': new_record.id,
               }

     def action_select_number(self):
          self.ensure_one()
          empty_record = self.env['pim.attribute.type'].search([
               ('type_name', '=', False),
               ('create_uid', '=', self.env.user.id),
          ], order='create_date desc', limit=1)

          if empty_record:
               empty_record.write({
                    'attribute_ids': [(6, 0, self.env['pim.attribute.type'].search([]).ids)],
                    'is_invisible': True,
                    'display_type': 'number',
                    'type_name': 'Integer',
               })
               return {
                    'type': 'ir.actions.act_window',
                    'name': 'Number Attribute',
                    'res_model': 'pim.attribute.type',
                    'view_id': self.env.ref('pim_ext.view_product_attribute_custom').id,
                    'view_mode': 'form',
                    'res_id': empty_record.id,
               }
          else:
               new_record = self.env['pim.attribute.type'].create({
                    'attribute_ids': [(6, 0, self.env['pim.attribute.type'].search([]).ids)],
                    'is_invisible': True,
                    'display_type': 'number',
                    'type_name': 'Integer',
               })
               return {
                    'type': 'ir.actions.act_window',
                    'name': 'Number Attribute',
                    'res_model': 'pim.attribute.type',
                    'view_id': self.env.ref('pim_ext.view_product_attribute_custom').id,
                    'view_mode': 'form',
                    'res_id': new_record.id,
               }

     def action_select_price(self):
          self.ensure_one()
          empty_record = self.env['pim.attribute.type'].search([
               ('type_name', '=', False),
               ('create_uid', '=', self.env.user.id),
          ], order='create_date desc', limit=1)

          if empty_record:
               empty_record.write({
                    'attribute_ids': [(6, 0, self.env['pim.attribute.type'].search([]).ids)],
                    'is_invisible': True,
                    'display_type': 'price',
                    'type_name': 'Price',
               })
               return {
                    'type': 'ir.actions.act_window',
                    'name': 'Price Attribute',
                    'res_model': 'pim.attribute.type',
                    'view_id': self.env.ref('pim_ext.view_product_attribute_custom').id,
                    'view_mode': 'form',
                    'res_id': empty_record.id,
               }
          else:
               new_record = self.env['pim.attribute.type'].create({
                    'attribute_ids': [(6, 0, self.env['pim.attribute.type'].search([]).ids)],
                    'is_invisible': True,
                    'display_type': 'price',
                    'type_name': 'Price',
               })
               return {
                    'type': 'ir.actions.act_window',
                    'name': 'Price Attribute',
                    'res_model': 'pim.attribute.type',
                    'view_id': self.env.ref('pim_ext.view_product_attribute_custom').id,
                    'view_mode': 'form',
                    'res_id': new_record.id,
               }

     def action_select_ref_data_multi(self):
          self.ensure_one()
          empty_record = self.env['pim.attribute.type'].search([
               ('type_name', '=', False),
               ('create_uid', '=', self.env.user.id),
          ], order='create_date desc', limit=1)

          if empty_record:
               empty_record.write({
                    'attribute_ids': [(6, 0, self.env['pim.attribute.type'].search([]).ids)],
                    'is_invisible': True,
                    'display_type': 'ref_data_multi',
                    'type_name': 'Ref Data Multi Select Attribute',
               })
               return {
                    'type': 'ir.actions.act_window',
                    'name': 'Ref Data Multi Select Attribute',
                    'res_model': 'pim.attribute.type',
                    'view_id': self.env.ref('pim_ext.view_product_attribute_custom').id,
                    'view_mode': 'form',
                    'res_id': empty_record.id,
               }
          else:
               new_record = self.env['pim.attribute.type'].create({
                    'attribute_ids': [(6, 0, self.env['pim.attribute.type'].search([]).ids)],
                    'is_invisible': True,
                    'display_type': 'ref_data_multi',
                    'type_name': 'Ref Data Multi Select Attribute',
               })
               return {
                    'type': 'ir.actions.act_window',
                    'name': 'Ref Data Multi Select Attribute',
                    'res_model': 'pim.attribute.type',
                    'view_id': self.env.ref('pim_ext.view_product_attribute_custom').id,
                    'view_mode': 'form',
                    'res_id': new_record.id,
               }

     def action_select_ref_data_simple(self):
          self.ensure_one()
          empty_record = self.env['pim.attribute.type'].search([
               ('type_name', '=', False),
               ('create_uid', '=', self.env.user.id),
          ], order='create_date desc', limit=1)

          if empty_record:
               empty_record.write({
                    'attribute_ids': [(6, 0, self.env['pim.attribute.type'].search([]).ids)],
                    'is_invisible': True,
                    'display_type': 'ref_data_simple_select',
                    'type_name': 'Ref Data Simple Select Attribute',
               })
               return {
                    'type': 'ir.actions.act_window',
                    'name': 'Ref Data Simple Select Attribute',
                    'res_model': 'pim.attribute.type',
                    'view_id': self.env.ref('pim_ext.view_product_attribute_custom').id,
                    'view_mode': 'form',
                    'res_id': empty_record.id,
               }
          else:
               new_record = self.env['pim.attribute.type'].create({
                    'attribute_ids': [(6, 0, self.env['pim.attribute.type'].search([]).ids)],
                    'is_invisible': True,
                    'display_type': 'ref_data_simple_select',
                    'type_name': 'Ref Data Simple Select Attribute',
               })
               return {
                    'type': 'ir.actions.act_window',
                    'name': 'Ref Data Simple Select Attribute',
                    'res_model': 'pim.attribute.type',
                    'view_id': self.env.ref('pim_ext.view_product_attribute_custom').id,
                    'view_mode': 'form',
                    'res_id': new_record.id,
               }

     def action_select_multi_checkbox(self):
          self.ensure_one()
          empty_record = self.env['pim.attribute.type'].search([
               ('type_name', '=', False),
               ('create_uid', '=', self.env.user.id),
          ], order='create_date desc', limit=1)

          if empty_record:
               empty_record.write({
                    'attribute_ids': [(6, 0, self.env['pim.attribute.type'].search([]).ids)],
                    'is_invisible': True,
                    'display_type': 'multi_checkbox',
                    'type_name': 'Multi Checkbox',
               })
               return {
                    'type': 'ir.actions.act_window',
                    'name': 'Multi Checkbox',
                    'res_model': 'pim.attribute.type',
                    'view_id': self.env.ref('pim_ext.view_product_attribute_custom').id,
                    'view_mode': 'form',
                    'res_id': empty_record.id,
               }
          else:
               new_record = self.env['pim.attribute.type'].create({
                    'attribute_ids': [(6, 0, self.env['pim.attribute.type'].search([]).ids)],
                    'is_invisible': True,
                    'display_type': 'multi_checkbox',
                    'type_name': 'Multi Checkbox',
               })
               return {
                    'type': 'ir.actions.act_window',
                    'name': 'Multi Checkbox',
                    'res_model': 'pim.attribute.type',
                    'view_id': self.env.ref('pim_ext.view_product_attribute_custom').id,
                    'view_mode': 'form',
                    'res_id': new_record.id,
               }

     def action_select_multi_color(self):
          self.ensure_one()
          empty_record = self.env['pim.attribute.type'].search([
               ('type_name', '=', False),
               ('create_uid', '=', self.env.user.id),
          ], order='create_date desc', limit=1)

          if empty_record:
               empty_record.write({
                    'attribute_ids': [(6, 0, self.env['pim.attribute.type'].search([]).ids)],
                    'is_invisible': True,
                    'display_type': 'color',
                    'type_name': 'Color',
               })
               return {
                    'type': 'ir.actions.act_window',
                    'name': 'Color',
                    'res_model': 'pim.attribute.type',
                    'view_id': self.env.ref('pim_ext.view_product_attribute_custom').id,
                    'view_mode': 'form',
                    'res_id': empty_record.id,
               }
          else:
               new_record = self.env['pim.attribute.type'].create({
                    'attribute_ids': [(6, 0, self.env['pim.attribute.type'].search([]).ids)],
                    'is_invisible': True,
                    'display_type': 'color',
                    'type_name': 'Color',
               })
               return {
                    'type': 'ir.actions.act_window',
                    'name': 'Color',
                    'res_model': 'pim.attribute.type',
                    'view_id': self.env.ref('pim_ext.view_product_attribute_custom').id,
                    'view_mode': 'form',
                    'res_id': new_record.id,
               }

     def action_select_radio(self):
          self.ensure_one()
          empty_record = self.env['pim.attribute.type'].search([
               ('type_name', '=', False),
               ('create_uid', '=', self.env.user.id),
          ], order='create_date desc', limit=1)

          if empty_record:
               empty_record.write({
                    'attribute_ids': [(6, 0, self.env['pim.attribute.type'].search([]).ids)],
                    'is_invisible': True,
                    'display_type': 'radio',
                    'type_name': 'Radio',
               })
               return {
                    'type': 'ir.actions.act_window',
                    'name': 'Radio',
                    'res_model': 'pim.attribute.type',
                    'view_id': self.env.ref('pim_ext.view_product_attribute_custom').id,
                    'view_mode': 'form',
                    'res_id': empty_record.id,
               }
          else:
               new_record = self.env['pim.attribute.type'].create({
                    'attribute_ids': [(6, 0, self.env['pim.attribute.type'].search([]).ids)],
                    'is_invisible': True,
                    'display_type': 'radio',
                    'type_name': 'Radio',
               })
               return {
                    'type': 'ir.actions.act_window',
                    'name': 'Radio',
                    'res_model': 'pim.attribute.type',
                    'view_id': self.env.ref('pim_ext.view_product_attribute_custom').id,
                    'view_mode': 'form',
                    'res_id': new_record.id,
               }

     def action_select_simple(self):
          self.ensure_one()
          empty_record = self.env['pim.attribute.type'].search([
               ('type_name', '=', False),
               ('create_uid', '=', self.env.user.id),
          ], order='create_date desc', limit=1)

          if empty_record:
               empty_record.write({
                    'attribute_ids': [(6, 0, self.env['pim.attribute.type'].search([]).ids)],
                    'is_invisible': True,
                    'display_type': 'simple_select',
                    'type_name': 'Simple Select Attribute',
               })
               return {
                    'type': 'ir.actions.act_window',
                    'name': 'Simple Select Attribute',
                    'res_model': 'pim.attribute.type',
                    'view_id': self.env.ref('pim_ext.view_product_attribute_custom').id,
                    'view_mode': 'form',
                    'res_id': empty_record.id,
               }
          else:
               new_record = self.env['pim.attribute.type'].create({
                    'attribute_ids': [(6, 0, self.env['pim.attribute.type'].search([]).ids)],
                    'is_invisible': True,
                    'display_type': 'simple_select',
                    'type_name': 'Simple Select Attribute',
               })
               return {
                    'type': 'ir.actions.act_window',
                    'name': 'Simple Select Attribute',
                    'res_model': 'pim.attribute.type',
                    'view_id': self.env.ref('pim_ext.view_product_attribute_custom').id,
                    'view_mode': 'form',
                    'res_id': new_record.id,
               }

     def action_select_text(self):
          self.ensure_one()

          # First, let's find the most recently created empty record
          # Assuming an empty record means minimal fields filled
          empty_record = self.env['pim.attribute.type'].search([
               ('type_name', '=', False),  # or other fields that would be empty
               ('create_uid', '=', self.env.user.id),  # created by current user
          ], order='create_date desc', limit=1)

          if empty_record:
               # Update the empty record with the context values
               empty_record.write({
                    'attribute_ids': [(6, 0, self.env['pim.attribute.type'].search([]).ids)],
                    'is_invisible': True,
                    'display_type': 'text',
                    'type_name': 'Text Attribute',
               })

               return {
                    'type': 'ir.actions.act_window',
                    'name': 'Text Attribute',
                    'res_model': 'pim.attribute.type',
                    'view_id': self.env.ref('pim_ext.view_product_attribute_custom').id,
                    'view_mode': 'form',
                    'res_id': empty_record.id,  # Open the updated record
               }
          else:
               # If no empty record found, create a new one
               new_record = self.env['pim.attribute.type'].create({
                    'attribute_ids': [(6, 0, self.env['pim.attribute.type'].search([]).ids)],
                    'is_invisible': True,
                    'display_type': 'text',
                    'type_name': 'Text Attribute',
               })

               return {
                    'type': 'ir.actions.act_window',
                    'name': 'Text Attribute',
                    'res_model': 'pim.attribute.type',
                    'view_id': self.env.ref('pim_ext.view_product_attribute_custom').id,
                    'view_mode': 'form',
                    'res_id': new_record.id,
               }

     def action_select_text_area(self):
          self.ensure_one()
          empty_record = self.env['pim.attribute.type'].search([
               ('type_name', '=', False),
               ('create_uid', '=', self.env.user.id),
          ], order='create_date desc', limit=1)

          if empty_record:
               empty_record.write({
                    'attribute_ids': [(6, 0, self.env['pim.attribute.type'].search([]).ids)],
                    'is_invisible': True,
                    'display_type': 'textarea',
                    'type_name': 'TextArea',
               })
               return {
                    'type': 'ir.actions.act_window',
                    'name': 'TextArea Attribute',
                    'res_model': 'pim.attribute.type',
                    'view_id': self.env.ref('pim_ext.view_product_attribute_custom').id,
                    'view_mode': 'form',
                    'res_id': empty_record.id,
               }
          else:
               new_record = self.env['pim.attribute.type'].create({
                    'attribute_ids': [(6, 0, self.env['pim.attribute.type'].search([]).ids)],
                    'is_invisible': True,
                    'display_type': 'textarea',
                    'type_name': 'TextArea',
               })
               return {
                    'type': 'ir.actions.act_window',
                    'name': 'TextArea Attribute',
                    'res_model': 'pim.attribute.type',
                    'view_id': self.env.ref('pim_ext.view_product_attribute_custom').id,
                    'view_mode': 'form',
                    'res_id': new_record.id,
               }

     def action_select_yes_no(self):
          self.ensure_one()
          empty_record = self.env['pim.attribute.type'].search([
               ('type_name', '=', False),
               ('create_uid', '=', self.env.user.id),
          ], order='create_date desc', limit=1)

          if empty_record:
               empty_record.write({
                    'attribute_ids': [(6, 0, self.env['pim.attribute.type'].search([]).ids)],
                    'is_invisible': True,
                    'display_type': 'yes_no',
                    'type_name': 'Checkbox',
               })
               return {
                    'type': 'ir.actions.act_window',
                    'name': 'Yes/No Attribute',
                    'res_model': 'pim.attribute.type',
                    'view_id': self.env.ref('pim_ext.view_product_attribute_custom').id,
                    'view_mode': 'form',
                    'res_id': empty_record.id,
               }
          else:
               new_record = self.env['pim.attribute.type'].create({
                    'attribute_ids': [(6, 0, self.env['pim.attribute.type'].search([]).ids)],
                    'is_invisible': True,
                    'display_type': 'yes_no',
                    'type_name': 'Checkbox',
               })
               return {
                    'type': 'ir.actions.act_window',
                    'name': 'Yes/No Attribute',
                    'res_model': 'pim.attribute.type',
                    'view_id': self.env.ref('pim_ext.view_product_attribute_custom').id,
                    'view_mode': 'form',
                    'res_id': new_record.id,
               }


class PimAttributeValue(models.Model):
    _name = 'pim.attribute.value'

    def _get_default_color(self):
        return randint(1, 11)

    attribute_type_id = fields.Many2one('pim.attribute.type',ondelete='cascade',
         required=True,
         index=True)
    name = fields.Char(string="Value", required=True, translate=True)
    sequence = fields.Integer(string="Sequence", help="Determine the display order", index=True)
    html_color = fields.Char(
         string="Color",
         help="Here you can set a specific HTML color index (e.g. #ff0000)"
              " to display the color if the attribute type is 'Color'.")
    display_type = fields.Selection(related='attribute_type_id.display_type')
    color = fields.Integer(string="Color Index", default=_get_default_color)
    image = fields.Image(
         string="Image",
         help="You can upload an image that will be used as the color of the attribute value.",
         max_width=70,
         max_height=70,
    )
