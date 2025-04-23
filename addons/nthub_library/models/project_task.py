from odoo import models, fields, api

class ProjectTask(models.Model):
    _inherit = 'project.task'

    state_library = fields.Selection([
        ('draft', 'BẢN THẢO'),
        ('through', 'THÔNG QUA'),
        ('progress', 'TIẾN HÀNH'),
        ('done', 'HOÀN THÀNH'),
        ('cancel', 'HỦY'),
    ], string='State', default='draft',tracking=True)
    
    def action_draft(self):
        self.state_library = 'draft'    
    def action_through(self):
        self.state_library = 'through'
    def action_progress(self):
        self.state_library = 'progress'
    def action_done(self):
        self.state_library = 'done'
    def action_cancel(self):
        self.state_library = 'cancel'