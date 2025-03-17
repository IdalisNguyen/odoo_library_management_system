# -*- coding: utf-8 -*-
from datetime import timedelta, datetime, date
from odoo import models, fields, api , _
from odoo.exceptions import ValidationError as UserError
import cv2,csv,os
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
    email = fields.Char(string='Email bạn đọc', size=256, readonly=True, compute='_compute_email')
    user = fields.Selection([("student", "Sinh Viên"), ("teacher", "Giảng Viên")],
        "Bạn Đọc", help="Select user")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('running', 'Running'),
        ('ended', 'Ended'),
        ('expire', 'Expired'),  # Thêm trạng thái expire
    ], default="draft", string='State')

    id_student = fields.Char(string="Mã Sinh Viên", help="ID of the student")
    id_teacher = fields.Char(string="Mã Giảng Viên", help="ID of the teacher")
    
    student_id = fields.Many2one("res.partner", "Teacher Name")
    teacher_id = fields.Many2one("res.partner", "Teacher Name")
    start_borrow = fields.Date("Ngày Tạo Thẻ", default=fields.Date.context_today,
        help="Enter start date")
    duration = fields.Integer("Khoảng Thời Gian", help="Duration in months",default = 6)
    end_borrow = fields.Date("Ngày Hết Hạn", compute="_compute_end_borrow",
        store=True, help="End date")
    active = fields.Boolean("Active", default=True,
        help="Activate/deactivate record")
    book_issue_count = fields.Integer(compute="compute_book_issue_count",
                                      string="Book Issue Count")
    
    # borrow_ids = fields.One2many('books.borrows', 'code')
    borrow_copies = fields.One2many('books.borrows','code')


    @api.depends('id_student','id_teacher')
    def _compute_email(self):
        for rec in self:
            if rec.user == 'student' and rec.id_student:
                rec.email = '{}@sv.ttn.edu.vn'.format(rec.id_student)
            elif rec.user == 'teacher' and rec.id_teacher:
                rec.email = '{}@gv.ttn.edu.vn'.format(rec.id_teacher)
            else:
                rec.email = ''

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

    def action_scan_barcode_name_student(self,vals):
        """ scan barcode of student """
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
        
    def update_ended_card(self):
        """Update state to ended"""
        current_date = fields.Date.today()
        for rec in self.search([("end_borrow", "<", current_date)]):
            rec.state = "ended"
        
        

    # Existing fields and methods...
    def check_and_generate_report(self):
        """Check and generate report for students or teachers with borrowed books"""
        input_dir = '/path/to/input/'  # Directory containing CSV files
        output_dir = '/path/to/output/'  # Directory to save reports

        if not os.path.exists(input_dir):
            print("Input directory not found.")
            return

        # Iterate through all CSV files in the directory
        for filename in os.listdir(input_dir):
            if filename.endswith('.csv'):
                input_file_path = os.path.join(input_dir, filename)
                report_data = []

                # Read IDs from the current CSV file
                with open(input_file_path, 'r') as file:
                    reader = csv.reader(file)
                    ids_to_check = [row[0] for row in reader]

                # Check for borrowed books
                for rec in self.search([('id_student', 'in', ids_to_check)]):
                    if rec.borrow_copies and rec.state == 'running':
                        report_data.append({
                            'id_student': rec.id_student,
                            'name_borrower': rec.name_borrower,
                            'borrowed_books': len(rec.borrow_copies),
                        })

                # Generate report if there are unreturned books
                if report_data:
                    report_file_path = os.path.join(output_dir, f'report_{filename}')
                    with open(report_file_path, 'w', newline='') as report_file:
                        writer = csv.DictWriter(report_file, fieldnames=['id_student', 'name_borrower', 'borrowed_books'])
                        writer.writeheader()
                        writer.writerows(report_data)
                    print(f"Report generated: {report_file_path}")
                else:
                    print(f"No borrowed books found in {filename}.")
