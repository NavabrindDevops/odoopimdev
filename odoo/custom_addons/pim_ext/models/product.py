# -*- coding: utf-8 -*-

import time,pytz
import re
from datetime import datetime,timedelta,timezone,date
from email.policy import default
from markupsafe import Markup
import pytz

from lxml import etree
from odoo import models, api, fields,_, tools
from odoo.exceptions import UserError, ValidationError
import traceback,pdb,inspect

from odoo.tools import drop_view_if_exists
import logging
from googletrans import Translator


_logger = logging.getLogger(__name__)

class ManufacturerAttribute(models.Model):
     _name = 'manufacturer.attribute'
     _description ='Manufacturer Attribute'
     _inherit = ['mail.thread', 'mail.activity.mixin']

     name = fields.Char('Name', required=True, tracking=True)

class BrandAttribute(models.Model):
     _name = 'brand.attribute'
     _description = 'Brand Attribute'
     _inherit = ['mail.thread', 'mail.activity.mixin']

     name = fields.Char('Name', required=True, tracking=True)

      
class FamilyProducts(models.Model):
     _name = 'family.products'
     _description='Family Products'

     product_id = fields.Many2one('product.template', 'Product', required=True)
     default_code = fields.Char('SKU #')
     family_id = fields.Many2one('family.attribute','Family')
     mpn_number = fields.Char('MPN')
     status = fields.Selection([('active','Active'),('inactive','In Active')],'Status')
     origin = fields.Char('Origin')
     po_min = fields.Integer('PO Min')
     po_max = fields.Integer('PO Max')
     p65 = fields.Char('P65')
     # attribute1_id = fields.Many2one('product.attribute1','',related='family_id.attribute1_id',)
     attribute1_val = fields.Char('Attribute 1')
     # attribute2_id = fields.Many2one('product.attribute2','',related='family_id.attribute2_id',)
     attribute2_val = fields.Char('Attribute 2')
     # attribute3_id = fields.Many2one('product.attribute3','',related='family_id.attribute3_id',)
     attribute3_val = fields.Char('Attribute 3')
     # attribute4_id = fields.Many2one('product.attribute4','',related='family_id.attribute4_id',)
     attribute4_val = fields.Char('Attribute 4')
     select_sku = fields.Boolean('Select')



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
     # attribute1_id = fields.Many2one('product.attribute1','Attribute 1')
     attribute1_val = fields.Char('Value 1')
     # attribute2_id = fields.Many2one('product.attribute2','Attribute 2')
     attribute2_val = fields.Char('Value 2')
     # attribute3_id = fields.Many2one('product.attribute3','Attribute 3')
     attribute3_val = fields.Char('Value 3')
     # attribute4_id = fields.Many2one('product.attribute4','Attribute 4')
     attribute4_val = fields.Char('Value 4')
     active_label = fields.Char(string="Status ", compute="_compute_active_label")

     readable_variant_names = fields.Char(string="Variants", compute="_compute_readable_variant_names")
     family_id = fields.Many2one('family.attribute', string='Family', readonly=True)
     sku = fields.Char(string='SKU')
     brand_id = fields.Many2one('product.brand', string='Brand')
     category_id = fields.Many2one('pim.category', string='Category')

     parent_id = fields.Many2one(
          'product.create',
          string='Parent Group',
          ondelete='cascade',
     )

     product_master_id = fields.Many2one(
          'product.create.master',
          string='Parent Group ',
          ondelete='cascade',
     )

     product_parent_id = fields.Many2one(
          'product.template',
          string='Parent-Group',
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
     product_attr_values_id = fields.Many2many('product.attribute.value', 'attr_value_id', 'products_id', string='Attribute Values ', readonly=True)
     product_attr_ids = fields.One2many('product.attribute', 'products_id', string='Attributes')
     is_variant_update = fields.Boolean(string='Variant updated', default=False)
     image_1 = fields.Image("Image1", max_width=1920, max_height=1920, compute="_compute_first_image",
        store=False)
     image_2 = fields.Image("Image2", max_width=1920, max_height=1920)
     image_3= fields.Image("Image3", max_width=1920, max_height=1920)
     image_4 = fields.Image("Image4", max_width=1920, max_height=1920)
     image_5 = fields.Image("Image5", max_width=1920, max_height=1920)
     image_6 = fields.Image("Image6", max_width=1920, max_height=1920)
     image_7 = fields.Image("Image7", max_width=1920, max_height=1920)
     image_8 = fields.Image("Image8", max_width=1920, max_height=1920)
     history_log = fields.Html(string='History Log', help="This field stores the history of changes.")
     image_ids = fields.One2many(
          'product.image',
          'product_tmpl_id',
          string='Images'
     )

     @api.depends('image_ids.image_1920')
     def _compute_first_image(self):
         for record in self:
             if record.image_ids:
                 record.image_1 = record.image_ids[0].image_1920
                 record.image_1920 = record.image_ids[0].image_1920
             else:
                 record.image_1 = False
     company_id = fields.Many2one('res.company', required=True, readonly=True, default=lambda self: self.env.company)

     def _prepare_history_log(self, vals, is_create=False):
          for rec in self:
               current_datetime_utc = fields.Datetime.now()
               user_tz = self.env.user.tz or 'UTC'
               current_datetime = current_datetime_utc.astimezone(pytz.timezone(user_tz)).strftime("%d/%m/%Y %H:%M:%S")
               user_name = self.env.user.display_name
               changes = []

               # Skip logging if this is an update immediately after creation
               if rec.history_log and not is_create:
                    last_log = rec.history_log.split('on ')[-1].split('</small>')[0]
                    if last_log == current_datetime:
                         continue  # Skip if timestamp matches the last log

               # Additional check: Skip if update happens within 1 second of creation
               if not is_create and rec.create_date:
                    time_diff = (fields.Datetime.now() - rec.create_date).total_seconds()
                    if time_diff < 1:  # Adjust this threshold as needed
                         continue

               excluded_fields = {'id', 'write_date', 'write_uid', 'create_date', 'create_uid', 'history_log'}
               for field_name in vals.keys():
                    if field_name in excluded_fields:
                         continue

                    field = rec._fields.get(field_name)
                    if not field:
                         continue

                    field_type = field.type
                    field_label = field.string

                    old_value = 'N/A' if is_create else getattr(rec, field_name, 'N/A')
                    new_value = vals[field_name]

                    # Skip if no change occurred (for write only)
                    if not is_create and old_value == new_value:
                         continue

                    # Handle relational fields
                    if field_type == 'many2one':
                         old_value = 'N/A' if is_create else (old_value.display_name if old_value else 'N/A')
                         new_value = self.env[field.comodel_name].browse(new_value).display_name if new_value else 'N/A'

                    elif field_type == 'one2many' and not is_create:
                         for command in new_value:
                              if command[0] == 1:  # Update
                                   sub_rec = rec[field_name].browse(command[1])
                                   for subfield, subval in command[2].items():
                                        sub_old = getattr(sub_rec, subfield, 'N/A')
                                        if sub_old != subval:
                                             changes.append(f"""
                                         <li>
                                             <strong>{field_label} ({subfield})</strong><br>
                                             <span style='color: red;'>Old value:</span> {sub_old}
                                                  
                                             <span style='color: green;'>New value:</span> {subval}
                                         </li>
                                     """)
                              elif command[0] == 0:  # Create
                                   changes.append(f"""
                                 <li><strong>Added to {field_label}:</strong> {command[2].get('name', 'New Record')}</li>
                             """)
                              elif command[0] == 2:  # Delete
                                   deleted_rec = rec[field_name].browse(command[1])
                                   changes.append(f"""
                                 <li><strong>Removed from {field_label}:</strong> {deleted_rec.display_name}</li>
                             """)
                         continue

                    elif field_type == 'many2many' and not is_create:
                         old_ids = rec[field_name].ids  # Current IDs before update
                         # Handle many2many commands in vals
                         new_ids = []
                         if isinstance(new_value, list) and new_value and isinstance(new_value[0], (list, tuple)):
                              # Process command list like [(6, 0, [ids])] or [(4, id), ...]
                              for command in new_value:
                                   if command[0] == 6:  # Replace with new list of IDs
                                        new_ids = command[2]
                                   elif command[0] == 4:  # Add an ID
                                        new_ids.append(command[1])
                                   elif command[0] == 3:  # Remove an ID
                                        if command[1] in new_ids:
                                             new_ids.remove(command[1])
                         else:
                              # Assume it's a direct list of IDs
                              new_ids = new_value if isinstance(new_value, (list, tuple)) else []

                         # Calculate added and removed IDs
                         added = set(new_ids) - set(old_ids)
                         removed = set(old_ids) - set(new_ids)

                         if added:
                              added_names = self.env[field.comodel_name].browse(added).mapped('display_name')
                              changes.append(f"""
                             <li><strong>Added to {field_label}:</strong> {', '.join(added_names)}</li>
                         """)
                         if removed:
                              removed_names = self.env[field.comodel_name].browse(removed).mapped('display_name')
                              changes.append(f"""
                             <li><strong>Removed from {field_label}:</strong> {', '.join(removed_names)}</li>
                         """)
                         continue

                    # Handle boolean values
                    if isinstance(old_value, bool):
                         old_value = 'Yes' if old_value else 'No'
                    if isinstance(new_value, bool):
                         new_value = 'Yes' if new_value else 'No'

                    # Format the change entry
                    changes.append(f"""
                     <li>
                         <strong>{field_label}</strong><br>
                         <span style='color: red;'>Old value:</span> {old_value}
                              
                         <span style='color: green;'>New value:</span> {new_value}
                     </li>
                 """)

               if changes:
                    action_text = 'Created by' if is_create else 'Updated by'
                    user_info = f"<small>{action_text} <strong>{user_name}</strong> on {current_datetime}</small>"
                    full_message = f"""
                         <div style="border-left: 3px solid #6C757D; padding-left: 10px; margin-bottom: 15px;">
                         {user_info}
                                <ul style="list-style-type: none; padding-left: 0;">{''.join(changes)}</ul>
                         </div>
                        """
                     # rec.history_log = tools.html_sanitize(full_message) + (rec.history_log or '')
                    rec.with_context(skip_history_log=True).write({
                       'history_log': tools.html_sanitize(full_message) + (rec.history_log or '')
                    })

     @api.model_create_multi
     def create(self, vals_list):
         records = super(ProductTemplate, self).create(vals_list)
         for rec, vals in zip(records, vals_list):
             rec.with_context(skip_history_log=True)._prepare_history_log(vals, is_create=True)
         return records

     def write(self, vals):
         if not self.env.context.get('skip_history_log'):
             self._prepare_history_log(vals, is_create=False)
         result = super(ProductTemplate, self).write(vals)
         return result

     def _compute_products_ids(self):
          for record in self:
               record.product_tmplt_ids = self.env['product.template'].search([])

     def action_back_to_product_menu(self):
          return {
               'name': 'products',
               'res_model': 'product.template',
               'type': 'ir.actions.act_window',
               'views': [
                      (self.env.ref('pim_ext.view_product_management_tree').id, 'list'),
                      (self.env.ref('pim_ext.view_product_management_kanban').id, 'kanban'),
                      (self.env.ref('pim_ext.view_product_creation_split_view_custom').id, 'form'),
                  ],
               'view_mode': 'list,kanban,form',
               'target': 'current',
               'context': {
                    'no_breadcrumbs': True,
               }
          }

     @api.depends('family_id')
     def _compute_percentage_complete(self):
         for product in self:
             filled_count = 0
             total_count = 0
             if product.family_id:
                 attributes = product.family_id.mapped('family_attribute_ids').mapped('attribute_id')
                 for attr_rec in attributes:
                     if attr_rec.is_completeness:
                         total_count += 1
                         # Correctly format the field name to replace spaces with underscores
                         field_name = attr_rec.original_name
                         if field_name in product._fields:
                             attribute_value = getattr(product, field_name, None)
                             if isinstance(product._fields[field_name], fields.Boolean):
                                 if attribute_value:
                                     filled_count += 1
                             else:
                                 if attribute_value not in [False, None, ""]:
                                     filled_count += 1
                         else:
                             # Log or handle missing field (debugging purposes)
                             pass  # Consider adding a debug log here
                 product.percentage_complete = (filled_count / total_count * 100) if total_count > 0 else 0
                 product._compute_progress_state(product.percentage_complete)
             else:
                 product.percentage_complete = 0

     def _compute_progress_state(self, percentage_complete):
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

