from odoo import models, fields, api
from odoo.exceptions import ValidationError as UserError

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    stock_quantity = fields.Float(string='Stock Quantity', compute='_compute_stock_quantity')
    category_ids = fields.Many2one('books.category', string="Dach Mục", required=True)
    price = fields.Float(string="Price")
    image = fields.Image(string="Book Cover")

    language = fields.Selection([('vn', 'Việt Nam'), ('en', 'English'), ('fr', 'French'), ('es', 'Spanish'), ('de', 'German'), ],
                                string='Language')
    description = fields.Text(string="Description")
    vergion = fields.Char(string="Vergion")
    ispn = fields.Char(string="Isbn")
    author_ids = fields.Many2many('books.author', string="Author Name")
    number_of_pages = fields.Integer(string="pages Book")
    color = fields.Integer(string="color")
    invoice = fields.Char(string="Invoice")

    select_rack = fields.Selection([
        ('new','Tạo mới Giá sách'),
        ('old','Chọn Giá sách hiện có')
    ] , help="Tạo mới Giá sách/Chọn Giá sách hiện có", string="Chọn Giá sách lưu ", default = "old")

    rack = fields.Many2one(
        'library.rack',
        required=False,
        store=True
    )

    library_shelf_id = fields.Many2one(
        'library.shelf', 
        string="Kệ Sách", 
        store=True,
        domain="[('id', 'in', available_shelf_ids)]"
    )

    available_shelf_ids = fields.Many2many(
        'library.shelf', compute="_compute_available_shelves"
    )

    name_rack = fields.Char("Name", help="Rack Name")
    code_rack = fields.Char("Code", help="Enter code here")
    active_rack = fields.Boolean("Active", default="True",
        help="To active/deactive record")
    library_shelf_ids = fields.Many2many('library.shelf', 'product_shelf_rel',
                                  'shelf_id', 'product_id', string="Shelf") 



    
    
    @api.onchange('select_rack')
    def _onchange_select_rack(self):
        if self.select_rack == 'new':
            self.rack = False
            self.env['library.rack'].create({
                'name_category_id': self.category_ids,
                'name': self.name_rack,
                'code': self.code_rack,
                'active': self.active_rack,
                'library_shelf_ids': [(6, 0, self.library_shelf_ids.ids)]
            })      

    @api.constrains('select_rack', 'rack')
    def _check_rack_required(self):
        for record in self:
            if record.select_rack != 'new' and not record.rack:
                raise UserError("The 'Rack' field is required when 'Select Rack' is not set to 'Create New Rack'.")
            
    @api.constrains('code_rack', 'name_rack', 'active_rack', 'library_shelf_ids')
    def _check_rack_fields(self):
        for record in self:
            if record.select_rack == 'new':
                if not record.code_rack or not record.name_rack or not record.active_rack:
                    raise UserError("Please fill in all required fields: code, name, and active status.")
                if not record.library_shelf_ids:
                    raise UserError("Please select at least one shelf.")
    
       

    @api.depends('product_variant_ids')
    def _compute_stock_quantity(self):
        for record in self:
            # Lấy tổng số lượng từ các stock.move liên quan đến các variants của product.template này
            moves = self.env['stock.move'].search([
                ('product_id.product_tmpl_id', '=', record.id),
                ('state', '=', 'done')  # Chỉ tính các move đã hoàn thành
            ])
            record.stock_quantity = sum(moves.mapped('quantity'))

    @api.depends('rack')
    def _compute_available_shelves(self):
        for record in self:
            if record.rack:
                record.available_shelf_ids = record.rack.library_shelf_ids
            else:
                record.available_shelf_ids = self.env['library.shelf'].search([])   
                
    @api.constrains("library_shelf_ids")
    def check_shelf(self):
        if self.env['library.rack'].search([
            ('library_shelf_ids','in',self.library_shelf_ids.ids)
        ]):
            raise UserError("""Kệ thư viện đã được phân bổ cho một cấp bậc khác!!""")
        else:
            self.env['library.rack'].create({
                'name' : self.name_rack,
                'code': self.code_rack,
                'active': self.active_rack,
                'library_shelf_ids': [(6, 0, self.library_shelf_ids.ids)]
            })
