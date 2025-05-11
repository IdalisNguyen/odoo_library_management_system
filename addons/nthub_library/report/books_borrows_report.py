from odoo import models, fields, api
from odoo.tools import format_date

class BookBorrowReport(models.Model):
    _name = 'books.borrows.report'
    _description = 'Thống kê mượn/trả sách'
    _auto = False  # dùng cho báo cáo SQL view

    name = fields.Char(string='Bạn đọc')
    student_id = fields.Char(string='Mã SV')
    borrow_id = fields.Char(string='Phiếu Mượn')
    total_borrows = fields.Integer(string='Tổng lượt mượn')
    total_returned = fields.Integer(string='Số lượt đã trả')
    total_delayed = fields.Integer(string='Trễ hạn')
    total_fine = fields.Float(string='Tổng phí phạt')
    last_borrow_date = fields.Date(string='Ngày mượn gần nhất')
    last_return_date = fields.Date(string='Ngày trả gần nhất')
    borrow_date = fields.Date(string='Ngày mượn')
    category_name = fields.Char(string='Danh mục')
    name_book = fields.Char(string='Tên sách')
    list_book_copy_borrowed_ids = fields.One2many(
        'book.copies', 'borrow_id',
        compute="_compute_list_book_copy_borrowed",
        string="Danh sách sách đang mượn",
    )
    borrow_copies_ids = fields.One2many('books.borrows','code_id', invisible=True)

    @api.depends('borrow_copies_ids')
    def _compute_list_book_copy_borrowed(self):
        for rec in self:
            if rec.borrow_copies_ids:
                borrowed_books = rec.borrow_copies_ids.book_copy_list_ids
                print("borrowed_books", borrowed_books)
                rec.list_book_copy_borrowed_ids = borrowed_books
            else:
                rec.list_book_copy_borrowed_ids = False
                         
    def _select(self):
        return """
            MIN(b.id) AS id,
            c.name_borrower::varchar AS name,
            c.id_student AS student_id,
            COUNT(b.id) AS total_borrows,
            COUNT(CASE WHEN b.state = 'ended' THEN 1 END) AS total_returned,
            COUNT(CASE WHEN b.state = 'delayed' THEN 1 END) AS total_delayed,
            COALESCE(SUM(b.delay_duration), 0) AS total_fine,
            MAX(b.start_borrow::date) AS last_borrow_date,
            MAX(b.return_date) AS last_return_date,
            b.start_borrow::date AS borrow_date,
            cat.name AS category_name,
            bks.name AS name_book,
            STRING_AGG(DISTINCT bks.name, ', ') AS borrowed_book_names,
            b.borrow_id AS borrow_id

        """

    def _from(self):
        return """
            books_borrows b
            LEFT JOIN library_card c ON b.code_id = c.id
            LEFT JOIN book_copies lb ON b.code_id = lb.id
            LEFT JOIN books_data bks ON lb.book_id = bks.id
            LEFT JOIN books_category cat ON bks.category_ids = cat.id

        """

    def _group_by(self):
        return """
            c.name_borrower, c.id_student, b.start_borrow::date, cat.name, bks.name, b.borrow_id
        """

    def init(self):
        self._cr.execute("DROP VIEW IF EXISTS books_borrows_report CASCADE")
        query = f"""
            CREATE VIEW books_borrows_report AS (
                SELECT
                    {self._select()}
                FROM
                    {self._from()}
                GROUP BY
                    {self._group_by()}
            )
        """
        self._cr.execute(query)
