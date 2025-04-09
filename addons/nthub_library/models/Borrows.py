# -*- coding: utf-8 -*-
from datetime import timedelta, datetime, date
from odoo import models, fields, api , _
from odoo.exceptions import ValidationError as UserError
import cv2
import re
from pyzbar.pyzbar import decode
from datetime import datetime
from dateutil.relativedelta import relativedelta as rd
import subprocess


from odoo import http
from odoo.http import request
'''
The Borrows class represents a model for book borrowings in the context of an application built using the Odoo framework. 
It extends the models.Model class, which is the base class for all Odoo models.
The _name attribute is used to specify the internal name of the model. In this case,
the internal name is set to 'books.borrows'.
This name is used to identify the model in the database and in various places within the Odoo framework.
The _description attribute provides a description for the model. In this case, it is set to 'books.borrows'.
The class defines several fields that represent different aspects of a book borrowing
'''
class Borrows(models.Model):
    _name = 'books.borrows'
    _description = 'books.borrows'
    _inherit = 'mail.thread'


    code_id = fields.Many2one('library.card', string='Thẻ Bạn Đọc')
    name_library_card = fields.Char(related='code_id.name_borrower', redonly = True, string = "Tên Bạn Đọc",size=250)
    name_card_id = fields.Many2one('res.partner', related='code_id.student_id', string="Tên Bạn Đọc")
    id_student = fields.Char(string="Mã Sinh Viên", size=256, related='code_id.id_student',readonly=True)


    start_borrow = fields.Datetime(string="Ngày Mượn", default=lambda self: fields.Datetime.now())
    state = fields.Selection([('draft', 'Draft'),
                              ('running', 'Running'),
                              ('delayed', 'Delayed'),
                              ('ended', 'Ended'),
                              ], default="draft", string='state')
    end_borrow = fields.Datetime(string="Ngày Trả", store=True,
                                 compute='_compute_end_borrow')

    color = fields.Integer()
    duration = fields.Integer()
    received_date = fields.Datetime()
    delay_duration = fields.Float(string="Delay Duration", readonly=True)
    delay_penalties_id = fields.Many2one('delay.penalities', string="Phạt Trì Hoãn")
    borrows_duration = fields.Float(string="Thời Hạn Mượn", default = 6)
    
    book_copy_list_ids = fields.Many2many('book.copies')
    book_copy_id = fields.Many2one('book.copies', string='Book Copy')
    
    partner_id = fields.Many2one('res.partner', string='Partner')

    borrow_id = fields.Char(string='Mã Mượn', compute='_default_borrow_id', store=True)
    return_date = fields.Date(string='Ngày Hoàn Trả')


    # search borrower
    @api.model
    def process_qr_scan(self):
        # Giả sử action_scan_qr_return_borrow trả về book_id
        book_id = self.action_scan_qr_return_borrow()
        if book_id:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Tìm kiếm theo ID sách',
                'res_model': 'books.borrows',
                'view_type': 'form',
                'view_mode': 'tree,form',
                'target': 'current',
                'domain': [('book_id.dkcd', '=', book_id)],
                'context': {'default_book_id.dkcd': book_id}
            }
        else:
            return {
                'type': 'ir.actions.act_window_close'
            }
    def action_scan_qr_return_borrow(self):
        a = 10
        # Mở camera
        cap = cv2.VideoCapture(0)

        # Kiểm tra xem camera có được mở không
        if not cap.isOpened():
            print("Không thể mở camera. Hãy chắc chắn rằng không có ứng dụng khác sử dụng camera.")
            return
        # Lặp để hiển thị hình ảnh từ camera
        while True:
            # Đọc frame từ camera
            ret, frame = cap.read()

            # Hiển thị frame
            cv2.imshow('Camera', frame)

            # Quét mã QR
            decoded_objects = decode(frame)
            for obj in decoded_objects:
                qr_data = obj.data.decode('utf-8')
                
                print(f'Mã QR đã quét: \n{qr_data}')
                # match = re.search(r'(\d+)', qr_data)
                # match = re.search(r'(\d+)', qr_data)
                match = re.search(r'(.+)', qr_data)

                if match:
                    book_id = match.group(1).strip()
                    print(f"Id scaned {book_id}")
                    return book_id
                return False
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        # Giải phóng camera và đóng cửa sổ hiển thị khi thoát vòng lặp
        cap.release()
        cv2.destroyAllWindows()        

    # tạo mã mượn của phiếu mượn 
    @api.depends('id_student')
    def _default_borrow_id(self):
        if self.id_student:
            student_id = self.id_student
            borrow_count = self.search_count([('id_student', '=', student_id)])
            self.borrow_id = '{}_{}'.format(student_id, borrow_count + 1)
        else:
            # Set a placeholder or temporary value for borrow_id when complete data isn't available.
            self.borrow_id = 'Incomplete_Info'
         
    # kiểm tra trong danh sách mượn có sách thì trạng thái borrow thành running
    @api.constrains('book_copy_list_ids')
    def _check_book_copy_list_ids(self):
        if self.book_copy_list_ids:
            if len(self.book_copy_list_ids) > self.code_id.book_limit:
                raise UserError(f'Số sách mượn vượt quá giới hạn cho phép ({self.code_id.book_limit}).')
            self.state = 'running'
            for book in self.book_copy_list_ids:
                book.state = 'borrowed'
            num = len(self.book_copy_list_ids)
            self.code_id.book_limit -= num
        else:
            self.state = 'ended'
    # in báo cáo mượn sách
    def action_report(self):
        # function to report wornning
        return self.env.ref('nthub_library.report_borrows_warning_id').report_action(self)


    # tính toán ngày trả
    @api.depends("start_borrow", "borrows_duration")
    def _compute_end_borrow(self):
        for rec in self:
            if rec.start_borrow:
                rec.end_borrow = rec.start_borrow + rd(months=rec.borrows_duration)            
            
    # chuyển trạng thái về kết thúc
    def action_ended(self):
        for record in self:
            for book in record.book_copy_list_ids:
                book.state = 'available'
            record.code_id.book_limit += len(self.book_copy_list_ids)
            record.book_copy_list_ids = [(5, 0, 0)]  # Clear all books from the record
            record.state = 'ended'
            record.return_date = fields.Date.today()

    # chuyển trạng thái về nháp
    def action_draft(self):
        for rec in self:
            if rec.state == 'ended':
                rec.state = 'draft'
            else:
                raise UserError('Không thể đặt lại về dạng nháp. Bản ghi không ở trạng thái "ended".')

    @api.onchange('end_borrow', 'received_date')
    def onchange_dates(self):
        '''
        to calculate delay_duration based on end_borrow and received_date
         delay_duration = received_date - end_borrow
        '''
        if self.end_borrow and self.received_date:
            delta = self.received_date - self.end_borrow
            if delta.days < 0:
                nod = 0
            else:
                nod = delta.days
            self.delay_duration = nod
        else:
            self.delay_duration = 0


    # kiểm tra thời gian mượn sách
    def update_delayed_status(self):
        # cron job every day to check state =running $ end_borrow < date today  change state from running to delayed
        today = date.today()
        running_borrows = self.env['books.borrows'].search([('state', '=', 'running'), ('end_borrow', '<', today)])
        for rec in running_borrows:
            if rec:
                rec.state = 'delayed'


    def action_barcode_name_student(self, vals):
        """ Scan student barcode using zbarcam (ổn định, không dùng cv2) """
        try:
            # Mở zbarcam
            process = subprocess.Popen(['zbarcam', '--raw'], stdout=subprocess.PIPE)
            print("🎥 Đang mở camera để quét mã sinh viên...")

            for line in iter(process.stdout.readline, b''):
                barcode_data = line.decode('utf-8').strip()
                print(f'📦 Mã Barcode đã quét: {barcode_data}')

                match = re.search(r'(\d+)', barcode_data)
                if match:
                    barcode_name = int(match.group(1))
                    print(f'🎯 ID Student Barcode: {barcode_name}')

                    # Tìm thẻ sinh viên
                    student = self.env['library.card'].search([('id_student', '=', barcode_name)], limit=1)

                    if student:
                        self.code_id = student.id
                        print(f'✅ Đã tìm thấy thẻ bạn đọc: {student.name_borrower}')
                    else:
                        raise UserError('❌ Không tìm thấy sinh viên trong hệ thống.')

                    process.terminate()  # Kết thúc quét sau khi tìm được
                    return
        except FileNotFoundError:
            raise UserError("Không tìm thấy `zbarcam`. Cài đặt bằng: sudo apt install zbar-tools")
        except Exception as e:
            raise UserError(f"Lỗi khi quét mã sinh viên: {e}")


    def action_scan_qr_book_copies(self, vals):
        """ Quét mã QR sách mượn bằng zbarcam (thay cv2) """
        if not self.code_id:
            raise UserError('Xác định thẻ bạn đọc trước khi thêm sách mượn.')

        try:
            # Mở camera và bắt đầu quét mã
            process = subprocess.Popen(['zbarcam', '--raw'], stdout=subprocess.PIPE)
            print("🎥 Đang mở camera để quét mã sách...")

            for line in iter(process.stdout.readline, b''):
                barcode_data = line.decode('utf-8').strip()
                print(f'📦 Mã Barcode đã quét: {barcode_data}')

                match = re.search(r'(\d+)', barcode_data)
                if not match:
                    continue

                barcode_book_copies = int(match.group(1))
                print(f'🎯 DKCB: {barcode_book_copies}')

                # Tìm bản sao sách
                book_copies = self.env['book.copies'].search([('DK_CB', '=', barcode_book_copies)], limit=1)

                if book_copies:
                    if book_copies in self.book_copy_list_ids:
                        raise UserError(f'Sách {book_copies.book_id.name} - {book_copies.DK_CB} đã có trong danh sách mượn.')

                    if book_copies.state == 'borrowed':
                        process.terminate()
                        raise UserError(f'Sách {book_copies.book_id.name} - {book_copies.DK_CB} đang được mượn.')

                    # Thêm sách vào danh sách mượn
                    self.book_copy_list_ids = [(4, book_copies.id)]
                    print(f'✅ Đã thêm sách: {book_copies.book_id.name} - {book_copies.DK_CB}')
                else:
                    print('❌ Không tìm thấy bản sao sách trong hệ thống.')
                    continue

                process.terminate()
                return  # Sau khi quét 1 sách thì dừng (hoặc bạn có thể lặp nếu muốn scan nhiều lần)
        except FileNotFoundError:
            raise UserError("Không tìm thấy `zbarcam`. Cài đặt bằng: sudo apt install zbar-tools")
        except Exception as e:
            raise UserError(f"Lỗi khi quét mã sách: {e}")



class ResPartner(models.Model):
    _inherit = 'res.partner'

    borrow_ids = fields.One2many('books.borrows', 'name_card_id', string='Books')
    card_no = fields.One2many('library.card','student_id', string='Library Card')    
    # library_card_code = fields.Char(related='card_no.code', string='Library Card Code')