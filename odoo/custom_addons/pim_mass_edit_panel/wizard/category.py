

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class CustomPopMessage(models.TransientModel):
    _name = "custom.pop.message"

    name = fields.Char('Message')

class CategoryWizard(models.TransientModel):
    _name = 'category.wizard'

    # product_ids = fields.Many2many('product.management')
    category_id = fields.Many2one('pim.category', 'Category')
    # mode = fields.Selection([('add_comp','add_comp'), ('add_taxonomy','add_taxonomy')])

    def add_taxonomy(self):
        product_ids = self.env.context.get('default_product_ids', [])
        if self.category_id and product_ids:
            records = self.env['product.management'].search([('id','in', product_ids)])
            records.write({'pim_category_id' : self.category_id.id})

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

