from odoo import models, fields, api
from odoo.tools import format_date

class BookBorrowReport(models.Model):
    _name = 'books.borrows.report'
    _description = 'Thống kê mượn/trả sách'
    _auto = False  # dùng cho báo cáo SQL view

    name = fields.Char(string='Bạn đọc')
    student_id = fields.Char(string='Mã SV')
    total_borrows = fields.Integer(string='Tổng lượt mượn')
    total_returned = fields.Integer(string='Số lượt đã trả')
    total_delayed = fields.Integer(string='Trễ hạn')
    total_fine = fields.Float(string='Tổng phí phạt')
    last_borrow_date = fields.Date(string='Ngày mượn gần nhất')
    last_return_date = fields.Date(string='Ngày trả gần nhất')
    borrow_date = fields.Date(string='Ngày mượn')


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
            b.start_borrow::date AS borrow_date
        """

    def _from(self):
        return """
            books_borrows b
            LEFT JOIN library_card c ON b.code_id = c.id
        """

    def _group_by(self):
        return """
            c.name_borrower, c.id_student, b.start_borrow::date
        """

    def init(self):
        query = f"""
            CREATE OR REPLACE VIEW books_borrows_report AS (
                SELECT
                    {self._select()}
                FROM
                    {self._from()}
                GROUP BY
                    {self._group_by()}
            )
        """
        self._cr.execute(query)