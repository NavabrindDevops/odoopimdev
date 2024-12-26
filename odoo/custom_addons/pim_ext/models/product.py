# -*- coding: utf-8 -*-

import time,pytz
import re
from datetime import datetime,timedelta,timezone,date
from email.policy import default
from markupsafe import Markup

from odoo import models, api, fields,_
from odoo.addons.test_impex.models import field
from odoo.exceptions import UserError, ValidationError
import traceback,pdb,inspect

from odoo.tools import drop_view_if_exists
import logging
from googletrans import Translator
_logger = logging.getLogger(__name__)



class AttributeForm(models.Model):
     _inherit = 'product.attribute'
     _rec_name = 'name'


     display_type = fields.Selection(
          selection=[
               ('radio', 'Radio'),
               ('date', 'Date'),
               ('file', 'File'),
               ('identifier', 'Identifier'),
               ('image', 'Image'),
               # ('measurement', 'Measurement'),
               ('multi_select', 'Multi Select'),
               ('multi_checkbox', 'Multi Checkbox'),
               ('link', 'Link'),
               ('number', 'Integer'),
               ('price', 'Price'),
               ('ref_data_multi', 'Reference Data Multi Select'),
               ('ref_data_simple_select', 'Reference Data Simple Select'),
               ('simple_select', 'Simple Select'),
               ('text', 'Text'),
               ('textarea', 'Text Area'),
               ('yes_no', 'Checkbox'),
               ('pills', 'Pills'),
               ('select', 'Select'),
               ('color', 'Color'),
               ('multi', 'Multi-checkbox (option)'),
          ],
          required=True,
          help="The display type used in the Product Configurator.")
     attribute_group = fields.Many2one('attribute.group', string='Attribute Group', tracking=True)
     attribute_type_id = fields.Many2one('pim.attribute.type', string='PIM Attribute Type')
     is_mandatory = fields.Boolean(string='Mandatory', default=False)
     is_required_in_clone = fields.Boolean(string='Required in Clone', default=True)
     is_cloning = fields.Boolean(string='Cloning', default=True)
     is_completeness = fields.Boolean(string='Completeness')
     original_name = fields.Char('Previous Name')

     attribute_types = fields.Selection([('basic', 'Basic'),
                                         ('optional', 'Optional')], string='Attribute Type')
     attribute_types_id = fields.Many2one('pim.attribute.type', string='Attribute Type')
     completed_in_percent = fields.Float('Completed Progressbar',compute="_compute_completness")
     state = fields.Selection([('unpublish', 'Unpublish'), ('publish', 'Publish')], string='Status', default='unpublish')


     position_ref_field_id = fields.Many2one("ir.model.fields", string="Position After", domain="[('model_id.model','=','product.management')]")



     def action_publish_attribute(self):
          for record in self:
               if not record.attribute_group:
                    raise ValidationError("Alert!! Please select the group of the '%s' attribute." % record.name)
               if record.state == 'unpublish':
                    if record.name:
                         field_name = f"x_{record.name.strip().replace(' ', '_').lower()}"
                         field_type = None
                         field_data = {}
                         if record.display_type == 'text':
                              field_type = 'char'
                         elif record.display_type == 'textarea':
                              field_type = 'text'
                         elif record.display_type == 'number':
                              field_type = 'integer'
                         elif record.display_type == 'file':
                              field_type = 'binary'
                         elif record.display_type == 'image':
                              field_type = 'binary'
                         elif record.display_type == 'simple_select':
                              field_type = 'selection'
                         elif record.display_type == 'date':
                              field_type = 'date'
                         if not field_type:
                              continue

                         field_data.update({
                              'name': field_name,
                              'field_description': record.name,
                              'ttype': field_type,
                              'model_id': self.env.ref('pim_ext.model_product_management').id,
                              'state': 'manual',
                         })
                         create_field = self.env['ir.model.fields'].create(field_data)
                         if field_type == 'selection' and record.value_ids:
                              for value in record.value_ids:
                                   sel_value = value.name.strip().replace(' ', '_').lower()
                                   sel_name = value.name
                                   self.env['ir.model.fields.selection'].create({
                                        'name': sel_name,
                                        'value': sel_value,
                                        'field_id': create_field.id
                                   })
                         view = self.env.ref('pim_ext.product_managemnt_form_view')
                         widget = "image" if record.display_type == "image" else ""
                         widget_attribute = f' widget="{widget}"' if widget else ""
                         new_field_xml = f'<field name="{field_name}"{widget_attribute}  required="False"/>'
                         arch_value = f"""
                         <xpath expr="//field[@name='{self.position_ref_field_id.name}']" position="after">
                             {new_field_xml}
                         </xpath>
                         """
                         self.env['ir.ui.view'].sudo().create({
                              'name': f'add_field_{field_name}_to_product_management',
                              'type': 'form',
                              'model': view.model,
                              'inherit_id': view.id,
                              'arch': arch_value,
                         })
                         group_line = self.env['attribute.group.lines'].search([
                              ('attr_group_id', '=', record.attribute_group.id),
                              ('product_attribute_id', '=', record.id)
                         ], limit=1)

                         if not group_line:
                              self.env['attribute.group.lines'].create({
                                   'attr_group_id': record.attribute_group.id,
                                   'product_attribute_id': record.id,
                                   'display_type': record.display_type,
                              })

                         record.write({'state': 'publish'})


     # def action_update_publish_attribute(self):
     #      for record in self:
     #           if not record.original_name:
     #                record.original_name = record.name
     #                print(record.original_name, 'originalllllllllllllll')
     #
     #           if record.name != record.original_name:
     #                field_name = f"x_{record.original_name.strip().replace(' ', '_').lower()}"
     #                ir_field = self.env['ir.model.fields'].sudo().search([
     #                     ('name', '=', field_name),
     #                     ('model_id', '=', self.env.ref('pim_ext.model_product_management').id)
     #                ], limit=1)
     #                if ir_field:
     #                     ir_field.write({
     #                          'field_description': record.name,
     #                     })
     #                     new_field_name = f"x_{record.name.strip().replace(' ', '_').lower()}"
     #                     self.env.cr.execute(f"""
     #                     ALTER TABLE product_management RENAME COLUMN {field_name} TO {new_field_name}
     #                 """)
     #                record.original_name = record.name
     #      return {
     #           'type': 'ir.actions.client',
     #           'tag': 'display_notification',
     #           'params': {
     #                'message': 'Attributes updated successfully, including related fields!',
     #                'type': 'success',
     #                'sticky': False,
     #           },
     #      }

     def _compute_completness(self):
          for rec in self:
               data = rec.search_read([('id','=',rec._origin.id)],fields=['attribute_type_id','display_type','attribute_types_id','attribute_types','attribute_group','is_mandatory','is_required_in_clone', 'is_cloning'])
               false_count = sum(1 for d in data for value in d.values() if value != False)
               rec.completed_in_percent = (false_count/7) * 100
               # raise ValidationError(false_count/8)

     def create_pim_attribute_type(self):
          # Return the action to open the product.attribute custom layout
          return {
               'type': 'ir.actions.act_window',
               'name': 'Create Attribute',
               'res_model': 'pim.attribute.type',
               'view_mode': 'form',
               'view_id': self.env.ref('pim_ext.view_product_attribute_custom').id,
               'target': 'current',
               'context': {
                    'default_attribute_ids': self.env['product.attribute'].search([]).ids,
               },
          }

     @api.constrains('name', 'value_ids')
     def check_attribute_name(self):
          pattern = "^(?=.*[a-zA-Z0-9])[A-Za-z0-9 ]+$"
          for rec in self:
               name_count = self.search_count([('name', '=ilike', rec.name)])
               if name_count > 1:
                    raise ValidationError("Attribute name already exist")
               if rec.name and not re.match(pattern, rec.name):
                    raise ValidationError("Attribute Name should be AlphaNumeric")
               if not rec.value_ids:
                    raise ValidationError("Please fill the Attribute values for dropdown")



     def write(self, vals):
          user_group = self.env.user.has_group('pim_ext.group_general_user')
          # if self.env.user.has_group('pim_ext.group_general_user') and self.env.user.has_group(
          #         'pim_ext.group_admin_user'):
          for rec in self:
               time_now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
               header = (
                             "Attribute Information Updated at %s<br/><table><tr><b/><th style='border:1px solid;padding-left:10px;text-align:left;text-wrap: nowrap;'>"
                             "Field</th><b/><th style='border:1px solid;text-align:left;padding-left:10px;text-wrap: nowrap;'>"
                             "Old Value</th><b/><th style='border:1px solid;text-align:left;padding-left:10px;text-wrap: nowrap;'>"
                             "New Value</th></tr>") % time_now
               msg_string = ''
               for key in vals:
                    if key in ['name', 'display_type', 'required_in_clone', 'mandatory', 'completeness']:
                         attribute = rec._fields[key].string
                         if key in ['display_type']:
                              selection_tuple = dict(rec._fields[key].selection)
                              old_value = selection_tuple[getattr(rec, key)] if getattr(rec, key) else 'N/A'
                         else:
                              old_value = getattr(rec, key) or 'N/A'
                         new_value = vals[key] or 'N/A'
                         msg_string += (("<tr><td style='border:1px solid;text-align:center;'>{key}</td>"
                                         "<td style='border:1px solid;text-align:center;'><span class='history_column'>{old_name} </span></td>"
                                         "<td style='border:1px solid;text-align:center;'><span class='history_column'>{new_name}</span></td></tr>").format(
                              key=attribute, old_name=old_value, new_name=new_value))

               if msg_string:
                    msg_string = header + msg_string + "</table>"
                    msg = (Markup(msg_string))
                    rec.message_post(body=msg, body_is_html=True)
               res = super().write(vals)
               return res

