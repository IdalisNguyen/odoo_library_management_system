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
                'block': block
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
    # def download_custom_borrow_report(self, model=None, domain=None, context=None, groupedBy=None, **kwargs):
    def download_custom_borrow_report(self, data, **kw):
        jdata = json.loads(data)
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet(jdata['title'])

        header_bold = workbook.add_format({'bold': True, 'pattern': 1, 'bg_color': '#AAAAAA'})
        header_plain = workbook.add_format({'pattern': 1, 'bg_color': '#AAAAAA'})
        common_format = {
            'font_name': 'Times New Roman',
            'font_size': 12,
            'align': 'center',
            'valign': 'vcenter',
        }
        common_bold_format = common_format.copy()
        common_bold_format.update({'bold': True})

        format_heading = workbook.add_format({**common_bold_format, 'font_size': 14})

        bold = workbook.add_format({'bold': True})

        measure_count = jdata['measure_count']
        origin_count = jdata['origin_count']

        # Step 1: writing col group headers
        col_group_headers = jdata['col_group_headers']
        
        worksheet.merge_range('A1:C1', 'TRƯỜNG ĐẠI HỌC TÂY NGUYÊN ', format_heading)
        worksheet.merge_range('E1:G1', 'CỘNG HÒA XÃHỘI CHỦNGHĨA VIỆT NAM ', format_heading)

        # x,y: current coordinates
        # carry: queue containing cell information when a cell has a >= 2 height
        #      and the drawing code needs to add empty cells below
        x, y, carry = 1, 0, deque()
        for i, header_row in enumerate(col_group_headers):
            worksheet.write(i, 0, '', header_plain)
            for header in header_row:
                while (carry and carry[0]['x'] == x):
                    cell = carry.popleft()
                    for j in range(measure_count * (2 * origin_count - 1)):
                        worksheet.write(y, x+j, '', header_plain)
                    if cell['height'] > 1:
                        carry.append({'x': x, 'height': cell['height'] - 1})
                    x = x + measure_count * (2 * origin_count - 1)
                for j in range(header['width']):
                    worksheet.write(y, x + j, header['title'] if j == 0 else '', header_plain)
                if header['height'] > 1:
                    carry.append({'x': x, 'height': header['height'] - 1})
                x = x + header['width']
            while (carry and carry[0]['x'] == x):
                cell = carry.popleft()
                for j in range(measure_count * (2 * origin_count - 1)):
                    worksheet.write(y, x+j, '', header_plain)
                if cell['height'] > 1:
                    carry.append({'x': x, 'height': cell['height'] - 1})
                x = x + measure_count * (2 * origin_count - 1)
            x, y = 1, y + 1

        # Step 2: writing measure headers
        measure_headers = jdata['measure_headers']

        if measure_headers:
            worksheet.write(y, 0, '', header_plain)
            for measure in measure_headers:
                style = header_bold if measure['is_bold'] else header_plain
                worksheet.write(y, x, measure['title'], style)
                for i in range(1, 2 * origin_count - 1):
                    worksheet.write(y, x+i, '', header_plain)
                x = x + (2 * origin_count - 1)
            x, y = 1, y + 1
            # set minimum width of cells to 16 which is around 88px
            worksheet.set_column(0, len(measure_headers), 16)

        # Step 3: writing origin headers
        origin_headers = jdata['origin_headers']

        if origin_headers:
            worksheet.write(y, 0, '', header_plain)
            for origin in origin_headers:
                style = header_bold if origin['is_bold'] else header_plain
                worksheet.write(y, x, origin['title'], style)
                x = x + 1
            y = y + 1

        # Step 4: writing data
        x = 0
        for row in jdata['rows']:
            worksheet.write(y, x, row['indent'] * '     ' + ustr(row['title']), header_plain)
            for cell in row['values']:
                x = x + 1
                if cell.get('is_bold', False):
                    worksheet.write(y, x, cell['value'], bold)
                else:
                    worksheet.write(y, x, cell['value'])
            x, y = 0, y + 1

        workbook.close()
        xlsx_data = output.getvalue()
        filename = osutil.clean_filename(_("Pivot %(title)s (%(model_name)s)", title=jdata['title'], model_name=jdata['model']))
        response = request.make_response(xlsx_data,
            headers=[('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
                    ('Content-Disposition', content_disposition(filename + '.xlsx'))],
        )

        return response