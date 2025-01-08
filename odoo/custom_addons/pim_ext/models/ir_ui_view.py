# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.exceptions import ValidationError
from lxml import etree
import re

class IrView(models.Model):
    _inherit = 'ir.ui.view'

    custom_view = fields.Boolean('Custom List View', default=False)
    custom_filter = fields.Char('Filter')
    share_user_ids = fields.Many2many("res.users", string="Share With")
    shared_user_id = fields.Many2one('res.users', String="View Shared To")
    user_view_parent_id = fields.Many2one('ir.ui.view',string="User View Parent")

    @api.constrains('share_user_ids')
    def _create_new_view(self):
        print('-----------------',self)
        records = self.search([('user_view_parent_id', '=', self._origin.id), ('type', '=', 'list')])
        data = set(self.share_user_ids.ids) - set(records.mapped('shared_user_id'))
        print('----------------rec', data)
        for rec in data:
            self.browse(self._origin.id).copy({'share_user_ids': None,'shared_user_id': rec,'user_view_parent_id':self._origin.id})


    def save_custom_list(self, description, view_id=None, res_model=None, optional_fields=None, filter_name=None):
        print("---------------save_custom_list",self._context, self.env)
        main_view = self.env['ir.ui.view'].sudo().search(
            [('id', '=', view_id), ('model', '=', res_model), ('type', '=', 'list')]
        )
        list_view_count = self.env['ir.ui.view'].sudo().search_count(
            [('model', '=', self._origin.model), ('type', '=', 'list'),
             ('active', '=', False), ('create_uid', '=', self.env.user.id)]
        )
        fields_with_widgets = [
            {'name': field['name'], 'widget': field['widget'], 'optional': 'show' if field['value'] else 'hide'}
            for field in optional_fields]

        fields_xml_new = ''.join([
            f'<field name="{field["name"]}"'
            + (f' widget="{field["widget"]}"' if field["widget"] else '')
            + f' optional="{field["optional"]}"'
            + '/>'
            for field in fields_with_widgets
        ])

        if list_view_count <= 9:
            custom_view = self.env['ir.ui.view'].sudo().create({
                'name': description,
                'type': 'list',
                'shared_user_id' : self.env.user.id,
                'model': main_view.model,
                'inherit_id': main_view.id,
                'xml_id': description,
                'custom_view': True,
                'active': True,
                'arch': """
                    <xpath expr="//list" position="replace">
                        <list create="false" string="Product" js_class="button_in_tree">
                        <header>
                            <button name="pim_product_creation" type="object" class="btn-primary"
                                string="Create" display="always"/>
                        </header>
                        <field name="name"/>
                        %s
                    </list>
                    </xpath>""" % fields_xml_new,
                'custom_filter': filter_name,
            })
            custom_view.model_data_id = custom_view.id
            list_view = self.env['ir.ui.view'].sudo().search([('model', '=', self._origin.model), ('type', '=', 'list'),
                                                          ('active', 'in', [True, False]),('id', '!=', custom_view.id),
                                                              ('create_uid', '=', self.env.user.id)])
            for l in list_view:
                if l.custom_view:
                    l.active = False

        elif list_view_count > 9:
            raise ValidationError('Current User Has exceeded the limit to add grid template')

        return list_view_count



    def get_custom_view_list(self):
        list_view = self.env['ir.ui.view'].sudo().search([('shared_user_id','=',self.env.user.id),('model', '=', self._origin.model), ('type', '=', 'list'),
                                                   ('active', '!=',None)])

        # list_view = list_view.filtered(lambda r : self.env.user.id in r.share_user_ids.ids or self.env.user.id == r.create_uid.id)
        default_view = self.env['ir.ui.view'].sudo().search([('model', '=', self._origin.model), ('type', '=', 'list'),
                                       ('inherit_id', '=', False), ('name', 'ilike', self._origin.name)])


        list_views = [{'view_id': l.id,'name': l.name,'active': l.active} for l in list_view if l.custom_view]

        selected_view = self.env['ir.ui.view'].sudo().search([('model', '=', self._origin.model), ('type', '=', 'list'),
                                                   ('active', 'in', [True]), ('shared_user_id', '=', self.env.user.id)],limit=1)
        data = {'list_views': list_views,
                'default_view':default_view.id,
                'selected_view_name':selected_view.name,
                'selected_view': selected_view.id,
                'selected_view_filter': selected_view.custom_filter or False
                }
        print("--------------data", data)
        return data

    def update_custom_list(self, view_id):
        print("---------------update_custom_list",self._context, self.env)

        lists = self.env['ir.ui.view'].sudo().search([('id', '=', int(view_id)), ('active', '!=', None)])
        lists.active = True
        list_views = self.env['ir.ui.view'].sudo().search([('model', '=', self._origin.model), ('type', '=', 'tree'),
                                                          ('active', '!=', None),('id', '!=', int(view_id)),
                                                          ('create_uid', '=', self.env.user.id)])
        list_views.write({'active': False})
        return lists.custom_filter


    def delete_custom_list(self, view_id):
        lists = self.env['ir.ui.view'].sudo().search([('id', '=', int(view_id)), ('active', 'in', [True, False])])
        lists.sudo().unlink()

    def update_default_custom_list(self, view_id):
        lists = self.env['ir.ui.view'].sudo().search([('id', '=', int(view_id)), ('active', 'in', [True, False])])
        lists.active = True
        print('--------------update_default_custom_list',self._origin.model)
        list_view = self.env['ir.ui.view'].sudo().search([('model', '=', self._origin.model), ('type', '=', 'tree'),
                                                          ('active', 'in', [True, False]),
                                                          ('create_uid', '=', self.env.user.id)])
        for l in list_view:
            if l.custom_view:
                l.active = False

    def update_saved_list(self, view_id, active_fields, filter_name):
        list_view = self.env['ir.ui.view'].sudo().search([('id', '=', int(view_id)), ('active', 'in', [True, False])])
        if filter_name:
            list_view.custom_filter = filter_name

        arch = list_view.arch_base
        arch_tree = etree.fromstring(arch)
        for field in active_fields:
            field_name = field['objName']
            field_status = field['status']
            field_element = arch_tree.xpath(f"//field[@name='{field_name}']")
            if field_element:
                field_element[0].set('optional', 'show' if field_status else 'hide')

        modified_arch = etree.tostring(arch_tree, pretty_print=True).decode()
        list_view.write({'arch_base': modified_arch})
        filter_name = list_view.custom_filter
        return filter_name