class Attributegroup(models.Model):
     _name = 'attribute.group'
     _inherit = ['mail.thread', 'mail.activity.mixin']

     name = fields.Char('Name', required=True,)
     description = fields.Text(string='Description')
     active = fields.Boolean('Active', default=True)
     attributes_ids = fields.One2many('product.attribute', 'attribute_group', string='Attributes', required=True, tracking=True, store=True)
     attribute_family_id = fields.Many2many('family.attribute', string='Attribute Family', required=True, tracking=True, store=True)
     attribute_group_line_ids = fields.One2many('attribute.group.lines', 'attr_group_id', string='Attribute group line')
     attribute_code = fields.Selection([('medias', 'Medias')], string="Code")
     attribute_code_rec = fields.Char(string='Code')
     attribute_label = fields.Char(string='English', compute="_compute_label_translation")
     parent_id = fields.Many2one(
          'attribute.group',
          string='Parent Group',
          ondelete='cascade',
     )
     child_ids = fields.One2many(
          'attribute.group',
          'parent_id',
          compute='_compute_child_ids',
          string='Sub-groups'
     )

     @api.depends('attribute_code_rec')
     def _compute_label_translation(self):
          translator = Translator()
          for record in self:
               if record.attribute_code_rec:
                    try:
                         user_lang = self.env.user.lang
                         lang_rec = self.env['res.lang'].search([('code', '=', user_lang)], limit=1)
                         src_lang = lang_rec.url_code
                         translation = translator.translate(record.attribute_code_rec, src=src_lang, dest='en')
                         record.attribute_label = translation.text.capitalize()
                    except Exception as e:
                         record.attribute_label = 'Error in translation'
               else:
                    record.attribute_label = ''

     # this is for loading tree view in while click edit button
     def _compute_child_ids(self):
          for record in self:
               record.child_ids = self.env['attribute.group'].search([])

     def attribute_group_unlink(self):
          print('deleteeeeeeeeeee')

     # attribute group edit button
     def attribute_group_open_form_view(self):
          all_attribute_group_ids = self.env['attribute.group'].search([]).ids
          self.ensure_one()
          return {
               'type': 'ir.actions.act_window',
               'name': 'Edit Attribute Group',
               'res_model': 'attribute.group',
               'view_mode': 'form',
               'view_id': self.env.ref('pim_ext.view_product_attribute_groups_custom').id,
               'context': {'no_breadcrumbs': True},
               'res_id': self.id,
          }

     # delete button group
     def attribute_group_unlink(self):
          return {
               'name': 'Confirm Deletion',
               'type': 'ir.actions.act_window',
               'res_model': 'attribute.group.unlink.wizard',
               'view_mode': 'form',
               'target': 'new',
               'context': {'default_group_id': self.id},
          }


     def action_back_to_menu(self):
          return {
               'type': 'ir.actions.client',
               'tag': 'reload',
               'params': {
                    'menu_id': 442,
               },
          }

     def save_attributes(self):
          return {
               'type': 'ir.actions.act_window',
               'view_mode': 'form',
               'res_model': 'attribute.group',
               'view_id': self.env.ref('pim_ext.view_product_attribute_groups_custom').id,
               'res_id': self.id,
               'context': {'no_breadcrumbs': True},
               'target': 'current',
          }

     # def attribute_group_unlink(self):
     #      print('dskjncccccccc')
     #      self.unlink()
     #      return {'type': 'ir.actions.client', 'tag': 'reload'}

     def create_pim_attribute_groups(self):
          print('grouppppppppppp')

     # @api.model
     # def create(self, vals):
     #      print('fkdjfkdfd', vals)
     #      record = super(Attributegroup, self).create(vals)
     #      record._check_unique_attributes()
     #      return record
     #
     # @api.model
     # def write(self, vals):
     #      print('fko9444444444', vals)
     #      res = super(Attributegroup, self).write(vals)
     #      if 'attribute_group_line_ids' in vals:
     #           self._check_unique_attributes()
     #      return res
     #
     # @api.constrains('attribute_group_line_ids')
     # def _check_unique_attributes(self):
     #      for record in self:
     #           attributes_in_group = record.attribute_group_line_ids.mapped('product_attribute_id')
     #           for attribute in attributes_in_group:
     #                other_groups = self.env['attribute.group'].search([
     #                     ('id', '!=', record.id),
     #                     ('attribute_group_line_ids.product_attribute_id', '=', attribute.id)
     #                ])
     #                if other_groups:
     #                     raise ValidationError(
     #                          f"The attribute '{attribute.name}' is already assigned to another attribute group."
     #                     )


