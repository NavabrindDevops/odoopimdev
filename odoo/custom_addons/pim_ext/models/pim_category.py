# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime


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
    history_log = fields.Text(string='History Log', help="This field stores the history of changes.")
    # is_primary = fields.Boolean()

    def write(self, vals):
        for rec in self:
            time_now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            msg_string = ''
            old_code = rec.code or 'N/A'
            new_code = vals.get('code', old_code)
            old_active = rec.active
            new_active = vals.get('active', old_active)
            old_parent = rec.parent_id.display_name if rec.parent_id else 'N/A'
            new_parent = self.env['pim.category'].browse(vals['parent_id']).display_name if vals.get(
                'parent_id') else 'N/A'
            old_complete_name = rec.complete_name or 'N/A'
            new_complete_name = vals.get('complete_name', old_complete_name)
            old_write_date = rec.write_date.strftime("%d/%m/%Y %H:%M:%S") if rec.write_date else 'N/A'
            new_write_date = fields.Datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            old_write_uid = rec.write_uid.display_name if rec.write_uid else 'N/A'
            new_write_uid = self.env.user.display_name

            for key in vals:
                if key in ['name', 'code', 'active', 'parent_id', 'complete_name']:
                    attribute = rec._fields[key].string
                    header = "• %s" % attribute

                    if key == 'parent_id':
                        old_value = old_parent
                        new_value = new_parent
                    else:
                        old_value = getattr(rec, key) or 'N/A'
                        new_value = vals[key] or 'N/A'

                    msg_string += ("Old value: %s | New Value: %s | Updated Date: %s | Updated By: %s\n") % (
                        old_value, new_value, old_write_date, old_write_uid
                    )
                    full_message = header + "\n" + msg_string
                    rec.history_log = full_message + "\n" + (rec.history_log or '')

            res = super(PimCategory, self).write(vals)
            return res

    @api.model
    def create(self, vals):
        vals['code'] = self.env['ir.sequence'].next_by_code(
            'pim.category') or None
        res = super(PimCategory, self).create(vals)
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
