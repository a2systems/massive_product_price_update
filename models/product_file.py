# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from unicodedata import name
from dateutil.relativedelta import relativedelta
from datetime import date,datetime,timedelta

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import ValidationError
import openpyxl
from io import BytesIO
import base64

class ProductPricesFile(models.Model):
    _name = 'product.prices.file'
    _description = 'product.prices.file'

    def btn_process_file(self):
        self.ensure_one()
        if not self.file:
            raise ValidationError('Por favor ingrese el archivo')
        if self.state != 'draft':
            raise ValidationError('Estado incorrecto')
        wb = openpyxl.load_workbook(filename=BytesIO(base64.b64decode(self.file)),read_only=True)
        worksheet = wb.active
        rows = worksheet.rows
        for x,row in enumerate(rows):
            # Saltea la primer fila porque tiene el nombre de las columnas
            if x == 0:
                continue
            # Lee cada una de las celdas en la fila
            vals = {}
            default_code = None
            new_price = 0
            for i,cell in enumerate(row):
                if i == 0 and cell.value:
                    default_code = cell.value
                if i == 1 and cell.value:
                    new_price = cell.value
            if default_code:
                product_tmpl_id = self.env['product.template'].search([('default_code','=',default_code)])
                if not product_tmpl_id:
                    raise ValidationError('Producto %s inexistente'%(default_code))
                vals = {
                        'file_id': self.id,
                        'product_tmpl_id': product_tmpl_id.id,
                        'old_price': product_tmpl_id.list_price,
                        'new_price': new_price,
                        }
                line_id = self.env['product.prices.file.line'].create(vals)
                product_tmpl_id.list_price = new_price
        self.state = 'done'


    name = fields.Char('Nombre')
    file = fields.Binary('Archivo')
    date = fields.Date('Fecha',default=fields.Date.today())
    line_ids = fields.One2many(comodel_name='product.prices.file.line',inverse_name='file_id',string='Líneas')
    state = fields.Selection(selection=[('draft','Borrador'),('done','Procesado')],string='Estado',default='draft')


class ProductPricesFileLine(models.Model):
    _name = 'product.prices.file.line'
    _description = 'product.prices.file.line'

    file_id = fields.Many2one('product.prices.file','Archivo')
    product_tmpl_id = fields.Many2one('product.template','Producto')
    old_price = fields.Float('Precio anterior')
    new_price = fields.Float('Nuevo precio')
