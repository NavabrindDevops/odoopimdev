# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class ProductCreate(models.Model):
    _name = 'product.create'
    _rec_name = 'name'

    name = fields.Char(string='Name')

    def create_product_rec(self):
        pass

    def create_product_rec_model(self):
        pass