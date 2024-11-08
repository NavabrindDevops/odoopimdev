# -*- coding: utf-8 -*-
{
    'name': 'Product Information Management',
    'version': '17.0',
    "author": "Abhinav By Navabrind",
    'summary': 'Dealing with product information management',
    'description': """
        Project Information Management
    """,
    'category': 'product',
    'depends': ['base', 'sale', 'product','stock','product_management','website_sale'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/product_view.xml',
        'wizard/mass_edit_view.xml',
        'views/pim_attribute_split_views.xml',
        'views/product_view.xml',
        'views/product_template_view.xml',
        'views/pim_attribute_type_views.xml',
        # 'views/pim_attribute_details_views.xml',
        'views/pim_attribute_group_views.xml',
        'wizard/attribute_group_wizard_views.xml',
        'wizard/attribute_wizard_views.xml',
        'wizard/attribute_variant_wizard_views.xml',
        'views/pim_category_views.xml',
        'views/pim_channels_views.xml',
        'views/pim.xml',

    ],
    'assets': {
                'web.assets_backend': [
                    'pim_ext/static/src/css/custom_style.scss',
                    'pim_ext/static/src/js/chatter_position.js',
                    # 'pim_ext/static/src/js/split_attribute_view.js',


                ],
        },
    'installable': True,
    'application': True,
    'auto_install': False,
}