class AttributeGroupLine(models.Model):
     _name = 'attribute.group.lines'

     attr_group_id = fields.Many2one('attribute.group', string='Attribute Group')
     used_attribute_ids = fields.Many2many(
          'product.attribute',
          compute='_compute_used_attribute_ids',
          string='Used Attributes',
          store=False
     )
     product_attribute_id = fields.Many2one('product.attribute', string='Product Attribute', domain="[('id', 'not in', used_attribute_ids)]")
     display_type = fields.Selection(
          selection=[
               ('radio', 'Radio'),
               ('date', 'Date'),
               ('file', 'File'),
               ('identifier', 'Identifier'),
               ('image', 'Image'),
               ('measurement', 'Measurement'),
               ('multi_select', 'Multi Select'),
               ('number', 'Number'),
               ('price', 'Price'),
               ('ref_data_multi', 'Reference Data Multi Select'),
               ('ref_data_simple_select', 'Reference Data Simple Select'),
               ('simple_select', 'Simple Select'),
               ('text', 'Text'),
               ('textarea', 'Text Area'),
               ('yes_no', 'Yes/No'),
               ('pills', 'Pills'),
               ('select', 'Select'),
               ('color', 'Color'),
               ('multi', 'Multi-checkbox (option)'),
          ],

          help="The display type used in the Product Configurator.")

     enable = fields.Boolean(string="Enable", default=True)
     value_per_channel = fields.Boolean(string="Value per channel", default=False)
     value_per_locale = fields.Boolean(string="Value per locale", default=False)

     @api.depends('attr_group_id', 'product_attribute_id')
     def _compute_used_attribute_ids(self):
          """Compute all attributes already assigned to groups."""
          all_used_attributes = self.env['attribute.group.lines'].search([]).mapped('product_attribute_id')
          for line in self:
               line.used_attribute_ids = all_used_attributes

     @api.onchange('enable')
     def _onchange_enable(self):
          if self.product_attribute_id:
               attribute_name = f"x_{self.product_attribute_id.name.lower().replace(' ', '_')}"
               name = f"add_field_{attribute_name}_to_product_management"
               attribute_view_exist = self.env['ir.ui.view'].search(
                    [('name', '=ilike', name), ('active', '!=', None)])
               arch = self._arch(attribute_name,self.enable)
               if attribute_view_exist.arch:
                    attribute_view_exist.arch = arch

     def _arch(self,attribute_name,active):
          if active == False:
               new_field_xml = f'<field name="{attribute_name}" invisible="True"/>'
          else:
               new_field_xml = f'<field name="{attribute_name}"/>'
          arch = f"""
                       <xpath expr="//field[@name='{self.product_attribute_id.position_ref_field_id.name}']" position="after">
                                                          %s
                                                  </xpath>""" % new_field_xml
          return arch


