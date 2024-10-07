# -*- coding: utf-8 -*-

import time,pytz
import re
from datetime import datetime,timedelta,timezone,date
from email.policy import default
from markupsafe import Markup

from odoo import models, api, fields,_
from odoo.exceptions import UserError, ValidationError
import traceback,pdb,inspect

from odoo.tools import drop_view_if_exists


class AttributeForm(models.Model):
     _inherit = 'product.attribute'


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
          required=True,
          help="The display type used in the Product Configurator.")
     attribute_group = fields.Many2one('attribute.group', string='Attribute Group', required=True, tracking=True)
     attribute_type_id = fields.Many2one('pim.attribute.type', string='PIM Attribute Type')
     is_mandatory = fields.Boolean(string='Mandatory', default=False)
     is_required_in_clone = fields.Boolean(string='Required in Clone', default=True)
     is_completeness = fields.Boolean(string='Completeness')

     attribute_types = fields.Selection([('basic', 'Basic'),
                                         ('optional', 'Optional')], string='Attribute Type')

     def create_pim_attribute_type(self):
          print('ffffffffff')
          return {
               "name": _("Create Attribute Type"),
               "type": "ir.actions.act_window",
               "res_model": "pim.attribute.type",
               "target": "current",
               "views": [[False, "form"]],
          }

     @api.constrains('name', 'value_ids')
     def check_attribute_name(self):
          pattern = "^(?=.*[a-zA-Z0-9])[A-Za-z0-9 ]+$"
          for rec in self:
               print('recccccccccc', rec)
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

     name = fields.Char('Name', required=True, )
     active = fields.Boolean('Active', default=True)
     attributes_ids = fields.One2many('product.attribute', 'attribute_group', string='Attributes', required=True, tracking=True, store=True)
     attribute_family_id = fields.Many2many('family.attribute', string='Attribute Family', required=True, tracking=True, store=True)
     attribute_group_line_ids = fields.One2many('attribute.group.lines', 'attr_group_id', string='Attribute group line')

     def create_pim_attribute_groups(self):
          print('grouppppppppppp')


class AttributeGroupLine(models.Model):
     _name = 'attribute.group.lines'

     attr_group_id = fields.Many2one('attribute.group', string='Attribute Group')
     product_attribute_id = fields.Many2one('product.attribute', string='Product Attribute', ondelete='cascade', index=True)
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
          related='product_attribute_id.display_type',
          help="The display type used in the Product Configurator.")


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

     name = fields.Char('Name', required=True, tracking=True)
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

