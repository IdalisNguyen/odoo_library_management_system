#-*- coding: utf-8 -*-
from odoo import http, _
from odoo.http import content_disposition, request
from odoo.tools import ustr, osutil
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from datetime import timedelta, datetime, date
import io
import json
import xlsxwriter
from collections import deque
import base64

class Borrows(CustomerPortal):
    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if 'borrow_count' in counters:
            borrow_count = request.env['books.borrows'].search_count([])
            values['borrow_count'] = borrow_count
        return values

    @http.route('/my/home/borrows_list_details', type="http", auth='public', website=True)
    def get_borrows(self, **kw):
        library_card = request.env['library.card'].sudo().search([('email', '=', request.env.user.email)], limit=1)
        borrows_list = []
        if library_card:
            borrows_list = request.env['books.borrows'].sudo().search([('code_id', '=', library_card.code), ('state', '=', 'running')])
            ended_list = request.env['books.borrows'].sudo().search([('code_id', '=', library_card.code), ('state', '=', 'ended')])
            reserve_list = request.env['books.borrows'].sudo().search([('code_id', '=', library_card.code), ('state', '=', 'reserve')])
        vals = {
            'borrows_list': borrows_list,
            'ended_list': ended_list,
            'reserve_list': reserve_list,
        }    

        return request.render('nthub_library.borrows_list_page', vals
                              , {'page_name': 'borrow_list'})




    @http.route(['/desired_borrower/<int:order_id>'], type="http", website=True, auth='public')
    def get_borrower_form(self, order_id, **kw):
        order = request.env['books.borrows'].sudo().browse(order_id)
        vals = {"order": order}
        return request.render('nthub_library.borrower_detail_form_shown_link', vals, {'page_name': 'desired_borrower'})



    # @http.route('/my/borrows_form', type="http", auth='public', website=True, csrf=True)
    # def borrowing_form_view(self, **kwargs):
    #     names = request.env['res.partner'].sudo().search([])
    #     book_ids = request.env['books.data'].sudo().search([])
    #     vals = {
    #         'borrowers': names,
    #         'books': book_ids,
    #         'page_name': 'borrow_form'
    #     }
    #     return request.render('nthub_library.borrowers_form',
    #                           vals)

    @http.route('/my/borrower/create', type="http", auth='public', website=True, csrf=True)
    def request_submit(self, **kwargs):
        request.env['books.borrows'].sudo().create(kwargs)
        response = http.request.render('nthub_library.create_borrowing_done'
                                       , {'page_name': 'borrowing_created'})
        return response
    
    # @http.route('/reserve-book/detail', type='http', auth='public', website=True)
    @http.route('/reserve-book/detail', type='http', auth='public', website=True, csrf=True)
    def reserve_book_details(self, **kw):
        
        book_id = int(kw.get('id', 0))
        reserve_book = request.env['books.data'].sudo().browse(book_id)
        list_book_copy = request.env['book.copies'].sudo().search([('book_id', '=', book_id), ('state', '=', 'available')])
        day_reserve = date.today()
        day_cancel = (date.today() + timedelta(days=3))
        current_user = request.env.user.name  
        email_user = request.env.user.email  
        vals = {
            'reserve_book': reserve_book,
            'list_book_copy': list_book_copy,
            'day_reserve': day_reserve,
            'day_cancel': day_cancel,
            'email_user': email_user,  
            'current_user': current_user,  
        }

        return request.render('nthub_library.reserve_book', vals)
       

    @http.route('/reserve/create/', type="http", auth='public', website=True, csrf=True)
    def test(self, **kwargs):

        book_copy_id = kwargs.get('book_copy')
        date_reserve = kwargs.get('date_reserve')
        date_cancel = kwargs.get('date_cancel')
        email = kwargs.get('email_from')

        # Optional: validation or lookup
        book_copy = request.env['book.copies'].sudo().browse(int(book_copy_id))
        library_card = request.env['library.card'].sudo().search([('email', '=', email)], limit=1)
        
        # Ensure book_copy_list_ids is a list of IDs
        borrow_record = request.env['books.borrows'].sudo().create({
            'code_id': library_card.id,
            'book_copy_list_ids': [(6, 0, [book_copy.id])],
            'reserve_date': date_reserve,
            'cancel_reserve': date_cancel,
        })
        borrow_record.write({'state': 'reserve',})
        book_copy.write({'state': 'reserve'})

        return request.redirect('/reserve-success')