class AttributeGroupUnlinkWizard(models.TransientModel):
    _name = 'attribute.group.unlink.wizard'
    _description = 'Wizard to Confirm Deletion of Attribute Group'

    group_id = fields.Many2one('attribute.group', string="Attribute Group")

    def confirm_unlink(self):
        if self.group_id:
             self.group_id.unlink()
        return {
             'type': 'ir.actions.client',
             'tag': 'reload',
             'params': {
                  'menu_id': 442,
             },
        }


class ManufacturerAttribute(models.Model):
     _name = 'manufacturer.attribute'
     _inherit = ['mail.thread', 'mail.activity.mixin']

     name = fields.Char('Name', required=True, tracking=True)

class BrandAttribute(models.Model):
     _name = 'brand.attribute'
     _inherit = ['mail.thread', 'mail.activity.mixin']

     name = fields.Char('Name', required=True, tracking=True)

      
class FamilyProducts(models.Model):
     _name = 'family.products'

     product_id = fields.Many2one('product.template', 'Product', required=True)
     default_code = fields.Char('SKU #')
     family_id = fields.Many2one('family.attribute','Family')
     mpn_number = fields.Char('MPN')
     status = fields.Selection([('active','Active'),('inactive','In Active')],'Status')
     origin = fields.Char('Origin')
     po_min = fields.Integer('PO Min')
     po_max = fields.Integer('PO Max')
     p65 = fields.Char('P65')
     attribute1_id = fields.Many2one('product.attribute1','',related='family_id.attribute1_id',)
     attribute1_val = fields.Char('Attribute 1')
     attribute2_id = fields.Many2one('product.attribute2','',related='family_id.attribute2_id',)
     attribute2_val = fields.Char('Attribute 2')
     attribute3_id = fields.Many2one('product.attribute3','',related='family_id.attribute3_id',)
     attribute3_val = fields.Char('Attribute 3')
     attribute4_id = fields.Many2one('product.attribute4','',related='family_id.attribute4_id',)
     attribute4_val = fields.Char('Attribute 4')
     select_sku = fields.Boolean('Select')


