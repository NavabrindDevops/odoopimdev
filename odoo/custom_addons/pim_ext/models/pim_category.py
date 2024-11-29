# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class PimCategory(models.Model):
    _name = 'pim.category'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Category'
    _parent_name = "parent_id"
    _parent_store = True
    _rec_name = 'complete_name'
    _order = 'complete_name'

    name = fields.Char(string='Name', required=True, translate=True)
    code = fields.Char(string='Code')
    active = fields.Boolean('Active', default=True)
    complete_name = fields.Char(
        'Complete Name', compute='_compute_complete_name', recursive=True,
        store=True)
    parent_id = fields.Many2one('pim.category', string='Parent Category', index=True, ondelete="cascade")
    parent_path = fields.Char(index=True, unaccent=False)
    # child_id = fields.One2many('family.category', 'parent_id', string='Children Categories')
    # is_primary = fields.Boolean()

    
    
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