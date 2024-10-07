# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class PimCategory(models.Model):
    _name = 'pim.category'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'parent child category'

    name = fields.Char(string='Name')