# -*- coding: utf-8 -*-
from datetime import timedelta, datetime, date
from odoo import models, fields, api , _
from odoo.exceptions import ValidationError as UserError
import re
from pyzbar.pyzbar import decode
from datetime import datetime
from dateutil.relativedelta import relativedelta as rd
import subprocess




class LibraryCard(models.Model):
    """Defining Library Card."""
    _name = "library.card"
    _description = "Library Card information"
    _rec_name = "code"
    _inherit = 'mail.thread'

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
    borrow_copies_ids = fields.One2many('books.borrows','code_id')
    list_book_copy_borrowed_ids = fields.One2many(
        'book.copies', 'code_id',
        string="Danh Sách Sách Đã Mượn",
        compute="_compute_list_book_copy_borrowed",
        help="Danh sách các sách đã mượn"
    )

    email = fields.Char(string='Email bạn đọc', size=256, readonly=True, compute='_compute_email',store = True)
    
    
    @api.depends('user', 'id_student', 'id_teacher')
    def _compute_email(self):
        for rec in self:
            if rec.user == 'student' and rec.id_student:
                rec.email = '{}@sv.ttn.edu.vn'.format(rec.id_student)
            elif rec.user == 'teacher' and rec.id_teacher:
                rec.email = '{}@gv.ttn.edu.vn'.format(rec.id_teacher)
            else:
                rec.email = ''


    @api.depends('borrow_copies_ids')
    def _compute_list_book_copy_borrowed(self):
        for rec in self:
            if rec.borrow_copies_ids:
                borrowed_books = rec.borrow_copies_ids.book_copy_list_ids.filtered(lambda copy: copy.state == 'borrowed')
                rec.list_book_copy_borrowed_ids = borrowed_books
            else:
                rec.list_book_copy_borrowed_ids = False
                
    
    def action_return_book(self):
        if not self.code:
            raise UserError('Xác định thẻ bạn đọc trước khi trả sách.')

        try:
            process = subprocess.Popen(['zbarcam', '--raw'], stdout=subprocess.PIPE)
            print("Đang quét mã sách để trả...")

            for line in iter(process.stdout.readline, b''):
                barcode_data = line.decode('utf-8').strip()
                print(f'Mã Barcode đã quét: {barcode_data}')
                match = re.search(r'(\d+)', barcode_data)

                if match:
                    barcode_book_copies = int(match.group(1))
                    print(f'DKCB: {barcode_book_copies}')

                    book_copies = self.env['book.copies'].search([('DK_CB', '=', barcode_book_copies)], limit=1)

                    if book_copies:
                        # Tìm borrow record liên quan
                        borrow_record = self.borrow_copies_ids.filtered(lambda b: book_copies in b.book_copy_list_ids)
                        if borrow_record.state == "delayed":
                            process.terminate()
                            return {
                                'type': 'ir.actions.act_window',
                                'name': 'Chi tiết phiếu mượn',
                                'res_model': 'books.borrows',
                                'view_mode': 'form',
                                'res_id': borrow_record.id,
                                'target': 'new',
                            }
                        elif borrow_record:
                            # Bỏ sách khỏi danh sách mượn
                            borrow_record.book_copy_list_ids = [(3, book_copies.id)]

                            # Nếu không còn sách nào => chuyển trạng thái về 'ended'
                            if not borrow_record.book_copy_list_ids:
                                borrow_record.state = 'ended'

                            # Cập nhật trạng thái sách
                            book_copies.state = 'available'

                            print(f'✅ Đã trả sách: {book_copies.book_id.name} ({book_copies.DK_CB})')
                        else:
                            print('⚠️ Không tìm thấy phiếu mượn liên quan đến sách này.')
                            continue
                    else:
                        print('❌ Không tìm thấy bản sao sách trong hệ thống.')
                        continue

                    # Dừng quét sau khi đã xử lý 1 sách
                    process.terminate()
                    return
        except FileNotFoundError:
            raise UserError("Không tìm thấy `zbarcam`. Cài bằng: sudo apt install zbar-tools")
        except Exception as e:
            raise UserError(f"Lỗi khi quét mã sách: {e}")
    def running_state(self):
        """Change state to running"""
        # self.code = self.env["ir.sequence"].next_by_code("library.card"
        #         ) or _("New")
        self.state = "running"
        for record in self:
            record.code = f"LIB_{self.id_student}"   
            record.state = "running"
            if record.email and record.code:
                group_user = self.env.ref('nthub_library.group_library_user_type')
                existing_user = self.env['res.users'].search([('login', '=', record.email)], limit=1)
                if not existing_user:
                    self.env['res.users'].create({
                        'name': record.name_borrower,
                        'login': record.email,
                        'email': record.email,
                        'password': record.id_student or record.id_teacher,
                        'groups_id': [(4, group_user.id)],  # ✅ chỉ thêm 1 group
                    })
                else:
                    # Nếu user đã tồn tại, vẫn thêm group thư viện nếu chưa có
                    if group_user.id not in existing_user.groups_id.ids:
                        existing_user.groups_id = [(4, group_user.id)]  # ✅ giữ nguyên các quyền cũ
                    else:
                        raise UserError(f"⚠️ Email {record.email} đã tồn tại và đã có quyền thư viện.")

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
     
    def action_scan_barcode_name_student(self, vals):
        """ Scan barcode of student using zbarcam """
        try:
            # Khởi động zbarcam dưới dạng process
            process = subprocess.Popen(['zbarcam', '--raw'], stdout=subprocess.PIPE)
            print("Đang chờ quét mã barcode sinh viên... (Bấm Ctrl+C hoặc đóng cửa sổ camera để hủy)")

            for line in iter(process.stdout.readline, b''):
                barcode_data = line.decode('utf-8').strip()
                print(f'Mã Barcode đã quét: {barcode_data}')
                
                match = re.search(r'(\d+)', barcode_data)
                if match:
                    student_id = match.group(1)
                    self.id_student = student_id  # Gán vào trường id_student
                    print(f'ID Sinh Viên: {student_id}')
                    process.terminate()
                    return
        except FileNotFoundError:
            raise UserError("Không tìm thấy lệnh `zbarcam`. Hãy cài đặt bằng: sudo apt install zbar-tools")
        except Exception as e:
            raise UserError(f"Lỗi khi quét mã: {e}")
            
        
    #cron update ended card
    def update_ended_card(self):
        """Update state to ended"""
        current_date = fields.Date.today()
        for rec in self.search([("end_borrow", "<", current_date)]):
            rec.state = "ended"
        
        

    @api.model
    def process_return(self):
        """Process the return of borrowed books by scanning QR code"""
        code = self.scan_barcode_with_zbarcam()
        if code:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Tìm kiếm theo ID bạn đọc',
                'res_model': 'library.card',
                'view_mode': 'tree,form',
                'views': [(self.env.ref('nthub_library.library_card_tree_view').id, 'tree'),
                          (self.env.ref('nthub_library.library_card_form_view').id, 'form')],
                'target': 'current',
                'domain': [('id_student', '=', code)],
                'context': {'default_id_student': code}
            }
        else:
            return {
                'type': 'ir.actions.act_window_close'
            }




    def scan_barcode_with_zbarcam(self):
        try:
            process = subprocess.Popen(['zbarcam', '--raw'], stdout=subprocess.PIPE)
            print("Đang chờ quét mã...")
            for line in iter(process.stdout.readline, b''):
                barcode_data = line.decode('utf-8').strip()
                print(f'Mã đã quét: {barcode_data}')
                process.terminate()
                return barcode_data
        except Exception as e:
            print(f'Lỗi: {e}')
            return None