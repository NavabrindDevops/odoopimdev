# -*- coding: utf-8 -*-
{
    'name': 'Odoo PIM Import Data',
    'version': '17.0',
    "author": "Navabrind IT",
    'summary': '',
    'description': """Odoo PIM Import Data""",
    'category': 'product',
    'depends': ['base','web','pim_ext','base_import'],
    'data': [
        'views/ir_attachments.xml'
            ],
    'assets': {
        'web.assets_backend': [
            'import_data/static/src/xml/import_action.xml',
            'import_data/static/src/js/import_action.js',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}
