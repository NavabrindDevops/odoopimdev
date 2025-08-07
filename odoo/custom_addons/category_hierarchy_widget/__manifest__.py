# -*- coding: utf-8 -*-
{
    'name': "MisterArt Odoo PIM-category widget",
    'version': '17.0',
    "author": "Navabrind IT",
    'summary': '',
    'description': """ OdooPIM For MisterArt

    """,
    'depends': ['base' ],
    'data': [
    ],
    'assets': {
        'web.assets_backend': [
            '/category_hierarchy_widget/static/src/scss/category_widget.scss',
            '/category_hierarchy_widget/static/src/js/category_widget.js',
            '/category_hierarchy_widget/static/src/js/category_form.js',
            '/category_hierarchy_widget/static/src/js/category_dialog.js',
            '/category_hierarchy_widget/static/src/xml/category_widget.xml',
            '/category_hierarchy_widget/static/src/xml/category_form.xml',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
