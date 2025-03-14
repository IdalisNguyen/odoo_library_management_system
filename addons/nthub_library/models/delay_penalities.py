# -*- coding: utf-8 -*-
from datetime import timedelta
from odoo import models, fields, api


class delay_penalities(models.Model):
    '''
    this class penalities borwwers content name and description
    '''
    _name = 'delay.penalities'
    _description = 'delay penalities'

    name = fields.Char(string="Title")
    description = fields.Text()
