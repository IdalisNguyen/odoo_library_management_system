from odoo import models, fields, api

class StockQuant(models.Model):
    _inherit = 'stock.quant'

    borrowed_book_copies = fields.Integer(
        compute="_compute_borrowed_books",
        store=True
    )

    @api.depends('product_id','product_id.book_copies_ids.state')
    def _compute_borrowed_books(self):
        for quant in self:
            borrowed_copies = self.env['book.copies'].search_count([
                ('product_id', '=', quant.product_id.id),
                ('state', '=', 'borrowed')
            ])
            # print(f"Product: {quant.product_id.name}, Borrowed Copies: {borrowed_copies}")
            quant.borrowed_book_copies = borrowed_copies

class ProductLabelReport(models.AbstractModel):
    _inherit = 'product.template'
    _description = 'Report for Product Label 2x7'
            
    
    @api.model
    def _get_report_values(self,docids,data=None):
        books_copies = self.env[books_copies].search(['book_id.product_id','in' ,docids])
        
        return{
            'docs': self.env['product.template'].browse(docids),
            'books_copies' : books_copies
        }
        
    