class ProductAttribute(models.Model):
     _name = 'product.attribute1'

     name = fields.Char('Name', required=True)


class ProductAttribute2(models.Model):
     _name = 'product.attribute2'

     name = fields.Char('Name', required=True)


class ProductAttribute3(models.Model):
     _name = 'product.attribute3'

     name = fields.Char('Name', required=True)
     
class ProductAttribute4(models.Model):
     _name = 'product.attribute4'

     name = fields.Char('Name', required=True)


class FamilyAttribute(models.Model):
     _name = 'family.attribute'
     _inherit = ['mail.thread', 'mail.activity.mixin']
     _description = 'Family'

     code = fields.Char(string="Code",required=True,
                          readonly=True, default=lambda self: _('New'))
     description = fields.Text(string="Description")

     name = fields.Char('Name', required=True, tracking=True)
     description = fields.Text(string="Description")

     supplier_id = fields.Many2one('res.partner','Supplier')
     brand_id = fields.Many2one('brand.attribute','Brand')
     manufacture_id = fields.Many2one('manufacturer.attribute','Manufacturer')
     attributes_group_ids = fields.Many2many('attribute.group', string='Attributes Groups', tracking=True, domain=[('active', '=', True)])
     taxonomy_ids = fields.Many2many('product.public.category', string="Taxonomy")
     attch_ids = fields.Many2many('ir.attachment', 'ir_attach_rel',  'record_relation_id', 'attachment_id', string="Attachments")
     complementary_categ_ids = fields.Many2many('product.public.category','custom_categ_rel','family_id','cteg_id', string="Complementary Categories")
     product_family_ids = fields.One2many('family.products','family_id','Products')
     product_image = fields.Image(string="Image",copy=False, attachment=True, max_width=1024, max_height=1024)
     buyer_id = fields.Many2one('res.partner','Buyer')
     availability = fields.Selection([('all','All Channel')],'Availability')
     swatch = fields.Selection([('yes','Yes'),('no','No')],'Swatch')
     gift = fields.Selection([('yes','Yes'),('no','No')],'Gift')
     attribute1_id = fields.Many2one('product.attribute1','Attribute 1')
     attribute2_id = fields.Many2one('product.attribute2','Attribute 2')
     attribute3_id = fields.Many2one('product.attribute3','Attribute 3')
     attribute4_id = fields.Many2one('product.attribute4','Attribute 4')
     asn_description = fields.Html('ASN Description')
     product_families_ids = fields.One2many('family.products.line', 'families_id', 'SKU', readonly=False)
     variant_line_ids = fields.One2many('family.variant.line', 'variant_familiy_id', 'Variants', readonly=False)

     @api.model
     def create(self, vals):
          vals['code'] = self.env['ir.sequence'].next_by_code(
               'family.attribute') or None
          res = super(FamilyAttribute, self).create(vals)
          return res
     
     def edit_family(self):
          pass

     def delete_family(self):

          return {
               'type': 'ir.actions.act_window',
               'res_model': 'delete.family.wizard',
               'view_mode': 'form',
               'target': 'new',
               'context': {
                    'default_current_family_id': self.id,
                    'default_current_family' : self._origin.id,
                    },
          }

     def action_update(self):
          attribute_group = self.env['attribute.group'].search([("attribute_family_id", "in", self.id)])
          for record in attribute_group:
               self.attributes_group_ids = [(4, record.id)]

     def mass_edit(self):
         res=[]
         return res

     def create_pim_attribute_family(self):
          return {
               'name':_('Create Family'),
               'type':'ir.actions.act_window',
               'view_mode':'form',
               'res_model':'family.attribute',
          }

     def action_open_attribute_group_wizard(self):
          return {
               'type': 'ir.actions.act_window',
               'res_model': 'attribute.group.wizard',
               'view_mode': 'form',
               'target': 'new',
               'context': {'default_attribute_family_id': self.id},
          }

     def action_open_add_attribute_wizard(self):
          return {
               'type': 'ir.actions.act_window',
               'res_model': 'add.attribute.wizard',
               'view_mode': 'form',
               'target': 'new',
               'context': {'default_attribute_family_id': self.id},
          }

     def action__add_variant_wizard(self):
          return {
               'type': 'ir.actions.act_window',
               'res_model': 'attribute.variant.wizard',
               'view_mode': 'form',
               'target': 'new',
               'context': {'default_attribute_family_id': self.id},
          }


