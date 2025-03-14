# -*- coding: utf-8 -*-
from datetime import timedelta, datetime, date
from odoo import models, fields, api , _
from odoo.exceptions import ValidationError as UserError
import cv2
import re
from pyzbar.pyzbar import decode
from datetime import datetime
from dateutil.relativedelta import relativedelta as rd


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

    name = fields.Many2one('res.partner', string="Name")
    code = fields.Many2one('library.card', string='Thẻ Bạn Đọc')
    name_library_card = fields.Char(related='code.name_borrower', redonly = True, string = "Tên Bạn Đọc",size=250)
    name_card = fields.Many2one('res.partner', related='code.student_id', string="Tên Bạn Đọc")
    id_student = fields.Char(string="Mã Sinh Viên", size=256, related='code.id_student',readonly=True)


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
    delay_penalties = fields.Many2one('delay.penalities', string="Phạt Trì Hoãn")
    borrows_duration = fields.Float(string="Thời Hạn Mượn", default = 6)
    
    book_copy_list = fields.Many2many('book.copies')
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

                    
                # Sử dụng regex để trích xuất số từ dòng có tên là "QR Code:"
                # match = re.search(r'QR Code: (\d+)', qr_data)
                # Giải phóng camera và đóng cửa sổ hiển thị
                cap.release()
                cv2.destroyAllWindows()

                # Kết thúc chương trình sau khi quét được mã QR
                return
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
    @api.onchange('book_copy_list')
    def _onchange_book_copy_list(self):
        if self.book_copy_list:
            for book in self.book_copy_list:
                if book.state == 'borrowed':
                    raise UserError(f'Trạng thái của sách {book.book_id.name} - {book.DK_CB} đã được mượn.')
            self.state = 'running'
            for book in self.book_copy_list:
                book.state = 'borrowed'
        else:
            self.state = 'draft'
            
    

  
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
        self.state = 'ended'
        for record in self:
            for book in record.book_copy_list:
                book.state = 'available'
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

    """ Scan name student """
    def action_scan_name_student(self, vals):
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
                # match = re.search(r'Id Student: (\d+)', qr_data)
                # if match:
                #     qr_code_name = int(match.group(1))
                match = re.search(r'Student Card: (.+)', qr_data)
                if match:
                    qr_code_content = match.group(1).strip()                
                    print(f'Library Card of Student: {qr_code_content}')

                    # qr_code = qr_code_number()  # Assume this function returns the scanned QR code

                    # Find the book with the scanned QR code
                    name_borrower = self.env['library.card'].search([('code', '=', qr_code_content)])

                    # If book is found, fill the qbook_id field
                    if name_borrower:
                        self.code = name_borrower.id
                        print()
                    else:
                        # Handle case when book is not found
                        pass
                # Sử dụng regex để trích xuất số từ dòng có tên là "QR Code:"
                # match = re.search(r'QR Code: (\d+)', qr_data)
                # Giải phóng camera và đóng cửa sổ hiển thị
                cap.release()
                cv2.destroyAllWindows()

                # Kết thúc chương trình sau khi quét được mã QR
                return

            # Kiểm tra phím nhấn để thoát (ví dụ: nhấn phím 'q')
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        # Giải phóng camera và đóng cửa sổ hiển thị khi thoát vòng lặp
        cap.release()
        cv2.destroyAllWindows()

    """ Scan barcode student """
    def action_barcode_name_student(self, vals):
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

            # Quét mã Barcode
            decoded_objects = decode(frame)
            for obj in decoded_objects:
                barcode_data = obj.data.decode('utf-8')
                
                print(f'Mã Barcode đã quét: \n{barcode_data}')
                match = re.search(r'(\d+)', barcode_data)
                if match:
                    barcode_name = int(match.group(1))
                    print(f'ID Student Barcode: {barcode_name}')

                    # Find the student with the scanned Barcode
                    student = self.env['res.partner'].search([('id_student', '=', barcode_name)],limit = 1)

                    # If student is found, fill the student_id field
                    if student:
                        self.name = student.id
                        self.code = self.env['library.card'].search([('student_id', '=', student.id)], limit=1).id
                        print(f'Student ID: {self.name_card}')
                    else:
                        # Handle case when student is not found
                        print('Student not found.')
                        pass

                    # Giải phóng camera và đóng cửa sổ hiển thị
                    cap.release()
                    cv2.destroyAllWindows()

                    # Kết thúc chương trình sau khi quét được mã Barcode
                    return

            # Kiểm tra phím nhấn để thoát (ví dụ: nhấn phím 'q')
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        # Giải phóng camera và đóng cửa sổ hiển thị khi thoát vòng lặp
        cap.release()
        cv2.destroyAllWindows()



    def action_scan_qr(self, vals):
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
                
                match = re.search(r'(.+)', qr_data)
                if match:
                    qr_code_number = match.group(1).strip() 


                    print(f'ID QR Code: {qr_code_number}')

                    # qr_code = qr_code_number()  # Assume this function returns the scanned QR code

                    # Find the book with the scanned QR code
                    book = self.env['books.data'].search([('dkcd', '=', qr_code_number)])

                    # If book is found, fill the qbook_id field
                    if book:
                        self.book_id = book.id
                        self.borrow_ids = [(4, book.id)]
                        if book.state == 'borrowed':
                            raise UserError('This book is already borrowed.')
                        book.state = 'available'
                    
                    else:
                        # Handle case when book is not found
                        pass
                # Sử dụng regex để trích xuất số từ dòng có tên là "QR Code:"
                # match = re.search(r'QR Code: (\d+)', qr_data)
                # Giải phóng camera và đóng cửa sổ hiển thị
                cap.release()
                cv2.destroyAllWindows()

                # Kết thúc chương trình sau khi quét được mã QR
                return

            # Kiểm tra phím nhấn để thoát (ví dụ: nhấn phím 'q')
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        # Giải phóng camera và đóng cửa sổ hiển thị khi thoát vòng lặp
        cap.release()
        cv2.destroyAllWindows()


class ResPartner(models.Model):
    _inherit = 'res.partner'

    borrow_ids = fields.One2many('books.borrows', 'name_card', string='Books')
    card_no = fields.One2many('library.card','student_id', string='Library Card')    
    # library_card_code = fields.Char(related='card_no.code', string='Library Card Code')


# class Resuser(models.Model):
#     _inherit = 'res.users'

#     id = fields.Many2one()
#     # library_card_code = fields.Char(related='card_no.code', string='Library Card Code')