

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class CategoryWizard(models.TransientModel):
    _name = 'family.wizard'

    # product_ids = fields.Many2many('product.management')
    family_id = fields.Many2one('family.attribute', 'Family')
    # mode = fields.Selection([('add_comp','add_comp'), ('add_taxonomy','add_taxonomy')])

    def add_taxonomy(self):
        product_ids = self.env.context.get('default_product_ids', [])
        if self.family_id and product_ids:
            records = self.env['product.management'].search([('id','in', product_ids)])
            records.write({'family_id' : self.family_id.id})

        return {
            'name': 'Successful',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'custom.pop.message',
            'target': 'new',
            'context': {'default_name': "Successfully Added Taxonomies."}
        }

# class CategoryWizardLine(models.TransientModel):
#     _name = 'category.wizard.line'
#
#     select = fields.Boolean(default=False)
#     category_id = fields.Many2one('pim.category')
#     wizard_id = fields.Many2one('category.wizard')

