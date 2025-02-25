# -*- coding: utf-8 -*-
from odoo import models, fields, api, _, tools
from odoo.exceptions import ValidationError
from datetime import datetime
import pytz


class PimCategory(models.Model):
    _name = 'pim.category'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Category'
    _parent_name = "parent_id"
    _parent_store = True
    _rec_name = 'complete_name'
    _order = 'complete_name'

    name = fields.Char(string='Name', required=True, translate=False)
    code = fields.Char(string='Code')
    active = fields.Boolean('Active', default=True)
    complete_name = fields.Char(
        'Complete Name', compute='_compute_complete_name', recursive=True,
        store=True)
    parent_id = fields.Many2one('pim.category', string='Parent Category', index=True, ondelete="cascade")
    parent_path = fields.Char(index=True, unaccent=False)
    category_ids = fields.One2many('pim.category', 'parent_id', string='Children Categories', compute='_compute_category_ids')
    child_ids = fields.One2many('pim.category', 'parent_id', string='Children Categories')
    history_log = fields.Html(string='History Log', help="This field stores the history of changes.")

    def _log_changes(self, rec, vals, action):
        # Get the current time in UTC
        updated_write_date_utc = fields.Datetime.now()
        # Convert to the user's timezone
        user_tz = self.env.user.tz or 'UTC'  # Default to UTC if no timezone is set
        updated_write_date = updated_write_date_utc.astimezone(pytz.timezone(user_tz)).strftime("%d/%m/%Y %H:%M:%S")

        new_write_uid = self.env.user.display_name
        changes = []  # Store changes in list

        for key in vals:
            if key in ['name', 'code', 'active', 'parent_id', 'complete_name']:
                attribute = rec._fields[key].string

                if key == 'parent_id':
                    old_value = rec.parent_id.display_name if rec.parent_id else 'N/A'
                    new_value = self.env['pim.category'].browse(vals[key]).display_name if vals.get(key) else 'N/A'
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
        for rec in self:
            self._log_changes(rec, vals, action="update")  # Call the common function with action as "update"
        return super(PimCategory, self).write(vals)

    @api.model
    def create(self, vals):
        vals['code'] = self.env['ir.sequence'].next_by_code(
            'pim.category') or None
        res = super(PimCategory, self).create(vals)
        self._log_changes(res, vals, action="create")
        return res

    
    @api.depends('name', 'parent_id.complete_name')
    def _compute_complete_name(self):
        for category in self:
            if category.parent_id:
                category.complete_name = '%s / %s' % (category.parent_id.complete_name, category.name)
            else:
                category.complete_name = category.name

    @api.constrains('name')
    def check_name(self):
        if self.env['pim.category'].search([('name', '=', self.name), ('id', '!=', self.id)]):
            raise ValidationError("The category name already exists.")

    def _compute_display_name(self):
        for record in self:
            record.display_name = record.complete_name

    def create_pim_category(self):
        return {
            'name': _('Create Category'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'pim.category',
        }

    def _compute_category_ids(self):
        for record in self:
            record.category_ids = self.env['pim.category'].search([])

    def save_attributes(self):
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'pim.category',
            'view_id': self.env.ref('pim_ext.view_form_pim_categories').id,
            'res_id': self.id,
            'context': {'no_breadcrumbs': True},
            'target': 'current',
        }

    def category_edit_open_form_view(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Edit Category',
            'res_model': 'pim.category',
            'view_mode': 'form',
            'view_id': self.env.ref('pim_ext.view_form_pim_categories').id,
            'context': {'no_breadcrumbs': True},
            'res_id': self.id,
        }

    def category_master_unlink(self):
        return {
            'name': 'Confirm Deletion',
            'type': 'ir.actions.act_window',
            'res_model': 'category.master.unlink.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_category_id': self.id},
        }

    def action_back_to_category_menu(self):
        menu_id = self.env.ref('pim_ext.menu_pim_categories')
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
            'params': {
                'menu_id': menu_id.id,
            },
        }

class CategoryMasterUnlinkWizard(models.TransientModel):
    _name = 'category.master.unlink.wizard'
    _description = 'Wizard to Confirm Deletion of Category master'

    category_id = fields.Many2one('pim.category', string="Category Master")

    def confirm_unlink(self):
        menu_id = self.env['ir.ui.menu'].search([('name', '=', 'Manage Categories')])
        if self.category_id:
            self.category_id.unlink()
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
            'params': {
                'menu_id': menu_id.id,
            },
        }
