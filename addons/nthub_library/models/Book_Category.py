# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError as UserError


class Book_Category(models.Model):
    '''
    class category content name of category books
    '''
    _name = 'books.category'
    _description = 'books category'

    name = fields.Char(string="Category")
    description = fields.Text(string="Description")


class LibraryBookShelf(models.Model):
    """Defining Library Shelf."""

    _name = "library.shelf"
    _description = "Library Shelf"

    name = fields.Char(string="Tên kệ sách")

    default_quantity = fields.Integer(string="Số lượng mặc định", default=80)
    quantity = fields.Integer(string="Số lượng Sách đã nhập", store=True, readonly=True, compute="_compute_quantity_book_in_shelf")
    book_copies_ids = fields.One2many('book.copies','library_shelf_id',string = "Sach luu tru ")

    rack_id = fields.Many2one('library.rack', string="Giá sách", help="Giá sách chứa kệ này", readonly = True)

    @api.model
    def _search(self, args, offset=0, limit=None, order=None, access_rights_uid=None):
        """
        We override the _search because we need to show the shelf
        according to the domain.
        """
        if 'library_shelf_domain' in self._context:
            domain_id = self.env["library.rack"].browse(self._context.get('library_shelf_domain'))
            shelf_ids = domain_id.library_shelf_ids
            if self.env.context.get('count'):
                return len(shelf_ids)
            return shelf_ids.ids
        return super(LibraryBookShelf, self)._search(args, offset=offset, limit=limit, order=order, access_rights_uid=access_rights_uid)
    
    @api.depends('book_copies_ids')
    def _compute_quantity_book_in_shelf(self):
        for record in self:
            record.quantity = len(record.book_copies_ids)
             


class LibraryRack(models.Model):
    """Defining Library Rack."""

    _name = "library.rack"
    _description = "Library Rack"

    quantity = fields.Integer(String ="Số lượng")

    name = fields.Char("Name", help="Rack Name")
    name_category_id = fields.Many2one('books.category',string="ten doanh muc")
    code = fields.Char("Code", help="Enter code here")
    active = fields.Boolean("Active", default="True",
        help="To active/deactive record")
    library_shelf_ids = fields.Many2many('library.shelf', 'library_rack_shelf_rel',
                                  'shelf_id', 'rack_id', string="Shelf")

    @api.constrains("library_shelf_ids")
    def check_shelf(self):
        if self.search([("id", "not in", self.ids),
                ("library_shelf_ids", "in", self.library_shelf_ids.ids)]):
            raise UserError("""Kệ thư viện đã được phân bổ cho một cấp bậc khác!!""")
        for shelf in self.library_shelf_ids:
            shelf.rack_id = self
    
    @api.constrains("code")
    def check_code(self):
        for record in self:
            code_old = self.env['library.rack'].search([('code', '=', record.code), ('id', '!=', record.id)])
            if code_old:
                raise UserError("Code đã được sử dụng ở giá khác, hãy điền lại")
        