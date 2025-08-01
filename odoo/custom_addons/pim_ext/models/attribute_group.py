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

import logging
from googletrans import Translator

_logger = logging.getLogger(__name__)


class AttributeGroup(models.Model):
    _name = 'attribute.group'
    _description = 'Attribute Group'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Name', required=True, )
    description = fields.Text(string='Description')
    active = fields.Boolean('Active', default=True)
    attributes_ids = fields.One2many('product.attribute', 'attribute_group', string='Attributes', required=True,
                                     tracking=True, store=True)
    attribute_family_id = fields.Many2many('family.attribute', string='Attribute Family', required=True, tracking=True,
                                           store=True)
    attribute_group_line_ids = fields.One2many('attribute.group.lines', 'attr_group_id', string='Attribute group line')
    attribute_code = fields.Selection([('medias', 'Medias')], string="Code")
    attribute_code_rec = fields.Char(string='Code ', readonly=True)
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
        string='Sub-groups '
    )
    user_id = fields.Many2one('res.users', string="User", default=lambda self: self.env.user)

    history_log = fields.Html(string='History Log', help="This field stores the history of changes.")

    is_create_mode = fields.Boolean(default=False, string='Create Mode')

    company_id = fields.Many2one('res.company', required=True, readonly=True, default=lambda self: self.env.company)

    def _log_changes(self, vals, action):
        updated_write_date_utc = fields.Datetime.now()
        user_tz = self.env.user.tz or 'UTC'
        updated_write_date = updated_write_date_utc.astimezone(pytz.timezone(user_tz)).strftime("%d/%m/%Y %H:%M:%S")
        new_write_uid = self.env.user.display_name

        changes = []

        tracked_fields = ['name', 'attribute_code_rec', 'active', 'parent_id', 'description', 'attribute_code']
        tracked_group_line_fields = ['product_attribute_id', 'display_type', 'enable', 'value_per_channel',
                                     'value_per_locale']

        # Track attribute.group changes
        for key in vals:
            if key in tracked_fields:
                attribute = self._fields[key].string
                old_value = getattr(self, key, 'N/A') if action == "update" else 'N/A'
                new_value = vals[key] or 'N/A'

                if key == 'parent_id':
                    old_value = self.parent_id.display_name if self.parent_id else 'N/A'
                    new_value = self.env['attribute.group'].browse(vals[key]).display_name if vals.get(key) else 'N/A'

                change_entry = f"""
                    <li>
                        <strong>{attribute}</strong><br>
                        <span style='color: red;'>Old value:</span> {old_value}
                        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
                        <span style='color: green;'>New value:</span> {new_value}
                    </li>
                """
                changes.append(change_entry)

        # Track attribute.group.lines changes
        if 'attribute_group_line_ids' in vals:
            for command in vals['attribute_group_line_ids']:
                if command[0] == 1:
                    line_id = self.env['attribute.group.lines'].browse(command[1])
                    line_changes = []
                    for field in tracked_group_line_fields:
                        if field in command[2]:
                            old_value = getattr(line_id, field, 'N/A')
                            new_value = command[2][field] or 'N/A'
                            if field == 'product_attribute_id':
                                old_value = line_id.product_attribute_id.display_name if line_id.product_attribute_id else 'N/A'
                                new_value = self.env['product.attribute'].browse(
                                    new_value).display_name if new_value else 'N/A'

                            line_changes.append(f"""
                                <li>
                                    <strong>{line_id._fields[field].string}</strong><br>
                                    <span style='color: red;'>Old:</span> {old_value}
                                    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
                                    <span style='color: green;'>New:</span> {new_value}
                                </li>
                            """)
                    if line_changes:
                        changes.append(f"""
                            <li>
                                <strong>Updated Attribute Group Line (ID {line_id.id})</strong>
                                <ul>{''.join(line_changes)}</ul>
                            </li>
                        """)

                elif command[0] == 0:
                    new_values = command[2]
                    new_line_changes = []
                    for field in tracked_group_line_fields:
                        if field in new_values:
                            field_label = self.env['attribute.group.lines']._fields[field].string
                            new_value = new_values[field] or 'N/A'
                            old_value = "N/A"
                            if field == 'product_attribute_id':
                                new_value = self.env['product.attribute'].browse(
                                    new_value).display_name if new_value else 'N/A'
                            new_line_changes.append(f"""
                                <li>
                                    <strong>{field_label}</strong><br>
                                    <span style='color: red;'>Old value:</span> {old_value}
                                    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
                                    <span style='color: green;'>New value:</span> {new_value}
                                </li>
                            """)
                    if new_line_changes:
                        changes.append(f"""
                            <li>
                                <strong>New Attribute Group Line Added:</strong><br>
                                <ul>{''.join(new_line_changes)}</ul>
                            </li>
                        """)

                elif command[0] == 2:
                    line_id = self.env['attribute.group.lines'].browse(command[1])
                    removed_line_changes = []
                    for field in tracked_group_line_fields:
                        field_label = line_id._fields[field].string
                        old_value = getattr(line_id, field, 'N/A')
                        new_value = "N/A"
                        if field == 'product_attribute_id':
                            old_value = line_id.product_attribute_id.display_name if line_id.product_attribute_id else 'N/A'
                        removed_line_changes.append(f"""
                            <li>
                                <strong>{field_label}</strong><br>
                                <span style='color: red;'>Old value:</span> {old_value}
                                &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
                                <span style='color: green;'>New value:</span> {new_value}
                            </li>
                        """)
                    if removed_line_changes:
                        changes.append(f"""
                            <li>
                                <strong>Removed Attribute Group Line:</strong><br>
                                <ul>{''.join(removed_line_changes)}</ul>
                            </li>
                        """)

        if changes:
            action_text = "Created by" if action == "create" else "Updated by"
            user_info = f"<small>{action_text} <strong>{new_write_uid}</strong> on {updated_write_date}</small>"
            full_message = f"""
                <div style="border-left: 3px solid #6C757D; padding-left: 10px; margin-bottom: 15px;">
                    {user_info}
                    <ul style="list-style-type: none; padding-left: 0;">{''.join(changes)}</ul>
                </div>
            """
            self.history_log = tools.html_sanitize(full_message) + (self.history_log or '')

    def write(self, vals):
        for rec in self:
            rec._log_changes(vals, action="update")
            super(AttributeGroup, rec).write(vals)
        return True

    def create(self, vals):
        vals['attribute_code_rec'] = self.env['ir.sequence'].next_by_code('attribute.group') or None
        record = super(AttributeGroup, self).create(vals)
        record._log_changes(vals, action="create")
        return record

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

    # @api.depends('attr_group_id', 'product_attribute_id')
    # def _compute_used_attribute_ids(self):
    #     """Compute all attributes already assigned to groups."""
    #     all_used_attributes = self.env['attribute.group.lines'].search([]).mapped('product_attribute_id')
    #     for line in self:
    #         line.used_attribute_ids = all_used_attributes

    @api.onchange('enable')
    def _onchange_enable(self):
        if self.product_attribute_id:
            attribute_name = f"x_{self.product_attribute_id.name.lower().replace(' ', '_')}"
            name = f"add_field_{attribute_name}_to_product_management"
            attribute_view_exist = self.env['ir.ui.view'].search(
                [('name', '=ilike', name), ('active', '!=', None)])
            arch = self._arch(attribute_name, self.enable)
            if attribute_view_exist.arch:
                attribute_view_exist.arch = arch

    def _arch(self, attribute_name, active):
        if active == False:
            new_field_xml = f'<field name="{attribute_name}" invisible="True"/>'
        else:
            new_field_xml = f'<field name="{attribute_name}"/>'
        arch = f"""
                       <xpath expr="//field[@name='{self.product_attribute_id.position_ref_field_id.name}']" position="after">
                                                          %s
                                                  </xpath>""" % new_field_xml
        return arch

    @api.model
    def create(self, vals):
        res = super(AttributeGroupLine, self).create(vals)
        # Add group to product_attribute's attribute_group field
        if res.product_attribute_id and res.attr_group_id:
            res.product_attribute_id.attribute_group = [(4, res.attr_group_id.id)]
        return res

    def unlink(self):
        for line in self:
            attribute = line.product_attribute_id
            group = line.attr_group_id
            if attribute and group:
                # Remove the group from product_attribute's attribute_group field
                attribute.attribute_group = [(3, group.id)]
        return super(AttributeGroupLine, self).unlink()

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