# class GridViewTemplate(models.Model):
#     _name = 'grid.view.template'
#     _description = 'Grid View Templates'
#
#     family_id = fields.Many2one('family.attribute')
#     sku_id = fields.Many2one('family.products', string="SKU")
#     template_selection = fields.One2many('grid.view.data', 'grid_template_id')
#     primary_sku_template = fields.Many2one('sku.grid.template')
#
#     @api.model
#     def default_get(self, fields):
#         res = super(GridViewTemplate, self).default_get(fields)
#         default_template_id = self.env['sku.grid.template'].search([('default_template', '=', True)])
#         template_list = self.env['sku.grid.template'].search([('name', '!=', False), ('shared_template', '=', True), ('family_id', '=', res.get('family_id'))])
#         template_list2 = self.env['sku.grid.template'].search([('name', '!=', False), ('user_id', '=', self.env.user.id),
#                                                                ('self_template', '=', True), ('family_id', '=', res.get('family_id'))])
#         combined_list = template_list.ids + template_list2.ids + default_template_id.ids
#         templates = self.env['sku.grid.template'].search([('id', 'in', combined_list)])
#         template_selection_defaults = []
#         # for rec in template_list:
#         # template_selection_defaults.append({
#         #     'is_primary': True,
#         #     'template_name': 'Default Template',
#         #     'default_template': True
#         # })
#         default_template_id = ''
#         for rec in templates:
#             if rec.name == 'Default Template':
#                 template_selection_defaults.append({
#                     'is_primary': True,
#                     # 'template_name': rec.name,
#                     'sku_template_id': rec.id,
#                     'default_template': True,
#                 })
#                 default_template_id = rec.id
#             else:
#                 template_selection_defaults.append({
#                     'is_primary': False,
#                     # 'template_name': rec.name,
#                     'sku_template_id': rec.id,
#                     'default_template': False,
#                 })
#
#         if 'template_selection' in fields:
#             res.update({
#                 'template_selection': [(0, 0, group) for group in template_selection_defaults],
#                 'primary_sku_template': default_template_id
#             })
#
#         return res
#
#     def grid_confirm(self):
#         for rec in self:
#             default_val = rec.template_selection.filtered(lambda x: x.is_primary)
#             name = default_val.sku_template_id.name
#             view_name = 'sku_template_update_' + name.lower().replace(' ', '_')
#             view_exist = self.env['ir.ui.view'].search(
#                 [('name', 'ilike', view_name), ('active', 'in', [True, False])])
#             view_exist.active = True
#
#         # return {
#         #     'type': 'ir.actions.client',
#         #     'tag': 'reload',
#         # }
#
#     @api.onchange('template_selection')
#     def onchange_template_primary_selection(self):
#         for rec in self:
#             primary_template_val = rec.template_selection.filtered(
#                 lambda x: x.sku_template_id == rec.primary_sku_template)
#             primary_template = rec.template_selection.filtered(lambda x: x.is_primary)
#             if rec.template_selection:
#                 if not len(primary_template):
#                     if primary_template_val:
#                         primary_template_val.is_primary = True
#                     else:
#                         if len(rec.template_selection) == 1:
#                             rec.template_selection[0].is_primary = True
#                 elif len(primary_template) == 1:
#                     rec.primary_sku_template = primary_template.sku_template_id
#                 if len(primary_template) > 1:
#                     if primary_template_val:
#                         primary_template_val.is_primary = False
#                     rec.primary_sku_template = rec.template_selection.filtered(lambda x: x.is_primary).sku_template_id
#
#     @api.onchange('primary_sku_template')
#     def onchange_primary_sku_template(self):
#         for rec in self:
#             rec.family_id.primary_sku_template = rec.primary_sku_template
#

# class GridViewData(models.Model):
#     _name = 'grid.view.data'
#     _description = 'Grid View Data'
#
#     is_primary = fields.Boolean('Primary', default=False)
#     grid_template_id = fields.Many2one('grid.view.template', string="Grid Template")
#     sku_template_id = fields.Many2one('sku.grid.template', string="Grid Template")
#     family_id = fields.Many2one('family.attribute')
#     template_name = fields.Char('Grid Template', related='sku_template_id.name')
#     default_template = fields.Boolean('Default', default=False)
#     sku_id = fields.Many2one('family.products', string="SKU")
#     shared_template = fields.Boolean('Shared',  related='sku_template_id.shared_template', store=True)


class IrFieldsModel(models.Model):
    _inherit = 'ir.model.fields'

    @api.depends('field_description')
    def _compute_display_name(self):
        for field in self:
            field.display_name = f'{field.field_description}'
