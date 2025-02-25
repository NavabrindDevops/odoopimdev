# -*- coding: utf-8 -*-
{
    'name': 'Product Information Management',
    'version': '18.0',
    "author": "Navabrind",
    'summary': 'Dealing with product information management',
    'description': """
        Project Information Management
    """,
    'category': 'product',
    'depends': ['web', 'base', 'sale', 'product','stock','website_sale','web_hierarchy'],
    'data': [
        'security/group_security.xml',
        'security/ir.model.access.csv',
        'data/general_attributes_data.xml',
        'data/sequence.xml',
        'data/server_actions.xml',
        'wizard/product_view.xml',
        'wizard/delete_family.xml',
        'wizard/mass_edit_view.xml',
        'views/pim_attribute_split_views.xml',
        'views/pim.xml',
        'views/product_view.xml',
        'views/product_template_view.xml',
        # 'views/pim_attribute_type_views.xml',
        # 'views/pim_attribute_details_views.xml',
        'views/pim_attribute_group_views.xml',
        'wizard/attribute_group_wizard_views.xml',
        'wizard/attribute_wizard_views.xml',
        'wizard/attribute_variant_wizard_views.xml',
        'views/pim_category_views.xml',
        'views/pim_channels_views.xml',
        'views/brand.xml',
        'views/product_select_family.xml',
	'views/general_attributes.xml',
        'views/supplier.xml',
        'views/pim_attribute_group_split_views.xml',
        'views/attribute_master_split_views.xml',
        'views/pim_family_custom_split_view.xml',
        'views/product_split_view.xml',
        'views/product_creation_views.xml',


        # 'views/ir_ui_view.xml',

    ],
    'assets': {
                'web.assets_backend': [
                    'pim_ext/static/src/css/custom_style.scss',
                    'pim_ext/static/src/css/custom_style.css',

                    # 'pim_ext/static/src/js/chatter_position.js',
                    # 'pim_ext/static/src/js/create_button.js',
                    'pim_ext/static/src/xml/create_button.xml',
                    # 'pim_ext/static/src/js/view_button.js',
                    # 'pim_ext/static/src/js/dis_button.js',
                    # 'pim_ext/static/src/xml/view_button.xml',


                    'pim_ext/static/src/js/progressbar_field.js',
                    # 'pim_ext/static/src/js/animated_number_custom.js',
                    'pim_ext/static/src/xml/progressbar_widget_extended.xml',
                ],
        },
    'installable': True,
    'license': 'LGPL-3',
    'application': True,
    'auto_install': False,
}
