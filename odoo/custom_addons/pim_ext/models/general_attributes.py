from odoo import models, fields, api


class GeneralAttributes(models.Model):
    _name = 'general.attribute'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char("Attribute Name")
    related_field = fields.Many2one('ir.model.fields', ondelete="cascade")
    model = fields.Char(string='Model')
    completeness = fields.Boolean(string="Completeness?")
