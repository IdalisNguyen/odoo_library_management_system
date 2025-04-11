# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from odoo import models, fields, api
import random
from odoo.tools.float_utils import float_is_zero
from odoo.exceptions import UserError, ValidationError


'''
copies with the internal name _name set to 'book.copies'
 and a description _description set to 'books.copies'.
 These lines define different fields in the book.copies model:
name: A character field to hold the name of the book copy.
book_id: A many-to-one field that establishes a relationship with the books.data model. 
It represents the book associated with the copy.
state: A selection field that allows the user to choose the state of the book copy (lost, borrowed, or available).
start_date: A datetime field that holds the starting date of the book copy.
end_date: A date field that represents the end date of the book copy. 
It is computed based on the start_date and duration fields.
'''

class bookcopies(models.Model):
    _name = 'book.copies'
    _description = 'books.copies'

    name = fields.Char()
    book_id = fields.Many2one('books.data', string='Sách')
    # count = fields.Integer(related="book_id.copy_count")
    code_id = fields.Many2one('library.card', string='Thẻ Bạn Đọc')

    serial_number = fields.Char(string='Serial Number', unique=True)  # Số đăng ký cá biệt
    DK_CB = fields.Char(String="Số Đăng Ký Cá Biệt")

    state = fields.Selection([('lost', 'Mất'),
                              ('borrowed', 'Đã Mượn'),
                              ('available', 'Có Sẵn'),
                              ], default="available", string='Trạng Thái')

    start_date = fields.Datetime(default=fields.Datetime.today)
    end_date = fields.Date(string="End Date", store=True,
                           compute='_get_end_date_', inverse='_set_end_date')
    progress = fields.Integer(string="Progress", compute='_compute_progress')
    borrow_id = fields.Many2one('books.borrows')
    product_id = fields.Many2one('product.product', string='Sản phẩm', related='book_id.product_id', store=True)

    library_shelf_id = fields.Many2one('library.shelf', string="Kệ Sách")
    library_rack_id = fields.Many2one('library.rack', related='library_shelf_id.rack_id', store=True, string="Giá Sách")

    @api.depends('start_date', 'duration')
    def _get_end_date(self):

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




    @api.onchange('book_id')
    def _onchange_book_id(self):

        if self.book_id:
            copy_count = self.search_count([('book_id', '=', self.book_id.id)])
            self.name = self.book_id.name +' # '+ str(copy_count + 1)



    @api.depends('state')
    def _compute_progress(self):
        for rec in self:
            if rec.state =='lost':
                progress = 0
            elif rec.state =='borrowed':
                progress = 50
            elif rec.state == 'available':
                progress =100
            else:
                progress = 25
            rec.progress =progress


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'
    
    library_label_ids = fields.One2many('library.label.report','purchase_order_id',string="Labels book")
    
    #select_rack
    def button_confirm(self):
        res = super(PurchaseOrder, self).button_confirm()
        for line in self.order_line:
                if line.product_id:  # Chỉ xử lý sản phẩm vật lý
                    book = self.env['books.data'].search([('product_id', '=', line.product_id.id)], limit=1)
                    book_data = {
                        'name': line.product_id.name,
                        'product_id': line.product_id.id,
                        'ispn': line.product_id.ispn,
                        'category_ids': line.product_id.category_ids.id,
                        'language': line.product_id.language,
                        'description': line.product_id.description,
                        'vergion': line.product_id.vergion,
                        'author_ids': line.product_id.author_ids.ids,
                        'number_of_pages': line.product_id.number_of_pages,
                    }
                    if line.product_id.select_rack != 'new':
                        book_data['rack_ids'] = line.product_id.rack.id
                        book_data['shelf_ids'] = line.product_id.library_shelf_id.id
                    else:
                        rack = self.env['library.rack'].search([['code', '=', line.product_id.code_rack]], limit=1)
                        book_data['rack_ids'] = rack.id
                        book_data['shelf_ids'] = line.product_id.library_shelf_ids.id
                    
                    if book:
                        book.write(book_data)
                    else:
                        book = self.env['books.data'].create(book_data)
                    
                    dk_cb_list = []
                    for i in range(int(line.product_qty)):  # Lặp theo số lượng sách
                        DK_CB = self.generate_serial_number_by_category(book.category_ids.id, book_data['rack_ids'], book_data['shelf_ids'])
                        book_copy = self.env['book.copies'].create({
                            'book_id': book.id,
                            'DK_CB': DK_CB,
                            'library_shelf_id': book_data['shelf_ids'],
                        })
                        dk_cb_list.append(book_copy.id)
                    
                    # Lưu DK_CB vào order line
                    line.dk_cb_ids = [(6, 0, dk_cb_list)]
        
        return res

    def generate_serial_number_by_category(self, category_id, rack_id_code, shelf_id):
        """ Tạo số đăng ký cá biệt với tiền tố 10 + ID danh mục và tự động tăng """
        category_code = f"10{category_id}"
        rack_id_code = f"{rack_id_code or '00'}"  # Sử dụng '00' nếu rack_id_code là False
        shelf_id_code = f"{shelf_id or '00'}"  # Sử dụng '00' nếu shelf_id là False
        # Lấy các số DK_CB đã tồn tại cho danh mục này
        existing_serials = self.env['book.copies'].search([
            ('book_id.category_ids', '=', category_id),
            ('library_shelf_id', '=', shelf_id),
            ('library_shelf_id.rack_id.code', '=', rack_id_code)
        ]).mapped('DK_CB')
        if existing_serials:
            # Tìm số lớn nhất trong danh sách
            max_number = max(int(serial[-3:]) 
                for serial in existing_serials 
                    if serial[-3:].isdigit())
            next_count = str(max_number + 1).zfill(3)  # Tăng lên 1 và giữ 3 số
        else:
            next_count = "001"
        # Tạo số DK_CB mới
        serial_number = f"{category_code}{rack_id_code}{shelf_id_code}{next_count}"
        return serial_number
    
    def action_print_library_labels(self):
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        invoice_vals_list = []
        sequence = 10
        for order in self:
            if order.invoice_status != 'to invoice':
                continue
            order = order.with_company(order.company_id)
            pending_section = None
            invoice_vals = order._prepare_invoice()

            for line in order.order_line:
                if line.display_type == 'line_section':
                    pending_section = line
                    continue
                if not float_is_zero(line.qty_to_invoice, precision_digits=precision):
                    if pending_section:
                        line_vals = pending_section._prepare_account_move_line()
                        line_vals.update({'sequence': sequence})
                        invoice_vals['invoice_line_ids'].append((0, 0, line_vals))
                        sequence += 1
                        pending_section = None
                    
                    line_vals = line._prepare_account_move_line()
                    line_vals.update({'sequence': sequence})

                    # Lấy danh sách DK_CB từ order line
                    dk_cb_list = line.dk_cb_ids.mapped('DK_CB')

                    # Thêm DK_CB vào invoice line
                    line_vals.update({
                        'dk_cb_text': ", ".join(dk_cb_list)
                    })

                    invoice_vals['invoice_line_ids'].append((0, 0, line_vals))
                    sequence += 1

            invoice_vals_list.append(invoice_vals)

        if not invoice_vals_list:
            raise UserError(('Sản Phẩm Chưa Nhập Vào Kho. Không Thể In Nhãn!!!'))

        # Lưu dữ liệu vào model library.label.report
        report_data = []
        for invoice in invoice_vals_list:
            for line in invoice['invoice_line_ids']:
                if 'product_id' in line[2] and 'dk_cb_text' in line[2]:
                    dk_cb_codes = line[2]['dk_cb_text'].split(", ")  # Chuyển chuỗi thành danh sách
                    report_data.append({
                        'product_name': line[2].get('name', 'N/A'),
                        'dk_cb_list': ", ".join(dk_cb_codes),  # Lưu dưới dạng chuỗi
                        'purchase_order_id': order.id  # Liên kết với đơn đặt hàng hiện tại
                    })

        # Tạo bản ghi trong model library.label.report
        # self.env['library.label.report'].create(report_data)
        print(report_data)
        
        existing_report = self.env['library.label.report'].search([
            ('purchase_order_id','=',order.id)
        ], limit = 1 )
        
        if not existing_report:
            self.env['library.label.report'].create(report_data)

        return self.env.ref('nthub_library.library_label_report_action').report_action(self.ids)
        
