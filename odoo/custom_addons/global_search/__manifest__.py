# -*- coding: utf-8 -*-
{
    'name': 'Odoo PIM Global Search',
    'version': '17.0',
    "author": "Navabrind IT",
    'summary': '',
    'description': """ Odoo PIM Global Search""",
    'category': 'product',
    'depends': ['base','web','pim_ext'],
    'data': [],
    'assets': {
        'web.assets_backend': [
            'global_search/static/src/js/global_search.js',
            'global_search/static/src/xml/global_search.xml',
            'global_search/static/src/css/search.css',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}
