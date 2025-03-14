# -*- coding: utf-8 -*-
from datetime import date
from odoo import models, fields, api
'''
The Publisher class represents a model in an object-relational mapping (ORM) framework, such as Odoo or Django. 
It is used to store information about book publishers.
The _name attribute is set to 'book.publisher', which determines the internal name of the model.
 This name will be used to identify the table or collection in the database associated with this model.
The _description attribute provides a brief description of the model. In this case, it is set to 'books.publisher', 
but you can replace it with a more appropriate description.
The name field is of type Char and represents the name of the book publisher. It has the attribute string="Name Book",
 which sets the label displayed for this field on the user interface. Additionally, 
tracking=True enables change tracking for this field, allowing you to keep a history of changes made to it.
'''

class Publisher(models.Model):
    _name = 'book.publisher'
    _description = 'books.publisher'

    name = fields.Char(string="Name Book")
    id = fields.Integer(string="Id")
    email = fields.Char(string='Email', size=256)
    phone_number = fields.Char(string='Phone Number', size=20)
    date_publisher = fields.Date(string="Date Of Publisher")
    count_books = fields.Integer(string="Count Of Books")
    state = fields.Selection([('draft', 'Draft'),
                              ('in_consulation', 'In Consulation'),
                              ('done', 'Done'),
                              ('cancel', 'Cancelled')], default="draft", string='state', required=True)



    def action_in_consultation(self):
        '''
         Method that transitions the state of the publisher to 'done'.
         This method is triggered when the action associated with transitioning to the 'done' state is performed.
        '''
        for rec in self:
            rec.state = 'done'

    def action_done(self):
        '''
        Method that transitions the state of the publisher to 'in_consulation'.
        This method is triggered when the action associated with transitioning to the 'in_consulation' state is performed.
        '''
        for rec in self:
            rec.state = 'in_consulation'

    def action_cancel(self):
        '''
        Method that transitions the state of the publisher to 'done'.
         This method is triggered when the action associated with transitioning to the 'done' state is performed.
        '''
        for rec in self:
            rec.state = 'done'

    def action_draft(self):
        '''
        Method that transitions the state of the publisher to 'cancel'.
        This method is triggered when the action associated with transitioning to the 'cancel' state is performed.
        '''
        for rec in self:
            rec.state = 'cancel'


