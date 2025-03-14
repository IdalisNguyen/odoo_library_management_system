# import datetime
# import calendar
# from odoo import models, fields, api
# from odoo.tools import date_utils
# from odoo.http import request
# from dateutil.relativedelta import relativedelta
# from datetime import datetime
#
#
#
#
# class dashboard(models.Model):
#     _inherit = 'books.borrows'
#
#
#
#     @api.model
#     def get_main_data(self):
#         all_borrows = self.env['books.borrows'].search([('state', '=', 'running'), ('state', '=', 'delayed')])
#         return {
#             'total_individual': len(all_borrows),
#         }
#
#     @api.model
#     def get_filter_data(self, text_value):
#         # all_borrows
#         all_borrows = self.env['books.borrows'].search(
#             [('state', '=', 'running'), ('partner_id.name', 'ilike', text_value)])
#         return {
#             'total_borrows': len(all_borrows)
#         }










