# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class ResConfigSettings(models.TransientModel):
    '''
    to inherit setting odoo to add field message to apper in warning report
    '''
    _inherit = 'res.config.settings'

    message = fields.Text(string="Message")

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param("nthub_library.message",
                                                         self.message)

    @api.model
    def get_values(self):
        #
        res = super(ResConfigSettings, self).get_values()
        get_param = self.env['ir.config_parameter'].sudo().get_param
        res['message'] = get_param('nthub_library.message')
        return res


