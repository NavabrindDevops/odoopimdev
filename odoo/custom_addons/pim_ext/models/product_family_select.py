from odoo import api, fields, models, _


class PimSelect(models.TransientModel):
    _name = "product.family.select"
    # _rec_name = 'sku'

    type_name = fields.Char(string="Attribute Type Name")
    is_invisible = fields.Boolean(default=False, string='Invisible Types')
    family_id = fields.Many2one('family.attribute',string="Choose Family")
    sku = fields.Char(string="SKU")

    def simple_product(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Date Attribute',
            'res_model': 'product.family.select',
            'view_id': self.env.ref('pim_ext.view_product_family_select_customs').id,
            'view_mode': 'form',
            'context': {
                # 'default_attribute_type_id': self.id,
                # 'default_attribute_ids': self.env['product.attribute'].search([]).ids,
                'default_family_id': None,
                'default_is_invisible': True,
                'default_sku': '',
            },
        }


    def variant_product(self):
        pass


    def create_product(self):
          if all([self.family_id, self.sku]):
               res = self.env['product.management'].create({
                    'family_id': self.family_id.id,
                    'sku': self.sku,
                    'active':True
               })
          return{
               'type': 'ir.actions.act_window',
               'res_model': 'product.management',
               'view_mode':'tree,form',
               'target': 'current',
               'context': {'no_breadcrumbs': False},
               }

