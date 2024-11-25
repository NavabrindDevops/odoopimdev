# -*- coding: utf-8 -*-
{
    'name': 'Odoo PIM Export Data',
    'version': '17.0',
    "author": "Navabrind IT",
    'summary': '',
    'description': """Odoo PIM Export Data""",
    'category': 'product',
    'depends': ['base','web','pim_ext','base_import'],
    'data': [],
    'assets': {
        'web.assets_backend': [
            'export_data/static/src/js/export.js',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}
