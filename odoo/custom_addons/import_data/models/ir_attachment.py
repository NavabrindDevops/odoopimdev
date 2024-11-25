from odoo import models, fields

class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    name_model = fields.Char('Name Model')
