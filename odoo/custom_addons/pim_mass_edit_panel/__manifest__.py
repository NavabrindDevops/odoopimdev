{
    'name': 'PIM Mass Edit Panel',
    'version': '17.0',
    "author": "Navabrind IT",
    'summary': 'Edit attribute for multiple records',
    'description': """
            Edit attribute for multiple records in tree view
    """,
    'category': 'product',
    'depends': ['pim_view_preference_button'],
    'data' : [
            'wizard/category.xml',
            'wizard/family.xml',
            'wizard/product_clone.xml',
            'security/ir.model.access.csv',
    ],
'assets': {
        'web.assets_backend': [
            'pim_mass_edit_panel/static/src/js/mass_edit_panel.js',
            'pim_mass_edit_panel/static/src/xml/mass_edit_panel.xml',
        ],
},
'installable': True,
    'application': True,
    'auto_install': False,
}
