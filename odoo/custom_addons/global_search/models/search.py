from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from urllib.parse import urlparse, parse_qs
from markupsafe import Markup
from datetime import datetime

from odoo.http import request
from odoo.tools import image_data_uri, FILETYPE_BASE64_MAGICWORD
import re
from lxml import etree


class SearchInfo(models.Model):
    _name = 'search.info'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Menu Info"

    def get_menu_name(self, menu_path):
        url = menu_path
        parsed_url = urlparse(url)
        query_string = parsed_url.fragment  # Since the parameters are after '#', we use fragment

        # Parse the query string to get the parameters
        params = parse_qs(query_string)

        # Extract menu_id
        menu_id = params.get('menu_id', [None])[0]
        menu_name = ''
        menu = self.env['ir.ui.menu'].search([('id', '=', menu_id)])
        if menu:
            if menu.complete_name:

                if "Product Management" in menu.complete_name:
                    menu_name = "Product Management"
                else:
                    menu_name = menu.name
            return menu_name

    def get_search_values_list(self, search_val):
        if search_val:
            family_info = []
            category_list_data = []
            brand_info = []
            family_data = self.env['family.attribute'].search([('name', 'ilike', search_val)])
            for f in family_data:
                fam_list = {
                    'name': f.name,
                    'id': f.id,
                             }
                family_info.append(fam_list)

            family_list_data = []
            family_relevant_data = self.env['family.attribute'].search([('name', 'ilike', search_val)])
            for fam in family_relevant_data:
                fam_data = {'name': fam.name,
                            'id': fam.id
                            }
                family_list_data.append(fam_data)

            category_list = self.env['pim.category'].search([('name','ilike',search_val)])
            for categ in category_list:
                categ_list = {'name':categ.name,
                              'id':categ.id}

                category_list_data.append(categ_list)

            brand_list = self.env['product.brand'].search([('name', 'ilike', search_val)])
            print(brand_list,'qqqqqqqqqqqqqqqq')
            for brand in brand_list:
                lists = {'name': brand.name,
                              'id': brand.id}

                brand_info.append(lists)

            data = {
                'family_info': family_info,
                'family_relevant_data': family_list_data,
                'category_list_data':category_list_data,
                'brand_info':brand_info,
            }
            return data