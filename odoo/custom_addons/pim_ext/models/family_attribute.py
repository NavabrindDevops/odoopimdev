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
    # attribute1_id = fields.Many2one('product.attribute1', 'Attribute 1')
    # attribute2_id = fields.Many2one('product.attribute2', 'Attribute 2')
    # attribute3_id = fields.Many2one('product.attribute3', 'Attribute 3')
    # attribute4_id = fields.Many2one('product.attribute4', 'Attribute 4')
    exist_attribute_ids = fields.Many2many('product.attribute','family_mapped_attributes_rel', 'family_id', 'attribute_id', string='Exist Attributes')
    exist_group_ids = fields.Many2many('attribute.group','family_mapped_groups_rel', 'family_id', 'attribute_group_id', string='Exist Attribute Groups')
    asn_description = fields.Html('ASN Description')
    product_families_ids = fields.One2many('family.products.line', 'families_id', 'Attributes', readonly=False)
    family_attribute_ids = fields.One2many('family.attributes', 'family_id', 'Family Attributes', readonly=False)
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
        res = super(FamilyAttribute, self).write(vals)
        if not self.env.context.get('syncing_exist_attrs'):
            self.with_context(syncing_exist_attrs=True).sync_exist_attribute_ids()
            self.update_attribute_group_views()
        return res

    def update_attribute_group_views(self):
        print("update_attribute_group_views ==== ")
        company_name = self.env.company.name
        for rec in self:
            attributes = rec.mapped('family_attribute_ids').mapped('attribute_id')
            print("attributes === ", attributes)
            attribute_lines = rec.family_attribute_ids

            attribute_groups = {}
            for line in attribute_lines:
                group_name = line.attribute_group_id.name or "default"
                attribute = line.attribute_id

                if group_name in attribute_groups:
                    attribute_groups[group_name].append(attribute)
                else:
                    attribute_groups[group_name] = [attribute]
            print("attribute_groups === ", attribute_groups)
            for group_name, group_attributes in attribute_groups.items():
                print("group_name, group_attributes  ==== ", group_name, group_attributes)
                safe_group_id = group_name.lower().replace(' ', '_').replace('&', 'and')
                group_view_name = 'product_attribute_'+ company_name.lower().replace(' ', '_') + '_' + safe_group_id
                print("group_view_name === ", group_view_name)
                group_exist = self.env['ir.ui.view'].search([
                    ('name', 'ilike', group_view_name),
                    ('active', 'in', [True, False])
                ], limit=1)

                if not group_exist:
                    continue

                if group_exist.arch_base:
                    grp_arch_tree = etree.fromstring(group_exist.arch_base)
                    updated = False
                    group_node = grp_arch_tree.find(f".//group[@id='{safe_group_id}']")
                    print("group_name === ", safe_group_id)
                    print("group_node === ", group_node)
                    if group_node is not None:
                        group_invisible = group_node.get("invisible")
                        new_id = str(rec.id)
                        print("grp line new_id 11 === ", new_id)
                        print("group_invisible 11 == ", group_invisible)
                        # Prepare new family condition
                        family_condition = f"family_id not in [{new_id}]"

                        if group_invisible and group_invisible.strip().lower() != 'false':
                            # If family_id already exists in condition, just extend its list
                            match = re.search(r'family_id\s+not\s+in\s+\[(.*?)\]', group_invisible)
                            print("match == ", match)
                            if match:
                                id_list = [x.strip() for x in match.group(1).split(',') if x.strip()]
                                print("group id_list --- ", id_list)
                                if new_id not in id_list:
                                    id_list.append(new_id)
                                family_condition = f"family_id not in [{', '.join(id_list)}]"

                                # Replace only the family part, keep company_id intact
                                updated_invisible = re.sub(
                                    r'family_id\s+not\s+in\s+\[.*?\]',
                                    family_condition,
                                    group_invisible
                                )

                            else:
                                print("esle === ")
                                # family_id condition not found → append it with AND
                                updated_invisible = f"({group_invisible}) and ({family_condition})"
                        else:
                            # No condition → start with family_id only
                            updated_invisible = family_condition
                            print("if no family kbsob")
                        print("updated_invisible === ", updated_invisible)
                        group_node.set("invisible", updated_invisible)
                        updated = True
                    # if group_node is not None:
                    #     group_invisible = group_node.get("invisible")
                    #     new_id = str(rec.id)
                    #     print("grp line new_id === ", new_id)
                    #     if group_invisible and group_invisible.strip().lower() != 'false':
                    #         match = re.search(r'\[(.*?)\]', group_invisible)
                    #         if match:
                    #             id_list = [x.strip() for x in match.group(1).split(',') if x.strip()]
                    #             print("group id_list --- ", id_list)
                    #             if new_id not in id_list:
                    #                 id_list.append(new_id)
                    #                 group_node.set("invisible", f"family_id not in [{', '.join(id_list)}]")
                    #                 updated = True
                    #         else:
                    #             group_node.set("invisible", f"family_id not in [{new_id}]")
                    #             updated = True
                    #     else:
                    #         group_node.set("invisible", f"family_id not in [{new_id}]")
                    #         updated = True
                    # Show fields that are in default_attrs_val
                    for a in group_attributes:
                        print("a == ", a)
                        # attributes_list.append(a.original_name)
                        xpath_expr = f".//field[@name='{a.original_name}']"
                        print("xpath_expr == ", xpath_expr)
                        field_node = grp_arch_tree.find(xpath_expr)
                        print("field_node === ", field_node)
                        if field_node is not None:
                            column_invisible = field_node.get("invisible")
                            print("column_invisible === ", column_invisible)
                            new_id = str(rec.id)
                            if column_invisible and column_invisible.strip().lower() != 'false':
                                match = re.search(r'\[(.*?)\]', column_invisible)
                                print("match === ", match)
                                if match:
                                    print("match if")
                                    id_list = [x.strip() for x in match.group(1).split(',') if x.strip()]
                                    if new_id not in id_list:
                                        id_list.append(new_id)
                                    field_node.set("invisible", f"family_id not in [{', '.join(id_list)}]")
                                    updated = True
                                else:
                                    print("match else ")
                                    # If column_invisible is set but not in expected format, override it
                                    field_node.set("invisible", f"family_id not in [{new_id}]")
                                    updated = True
                            else:
                                print("els jnifn")
                                # If column_invisible is 'False' or not set at all
                                field_node.set("invisible", f"parent.id not in [{new_id}]")
                                updated = True
                    print("updated === ", updated)
                    if updated:
                        updated_arch = etree.tostring(grp_arch_tree, pretty_print=True).decode()
                        group_exist.write({'arch_base': updated_arch})

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

        self.update_attribute_group_views()
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
        if self.family_attribute_ids:
            self.sync_exist_attribute_ids()
        self._log_changes(res, vals, action="create")
        return res

    def sync_exist_attribute_ids(self):
        print("_sync_exist_attribute_ids =================")
        for rec in self:
            attributes = []
            groups = []
            for line in rec.family_attribute_ids:
                if line.attribute_id:
                    attributes.append(line.attribute_id.id)
                if line.attribute_group_id:
                    groups.append(line.attribute_group_id.id)

            # Use `with_context` to avoid re-triggering `write()` logic
            rec.with_context(syncing_exist_attrs=True).write({
                'exist_attribute_ids': [(6, 0, attributes)],
                'exist_group_ids': [(6, 0, groups)]
            })

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

class FamilyAttributes(models.Model):
    _name = 'family.attributes'
    _description = 'Family Attributes'

    attribute_id = fields.Many2one('product.attribute', string='Attribute')
    attribute_group_id = fields.Many2one('attribute.group', string='Attribute Group')
    family_id = fields.Many2one('family.attribute', 'Family')
