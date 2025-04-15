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
        print("library_card", library_card) 
        print("library_card code code", library_card.code)
        borrows_list = []
        if library_card:
            borrows_list = request.env['books.borrows'].sudo().search([('code_id', '=', library_card.code)])
        print("library_card email", request.env.user.email)
        print("library_card", library_card.code)
        print("borrows_list", borrows_list)
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