class LibraryController(http.Controller):


    @http.route('/', type='http', auth='public', website=True)
    def library_home(self, **kw):
        return request.render('nthub_library.home_website')

    @http.route('/category', type='http', auth='public', website=True)
    def library_category(self, **kw):
        categories = request.env['books.category'].sudo().search([])
        return request.render('nthub_library.library_home_category', {
            'categories': categories,
        })
        
            
    @http.route('/books-data', type='http', auth='public', website=True)
    def library_book_data(self, search='', page=1, **kw):
        books = request.env['books.data'].sudo()
        page = int(page) if page else 1
        per_page = 8
        offset = (page - 1) * per_page
        if search:
            total_books = books.search_count([('name', 'ilike', search)])
            books_data = books.search([('name', 'ilike', search)], limit=per_page, offset=offset)
            url = f'/books-data?search={search}'
        else:
            total_books = books.search_count([])
            books_data = books.search([], limit=per_page, offset=offset)
            url = '/books-data'
        books_with_borrowed_count = []
        for book in books_data:
            copy_ids = request.env['book.copies'].sudo().search_count([('book_id', '=', book.id)])
            borrowed_count = request.env['book.copies'].sudo().search_count([('state', '=', 'borrowed'), ('book_id', '=', book.id)])
            book_reserved = request.env['book.copies'].sudo().search_count([('state', '=', 'reserve'), ('book_id', '=', book.id)])
            block = borrowed_count + book_reserved

            books_with_borrowed_count.append({
                'book': book,
                'copy_ids': copy_ids,
                'borrowed_count': borrowed_count,
                'book_reserved': book_reserved,
                'block': block,
                'has_file': bool(book.copy_ids.filtered(lambda c: c.file_download)),
                'first_file_copy': book.copy_ids.filtered(lambda c: c.file_download)[:1],  # lấy bản đầu tiên có file
       
            })
            
        paper = portal_pager(
            url=url,
            total=total_books,
            page=page,
            step=per_page,
            scope=5,
        )
        return request.render('nthub_library.library_books_data', {
            'books_data': books_with_borrowed_count,
            'pager': paper,
        })
    
    @http.route(['/category=<int:category_id>/book'], type="http", website=True, auth='public')
    def get_book_data_by_category(self, category_id, page=1, **kw):
        books = request.env['books.data'].sudo()
        page = int(page) if page else 1        
        per_page = 8
        offset = (page - 1) * per_page
        total = books.search_count([('category_ids', '=', category_id)])
        book_data = books.search([('category_ids', '=', category_id)], limit=per_page, offset=offset)
        books_with_borrowed_count = []
        for book in book_data:
            copy_ids = request.env['book.copies'].sudo().search_count([('book_id', '=', book.id)])
            borrowed_count = request.env['book.copies'].sudo().search_count([('state', '=', 'borrowed'), ('book_id', '=', book.id)])
            books_with_borrowed_count.append({
                'book': book,
                'copy_ids': copy_ids,
                'borrowed_count': borrowed_count
            })
        paper = portal_pager(
            url=f'/category={category_id}/book',
            total=total,
            page=page,
            step=per_page,
            scope=5,
        )
        return request.render('nthub_library.book_data_fl_category', {
            'books_data': books_with_borrowed_count, 
            'pager': paper,
        })


