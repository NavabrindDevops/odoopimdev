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


class FamilyAttribute(models.Model):
     _name = 'family.attribute'
     _inherit = ['mail.thread', 'mail.activity.mixin']
     _description = 'Family'

     code = fields.Char(string="Code", readonly=True)
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
     product_families_ids = fields.One2many('family.products.line', 'families_id', 'Attributes', readonly=False)
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

     history_log = fields.Html(string='History Log', help="This field stores the history of changes.")

     is_create_mode = fields.Boolean(default=False, string='Create Mode')

     def _log_changes(self, rec, vals, action):
          # Get the current time in UTC and convert to user's timezone
          updated_write_date_utc = fields.Datetime.now()
          user_tz = self.env.user.tz or 'UTC'
          updated_write_date = updated_write_date_utc.astimezone(pytz.timezone(user_tz)).strftime("%d/%m/%Y %H:%M:%S")
          user_name = self.env.user.display_name
          changes = []

          # Fields to track
          tracked_fields = ['name', 'description', 'supplier_id', 'brand_id', 'manufacture_id', 'availability',
                            'swatch', 'gift']
          tracked_one2many_fields = {
               'product_families_ids': ['attribute_id', 'attribute_group_id', 'completeness_percent'],
               'variant_line_ids': ['name', 'variant_ids'],
          }

          # Track direct field changes
          for key in vals:
               if key in tracked_fields:
                    field_label = rec._fields[key].string
                    old_value = getattr(rec, key, 'N/A') if action == "update" else 'N/A'
                    new_value = vals[key] if vals[key] is not None else 'N/A'

                    if isinstance(rec._fields[key], fields.Many2one):
                         old_value = old_value.display_name if old_value and old_value != 'N/A' else 'N/A'
                         new_value = self.env[rec._fields[key].comodel_name].browse(
                              new_value).display_name if new_value != 'N/A' else 'N/A'

                    change_entry = f"""
                  <li>
                      <strong>{field_label}</strong><br>
                      <span style='color: red;'>Old value:</span> {old_value}  
                           
                      <span style='color: green;'>New value:</span> {new_value}
                  </li>
                  """
                    changes.append(change_entry)

          # Track One2many field changes
          for field, subfields in tracked_one2many_fields.items():
               if field in vals:
                    field_label = rec._fields[field].string
                    for command in vals[field]:
                         if command[0] == 1:  # Update existing record
                              line_id = rec[field].browse(command[1])
                              for subfield in subfields:
                                   if subfield in command[2]:
                                        subfield_label = line_id._fields[subfield].string
                                        old_value = getattr(line_id, subfield, 'N/A')
                                        new_value = command[2][subfield] if command[2][subfield] is not None else 'N/A'

                                        if isinstance(line_id._fields[subfield], fields.Many2one):
                                             old_value = old_value.display_name if old_value and old_value != 'N/A' else 'N/A'
                                             new_value = self.env[line_id._fields[subfield].comodel_name].browse(
                                                  new_value).display_name if new_value != 'N/A' else 'N/A'
                                        elif isinstance(line_id._fields[subfield], fields.Many2many):
                                             old_value = ', '.join(
                                                  old_value.mapped('display_name')) if old_value else 'N/A'
                                             if isinstance(new_value, (list, tuple)):
                                                  ids = [cmd[1] if isinstance(cmd, tuple) and cmd[0] in (1, 4) else cmd
                                                         for cmd in new_value if isinstance(cmd, (int, tuple))]
                                                  new_value = ', '.join(
                                                       self.env[line_id._fields[subfield].comodel_name].browse(
                                                            ids).mapped('display_name')) if ids else 'N/A'
                                             else:
                                                  new_value = new_value if new_value is not None else 'N/A'

                                        change_entry = f"""
                                  <li>
                                      <strong>{subfield_label} (in {field_label})</strong><br>
                                      <span style='color: red;'>Old value:</span> {old_value}  
                                           
                                      <span style='color: green;'>New value:</span> {new_value}
                                  </li>
                                  """
                                        changes.append(change_entry)

                         elif command[0] == 0:  # New record added
                              new_vals = command[2]
                              for subfield in subfields:
                                   subfield_label = self.env[rec._fields[field].comodel_name]._fields[subfield].string
                                   new_value = new_vals.get(subfield, 'N/A') if subfield in new_vals else 'N/A'
                                   old_value = 'N/A'  # New records have no old value

                                   if isinstance(self.env[rec._fields[field].comodel_name]._fields[subfield],
                                                 fields.Many2one):
                                        new_value = self.env[self.env[rec._fields[field].comodel_name]._fields[
                                             subfield].comodel_name].browse(
                                             new_value).display_name if new_value != 'N/A' else 'N/A'
                                   elif isinstance(self.env[rec._fields[field].comodel_name]._fields[subfield],
                                                   fields.Many2many):
                                        if isinstance(new_value, (list, tuple)):
                                             ids = [cmd[1] if isinstance(cmd, tuple) and cmd[0] in (1, 4) else cmd for
                                                    cmd in new_value if isinstance(cmd, (int, tuple))]
                                             new_value = ', '.join(self.env[self.env[
                                                  rec._fields[field].comodel_name]._fields[
                                                  subfield].comodel_name].browse(ids).mapped(
                                                  'display_name')) if ids else 'N/A'
                                        else:
                                             new_value = new_value if new_value is not None else 'N/A'

                                   change_entry = f"""
                              <li>
                                  <strong>{subfield_label} (in New {field_label})</strong><br>
                                  <span style='color: red;'>Old value:</span> {old_value}  
                                       
                                  <span style='color: green;'>New value:</span> {new_value}
                              </li>
                              """
                                   changes.append(change_entry)

                         elif command[0] == 2:  # Deletion
                              removed_record = rec[field].browse(command[1])
                              if removed_record.exists():
                                   for subfield in subfields:
                                        subfield_label = removed_record._fields[subfield].string
                                        old_value = getattr(removed_record, subfield, 'N/A')
                                        new_value = 'N/A'  # Removed records have no new value

                                        if isinstance(removed_record._fields[subfield], fields.Many2one):
                                             old_value = old_value.display_name if old_value and old_value != 'N/A' else 'N/A'
                                        elif isinstance(removed_record._fields[subfield], fields.Many2many):
                                             old_value = ', '.join(
                                                  old_value.mapped('display_name')) if old_value else 'N/A'

                                        change_entry = f"""
                                  <li>
                                      <strong>{subfield_label} (in Removed {field_label})</strong><br>
                                      <span style='color: red;'>Old value:</span> {old_value}  
                                           
                                      <span style='color: green;'>New value:</span> {new_value}
                                  </li>
                                  """
                                        changes.append(change_entry)

          if changes:
               action_text = "Created by" if action == "create" else "Updated by"
               header = f"<small>{action_text} {user_name} on {updated_write_date}</small>"
               full_message = f"""
              <div style="border-left: 3px solid #6C757D; padding-left: 10px; margin-bottom: 15px;">
                  {header}
                  <ul style="list-style-type: none; padding-left: 0;">
                      {''.join(changes)}
                  </ul>
              </div>
              """
               rec.history_log = tools.html_sanitize(full_message) + (rec.history_log or '')

     def write(self, vals):
          for rec in self:
               self._log_changes(rec, vals, action="update")
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
          self._log_changes(res, vals, action="create")
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
     active_label = fields.Char(string="Status", compute="_compute_active_label")

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
     product_attr_values_id = fields.Many2many('product.attribute.value', 'attr_value_id', 'products_id', string='Attribute Values', readonly=True)
     product_attr_ids = fields.One2many('product.attribute', 'products_id', string='Attributes')
     is_variant_update = fields.Boolean(string='Variant updated', default=False)
     image_1 = fields.Image("Image1", max_width=1920, max_height=1920)
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
                    rec.history_log = tools.html_sanitize(full_message) + (rec.history_log or '')

     @api.model
     def create(self, vals):
          record = super(ProductTemplate, self).create(vals)
          record._prepare_history_log(vals, is_create=True)
          return record

     def write(self, vals):
          self._prepare_history_log(vals, is_create=False)
          return super(ProductTemplate, self).write(vals)

     def _compute_products_ids(self):
          for record in self:
               record.product_tmplt_ids = self.env['product.template'].search([])

     def action_back_to_product_menu(self):
          return {
               'name': 'products',
               'res_model': 'product.template',
               'type': 'ir.actions.act_window',
               'view_id': self.env.ref('pim_ext.view_product_management_kanban').id,
               'view_mode': 'kanban',
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
                 attributes = product.family_id.mapped('product_families_ids').mapped('attribute_id')
                 for attr_rec in attributes:
                     if attr_rec.is_completeness:
                         total_count += 1
                         # Correctly format the field name to replace spaces with underscores
                         field_name = f"x_{attr_rec.name.replace(' ', '_').lower()}"
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

