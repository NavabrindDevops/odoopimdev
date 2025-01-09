# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class ProductCreate(models.Model):
    _name = 'product.create'
    _rec_name = 'name'

    name = fields.Char(string='Name')

    def create_product_rec(self):
        return {
            'name': 'Product create',
            'type': 'ir.actions.act_window',
            'res_model': 'product.create.master',
            'view_mode': 'form',
            'context': {'no_breadcrumbs': True},
            'view_id': self.env.ref('pim_ext.product_creation_view_master').id,
        }

    def create_product_rec_model(self):
        pass


class ProductCreateMaster(models.Model):
    _name='product.create.master'
    _description='Product creation page'

    family_id = fields.Many2one('family.attribute', string='Family')
    sku = fields.Char(string='SKU')

    def product_save(self):
        print('dkfjdkfjdfdf')
        family = self.family_id
        attributes = family.mapped('attributes_group_ids.attributes_ids')
        product = self.env['product.template'].create({
            'name': f"{self.sku}",
            'sku': self.sku,
            'family_id': family.id,
        })
        # context = dict(self.env.context, default_family_id=family.id, default_attributes=attributes)
        context = {
            'default_family_id': family.id,
            'default_attributes': attributes,
            'no_breadcrumbs': True,
        }
        print('dskdjskdjs99', context)
        print('ereeeeeeeeee', product)
        return {
            'type': 'ir.actions.act_window',
            'name': 'Product',
            'view_mode': 'form',
            'res_model': 'product.template',
            'res_id': product.id,
            'target': 'current',
            'context': context,
        }



    def product_cancel(self):
        pass

