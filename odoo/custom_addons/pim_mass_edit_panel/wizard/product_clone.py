from odoo import models, fields, api, _


class CloneProductWizard(models.TransientModel):
    _name = 'clone.product.wizard'
    _description = 'Clone Product Wizard'

    count = fields.Integer(default=1)
    active_product_ids = fields.Many2many('product.management', string='PM Ids')
    product_line_ids = fields.One2many('clone.product.lines', 'clone_wizard_id')

    @api.model
    def get_clone_product_view_id(self):
        view = self.env.ref('pim_ext.clone_product_wizard_form', raise_if_not_found=False)
        return view.id if view else False

    def clone_product(self):
        for wizard in self:
            for product in wizard.active_product_ids:
                for _ in range(wizard.count):
                    product_data = {}
                    for line in wizard.product_line_ids:
                        if line.field_id:
                            try:
                                product_data[line.field_id.name] = getattr(product, line.field_id.name, False).id
                            except:
                                product_data[line.field_id.name] = getattr(product, line.field_id.name, False)
                    self.env['product.management'].create(product_data)
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': 'Product Cloned Successfully!!',
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }


class CloneProductLines(models.TransientModel):
    _name = 'clone.product.lines'

    clone_wizard_id = fields.Many2one('clone.product.wizard')
    field_id = fields.Many2one('ir.model.fields', ondelete="cascade")