class ProductProduct(models.Model):
     _inherit = 'product.product'

     attribute_group_ids = fields.Many2many('attribute.group', string='Attribute Group', compute='_compute_attribute_group_ids', store=True)
     attribute_family_ids = fields.Many2many('family.attribute', string='Family Attribute', compute='_compute_attribute_group_ids', store=True)
     hs_code = fields.Char('HS Code')
     
     @api.depends('product_template_attribute_value_ids')
     def _compute_attribute_group_ids(self):
          self.attribute_group_ids = self.product_template_attribute_value_ids.attribute_id.attribute_group
          self.attribute_family_ids = self.product_template_attribute_value_ids.attribute_id.attribute_group.attribute_family_id


class ProductTemplate(models.Model):
     _inherit = 'product.template'

     hs_code = fields.Char('HS Code')
     mpn_number = fields.Char('MPN')
     status = fields.Selection([('active','Active'),('inactive','In Active')],'Status')
     origin = fields.Char('Origin')
     po_min = fields.Integer('PO Min')
     po_max = fields.Integer('PO Max')
     p65 = fields.Char('P65')
     attribute1_id = fields.Many2one('product.attribute1','Attribute 1')
     attribute1_val = fields.Char('Value 1')
     attribute2_id = fields.Many2one('product.attribute2','Attribute 2')
     attribute2_val = fields.Char('Value 2')
     attribute3_id = fields.Many2one('product.attribute3','Attribute 3')
     attribute3_val = fields.Char('Value 3')
     attribute4_id = fields.Many2one('product.attribute4','Attribute 4')
     attribute4_val = fields.Char('Value 4')
     family_id = fields.Many2one('family.attribute','Product Family')

