
from odoo import api, fields, models, _


class ProductBrand(models.Model):
    _name = 'product.brand'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Brand Information'
    _rec_name = 'name'

    name = fields.Char('Brand Name', required=True)
    brand_logo = fields.Image('Logo')
    description = fields.Text('Description')
    website = fields.Char("Website URL")
    completeness = fields.Float(string='Completeness', compute='_compute_completeness')

    def _compute_completeness(self):
        for rec in self:
            required_brand_fields = self.env['general.attribute'].search([
                ('completeness', '=', True),
                ('related_field.model_id.model', '=', 'product.brand')])
            field_list = required_brand_fields.mapped('related_field').mapped('name')
            filled_count = 0
            total_count = 0
            for field in field_list:
                if getattr(rec, field, False):
                    filled_count += 1
                total_count += 1
            if total_count > 0:
                rec.completeness = (filled_count / total_count) * 100
            else:
                rec.completeness = 0
