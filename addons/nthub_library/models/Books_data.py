# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime, timedelta
'''
Books_data is a model defined in an object-relational mapping (ORM) framework, 
which is often used in Python-based web applications, such as Odoo or Django.
 This class represents a table or collection in a database where information about books is stored.
The _name attribute is used to specify the internal name of the model. In this case, 
it is set to 'books.data',
 which means the table or collection name associated with this model will be 'books_data'.
'''
class Books_data(models.Model):
    _name = 'books.data'
    _description = 'books.dat'

    name = fields.Char(string="Tittle")
    price = fields.Float(string="Price")
    image = fields.Image(string="Book Cover")

    language = fields.Selection([('vn', 'Việt Nam'), ('en', 'English'), ('fr', 'French'), ('es', 'Spanish'), ('de', 'German'), ],
                                string='Language')
    description = fields.Text(string="Description")
    number_of_pages = fields.Integer(string="pages Book")
    author_ids = fields.Many2many('books.author', string="Author Name")
    copy_ids = fields.One2many('book.copies', 'book_id', string='Copies')
    copy_count = fields.Integer(string='Copy Count', compute='_compute_copy_count')
    start_date = fields.Datetime(default=fields.Datetime.today)
    end_date = fields.Date(string="End Date", store=True,
                           compute='_get_end_date_', inverse='_set_end_date')
    color = fields.Integer(string="color")
    priority = fields.Selection([('0', 'normal'), ('1', 'low'),
                                 ('2', 'high'),
                                 ('3', 'very high')], string='priority')
    category_ids = fields.Many2one('books.category', string="Category Book")
    vergion = fields.Char(string="Vergion")
    ispn = fields.Char(string="Isbn")
    invoice = fields.Char(string="Invoice")
    product_id = fields.Many2one('product.product', string='Product')  # Liên kết với sản phẩm
    
    rack_ids = fields.Many2one('library.rack', string="Library Rạck")
    shelf_ids = fields.Many2one('library.shelf', string="Library Shelf")
    
    @api.depends('copy_ids')
    def _compute_copy_count(self):
        '''
        compute_copy_count: Method decorated with @api.depends('copy_ids').
        This method calculates the value of
         the copy_count field.
         It iterates over each record and sets the copy_count field to the length of the copy_ids field.
        '''
        for book in self:
            # book.copy_count = len(book.copy_ids)
            book.copy_count = str(len(book.copy_ids))

    @api.depends('start_date', 'duration')
    def _get_end_date(self):
        """
            Sets the end date based on the start date and duration.

            This method calculates the end date by adding the duration (in days) to the start date.
            The calculated end date is then assigned to the 'end_date' field of the record.

            If either the start date or duration is not available, the function does nothing.

            Note: This method assumes that the 'start_date' and 'duration' fields are already populated.
            """
        for r in self:
            if not (r.start_date and r.duration):
                r.end_date = r.start_date
                continue

            duration = timedelta(days=r.duration, seconds=-1)
            r.end_date = r.start_date + duration

    def _set_end_date(self):
        for r in self:
            if not (r.start_date and r.duration):
                continue

            r.duration = (r.end_date - r.start_date).days + 1








