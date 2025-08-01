# -*- coding: utf-8 -*-

import time, pytz
import re
from datetime import datetime, timedelta, timezone, date
from email.policy import default
from markupsafe import Markup
import pytz

from lxml import etree
from odoo import models, api, fields, _, tools
from odoo.exceptions import UserError, ValidationError
import traceback, pdb, inspect

from odoo.tools import drop_view_if_exists
import logging
from googletrans import Translator

_logger = logging.getLogger(__name__)


class FamilyAttribute(models.Model):
    _name = 'family.attribute'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Family'

    code = fields.Char(string="Code", readonly=True)
    description = fields.Text(string="Description")

    name = fields.Char('Name', required=True, tracking=True)
    supplier_id = fields.Many2one('res.partner', 'Supplier')
    brand_id = fields.Many2one('brand.attribute', 'Brand')
    manufacture_id = fields.Many2one('manufacturer.attribute', 'Manufacturer')
    attributes_group_ids = fields.Many2many('attribute.group', string='Attributes Groups', tracking=True,
                                            domain=[('active', '=', True)])
    taxonomy_ids = fields.Many2many('product.public.category', string="Taxonomy")
    attch_ids = fields.Many2many('ir.attachment', 'ir_attach_rel', 'record_relation_id', 'attachment_id',
                                 string="Attachments")
    complementary_categ_ids = fields.Many2many('product.public.category', 'custom_categ_rel', 'family_id', 'cteg_id',
                                               string="Complementary Categories")
    product_family_ids = fields.One2many('family.products', 'family_id', 'Products')
    product_image = fields.Image(string="Image", copy=False, attachment=True, max_width=1024, max_height=1024)
    buyer_id = fields.Many2one('res.partner', 'Buyer')
    availability = fields.Selection([('all', 'All Channel')], 'Availability')
    swatch = fields.Selection([('yes', 'Yes'), ('no', 'No')], 'Swatch')
    gift = fields.Selection([('yes', 'Yes'), ('no', 'No')], 'Gift')
    attribute1_id = fields.Many2one('product.attribute1', 'Attribute 1')
    attribute2_id = fields.Many2one('product.attribute2', 'Attribute 2')
    attribute3_id = fields.Many2one('product.attribute3', 'Attribute 3')
    attribute4_id = fields.Many2one('product.attribute4', 'Attribute 4')
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

    company_id = fields.Many2one('res.company', required=True, readonly=True, default=lambda self: self.env.company)

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
                'default_current_family': self._origin.id,
            },
        }

    def action_update(self):
        attribute_group = self.env['attribute.group'].search([("attribute_family_id", "in", self.id)])
        for record in attribute_group:
            self.attributes_group_ids = [(4, record.id)]

    def mass_edit(self):
        res = []
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
