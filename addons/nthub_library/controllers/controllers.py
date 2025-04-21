#-*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from datetime import timedelta, datetime, date


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
        print("order", order)
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
        print("kwargs", kwargs)
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
        print("kwargs", kwargs)

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
            print("block", block)
            print("copy_ids", copy_ids)
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
        print("paper", paper)        
        return request.render('nthub_library.book_data_fl_category', {
            'books_data': books_with_borrowed_count, 
            'pager': paper,
        })

