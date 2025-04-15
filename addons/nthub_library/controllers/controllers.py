#-*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal


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
            borrows_list = request.env['books.borrows'].sudo().search([('code_id', '=', library_card.code)])
        return request.render('nthub_library.borrows_list_page', {'my_details': borrows_list}
                              , {'page_name': 'borrow_list'})




    @http.route(['/desired_borrower/<int:order_id>'], type="http", website=True, auth='public')
    def get_borrower_form(self, order_id, **kw):
        order = request.env['books.borrows'].sudo().browse(order_id)
        vals = {"order": order}
        print("order", order)
        return request.render('nthub_library.borrower_detail_form_shown_link', vals, {'page_name': 'desired_borrower'})



    @http.route('/my/borrows_form', type="http", auth='public', website=True, csrf=True)
    def borrowing_form_view(self, **kwargs):
        names = request.env['res.partner'].sudo().search([])
        book_ids = request.env['books.data'].sudo().search([])
        vals = {
            'borrowers': names,
            'books': book_ids,
            'page_name': 'borrow_form'
        }
        return request.render('nthub_library.borrowers_form',
                              vals)

    @http.route('/my/borrower/create', type="http", auth='public', website=True, csrf=True)
    def request_submit(self, **kwargs):
        request.env['books.borrows'].sudo().create(kwargs)
        response = http.request.render('nthub_library.create_borrowing_done'
                                       , {'page_name': 'borrowing_created'})
        return response



class LibraryController(http.Controller):

    @http.route('/category', type='http', auth='public', website=True)
    def library_category(self, **kw):
        categories = request.env['books.category'].sudo().search([])
        return request.render('nthub_library.library_home_category', {
            'categories': categories,
        })
        
        
    @http.route('/books-data', type='http', auth='public', website=True)
    def library_book_data(self, **kw):
        books_data = request.env['books.data'].sudo().search([])
        books_with_borrowed_count = []
        for book in books_data:
            copy_ids = request.env['book.copies'].sudo().search_count([('book_id', '=', book.id)])
            borrowed_count = request.env['book.copies'].sudo().search_count([('state', '=', 'borrowed'), ('book_id', '=', book.id)])
            books_with_borrowed_count.append({
                'book': book,
                'copy_ids': copy_ids,
                'borrowed_count': borrowed_count
            })
        return request.render('nthub_library.library_books_data', {
            'books_data': books_with_borrowed_count
        })
        
    @http.route(['/category=<int:category_id>/book'], type="http", website=True, auth='public')
    def get_book_data_by_category(self, category_id, **kw):
        books = request.env['books.data'].sudo().search([('category_ids', '=', category_id)])
        books_with_borrowed_count = []
        for book in books:
            copy_ids = request.env['book.copies'].sudo().search_count([('book_id', '=', book.id)])
            borrowed_count = request.env['book.copies'].sudo().search_count([('state', '=', 'borrowed'), ('book_id', '=', book.id)])
            books_with_borrowed_count.append({
                'book': book,
                'copy_ids': copy_ids,
                'borrowed_count': borrowed_count
            })
        return request.render('nthub_library.book_data_fl_category', {
            'books_data': books_with_borrowed_count
        })
