{
    'name': 'PIM view preference',
    'version': '17.0',
    "author": "Navabrind IT",
    'summary': 'if this button switched on discontined products also shows in tree view',
    'description': """
            if this button switched on discontined products also shows in tree view
    """,
    'category': 'product',
    'depends': ['pim_ext'],
    'data' : [
        'views/pim.xml',
        'views/ir_ui_view.xml',
    ],

'assets': {
        'web.assets_backend': [
            'pim_view_preference_button/static/src/js/pim_view_preference.js',

            'pim_view_preference_button/static/src/xml/pim_view_preference.xml',

        ],
},
'installable': True,
    'application': True,
    'auto_install': False,
}