# -*- coding: utf-8 -*-
from datetime import timedelta, datetime, date
from odoo import models, fields, api , _
from odoo.exceptions import ValidationError as UserError
import cv2
import re
from pyzbar.pyzbar import decode
from datetime import datetime
from dateutil.relativedelta import relativedelta as rd



class LibraryCard(models.Model):
    """Defining Library Card."""

    _name = "library.card"
    _description = "Library Card information"
    _rec_name = "code"

    # @api.depends("student_id")
    # def _compute_name(self):
    #     """Compute name"""
    #     for rec in self:
    #         if rec.student_id:
    #             user = rec.student_id.name
    #         user = rec.teacher_id.name
    #         rec.card_name = user

    @api.depends("start_borrow", "duration")
    def _compute_end_borrow(self):
        for rec in self:
            if rec.start_borrow:
                rec.end_borrow = rec.start_borrow + rd(months=rec.duration)



    code = fields.Char("Mã Thẻ", required=True, default=lambda self: _("New"),
        help="Enter card number")
    book_limit = fields.Integer("Giới Hạn Số Lượng Sách", required=True,
        help="Enter no of book limit")
    
    """note"""
    name_borrower = fields.Char(string='Tên Bạn Đọc',size=250)
    email = fields.Char(string='Email Borrower', size=256, readonly=True)
    user = fields.Selection([("student", "Sinh Viên"), ("teacher", "Giảng Viên")],
        "Bạn Đọc", help="Select user")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('running', 'Running'),
        ('ended', 'Ended'),
        ('expire', 'Expired'),  # Thêm trạng thái expire
    ], default="draft", string='State')

    id_student = fields.Char(string="Mã Sinh Viên", help="ID of the student")
    
    student_id = fields.Many2one("res.partner", "Teacher Name")
    teacher_id = fields.Many2one("res.partner", "Teacher Name")
    start_borrow = fields.Date("Ngày Tạo Thẻ", default=fields.Date.context_today,
        help="Enter start date")
    duration = fields.Integer("Khoảng Thời Gian", help="Duration in months")
    end_borrow = fields.Date("Ngày Hết Hạn", compute="_compute_end_borrow",
        store=True, help="End date")
    active = fields.Boolean("Active", default=True,
        help="Activate/deactivate record")
    book_issue_count = fields.Integer(compute="compute_book_issue_count",
                                      string="Book Issue Count")
    
    # borrow_ids = fields.One2many('books.borrows', 'code')
    borrow_copies = fields.One2many('books.borrows','code')



    def running_state(self):
        """Change state to running"""
        # self.code = self.env["ir.sequence"].next_by_code("library.card"
        #         ) or _("New")
        self.code = f"LIB_{self.id_student}"   
        self.state = "running"

    def draft_state(self):
        """Change state to draft"""
        self.state = "draft"

    def unlink(self):
        for rec in self:
            if rec.state == "running":
                raise UserError(_(
                    """You cannot delete a confirmed library card!"""))
        return super(LibraryCard, self).unlink()

    def librarycard_expire(self):
        current_date = fields.Date.today()
        library_card_obj = self.env["library.card"]
        for rec in library_card_obj.search([("end_borrow", "<", current_date)]):
            rec.state = "expire"



    """ Scan name student """
    def action_scan_name_student(self):
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            print("Không thể mở camera.")
            return

        while True:
            ret, frame = cap.read()
            cv2.imshow('Camera', frame)

            decoded_objects = decode(frame)
            for obj in decoded_objects:
                qr_data = obj.data.decode('utf-8')
                print(f'Mã QR đã quét: \n{qr_data}')

                match = re.search(r'Id Student: (\d+)', qr_data)
                if match:
                    self.id_student = match.group(1)  # Gán giá trị ID sinh viên vào trường id_student
                    print(f'ID Sinh Viên: {self.id_student}')

                cap.release()
                cv2.destroyAllWindows()
                return

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        cap.release()
        cv2.destroyAllWindows()

    """ scan barcode of student """
    def action_scan_barcode_name_student(self):
        cap = cv2.VideoCapture(0)

        if not cap.isOpened():
            print("Không thể mở camera.")
            return

        while True:
            ret, frame = cap.read()
            cv2.imshow('Camera', frame)

            decoded_objects = decode(frame)
            for obj in decoded_objects:
                barcode_data = obj.data.decode('utf-8')
                print(f'Mã Barcode đã quét: \n{barcode_data}')

                match = re.search(r'(\d+)', barcode_data)
                if match:
                    self.id_student = match.group(1)  # Lưu ID sinh viên vào trường id_student
                    print(f'ID Sinh Viên: {self.id_student}')

                cap.release()
                cv2.destroyAllWindows()
                return

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        cap.release()
        cv2.destroyAllWindows()