class ProductProduct(models.Model):
    _inherit = 'product.product'

    book_copies_ids = fields.One2many('book.copies', 'product_id', string="Book Copies")
    
    library_shelf_stock_id = fields.Many2one('library.shelf',related='book_copies_ids.library_shelf_id', string="Kệ Sách")
    library_rack_stock_id = fields.Many2one('library.rack', related='library_shelf_id.rack_id', store=True, string="Giá Sách")
   
    
    qty_borrowed_book_copies = fields.Integer(
        compute="_compute_qty_borrowed_books",
        store=True
    )
    @api.depends('book_copies_ids.state')
    def _compute_qty_borrowed_books(self):
        for quant in self:
            borrowed_copies = self.env['book.copies'].search_count([
                ('product_id', '=', quant.id),
                ('state', '=', 'borrowed')
            ])
            # print(f"Product: {quant.product_id.name}, Borrowed Copies: {borrowed_copies}")
            quant.qty_borrowed_book_copies = borrowed_copies
    
    
class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    dk_cb_ids = fields.Many2many('book.copies', string="Số ĐK_CB",store=True)

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    dk_cb_text = fields.Text(string="Mã ĐK_CB")

class LibraryLabelReport(models.Model):
    _name = 'library.label.report'
    _description = 'Library Label Report'

    product_name = fields.Char(string="Tên Sản Phẩm")
    dk_cb_list = fields.Text(string="Danh Sách ĐKCB")  # Lưu dưới dạng chuỗi JSON hoặc text
    report_date = fields.Datetime(string="Ngày Tạo Báo Cáo", default=fields.Datetime.now)
    purchase_order_id = fields.Many2one('purchase.order', string="Đơn Đặt Hàng", ondelete='cascade')  # Khóa ngoại liên kết tới purchase.order