class CustomBorrowReportController(http.Controller):

    @http.route('/nthub_library/custom_borrow_report_xlsx', type='http', auth='user')
    def download_custom_borrow_report(self, data, **kw):
        jdata = json.loads(data)
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet(jdata['title'])

        header_bold = workbook.add_format({'bold': True,  'bg_color': '#ffffff'})
        header_plain = workbook.add_format({ 'bg_color': '#ffffff'})
        common_format = {
            'font_name': 'Times New Roman',
            'font_size': 12,
            'align': 'center',
            'valign': 'vcenter',
        }
        common_bold_format = common_format.copy()
        common_bold_format.update({'bold': True})

        format_heading = workbook.add_format({**common_bold_format, 'font_size': 14})
        format_heading_underline = workbook.add_format({**common_bold_format, 'font_size': 14, 'underline': True})
        format_topic = workbook.add_format({**common_bold_format, 'font_size': 16})
        format_italic = workbook.add_format({**common_format, 'italic': True})
        format_datetime = workbook.add_format({'align': 'right',  'font_name': 'Times New Roman','italic': True})
        
        bold = workbook.add_format({'bold': True})

        format_table = workbook.add_format({**common_bold_format})


        measure_count = jdata['measure_count']
        origin_count = jdata['origin_count']

        # Step 1: writing col group headers
        col_group_headers = jdata['col_group_headers']
        worksheet.set_column('A1:C1', 15)
        worksheet.set_column('E1:G1', 15)
        worksheet.set_column('C:E', 22)

        worksheet.merge_range('A1:C1', 'TRƯỜNG ĐẠI HỌC TÂY NGUYÊN ', format_heading)
        worksheet.merge_range('E1:G1', 'CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM', format_heading)
        worksheet.merge_range('E2:G2', 'Độc lập - Tự do - Hạnh phúc', format_heading_underline)
        worksheet.merge_range('E3:G3', 'Đắk Lắk, ngày …  tháng … năm 20…', format_datetime)
        
        
        worksheet.merge_range('C4:E4', 'BÁO CÁO THỐNG KÊ KẾT QUẢ PHỤC VỤ NĂM …..', format_topic)
        worksheet.merge_range('C5:E5', '(Từ ngày ….. đến ngày ….)', format_italic)
        measure_headers = jdata['measure_headers']
        origin_headers = jdata['origin_headers']
        

        # x,y: current coordinates
        # carry: queue containing cell information when a cell has a >= 2 height
        #      and the drawing code needs to add empty cells below
        start_row = 6  # B7 tương đương hàng thứ 7 (0-indexed: 6)
        start_col = 2  # B là cột thứ 2 (0-indexed: 1)

        # Step 1: Write col_group_headers
        carry = deque()
        current_row = start_row
        for i, header_row in enumerate(col_group_headers):
            worksheet.write(current_row, start_col - 1, '', bold)
            current_col = start_col
            for header in header_row:
                while carry and carry[0]['x'] == current_col:
                    cell = carry.popleft()
                    for j in range(measure_count * (2 * origin_count - 1)):
                        worksheet.write(current_row, current_col + j, '', bold)
                    if cell['height'] > 1:
                        carry.append({'x': current_col, 'height': cell['height'] - 1})
                    current_col += measure_count * (2 * origin_count - 1)
                for j in range(header['width']):
                    worksheet.write(current_row, current_col + j, header['title'] if j == 0 else '', bold)
                if header['height'] > 1:
                    carry.append({'x': current_col, 'height': header['height'] - 1})
                current_col += header['width']
            while carry and carry[0]['x'] == current_col:
                cell = carry.popleft()
                for j in range(measure_count * (2 * origin_count - 1)):
                    worksheet.write(current_row, current_col + j, '', bold)
                if cell['height'] > 1:
                    carry.append({'x': current_col, 'height': cell['height'] - 1})
                current_col += measure_count * (2 * origin_count - 1)
            current_row += 1

        # Step 2: Write measure_headers
        if measure_headers:
            worksheet.write(current_row, start_col - 1, '', bold)
            current_col = start_col
            for measure in measure_headers:
                style =  bold
                worksheet.write(current_row, current_col, measure['title'], style)
                for i in range(1, 2 * origin_count - 1):
                    worksheet.write(current_row, current_col + i, '', bold)
                current_col += (2 * origin_count - 1)
            worksheet.set_column(0, len(measure_headers) + start_col, 16)
            current_row += 1

        # Step 3: Write origin_headers
        if origin_headers:
            worksheet.write(current_row, start_col - 1, '', bold)
            current_col = start_col
            for origin in origin_headers:
                style =  bold
                worksheet.write(current_row, current_col, origin['title'], style)
                current_col += 1
            current_row += 1

        # Step 4: Write data rows
        for row in jdata['rows']:
            current_col = start_col - 1
            worksheet.write(current_row, current_col, row['indent'] * '     ' + ustr(row['title']), format_table)
            for cell in row['values']:
                current_col += 1
                if cell.get('is_bold', False):
                    worksheet.write(current_row, current_col, cell['value'], format_table)
                else:
                    worksheet.write(current_row, current_col, cell['value'])
            current_row += 1

        workbook.close()
        xlsx_data = output.getvalue()
        filename = osutil.clean_filename(_("Pivot %(title)s (%(model_name)s)", title=jdata['title'], model_name=jdata['model']))
        response = request.make_response(xlsx_data,
            headers=[('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
                    ('Content-Disposition', content_disposition(filename + '.xlsx'))],
        )

        return response
    
    
class LibraryPDFPreviewController(http.Controller):

    @http.route('/library/endogenous_document/pdf/<int:copy_id>', type='http', auth='public', website=True)
    def preview_pdf(self, copy_id):
        copy = request.env['book.copies'].sudo().browse(copy_id)
        if not copy.exists() or not copy.file_download:
            return request.not_found()
        
        return request.make_response(
            base64.b64decode(copy.file_download),
            headers=[
                ('Content-Type', 'application/pdf'),
                ('Content-Disposition', f'inline; filename="{copy.DK_CB or 'preview'}.pdf"'),
            ]
        )