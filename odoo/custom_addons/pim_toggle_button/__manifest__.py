{
    'name': 'Toggle Button for Discountinued Product Management',
    'version': '17.0',
    "author": "Navabrind IT",
    'summary': 'if this button switched on discontined products also shows in tree view',
    'description': """
            if this button switched on discontined products also shows in tree view
    """,
    'category': 'product',
    'depends': ['pim_view_preference_button'],
    'data' : [],
'assets': {
        'web.assets_backend': [
            'pim_toggle_button/static/src/js/discontinued_button.js',
            'pim_toggle_button/static/src/xml/discontinued_button.xml',
        ],
},
'installable': True,
    'application': True,
    'auto_install': False,
}