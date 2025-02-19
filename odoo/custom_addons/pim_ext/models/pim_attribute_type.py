# -*- coding: utf-8 -*-

from odoo import models, api, fields,_,tools
import pytz

class PIMAttributeType(models.Model):
     _name = 'pim.attribute.type'
     _description = 'PIM Attribute Type'
     _rec_name = 'name'

     name = fields.Char(string="Attribute Name", default=' ')
     type_name = fields.Char(string="Attribute Type Name")
     attribute_ids = fields.One2many('product.attribute', 'attribute_types_id', string='Attributes')
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

     code = fields.Char(string='Code')

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
     value_ids = fields.Many2many(
          comodel_name='product.attribute.value',
          relation='attribute_text_value_product_template_rel',
          string="Values",
          # domain="[('attribute_id', '=', attribute_id)]",
          ondelete='cascade')

     history_log = fields.Html(string='History Log', help="This field stores the history of changes.")

     def write(self, vals):
          for rec in self:
               # Get the current time in UTC
               updated_write_date_utc = fields.Datetime.now()
               # Convert to the user's timezone
               user_tz = self.env.user.tz or 'UTC'  # Default to UTC if no timezone is set
               updated_write_date = updated_write_date_utc.astimezone(pytz.timezone(user_tz)).strftime(
                    "%d/%m/%Y %H:%M:%S")
               new_write_uid = self.env.user.display_name

               changes = []  # Store changes in list

               for key in vals:
                    if key in ['name', 'code', 'active', 'create_variant', 'sequence', 'attribute_group',
                               'display_type',
                               'attribute_type_id', 'is_mandatory', 'is_required_in_clone', 'is_cloning',
                               'is_completeness',
                               'original_name', 'attribute_types', 'attribute_types_id', 'completed_in_percent',
                               'state',
                               'position_ref_field_id', 'unique_value', 'value_per_channel', 'value_per_locale',
                               'usable_in_grid',
                               'locale_specific', 'master_attribute_ids', 'label_transaltion']:

                         attribute = rec._fields[key].string

                         if key == 'attribute_group':
                              old_value = rec.attribute_group.display_name if rec.attribute_group else 'N/A'
                              new_value = self.env['attribute.group'].browse(vals[key]).display_name if vals.get(
                                   key) else 'N/A'
                         else:
                              old_value = getattr(rec, key) or 'N/A'
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
                    user_info = f"<small>Updated by <strong>{new_write_uid}</strong> on {updated_write_date}</small>"

                    full_message = f"""
                     <div style="border-left: 3px solid #6C757D; padding-left: 10px; margin-bottom: 15px;">
                         {user_info}
                         <ul style="list-style-type: none; padding-left: 0;">{''.join(changes)}</ul>
                     </div>
                 """

                    rec.history_log = tools.html_sanitize(full_message) + (rec.history_log or '')

          return super(PIMAttributeType, self).write(vals)

     def create_attributes(self):

          if all([self.name, self.display_type]):
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
                    'value_ids': [(0, 0, {
                         'name': self.display_type.replace('_', ' '),
                    })]
               }
          attribute = self.env['product.attribute'].create(attribute_vals)

          if self.attribute_group:
               self.env['attribute.group.lines'].create({
                    'attr_group_id': self.attribute_group.id,
                    'product_attribute_id': attribute.id,
               })

          menu_id = self.env.ref('pim_ext.menu_pim_attribute_action')
          return {
               'type': 'ir.actions.client',
               'tag': 'reload',
               'params': {
                    'menu_id': menu_id.id,
               },
          }
          # return {
          #      'type': 'ir.actions.act_window',
          #      'res_model': 'product.attribute',
          #      'view_mode':'list,form',
          #      'target': 'current',
          #      'context': {'no_breadcrumbs': True},
          # }


     # def cancel_attributes(self):
     #      return{
     #           'type': 'ir.actions.act_window',
     #           'res_model': 'product.attribute',
     #           'view_mode':'tree,form',
     #           'target': 'current',
     #           'context': {'no_breadcrumbs': True},
     #      }

     def action_back_to_menu_attribute(self):
          menu_id = self.env.ref('pim_ext.menu_pim_attribute_action')

          # return {
          #      'type': 'ir.actions.act_window',
          #      'res_model': 'product.attribute',
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
          return {
               'type': 'ir.actions.act_window',
               'name': 'Link',
               'res_model': 'pim.attribute.type',
               'view_id': self.env.ref('pim_ext.view_product_attribute_custom').id,
               'view_mode': 'form',
               'context': {
                    'default_attribute_ids': self.env['product.attribute'].search([]).ids,
                    'default_is_invisible': True,
                    'default_display_type': 'link',
                    'default_type_name': 'Link',
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
                    'default_type_name': 'Integer',
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

     def action_select_multi_checkbox(self):
          self.ensure_one()
          return {
               'type': 'ir.actions.act_window',
               'name': 'Multi Checkbox',
               'res_model': 'pim.attribute.type',
               'view_id': self.env.ref('pim_ext.view_product_attribute_custom').id,
               'view_mode': 'form',
               'context': {
                    'default_attribute_ids': self.env['product.attribute'].search([]).ids,
                    'default_is_invisible': True,
                    'default_display_type': 'multi_checkbox',
                    'default_type_name': 'Multi Checkbox',
               },
          }

     def action_select_multi_color(self):
          self.ensure_one()
          return {
               'type': 'ir.actions.act_window',
               'name': 'Color',
               'res_model': 'pim.attribute.type',
               'view_id': self.env.ref('pim_ext.view_product_attribute_custom').id,
               'view_mode': 'form',
               'context': {
                    'default_attribute_ids': self.env['product.attribute'].search([]).ids,
                    'default_is_invisible': True,
                    'default_display_type': 'color',
                    'default_type_name': 'Color',
               },
          }

     def action_select_radio(self):
          self.ensure_one()
          return {
               'type': 'ir.actions.act_window',
               'name': 'Radio',
               'res_model': 'pim.attribute.type',
               'view_id': self.env.ref('pim_ext.view_product_attribute_custom').id,
               'view_mode': 'form',
               'context': {
                    'default_attribute_ids': self.env['product.attribute'].search([]).ids,
                    'default_is_invisible': True,
                    'default_display_type': 'radio',
                    'default_type_name': 'Radio',
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
                    'default_type_name': 'Checkbox',
               },
          }

